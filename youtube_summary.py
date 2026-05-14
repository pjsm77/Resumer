import os
import time
import datetime
import feedparser
import warnings
from googleapiclient.discovery import build
from google import genai
from telebot import TeleBot

# Silenciar avisos irrelevantes
warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO E EXECUÇÃO ---")

# --- CONFIGURAÇÃO DE AMBIENTE ---
try:
    YOUTUBE_KEY = os.environ.get('YOUTUBE_API_KEY')
    GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # CONFIGURAÇÃO VITAL: Forçamos a versão 'v1' para evitar o erro 404 Not Found
    client = genai.Client(
        api_key=GEMINI_KEY,
        http_options={'api_version': 'v1'}
    )
    
    bot = TeleBot(TELEGRAM_TOKEN)
    yt_service = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    
    print("[OK] Conexão estabelecida com API v1 estável.")

except Exception as e:
    print(f"[ERRO DE CONFIGURAÇÃO]: {e}")
    exit(1)

# Lista de canais monitorados
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCyHOBY6IDZF9zOKJPou2Rgg'
]

def get_video_details(video_id):
    """Busca a descrição do vídeo para enriquecer o resumo da IA"""
    try:
        request = yt_service.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response.get('items'):
            return response['items'][0]['snippet'].get('description', '')
    except Exception as e:
        print(f"   [AVISO YOUTUBE]: {e}")
    return ""

def main():
    # Verifica vídeos das últimas 24 horas
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > time_threshold:
                try:
                    print(f"-> Processando: {entry.title}")
                    
                    description = get_video_details(entry.yt_videoid)
                    context = description if description else entry.summary

                    prompt = f"""
                    Aja como um analista de tecnologia. Resuma o vídeo: '{entry.title}'
                    Canal: {entry.author}
                    Descrição: {context[:3500]}
                    
                    Formate para Telegram (Markdown):
                    1. **Resumo**: (2 frases)
                    2. **Destaques**: (Lista de pontos)
                    3. **Conceito Técnico**: (Explicação curta de algo citado)
                    """
                    
                    # Chamada corrigida para o modelo flash na API v1
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    
                    summary = response.text
                    msg = f"📺 *{entry.title}*\n👤 {entry.author}\n\n{summary}\n\n🔗 [Assistir]({entry.link})"
                    
                    # Envio com tratamento de tamanho
                    if len(msg) > 4000:
                        bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    
                    print("   [SUCESSO] Mensagem enviada.")
                    time.sleep(5) # Delay para evitar limites de taxa
                    
                except Exception as e:
                    print(f"   [FALHA NO VÍDEO]: {e}")

if __name__ == "__main__":
    main()
    print("--- SCRIPT FINALIZADO ---")
