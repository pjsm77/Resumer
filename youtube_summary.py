import os
import time
import datetime
import feedparser
import warnings

# Silencia avisos de sistema para manter o log limpo
warnings.filterwarnings("ignore")

print("--- INICIANDO DIAGNÓSTICO DO SCRIPT ---")

try:
    import google.generativeai as genai
    from youtube_transcript_api import YouTubeTranscriptApi
    from telebot import TeleBot
    print("[OK] Bibliotecas carregadas com sucesso.")
except Exception as e:
    print(f"[ERRO] Falha ao carregar bibliotecas: {e}")

# Lista de URLs de feed com IDs de canal validados
CHANNELS = [
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCXpYpY8O6-C_V8z72Y4KkYw', # bruno_faggion
    'https://www.youtube.com/feeds/videos.xml?channel_id=UC3YyP79q2mO6-f1_0ZfF9OQ', # brunogabarra
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCmG9O80pUf2m-46e_FmP9Xg', # CanaldoEslen
    'https://www.youtube.com/feeds/videos.xml?channel_id=UC70769I-5i8C1e32pA_L_yA', # canalsandeco
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCW0n0v0Q7m_D9fX6p5pQ_7g', # Danilo-CM
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCX_Nf-M9m2K2R6D5_f_vS7A', # deborahfolloni
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCW5P2M6C9S7p3Q0L6Q6z1aA', # DesfrutandoaVida
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCY08r_5A7mS3m6qX8-5L_6w'  # LucasMontano
]

# Configuração das APIs via Secrets do GitHub
try:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
    bot = TeleBot(os.environ['TELEGRAM_TOKEN'])
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    print("[OK] Variáveis de ambiente e APIs configuradas.")
except Exception as e:
    print(f"[ERRO] Falha nas chaves de API: {e}")

def get_deep_summary(video_id, title):
    """
    Gera um resumo denso com teoria, pontos-chave e aplicações práticas.
    """
    try:
        # Tenta capturar a transcrição (em português ou inglês)
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        text = " ".join([i['text'] for i in srt])[:15000]
        
        prompt = f"""
        Você é um especialista em síntese de conhecimento e educação executiva. 
        Analise a transcrição do vídeo "{title}" e crie um guia completo seguindo esta estrutura:

        --- 1. RESUMO EXECUTIVO ---
        - Teoria: O conceito central do vídeo em um parágrafo denso.
        - Pontos-Chave: Os 3 pilares fundamentais discutidos.

        --- 2. LEITURA AVANÇADA E APROFUNDAMENTO ---
        - Detalhamento Teórico: Explique os termos técnicos ou metodologias citadas (ex: se falar de 'Playbook', explique o que compõe um).
        - Matriz de Valor: Diferencie exemplos práticos de tarefas de "Baixo Valor" vs "Alto Valor" baseados no contexto do vídeo.
        - Aplicação no Dia-a-Dia: Crie um cenário real de aplicação e descreva o passo-a-passo para implementar o que foi ensinado.
        - Insights Extras: Adicione uma correlação com conceitos de mercado ou produtividade que complementem o que foi ensinado.

        Restrições de Formatação:
        - Use negrito para termos importantes.
        - O texto total deve ter entre 2500 e 3800 caracteres.
        - Se o autor não citar exemplos, VOCÊ deve criar exemplos plausíveis baseados na teoria dele para ilustrar.

        Transcrição: {text}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"   [AVISO] Não foi possível gerar resumo para {video_id}: {e}")
        return "Resumo detalhado indisponível (vídeo sem legendas acessíveis ou erro na IA)."

def main():
    # TESTE: Busca vídeos dos últimos 30 dias. 
    # Após validar que está recebendo, você pode mudar 'days=30' para 'hours=26'.
    time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    print(f"Buscando vídeos desde: {time_threshold}")

    for feed_url in CHANNELS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Verificando feed: {feed_url} - Encontrados: {len(feed.entries)} vídeos.")
            
            for entry in feed.entries:
                published = datetime.datetime.fromisoformat(entry.published)
                
                if published > time_threshold:
                    print(f"-> INICIANDO PROCESSO: {entry.title}")
                    
                    # Log de segurança para verificar o destino da mensagem
                    print(f"   Gerando resumo e enviando para CHAT_ID: {CHAT_ID}")
                    
                    summary = get_deep_summary(entry.yt_videoid, entry.title)
                    
                    # Formatação da mensagem para o Telegram
                    msg = (
                        f"📺 *{entry.title}*\n"
                        f"👤 Canal: {entry.author}\n"
                        f"📅 {published.strftime('%d/%m/%Y')}\n\n"
                        f"{summary}\n\n"
                        f"🔗 [Assista no YouTube]({entry.link})"
                    )
                    
                    # Envio da mensagem com tratamento de tamanho
                    if len(msg) > 4000:
                        bot.send_message(CHAT_ID, msg[:4000], parse_mode='Markdown')
                        bot.send_message(CHAT_ID, "...(continua)\n" + msg[4000:], parse_mode='Markdown')
                    else:
                        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    
                    print(f"   [OK] Sucesso total no envio!")
                    
                    # Pausa para evitar bloqueios por excesso de requisições
                    time.sleep(10)
        except Exception as e:
            print(f"   [ERRO CRÍTICO NO CANAL]: {e}")

if __name__ == "__main__":
    main()
