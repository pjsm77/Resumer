import os
import time
import datetime
import feedparser
import warnings
from googleapiclient.discovery import build
import google.generativeai as genai
from telebot import TeleBot

# Ignorar avisos de depreciação para manter o log limpo
warnings.filterwarnings("ignore")

print("--- INICIANDO PROCESSO DE RESUMO ---")

# --- CONFIGURAÇÃO INICIAL ---
try:
    # Captura das variáveis de ambiente (Secrets do GitHub)
    YOUTUBE_KEY = os.environ.get('YOUTUBE_API_KEY')
    GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # Inicialização das APIs
    genai.configure(api_key=GEMINI_KEY)
    # Usamos o 1.5-flash por ser mais rápido e evitar o erro 404 da versão Pro antiga
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    bot = TeleBot(TELEGRAM_TOKEN)
    yt_service = build('youtube', 'v3', developerKey=YOUTUBE_KEY)
    
    print("[OK] Conexão com APIs estabelecida.")

except Exception as e:
    print(f"[ERRO CRÍTICO NA CONFIGURAÇÃO]: {e}")
    exit(1)

# Lista de canais para monitorar
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', 'UC3YyP79q2mO6-f1_0ZfF9OQ', 
    'UCmG9O80pUf2m-46e_FmP9Xg', 'UC70769I-5i8C1e32pA_L_yA', 
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', 'UCX_Nf-M9m2K2R6D5_f_vS7A', 
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', 'UCyHOBY6IDZF9zOKJPou2Rgg'
]

def get_video_details(video_id):
    """Recupera a descrição completa do vídeo via API do YouTube"""
    try:
        request = yt_service.videos().list(part="snippet", id=video_id)
        response = request.execute()
        if response.get('items'):
            snippet = response['items'][0]['snippet']
            return snippet.get('description', '')
    except Exception as e:
        print(f"   [ERRO YOUTUBE API]: {e}")
    return ""

def main():
    # Define o período de busca (últimas 24 horas para evitar duplicatas no log)
    # Você pode ajustar para 'days=7' se quiser processar mais vídeos antigos na primeira vez
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    for channel_id in CHANNELS:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed = feedparser.parse(feed_url)
        
        print(f"\nVerificando canal: {channel_id}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > time_threshold:
                try:
                    print(f"-> Analisando: {entry.title}")
                    
                    # Busca descrição completa para um resumo melhor
                    full_description = get_video_details(entry.yt_videoid)
                    contexto = full_description if full_description else entry.summary

                    prompt = f"""
                    Você é um assistente especialista em tecnologia e análise de dados.
                    Analise o conteúdo do vídeo '{entry.title}' do canal {entry.author}.
                    
                    Conteúdo para análise: {contexto[:5000]}
                    
                    Gere um resumo formatado para Telegram (Markdown):
                    1. **Resumo Executivo**: (O que é o vídeo em 2 frases)
                    2. **Pontos Chave**: (Lista de insights principais)
                    3. **Leitura Avançada**: (Explicação técnica de um conceito citado)
                    """
                    
                    response = model.generate_content(prompt)
                    summary_text = response.text
                    
                    # Formata a mensagem final
                    msg = f"📺 *{entry.title}*\n👤 {entry.author}\n\n{summary_text}\n\n🔗 [Assistir no YouTube]({entry.link})"
                    
                    # Envia para o Telegram (respeitando o limite de caracteres)
                    if len(msg) > 4090:
                        bot.send_message(CHAT_ID, msg[:4090], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    
                    print("   [OK] Mensagem enviada!")
                    
                    # Pausa para evitar rate limit das APIs
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"   [ERRO AO PROCESSAR VÍDEO]: {e}")

if __name__ == "__main__":
    main()
    print("\n--- SCRIPT FINALIZADO ---")
