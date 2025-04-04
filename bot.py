import requests
import os
import time
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
CONVERTKIT_API_KEY = os.getenv("CONVERTKIT_API_KEY")

def fetch_api_data(url, headers=None, retries=3, delay=5):
    """Helper function to fetch data with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Attempt {attempt+1}: API error {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt+1}: Network error - {e}")
        time.sleep(delay)
    return None  # Return None if all attempts fail

def get_gumroad_earnings():
    url = "https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    
    data = fetch_api_data(url, headers)
    if data and "sales" in data:
        total_earnings = sum(float(sale['price']) / 100 for sale in data['sales'])
        return f"💰 **Gumroad Earnings**: ₹{total_earnings:,.2f}"
    return "❌ Failed to fetch Gumroad earnings."

def get_convertkit_earnings():
    url = f"https://api.convertkit.com/v3/subscribers?api_key={CONVERTKIT_API_KEY}"
    
    data = fetch_api_data(url)
    if data and "subscribers" in data:
        total_subscribers = len(data['subscribers'])
        return f"📧 **ConvertKit Subscribers**: {total_subscribers} active."
    return "❌ Failed to fetch ConvertKit data."

def send_telegram_message():
    print("🚀 Fetching earnings data...")
    
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
    print("🚀 Bot started...")
    app.run(host="0.0.0.0", port=5000)
