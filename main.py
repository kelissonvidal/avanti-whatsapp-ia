import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
SESSOES = {}

ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
API_BASE = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"
HEADERS = {"Client-Token": ZAPI_CLIENT_TOKEN}
CONSULTOR_NUMERO = "553734490005"

def enviar_mensagem(telefone, mensagem):
    print(f"📤 Enviando para {telefone}:\n{mensagem}")
    payload = {"phone": telefone, "message": mensagem}
    requests.post(f"{API_BASE}/send-text", headers=HEADERS, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📥 Webhook recebido:", data)

    if data.get("type") != "ReceivedCallback" or data.get("fromMe"):
        return jsonify({"status": "ignorado"})

    numero = data.get("phone") or data.get("message", {}).get("from", "")
    mensagem = data.get("text", {}).get("message") or                data.get("message", {}).get("text", {}).get("body") or ""

    if not numero or not mensagem:
        print("⚠️ Dados incompletos - número ou mensagem ausente.")
        return jsonify({"status": "sem dados"})

    numero = str(numero).replace("+", "").strip()
    mensagem = mensagem.strip().lower()

    sessao = SESSOES.get(numero, {"etapa": "inicio"})

    def avancar(etapa):
        print(f"🔄 Avançando {numero} para etapa: {etapa}")
        sessao["etapa"] = etapa
        SESSOES[numero] = sessao

    if sessao["etapa"] == "inicio":
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.\n\nQual o seu nome, por favor?")
        avancar("nome")
        return jsonify({"status": "aguardando_nome"})

    elif sessao["etapa"] == "nome":
        if not mensagem:
            enviar_mensagem(numero, "Desculpe, não entendi seu nome. Pode repetir?")
            return jsonify({"status": "erro_nome"})
        nome = mensagem.split(" ")[0].capitalize()
        sessao["nome"] = nome
        texto = f"""Prazer em te conhecer, {nome}! 😊

Todos os nossos consultores estão em atendimento nesse momento, vou tirando suas dúvidas aqui enquanto eles terminam.

Você está interessado em:

1. Investir
2. Construir sede própria

(Digite apenas o número da opção desejada)"""
        enviar_mensagem(numero, texto)
        avancar("interesse")
        return jsonify({"status": "coletou_nome"})

    # Fallback final
    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)