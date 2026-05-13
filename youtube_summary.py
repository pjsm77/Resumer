import os
import time
import datetime
import feedparser
# Força o silenciamento de avisos que travam o console do GitHub
import warnings
warnings.filterwarnings("ignore")

print("Iniciando script...")
try:
    import google.generativeai as genai
    from youtube_transcript_api import YouTubeTranscriptApi
    from telebot import TeleBot
    print("Bibliotecas importadas com sucesso!")
except Exception as e:
    print(f"Erro ao importar bibliotecas: {e}")

# Lista de Canais (IDs internos do YouTube)
CHANNELS = [
    'UCXpYpY8O6-C_V8z72Y4KkYw', # bruno_faggion
    'UC3YyP79q2mO6-f1_0ZfF9OQ', # brunogabarra
    'UCmG9O80pUf2m-46e_FmP9Xg', # CanaldoEslen
    'UC70769I-5i8C1e32pA_L_yA', # canalsandeco
    'UCW0n0v0Q7m_D9fX6p5pQ_7g', # Danilo-CM
    'UCX_Nf-M9m2K2R6D5_f_vS7A', # deborahfolloni
    'UCW5P2M6C9S7p3Q0L6Q6z1aA', # DesfrutandoaVida
    'UCY08r_5A7mS3m6qX8-5L_6w'  # LucasMontano
]

# Inicialização
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')
bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def get_deep_summary(video_id, title):
    try:
        # Puxa até 15k caracteres da transcrição para análise profunda
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        text = " ".join([i['text'] for i in srt])[:15000]
        
        prompt = f"""
        Você é um especialista em síntese de conhecimento. Analise a transcrição de "{title}" e crie um guia:

        --- 1. RESUMO EXECUTIVO ---
        - Teoria: O conceito central em um parágrafo denso.
        - Pontos-Chave: Os 3 pilares fundamentais.

        --- 2. LEITURA AVANÇADA ---
        - Detalhamento Teórico: Explique termos técnicos ou metodologias (ex: Playbooks, Gatilhos, etc).
        - Matriz de Valor: Diferencie exemplos de "Baixo Valor" vs "Alto Valor" baseados no vídeo.
        - Aplicação Prática: Cenário real e passo-a-passo para implementar.
        - Insights Extras: Correlação com conceitos de mercado/produtividade.

        Regras: Use negrito em termos importantes. Máximo 3500 caracteres. Se não houver exemplos no vídeo, crie exemplos plausíveis baseados na teoria do autor.
        Transcrição: {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro no resumo do vídeo {video_id}: {e}")
        return "Resumo detalhado indisponível (transcrição desativada ou vídeo muito longo)."

def main():
    # Margem de 26h para garantir que nada escape entre execuções do GitHub
    one_day_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=260)

    for channel_id in CHANNELS:
        feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        
        for entry in feed.entries:
            published = datetime.datetime.fromisoformat(entry.published)
            
            if published > one_day_ago:
                print(f"Processando: {entry.title}")
                summary = get_deep_summary(entry.yt_videoid, entry.title)
                
                msg = (
                    f"📺 *{entry.title}*\n"
                    f"👤 Canal: {entry.author}\n"
                    f"📅 {published.strftime('%d/%m/%Y')}\n\n"
                    f"{summary}\n\n"
                    f"🔗 [Assista no YouTube]({entry.link})"
                )
                
                try:
                    # Envia em partes se exceder o limite (segurança extra)
                    if len(msg) > 4000:
                        bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                        bot.send_message(CHAT_ID, "...(continua)\n" + msg[4000:], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                except:
                    bot.send_message(CHAT_ID, f"Erro de formatação no vídeo: {entry.title}\n{entry.link}")

                time.sleep(10) # Delay seguro para API Gemini (15/min) e Telegram

if __name__ == "__main__":
    main()
