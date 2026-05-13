import os
import time
import datetime
import feedparser
import warnings

# Silencia avisos de depreciação do sistema para limpar o log
warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO DO SCRIPT ---")

try:
    import google.generativeai as genai
    from youtube_transcript_api import YouTubeTranscriptApi
    from telebot import TeleBot
    print("[OK] Bibliotecas carregadas com sucesso.")
except Exception as e:
    print(f"[ERRO] Falha ao carregar bibliotecas: {e}")

# Lista de IDs dos canais
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCY08r_5A7mS3m6qX8-5L_6w'
]

# Configuração de chaves
try:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
    bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    print("[OK] Chaves de API configuradas.")
except Exception as e:
    print(f"[ERRO] Falha nas variáveis de ambiente: {e}")

def get_deep_summary(video_id, title):
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        text = " ".join([i['text'] for i in srt])[:15000]
        
        prompt = f"""
        Você é um especialista em síntese de conhecimento. Analise a transcrição de "{title}" e crie um guia:
        --- 1. RESUMO EXECUTIVO ---
        - Teoria: Conceito central em um parágrafo.
        - Pontos-Chave: Os 3 pilares fundamentais.
        --- 2. LEITURA AVANÇADA ---
        - Detalhamento Teórico: Explique metodologias.
        - Matriz de Valor: Exemplos de Baixo vs Alto Valor.
        - Aplicação Prática: Passo-a-passo.
        Regras: Negrito em termos importantes. Máximo 3500 caracteres.
        Transcrição: {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Resumo detalhado indisponível para este vídeo."

def main():
    # TESTE: Alterado para 30 dias para garantir que encontre algo hoje
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    print(f"Buscando vídeos postados após: {time_threshold}")

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        print(f"Verificando canal {channel_id}: {len(feed.entries)} vídeos totais no feed.")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > time_threshold:
                print(f"-> PROCESSANDO: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title)
                
                msg = (
                    f"📺 *{entry.title}*\n👤 Canal: {entry.author}\n"
                    f"📅 {published.strftime('%d/%m/%Y')}\n\n"
                    f"{summary}\n\n🔗 [Link]({entry.link})"
                )
                
                try:
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print(f"   [OK] Mensagem enviada para o Telegram.")
                except Exception as e:
                    print(f"   [ERRO] Falha ao enviar Telegram: {e}")
                    bot.send_message(CHAT_ID, f"Vídeo: {entry.title}\nLink: {entry.link}")
                
                time.sleep(10)

if __name__ == "__main__":
    main()
