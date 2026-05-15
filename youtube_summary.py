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
    'UCCwNmdz91xrj09WK2zL3MpA', # Bruno Faggion | https://www.youtube.com/@bruno_faggion
    'UC8sEDBcXsQdOOT52NuKvm_A', # Bruno Gabarra | https://www.youtube.com/@brunogabarra
    'UCwOxBQR9QK24qk6XM5jeGgA', # Eslen Delanogare (Canal do Eslen) | https://www.youtube.com/@CanaldoEslen
    'UCIQne9yW4TvCCNYQLszfXCQ', # Sandeco (Canal Sandeco) | https://www.youtube.com/@canalsandeco
    'UCn5EO29OZpqazhaYuox-ieA', # Danilo-CM | https://www.youtube.com/@Danilo-CM
    'UCta1sF9e9YzzNG4OlQgIlXw', # Deborah Folloni | https://www.youtube.com/@deborahfolloni
    'UC-bvuG8yEG1SEPYLzABkvlA', # Desfrutando a Vida | https://www.youtube.com/@DesfrutandoaVida
    'UCyHOBY6IDZF9zOKJPou2Rgg', # Lucas Montano | https://www.youtube.com/@LucasMontano
    'UC4ZVkG3RQPzvZk7alIVjcCg', # The Mit Monk | https://www.youtube.com/@themitmonk
    'UCTRSsrDFesxZnUPS6AaQSJg', # Onde Estiver o Grêmio TV | https://www.youtube.com/@oegtv-ondeestiverogremio7116
    'UC5fI3kxC-ewZ6ZXEYgznM7g', # Codie Sanchez | https://www.youtube.com/@codiesanchezct
    'UC3cguahrF3GVOrAHhfKn08g', # Resumindo Conhecimento | https://www.youtube.com/@resumindoconhecimento
    'UCaahmXNbcyTFsJDH3f-bxvg', # Silvia Machado Finanças | https://www.youtube.com/@silviamachadofinancas
    'UCyTpvFRG2v9kuzJZwUZ8M2Q', # Rascunhos Econômicos | https://www.youtube.com/@rascunhoseconomicos
    'UCkJ8uPxz6UvoI6ihgQJZnww', # DW Brasil | https://www.youtube.com/@dwbrasil
    'UCF4UF3ucpJtmfWrEyJDVUlg'  # Kim Foster MD | https://www.youtube.com/@kimfostermd
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
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=10)

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
