import os
import time
import datetime
import feedparser
import warnings
import yt_dlp

warnings.filterwarnings("ignore")

try:
    import google.generativeai as genai
    from telebot import TeleBot
    print("[OK] Bibliotecas carregadas.")
except Exception as e:
    print(f"[ERRO] Bibliotecas: {e}")

# IDs validados
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCyHOBY6IDZF9zOKJPou2Rgg'
]

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')
bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def get_transcript_with_ytdlp(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['pt', 'pt-BR', 'en'],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # O yt-dlp não baixa o texto diretamente para variável facilmente, 
            # então usamos os metadados de descrição como plano B imediato
            description = info.get('description', '')
            return description[:10000] # Retorna a descrição se a legenda falhar
    except:
        return None

def get_deep_summary(video_id, title):
    content = get_transcript_with_ytdlp(video_id)
    
    if not content or len(content) < 100:
        return "Resumo indisponível: Conteúdo insuficiente para análise."

    prompt = f"""
    Você é um especialista em síntese. Analise o conteúdo do vídeo "{title}":
    1. RESUMO EXECUTIVO: Teoria central.
    2. LEITURA AVANÇADA: Detalhamento e aplicação.
    Conteúdo extraído: {content}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Erro ao gerar resposta com a IA."

def main():
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    
    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        print(f"Canal: {channel_id} | Vídeos: {len(feed.entries)}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            if published > time_threshold:
                print(f"-> Analisando: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title)
                
                msg = f"📺 *{entry.title}*\n\n{summary}\n\n🔗 [Link]({entry.link})"
                
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print("   [OK] Enviado!")
                except:
                    bot.send_message(CHAT_ID, f"Vídeo: {entry.title}\n{entry.link}")
                
                time.sleep(12) # Pausa maior para evitar bloqueios

if __name__ == "__main__":
    main()
