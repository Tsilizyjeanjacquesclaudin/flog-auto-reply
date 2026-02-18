import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

MESSAGE_TEMPLATE = """Bonjour {first_name} 👋

Ceci est un message automatique de FLOG INTL Agency.

Merci pour votre commentaire ! Si cette offre vous intéresse, envoyez votre CV à :
📧 tati@flogintl.com
📧 haingo@flogintl.com

Et même si ce poste ne correspond pas à votre profil, nous vous encourageons quand même à nous envoyer votre CV ! Nous l'étudierons et vous contacterons dès qu'une offre correspondra à votre profil. 🎯

🔔 Abonnez-vous à notre page pour ne manquer aucune de nos offres d'emploi à Maurice !

L'équipe FLOG INTL 💼"""


def get_user_first_name(user_id):
    url = f"https://graph.facebook.com/{user_id}"
    params = {"fields": "first_name", "access_token": PAGE_ACCESS_TOKEN}
    response = requests.get(url, params=params)
    return response.json().get("first_name", "")


def send_message(recipient_id, first_name):
    url = "https://graph.facebook.com/v24.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": MESSAGE_TEMPLATE.format(first_name=first_name)},
        "access_token": PAGE_ACCESS_TOKEN
    }
    requests.post(url, json=payload)


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "feed":
                    value = change.get("value", {})
                    if value.get("item") == "comment" and value.get("verb") == "add":
                        commenter_id = value.get("from", {}).get("id")
                        if commenter_id:
                            first_name = get_user_first_name(commenter_id)
                            send_message(commenter_id, first_name)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
