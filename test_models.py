import os
from google import genai

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

print("Listando modelos disponíveis para sua chave:")
for m in client.models.list():
    print(f"Nome: {m.name} | Suporta gerar conteúdo: {'generateContent' in m.supported_methods}")
