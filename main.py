import os
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Inicializa OpenAI com chave de API do ambiente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Z-API: ID da instância e token (do ambiente)
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")

# Endpoint de envio da Z-API
ZAPI_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}/send-text"

# Função para gerar resposta com OpenAI
def gerar_resposta(mensagem):
    prompt = f"""Você é um assistente comercial humanizado do Avanti Parque Empresarial. Sempre cumprimente o cliente pelo nome, se souber. O foco é informar sobre os lotes, formas de pagamento, localização e imagens. Seja gentil e direto. Evite termos técnicos ou respostas genéricas.

Mensagem do cliente: {mensagem}

Resposta da IA:"""
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": prompt }],
        temperature=0.7
    )
    return resposta.choices[0].message.content.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("🔵 Dados recebidos do webhook:", data)

    mensagem = data.get("text", {}).get("message") or \
               data.get("message", {}).get("text", {}).get("body") or \
               data.get("message", "")

    numero = data.get("phone") or \
             data.get("message", {}).get("from")

    print(f"📨 Mensagem recebida: {mensagem}")
    print(f"📱 Número: {numero}")

    if mensagem and numero:
        try:
            resposta = gerar_resposta(mensagem)
            print("✅ Resposta gerada pela IA:", resposta)

            payload = {
                "phone": numero,
                "message": resposta
            }
            r = requests.post(ZAPI_URL, json=payload)
            print("📤 Resposta enviada. Status:", r.status_code)
            print("📤 Retorno da ZAPI:", r.text)
        except Exception as e:
            print("❌ Erro ao gerar ou enviar resposta:", str(e))

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)