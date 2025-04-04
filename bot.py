import os
import time
import logging
import requests
from flask import Flask
import schedule
import threading

# Flask app setup
app = Flask(__name__)

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
CONVERTKIT_API_KEY = os.getenv("CONVERTKIT_API_KEY")
PINTEREST_API_KEY = os.getenv("PINTEREST_API_KEY")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Logging setup
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

def fetch_api_data(url, headers=None, retries=3, delay=5):
    """Fetch data from API with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"[API Error] Attempt {attempt + 1}: {e}")
            time.sleep(delay)
    return None

def get_gumroad_earnings():
    """Fetch earnings from Gumroad API."""
    url = "https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    
    data = fetch_api_data(url, headers)
    if data and "sales" in data:
        try:
            total_earnings = sum(float(sale.get('price', 0)) / 100 for sale in data['sales'])
            return f"💰 **Gumroad Earnings**: ₹{total_earnings:,.2f}"
        except Exception as e:
            logging.error(f"[Gumroad] Data parsing error: {e}")
    return "❌ Failed to fetch Gumroad earnings."

def get_convertkit_subscribers():
    """Fetch subscriber count from ConvertKit API."""
    url = f"https://api.convertkit.com/v3/subscribers?api_key={CONVERTKIT_API_KEY}"
    
    data = fetch_api_data(url)
    if data and "subscribers" in data:
        try:
            return f"📧 **ConvertKit Subscribers**: {len(data['subscribers'])} active."
        except Exception as e:
            logging.error(f"[ConvertKit] Data parsing error: {e}")
    return "❌ Failed to fetch ConvertKit data."

def get_pinterest_analytics():
    """Fetch analytics from Pinterest API."""
    url = f"https://api.pinterest.com/v5/user_account?access_token={PINTEREST_API_KEY}"
    
    data = fetch_api_data(url)
    if data and "monthly_views" in data:
        try:
            return f"📌 **Pinterest Views**: {data['monthly_views']:,} this month."
        except Exception as e:
            logging.error(f"[Pinterest] Data parsing error: {e}")
    return "❌ Failed to fetch Pinterest analytics."

def send_telegram_message():
    """Send daily report to Telegram."""
    logging.info("🚀 Fetching earnings data...")

    gumroad_msg = get_gumroad_earnings()
    convertkit_msg = get_convertkit_subscribers()
    pinterest_msg = get_pinterest_analytics()

    message = (
        "🚀 **Daily Earnings Report**\n\n"
        f"{gumroad_msg}\n"
        f"{convertkit_msg}\n"
        f"{pinterest_msg}\n\n"
        "✅ Automated update at 7:30 AM IST."
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logging.info("✅ Telegram message sent.")
        else:
            logging.error(f"❌ Telegram error: {response.text}")
    except Exception as e:
        logging.error(f"❌ Telegram send error: {e}")

@app.route("/")
def manual_trigger():
    """Trigger report manually."""
    send_telegram_message()
    return "✅ Message sent to Telegram", 200

def run_scheduler():
    """Run scheduled job in background thread."""
    schedule.every().day.at("02:00").do(send_telegram_message)  # 7:30 AM IST = 2:00 AM UTC
    logging.info("🕒 Scheduler started... Will run at 7:30 AM IST daily.")

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Start scheduler in a background thread
    threading.Thread(target=run_scheduler, daemon=True).start()

    logging.info("🚀 Bot server running...")
    app.run(host="0.0.0.0", port=5000)
