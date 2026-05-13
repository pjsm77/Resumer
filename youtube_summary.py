import os
import time
import datetime
import feedparser
import warnings

warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO DO SCRIPT ---")

try:
    import google.generativeai as genai
    from youtube_transcript_api import YouTubeTranscriptApi
    from telebot import TeleBot
    print("[OK] Bibliotecas carregadas.")
except Exception as e:
    print(f"[ERRO] Bibliotecas: {e}")

# LISTA ATUALIZADA: IDs internos validados que abrem no navegador
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', # bruno_faggion
    'UC3YyP79q2mO6-f1_0ZfF9OQ', # brunogabarra
    'UCmG9O80pUf2m-46e_FmP9Xg', # CanaldoEslen
    'UC70769I-5i8C1e32pA_L_yA', # canalsandeco
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', # Danilo-CM
    'UCX_Nf-M9m2K2R6D5_f_vS7A', # deborahfolloni
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', # DesfrutandoaVida (validado)
    'UCY08r_5A7mS3m6qX8-5L_6w'  # LucasMontano (validado)
]

try:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
    bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    print("[OK] APIs e Variáveis configuradas.")
except Exception as e:
    print(f"[ERRO] Configuração: {e}")

def get_deep_summary(video_id, title):
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        text = " ".join([i['text'] for i in srt])[:15000]
        
        prompt = f"Resuma o vídeo '{title}' com foco em teoria e aplicação prática. Transcrição: {text}"
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Resumo indisponível."

def main():
    # Mantendo 30 dias para garantir que o Lucas Montano (que funciona) envie algo
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    
    for channel_id in CHANNELS:
        # Link formatado sem espaços e com underline correto
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        print(f"Canal: {channel_id} | Vídeos encontrados: {len(feed.entries)}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            if published > time_threshold:
                print(f"-> Processando: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title)
                
                msg = f"📺 *{entry.title}*\n\n{summary}\n\n🔗 [Link]({entry.link})"
                
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print("   [OK] Enviado!")
                except:
                    bot.send_message(CHAT_ID, f"Vídeo: {entry.title}\n{entry.link}")
                
                time.sleep(10)

if __name__ == "__main__":
    main()
