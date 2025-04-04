import requests
import os
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
CONVERTKIT_API_KEY = os.getenv("CONVERTKIT_API_KEY")

def get_gumroad_earnings():
    url = "https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        total_earnings = sum(float(sale['price']) / 100 for sale in data['sales'])
        return f"💰 **Gumroad Earnings**: ₹{total_earnings:,.2f}"
    else:
        return "❌ Failed to fetch Gumroad earnings."

def get_convertkit_earnings():
    url = f"https://api.convertkit.com/v3/subscribers?api_key={CONVERTKIT_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        total_subscribers = len(data['subscribers'])
        return f"📧 **ConvertKit Subscribers**: {total_subscribers} active."
    else:
        return "❌ Failed to fetch ConvertKit data."

def send_telegram_message():
    gumroad_message = get_gumroad_earnings()
    convertkit_message = get_convertkit_earnings()

    message = (
        "🚀 **Daily Earnings Report**\n\n"
        f"{gumroad_message}\n"
        f"{convertkit_message}\n\n"
        "✅ Automated updates sent every day at 7:30 AM IST!"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("✅ Telegram message sent successfully!")
    else:
        print(f"❌ Failed to send Telegram message. Response: {response.text}")

@app.route("/")
def trigger():
    send_telegram_message()
    return "✅ Message Sent", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
