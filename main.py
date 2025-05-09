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
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.\nQual o seu nome, por favor?")
        avancar("nome")

    elif sessao["etapa"] == "nome":
        sessao["nome"] = mensagem.title()
        enviar_mensagem(numero, f"Prazer em te conhecer, {sessao['nome']}!\nVocê está interessado em:\n1. Investir\n2. Construir sede própria")
        avancar("interesse")

    elif sessao["etapa"] == "interesse":
        sessao["interesse"] = "Investir" if "1" in mensagem else "Construir sede própria"
        enviar_mensagem(numero, "Você pretende pagar:\n1. À vista com desconto imperdível\n2. Parcelado em suaves parcelas")
        avancar("forma_pagamento")

    elif sessao["etapa"] == "forma_pagamento":
        if "1" in mensagem:
            sessao["forma_pagamento"] = "À vista"
            enviar_mensagem(numero, "O pagamento será:\n1. Em Dinheiro\n2. Imóvel + dinheiro\n3. Veículo + dinheiro\n4. Imóvel, Veículo + Dinheiro")
            avancar("avista_tipo")
        else:
            sessao["forma_pagamento"] = "Parcelado"
            enviar_mensagem(numero, "Qual o valor de entrada você pretende investir?\n1. R$ 10.000\n2. R$ 25.000\n3. R$ 50.000\n4. Pretendo comprar à vista\n5. Outro valor")
            avancar("entrada_valor")

    elif sessao["etapa"] == "avista_tipo":
        opcoes = {
            "1": "Dinheiro",
            "2": "Imóvel + dinheiro",
            "3": "Veículo + dinheiro",
            "4": "Imóvel, veículo + dinheiro"
        }
        sessao["avista_detalhe"] = opcoes.get(mensagem[0], "Outro")
        avancar("info_extra")
        enviar_mensagem(numero, "Gostaria de saber mais alguma informação sobre os lotes?\n1. Localidade\n2. Metragem\n3. Infraestrutura já pronta\n4. Ir direto para o consultor")

    elif sessao["etapa"] == "entrada_valor":
        valores = {
            "1": "R$ 10.000",
            "2": "R$ 25.000",
            "3": "R$ 50.000",
            "4": "À vista",
            "5": "Outro valor"
        }
        escolha = valores.get(mensagem[0], "Outro valor")
        if escolha == "Outro valor":
            avancar("entrada_custom")
            enviar_mensagem(numero, "Digite o valor desejado para entrada:")
        else:
            sessao["entrada"] = escolha
            avancar("parcelas")
            enviar_mensagem(numero, "Em quantas parcelas pretende pagar?\n1. 60 parcelas\n2. 120 parcelas\n3. 240 parcelas\n4. Outro número")

    elif sessao["etapa"] == "entrada_custom":
        sessao["entrada"] = mensagem
        avancar("parcelas")
        enviar_mensagem(numero, "Em quantas parcelas pretende pagar?\n1. 60 parcelas\n2. 120 parcelas\n3. 240 parcelas\n4. Outro número")

    elif sessao["etapa"] == "parcelas":
        opcoes = {
            "1": "60 parcelas",
            "2": "120 parcelas",
            "3": "240 parcelas",
            "4": "Outro"
        }
        escolha = opcoes.get(mensagem[0], "Outro")
        if escolha == "Outro":
            avancar("parcelas_custom")
            enviar_mensagem(numero, "Digite o número de parcelas que deseja:")
        else:
            sessao["parcelas"] = escolha
            avancar("info_extra")
            enviar_mensagem(numero, "Gostaria de saber mais alguma informação sobre os lotes?\n1. Localidade\n2. Metragem\n3. Infraestrutura já pronta\n4. Ir direto para o consultor")

    elif sessao["etapa"] == "parcelas_custom":
        sessao["parcelas"] = mensagem
        avancar("info_extra")
        enviar_mensagem(numero, "Gostaria de saber mais alguma informação sobre os lotes?\n1. Localidade\n2. Metragem\n3. Infraestrutura já pronta\n4. Ir direto para o consultor")

    elif sessao["etapa"] == "info_extra":
        if "1" in mensagem:
            enviar_mensagem(numero, "📍 Localidade: Lotes com acesso direto à rodovia em Lagoa da Prata.")
        elif "2" in mensagem:
            enviar_mensagem(numero, "📐 Metragem: Lotes a partir de 500 m².")
        elif "3" in mensagem:
            enviar_mensagem(numero, "🛠️ Infraestrutura: asfalto, água, esgoto e iluminação já instalados.")
        elif "4" in mensagem:
            avancar("finalizar")

        if sessao["etapa"] != "finalizar":
            avancar("info_extra")

    if sessao["etapa"] == "finalizar":
        enviar_mensagem(numero, "Já anotei todas as suas informações. Agora vou te encaminhar para nosso consultor. 👇")
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
        sessao["etapa"] = "encerrado"

    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)