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
    payload = {"phone": telefone, "message": mensagem}
    requests.post(f"{API_BASE}/send-text", headers=HEADERS, json=payload)

def reapresentar_opcoes(numero, sessao):
    restantes = sessao.get("info_pendentes", [])
    frases = [
        "Legal! Quer saber mais algum ponto?",
        "Tem mais alguma dessas que você gostaria de ver?",
        "Me avisa se quiser ver mais algum detalhe antes de continuar:"
    ]
    if not restantes or all(o.startswith("4") for o in restantes):
        sessao["etapa"] = "finalizar"
        return webhook_finalizar(numero, sessao)
    frase = frases[len(frases) - len(restantes)] if len(restantes) <= len(frases) else frases[-1]
    texto = f"{frase}\n\n" + "\n".join(restantes) + "\n\n(Digite apenas o número da opção desejada)"
    enviar_mensagem(numero, texto)

def webhook_finalizar(numero, sessao):
    enviar_mensagem(numero, "Perfeito, você já conferiu todas as informações importantes. Agora vou te encaminhar para nosso consultor. 👇")
    enviar_mensagem(numero, "https://wa.me/553734490005")
    msg = (
        f"🚀 Lead qualificado do Avanti\n"
        f"📛 Nome: {sessao.get('nome')}\n"
        f"🎯 Interesse: {sessao.get('interesse')}\n"
        f"💳 Pagamento: {sessao.get('forma_pagamento')}\n"
        f"💰 Entrada: {sessao.get('entrada', sessao.get('avista_detalhe', 'Não informado'))}\n"
        f"📆 Parcelas: {sessao.get('parcelas', 'Não informado')}\n"
        f"📞 WhatsApp: https://wa.me/{numero}"
    )
    enviar_mensagem(CONSULTOR_NUMERO, msg)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("type") != "ReceivedCallback" or data.get("fromMe"):
        return jsonify({"status": "ignorado"})

    numero = data.get("phone") or data.get("message", {}).get("from")
    mensagem = data.get("text", {}).get("message", "").strip().lower()
    if not numero or not mensagem:
        return jsonify({"status": "sem dados"})

    numero = str(numero).replace("+", "").strip()
    sessao = SESSOES.get(numero, {"etapa": "inicio"})

    def avancar(etapa): sessao["etapa"] = etapa

    if sessao["etapa"] == "inicio":
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.\n\nQual o seu nome, por favor?")
        avancar("nome")

    elif sessao["etapa"] == "nome":
        sessao["nome"] = mensagem.title()
        enviar_mensagem(numero,
            f"Prazer em te conhecer, {sessao['nome']}! 😊\n\n"
            "Todos os nossos consultores estão em atendimento nesse momento, vou tirando suas dúvidas aqui enquanto eles terminam.\n\n"
            "Você está interessado em:\n\n"
            "1. Investir\n"
            "2. Construir sede própria\n\n"
            "(Digite apenas o número da opção desejada)"
        )
        avancar("interesse")

    # A lógica das demais etapas permanece como na versão anterior

    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)