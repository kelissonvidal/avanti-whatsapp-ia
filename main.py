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

def finalizar_fluxo(numero, sessao):
    nome = sessao.get("nome", "cliente")
    mensagem_final = f"""Perfeito {nome}!

Como já adiantamos suas informações e suas dúvidas, agora vou te encaminhar para nosso consultor. Ele já vai falar com você.

Parabéns pelo interesse em nosso Parque Empresarial. 🎯"""
    enviar_mensagem(numero, mensagem_final)

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
    print("📥 Webhook recebido:", data)

    if data.get("type") != "ReceivedCallback" or data.get("fromMe"):
        return jsonify({"status": "ignorado"})

    numero = data.get("phone") or data.get("message", {}).get("from", "")
    mensagem = data.get("text", {}).get("message") or data.get("message", {}).get("text", {}).get("body") or ""

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

    elif sessao["etapa"] == "interesse":
        if mensagem == "1":
            sessao["interesse"] = "Investir"
        elif mensagem == "2":
            sessao["interesse"] = "Construir sede própria"
        else:
            enviar_mensagem(numero, "Por favor, responda com 1 ou 2.")
            return jsonify({"status": "aguardando_interesse"})

        texto = """Você pretende pagar:

1. À vista com desconto imperdível
2. Parcelado em suaves parcelas

(Digite apenas o número da opção desejada)"""
        enviar_mensagem(numero, texto)
        avancar("forma_pagamento")
        return jsonify({"status": "coletou_interesse"})

    elif sessao["etapa"] == "forma_pagamento":
        if mensagem == "1":
            sessao["forma_pagamento"] = "À vista"
            texto = """O pagamento será:

1. Em Dinheiro
2. Imóvel + dinheiro
3. Veículo + dinheiro
4. Imóvel, Veículo + Dinheiro

(Digite apenas o número da opção desejada)"""
            enviar_mensagem(numero, texto)
            avancar("avista_tipo")
        elif mensagem == "2":
            sessao["forma_pagamento"] = "Parcelado"
            texto = """Qual o valor de entrada você pretende investir?

1. R$ 10.000
2. R$ 25.000
3. R$ 50.000
4. À vista
5. Outro valor

(Digite apenas o número da opção desejada)"""
            enviar_mensagem(numero, texto)
            avancar("entrada_valor")
        else:
            enviar_mensagem(numero, "Por favor, responda com 1 ou 2.")
            return jsonify({"status": "aguardando_forma_pagamento"})

    elif sessao["etapa"] == "avista_tipo":
        opcoes = {
            "1": "Dinheiro",
            "2": "Imóvel + dinheiro",
            "3": "Veículo + dinheiro",
            "4": "Imóvel, Veículo + dinheiro"
        }
        sessao["avista_detalhe"] = opcoes.get(mensagem[0], "Outro")
        finalizar_fluxo(numero, sessao)
        return jsonify({"status": "finalizou_avista"})

    elif sessao["etapa"] == "entrada_valor":
        valores = {
            "1": "R$ 10.000",
            "2": "R$ 25.000",
            "3": "R$ 50.000",
            "4": "À vista",
            "5": "Outro"
        }
        escolha = valores.get(mensagem[0], "Outro")
        if escolha == "Outro":
            enviar_mensagem(numero, "Digite o valor desejado para entrada:")
            avancar("entrada_custom")
        else:
            sessao["entrada"] = escolha
            texto = """Em quantas parcelas pretende pagar?

1. 60 parcelas
2. 120 parcelas
3. 240 parcelas
4. Outro número

(Digite apenas o número da opção desejada)"""
            enviar_mensagem(numero, texto)
            avancar("parcelas")

    elif sessao["etapa"] == "entrada_custom":
        sessao["entrada"] = mensagem
        texto = """Em quantas parcelas pretende pagar?

1. 60 parcelas
2. 120 parcelas
3. 240 parcelas
4. Outro número

(Digite apenas o número da opção desejada)"""
        enviar_mensagem(numero, texto)
        avancar("parcelas")

    elif sessao["etapa"] == "parcelas":
        parcelas_map = {
            "1": "60 parcelas",
            "2": "120 parcelas",
            "3": "240 parcelas",
            "4": "Outro"
        }
        escolha = parcelas_map.get(mensagem[0], "Outro")
        if escolha == "Outro":
            enviar_mensagem(numero, "Digite o número de parcelas que deseja:")
            avancar("parcelas_custom")
        else:
            sessao["parcelas"] = escolha
            finalizar_fluxo(numero, sessao)

    elif sessao["etapa"] == "parcelas_custom":
        sessao["parcelas"] = mensagem
        finalizar_fluxo(numero, sessao)

    SESSOES[numero] = sessao
    return jsonify({"status": f"etapa_{sessao['etapa']}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)