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
    mensagem = data.get("text", {}).get("message") or data.get("message", "")
    if not numero or not mensagem:
        return jsonify({"status": "sem dados"})

    numero = str(numero).replace("+", "").strip()
    sessao = SESSOES.get(numero, {"etapa": "inicio"})

    if sessao["etapa"] == "inicio":
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.\nQual o seu nome, por favor?")
        sessao["etapa"] = "nome"

    elif sessao["etapa"] == "nome":
        nome = mensagem.strip().split(" ")[0].capitalize()
        if nome.isalpha():
            sessao["nome"] = nome
            enviar_mensagem(numero, f"Prazer em te conhecer, {nome}! 😊\nSobre o que você gostaria de saber?\n1️⃣ Tamanhos e preços\n2️⃣ Pagamento\n3️⃣ Localização\n4️⃣ Imagens e vídeos\n5️⃣ Falar com um consultor")
            sessao["etapa"] = "opcao"
        else:
            enviar_mensagem(numero, "Desculpe, não entendi. Qual o seu nome, por favor?")

    elif sessao["etapa"] == "opcao":
        if "1" in mensagem:
            enviar_mensagem(numero, "Os lotes do Avanti começam a partir de 500 m². O valor exato depende da localização. Posso te enviar uma proposta personalizada — posso seguir com isso?")
        elif "2" in mensagem:
            enviar_mensagem(numero, "Temos financiamento direto com o empreendedor. Qual valor de entrada você pretende investir?")
            sessao["etapa"] = "entrada"
        elif "3" in mensagem:
            enviar_mensagem(numero, "📍 O Avanti está às margens da rodovia em Lagoa da Prata: https://goo.gl/maps/FakeLink")
        elif "4" in mensagem:
            enviar_mensagem(numero, "Veja as imagens: https://simbadigital.com.br/imagem/imagem1.webp\n🎥 Vídeo: https://simbadigital.com.br/video/Avanti-Drone-com-Audio-480p.mp4")
        elif "5" in mensagem:
            enviar_mensagem(numero, "Perfeito! Para agilizar seu atendimento, preciso de algumas informações.\nQual valor de entrada você pretende investir?")
            sessao["etapa"] = "entrada"
        else:
            enviar_mensagem(numero, "Por favor, responda com um número de 1 a 5.")

    elif sessao["etapa"] == "entrada":
        sessao["entrada"] = mensagem.strip()
        enviar_mensagem(numero, "E em quantas parcelas você gostaria de dividir?")
        sessao["etapa"] = "parcelas"

    elif sessao["etapa"] == "parcelas":
        sessao["parcelas"] = mensagem.strip()
        enviar_mensagem(numero, "Agora me informe seu e-mail para contato:")
        sessao["etapa"] = "email"

    elif sessao["etapa"] == "email":
        sessao["email"] = mensagem.strip()
        enviar_mensagem(numero, "Tudo certo! Agora vou te encaminhar para o consultor responsável que vai finalizar sua proposta. 👇")
        enviar_mensagem(numero, "https://wa.me/553734490005")
        sessao["etapa"] = "finalizado"

        msg_consultor = (
            f"🚀 Novo lead qualificado do Avanti\n"
            f"📛 Nome: {sessao.get('nome')}\n"
            f"📞 WhatsApp: https://wa.me/{numero}\n"
            f"💰 Entrada: {sessao.get('entrada')}\n"
            f"📆 Parcelas: {sessao.get('parcelas')}\n"
            f"✉️ E-mail: {sessao.get('email')}"
        )
        enviar_mensagem(CONSULTOR_NUMERO, msg_consultor)

    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)