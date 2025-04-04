import requests
from flask import Flask

app = Flask(name)

# Hardcoded "environment variables"
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"  # Replace with your bot token
TELEGRAM_CHANNEL_ID = "@aiappsselfcreation"              # Use @username or chat_id
MESSAGE_TEXT = "Hi, this is a message from AI Bot"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"  # Your Gumroad access token
CONVERTKIT_API_KEY = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"  # Your ConvertKit API key


@app.route("/")
def send_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": MESSAGE_TEXT,
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return "✅ Message sent successfully!", 200
    else:
        return f"❌ Failed to send message. {response.text}", 500

if name == "main":
    app.run(host="0.0.0.0", port=5000)
