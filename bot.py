import requests
import os
import time
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
CONVERTKIT_API_KEY = os.getenv("CONVERTKIT_API_KEY")
PINTEREST_API_KEY = os.getenv("PINTEREST_API_KEY")

def fetch_api_data(url, headers=None, retries=3, delay=5):
    """Fetch data from API with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise error for 4xx/5xx responses
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt+1}: API error - {e}")
        time.sleep(delay)
    return None  # Return None if all attempts fail

def get_gumroad_earnings():
    """Fetch earnings from Gumroad API."""
    url = "https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    
    data = fetch_api_data(url, headers)
    if data and "sales" in data:
        total_earnings = sum(float(sale['price']) / 100 for sale in data['sales'])
        return f"💰 **Gumroad Earnings**: ₹{total_earnings:,.2f}"
    return "❌ Failed to fetch Gumroad earnings."

def get_convertkit_subscribers():
    """Fetch subscriber count from ConvertKit API."""
    url = f"https://api.convertkit.com/v3/subscribers?api_key={CONVERTKIT_API_KEY}"
    
    data = fetch_api_data(url)
    if data and "subscribers" in data:
        return f"📧 **ConvertKit Subscribers**: {len(data['subscribers'])} active."
    return "❌ Failed to fetch ConvertKit data."

def get_pinterest_analytics():
    """Fetch analytics from Pinterest API."""
    url = f"https://api.pinterest.com/v5/user_account?access_token={PINTEREST_API_KEY}"
    
    data = fetch_api_data(url)
    if data and "monthly_views" in data:
        return f"📌 **Pinterest Views**: {data['monthly_views']:,} this month."
    return "❌ Failed to fetch Pinterest analytics."

def send_telegram_message():
    """Send daily earnings report to Telegram."""
    logging.info("🚀 Fetching earnings data...")

    gumroad_message = get_gumroad_earnings()
    convertkit_message = get_convertkit_subscribers()
    pinterest_message = get_pinterest_analytics()

    message = (
        "🚀 **Daily Earnings Report**\n\n"
        f"{gumroad_message}\n"
        f"{convertkit_message}\n"
        f"{pinterest_message}\n\n"
        "✅ Automated updates sent every day at 7:30 AM IST!"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        logging.info("✅ Telegram message sent successfully!")
    else:
        logging.error(f"❌ Failed to send Telegram message. Response: {response.text}")

@app.route("/")
def trigger():
    """Trigger the report manually."""
    send_telegram_message()
    return "✅ Message Sent", 200

if __name__ == "__main__":
    logging.info("🚀 Bot started...")
    app.run(host="0.0.0.0", port=5000)
