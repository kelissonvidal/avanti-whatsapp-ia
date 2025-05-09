import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Sessões por telefone
SESSOES = {}

# Z-API
ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
API_BASE = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"
HEADERS = {"Client-Token": ZAPI_CLIENT_TOKEN}

# Envia mensagem via Z-API
def enviar_mensagem(telefone, mensagem):
    payload = {
        "phone": telefone,
        "message": mensagem
    }
    requests.post(f"{API_BASE}/send-text", headers=HEADERS, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Bloqueia loops
    if data.get("type") != "ReceivedCallback" or data.get("fromMe"):
        return jsonify({"status": "ignorado"})

    numero = data.get("phone") or data.get("message", {}).get("from")
    mensagem = data.get("text", {}).get("message", "") or data.get("message", {}).get("text", {}).get("body", "")

    if not numero or not mensagem:
        return jsonify({"status": "sem dados"})

    numero = str(numero).replace("+", "").strip()
    sessao = SESSOES.get(numero, {"etapa": "inicio", "nome": None})
    
    if sessao["etapa"] == "inicio":
        enviar_mensagem(numero, "Olá! Seja muito bem-vindo ao Avanti Parque Empresarial.
Qual o seu nome, por favor?")
        sessao["etapa"] = "aguardando_nome"

    elif sessao["etapa"] == "aguardando_nome":
        nome = mensagem.strip().split(" ")[0].capitalize()
        sessao["nome"] = nome
        enviar_mensagem(numero, f"Prazer em te conhecer, {nome}! 😊
Me conta rapidinho, o que você gostaria de saber?

📐 Tamanhos e preços dos lotes
💰 Formas de pagamento
📍 Localização
📸 Imagens e vídeos
👤 Falar com um consultor")
        sessao["etapa"] = "aguardando_escolha"

    elif sessao["etapa"] == "aguardando_escolha":
        texto = mensagem.lower()
        if "preço" in texto or "tamanho" in texto or "lote" in texto:
            enviar_mensagem(numero, "Os lotes do Avanti começam a partir de 500 m² e temos diversas opções com ótima metragem.
O valor exato depende da localização dentro do parque. Posso te enviar uma proposta personalizada — posso seguir com isso?")
        elif "pagamento" in texto or "parcel" in texto or "entrada" in texto:
            enviar_mensagem(numero, "Temos financiamento próprio direto com o empreendedor, com entrada facilitada e parcelamento em até 120 vezes.
Você gostaria de simular uma proposta? Me diga o valor de entrada e o número de parcelas que tem em mente.")
        elif "localiza" in texto or "onde" in texto:
            enviar_mensagem(numero, "O Avanti está localizado às margens da rodovia em Lagoa da Prata, com acesso rápido ao centro e a vias estratégicas.
📍 Veja a localização no mapa: https://goo.gl/maps/FakeLink")
        elif "imagem" in texto or "vídeo" in texto or "foto" in texto:
            enviar_mensagem(numero, "Confira as imagens do empreendimento:
https://simbadigital.com.br/imagem/imagem1.webp
🎥 Vídeo aéreo:
https://simbadigital.com.br/video/Avanti-Drone-com-Audio-480p.mp4")
        elif "consultor" in texto or "humano" in texto:
            enviar_mensagem(numero, "Claro! Já vou te encaminhar para um dos nossos especialistas. Aguarde um instante, ele vai te chamar aqui mesmo. ✅")
        else:
            enviar_mensagem(numero, "Essa é uma ótima pergunta! Já estou registrando e logo um dos nossos consultores vai te responder com mais detalhes.
Enquanto isso, posso te mostrar as informações principais sobre os lotes, localização e formas de pagamento.")

    SESSOES[numero] = sessao
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)