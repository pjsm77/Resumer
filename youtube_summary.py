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

# Lista de URLs de feed baseadas nos nomes dos canais (Handles)
CHANNELS = [
    'https://www.youtube.com/feeds/videos.xml?user=bruno_faggion',
    'https://www.youtube.com/feeds/videos.xml?user=brunogabarra',
    'https://www.youtube.com/feeds/videos.xml?user=CanaldoEslen',
    'https://www.youtube.com/feeds/videos.xml?user=canalsandeco',
    'https://www.youtube.com/feeds/videos.xml?user=Danilo-CM',
    'https://www.youtube.com/feeds/videos.xml?user=deborahfolloni',
    'https://www.youtube.com/feeds/videos.xml?user=DesfrutandoaVida',
    'https://www.youtube.com/feeds/videos.xml?user=LucasMontano'
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
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    print(f"Buscando vídeos desde: {time_threshold}")

    for feed_url in CHANNELS:
        feed = feedparser.parse(feed_url)
        print(f"Verificando feed: {feed_url} - Encontrados: {len(feed.entries)} vídeos.")

        
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
