import os
import time
import datetime
import feedparser
import warnings
from googleapiclient.discovery import build

warnings.filterwarnings("ignore")

# Configuração das APIs
try:
    import google.generativeai as genai
    from telebot import TeleBot
    
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
    bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    
    # Cliente oficial do YouTube
    yt_service = build('youtube', 'v3', developerKey=os.environ['YOUTUBE_API_KEY'])
    print("[OK] APIs configuradas.")
except Exception as e:
    print(f"[ERRO] Configuração: {e}")

# Canais que você acompanha (IDs validados)
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCyHOBY6IDZF9zOKJPou2Rgg'
]

def get_video_details(video_id):
    try:
        print(f"   [API] Consultando metadados do vídeo: {video_id}")
        request = yt_service.videos().list(part="snippet", id=video_id)
        response = request.execute()
        
        if not response.get('items'):
            print(f"   [AVISO] API retornou lista vazia para o ID: {video_id}")
            return None
            
        snippet = response['items'][0]['snippet']
        return {
            "description": snippet.get('description', ''),
            "tags": ", ".join(snippet.get('tags', []))
        }
    except Exception as e:
        print(f"   [ERRO API YOUTUBE]: {e}")
        return None

def get_deep_summary(video_id, title, author):
    data = get_video_details(video_id)
    desc = data['description'] if data else ""
    tags = data['tags'] if data else ""

    # Prompt que usa metadados para construir a teoria
    prompt = f"""
    Analise o vídeo "{title}" de {author}.
    Contexto (Descrição): {desc[:4000]}
    Palavras-chave: {tags}
    
    Crie um guia técnico estruturado:
    1. RESUMO EXECUTIVO (Essência teórica da abordagem)
    2. LEITURA AVANÇADA (Aprofundamento conceitual e aplicação prática)
    
    Nota: Use o seu conhecimento sobre o estilo do autor e o tema para expandir os pontos citados na descrição.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Resumo indisponível via metadados."

def main():
    # Janela de 30 dias para o teste inicial
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        print(f"Processando canal: {channel_id}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            if published > time_threshold:
                print(f"-> Vídeo: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title, entry.author)
                
                msg = f"📺 *{entry.title}*\n👤 {entry.author}\n\n{summary}\n\n🔗 [Link]({entry.link})"
                
                try:
                    # Divisão de mensagens longas (>4096 caracteres)
                    if len(msg) > 4000:
                        bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                        bot.send_message(CHAT_ID, msg[4000:], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print("   [OK] Enviado!")
                except:
                    bot.send_message(CHAT_ID, f"Vídeo: {entry.title}\n{entry.link}")
                
                time.sleep(8) # Pausa amigável para a quota da API

if __name__ == "__main__":
    main()
