import os
from google import genai

try:
    api_key = os.environ.get('GEMINI_API_KEY')
    client = genai.Client(api_key=api_key)

    print("--- LISTA DE MODELOS DISPONÍVEIS ---")
    # Simplificado para não causar erro de atributo
    for m in client.models.list():
        print(f"ID do Modelo: {m.name}")
    print("------------------------------------")

except Exception as e:
    print(f"Erro ao listar: {e}")
