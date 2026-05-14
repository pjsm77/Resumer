import os
import time
import datetime
import feedparser
import warnings

# Silencia avisos de sistema
warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO DO SCRIPT ---")

try:
    import google.generativeai as genai
    from youtube_transcript_api import YouTubeTranscriptApi
    from telebot import TeleBot
    print("[OK] Bibliotecas carregadas.")
except Exception as e:
    print(f"[ERRO] Bibliotecas: {e}")

# LISTA DE IDs: Substitua pelos IDs internos (UC...) que você validar
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', # bruno_faggion
    'UC3YyP79q2mO6-f1_0ZfF9OQ', # brunogabarra
    'UCmG9O80pUf2m-46e_FmP9Xg', # CanaldoEslen
    'UC70769I-5i8C1e32pA_L_yA', # canalsandeco
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', # Danilo-CM
    'UCX_Nf-M9m2K2R6D5_f_vS7A', # deborahfolloni
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', # DesfrutandoaVida
    'UCyHOBY6IDZF9zOKJPou2Rgg'  # LucasMontano (ID Corrigido)
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
        # 1. Obtém a lista de todas as legendas disponíveis para o vídeo
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 2. Tenta encontrar qualquer legenda em Português (manual ou automática)
        try:
            srt = transcript_list.find_transcript(['pt', 'pt-BR']).fetch()
        except:
            # 3. Se não houver PT, busca Inglês e traduz automaticamente para PT
            srt = transcript_list.find_transcript(['en']).translate('pt').fetch()
            
        # Junta o texto e limita o tamanho para o Gemini
        text = " ".join([i['text'] for i in srt])[:15000]
        
        prompt = f"""
        Você é um especialista em síntese de conhecimento. Analise a transcrição de "{title}":
        --- 1. RESUMO EXECUTIVO ---
        - Teoria central em um parágrafo.
        --- 2. LEITURA AVANÇADA ---
        - Detalhamento e aplicação prática.
        Transcrição: {text}
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Erro no vídeo {video_id}: {e}")
        return "Resumo indisponível (Este vídeo não possui legendas ou transcrição habilitada)."

def main():
    # Janela de 30 dias para garantir que capture os vídeos do Lucas Montano no teste
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    print(f"Buscando vídeos desde: {time_threshold}")

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        print(f"Canal: {channel_id} | Vídeos no feed: {len(feed.entries)}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > time_threshold:
                print(f"-> Processando: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title)
                
                msg = (
                    f"📺 *{entry.title}*\n"
                    f"👤 Canal: {entry.author}\n\n"
                    f"{summary}\n\n"
                    f"🔗 [Link]({entry.link})"
                )
                
                try:
                    # Tenta enviar com Markdown, se falhar envia texto puro
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print("   [OK] Enviado para o Telegram!")
                except:
                    bot.send_message(CHAT_ID, f"Vídeo: {entry.title}\n{entry.link}\n\n(Erro de formatação no resumo)")
                
                # Pausa para evitar bloqueios
                time.sleep(10)

if __name__ == "__main__":
    main()
