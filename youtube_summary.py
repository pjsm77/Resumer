import os
import time
import datetime
import feedparser
import warnings
from googleapiclient.discovery import build
from google import genai
from telebot import TeleBot

warnings.filterwarnings("ignore")

# --- CONFIGURAÇÃO ---
try:
    YOUTUBE_KEY = os.environ.get('YOUTUBE_API_KEY')
    GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    client = genai.Client(api_key=GEMINI_KEY)
    bot = TeleBot(TELEGRAM_TOKEN)
    yt_service = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    
    print("[OK] Conexão estabelecida.")

except Exception as e:
    print(f"[ERRO]: {e}")
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
            return response['items'][0]['snippet'].get('description', '')
    except:
        return ""
    return ""

def main():
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > time_threshold:
                try:
                    print(f"-> Analisando: {entry.title}")
                    desc = get_video_details(entry.yt_videoid)
                    
                    # Usando o ID exato confirmado na imagem image_9564fa.png
                    response = client.models.generate_content(
                        model="models/gemini-3-flash-preview", 
                        contents=f"Resuma este vídeo de forma concisa: {entry.title}. Contexto: {desc[:3000]}"
                    )
                    
                    summary = response.text
                    msg = f"📺 *{entry.title}*\n👤 {entry.author}\n\n{summary}\n\n🔗 [Link]({entry.link})"
                    
                    bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                    print("   [OK] Enviado para o Telegram!")
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"   [ERRO NO VÍDEO]: {e}")

if __name__ == "__main__":
    main()
