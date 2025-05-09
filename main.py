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

def webhook_finalizar(numero, sessao):
    nome = sessao.get("nome", "cliente")
    mensagem_final = f"""Perfeito {nome}!

Como já adiantamos suas informações e suas dúvidas, agora vou te encaminhar para nosso consultor. Ele já vai falar com você.

Parabéns pelo interesse em nosso Parque Empresarial. 🎯"""
    enviar_mensagem(numero, mensagem_final)

    msg = (
        f"🚀 Lead qualificado do Avanti\n"
        f"📛 Nome: {sessao.get('nome')}\n"
        f"🎯 Interesse: {sessao.get('interesse', 'Não informado')}\n"
        f"💳 Pagamento: {sessao.get('forma_pagamento', 'Não informado')}\n"
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

    def avancar(etapa):
        sessao["etapa"] = etapa
        SESSOES[numero] = sessao

    if sessao["etapa"] == "inicio":
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.\n\nQual o seu nome, por favor?")
        avancar("nome")
        return jsonify({"status": "aguardando_nome"})

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
        return jsonify({"status": "coletou_nome"})

    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)