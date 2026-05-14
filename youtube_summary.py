import os
import time
import datetime
import feedparser
import warnings
from googleapiclient.discovery import build
from google import genai
from telebot import TeleBot

warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO DO SCRIPT ---")

# Inicialização de variáveis
yt_service = None
client = None

try:
    # Captura das Secrets
    youtube_key = os.environ.get('YOUTUBE_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    telegram_token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # Configuração do novo cliente Gemini
    client = genai.Client(api_key=gemini_key)
    
    # Configuração Telegram
    bot = TeleBot(telegram_token)
    CHAT_ID = chat_id
    
    # Cliente YouTube
    yt_service = build('youtube', 'v3', developerKey=youtube_key)
    print("[OK] APIs e novo cliente Gemini configurados.")

except Exception as e:
    print(f"[ERRO CRÍTICO]: {e}")
    exit(1)

CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCyHOBY6IDZF9zOKJPou2Rgg'
]

def get_video_details(video_id):
    try:
        request = yt_service.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response.get('items'):
            snippet = response['items'][0]['snippet']
            return {
                "description": snippet.get('description', ''),
                "tags": ", ".join(snippet.get('tags', []))
            }
    except Exception as e:
        print(f"   [API YOUTUBE ERRO]: {e}")
    return None

def main():
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        print(f"Canal: {channel_id} | Feed OK")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            if published > time_threshold:
                try:
                    print(f"-> Processando: {entry.title}")
                    data = get_video_details(entry.yt_videoid)
                    
                    desc = data['description'] if data else "Sem descrição disponível."
                    tags = data['tags'] if data else ""

                    prompt = f"""
                    Analise o vídeo '{entry.title}' de {entry.author}. 
                    Descrição técnica: {desc[:4000]}
                    
                    Gere um Resumo Executivo e Leitura Avançada com foco em teoria e aplicação prática.
                    """
                    
                    # Chamada para a nova biblioteca google-genai
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    
                    summary = response.text
                    msg = f"📺 *{entry.title}*\n👤 {entry.author}\n\n{summary}\n\n🔗 [Link]({entry.link})"
                    
                    if len(msg) > 4000:
                        bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    
                    print("   [OK] Enviado!")
                    time.sleep(10)
                except Exception as e:
                    print(f"   [ERRO NO VÍDEO]: {e}")

if __name__ == "__main__":
    main()
