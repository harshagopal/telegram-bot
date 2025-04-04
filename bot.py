import logging
import time
import requests
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# Hardcoded values
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"  # Replace with your bot token
TELEGRAM_CHANNEL_ID = "@aiappsselfcreation"  # Replace with your channel ID or username
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A" # Replace with your Gumroad access token
CONVERTKIT_API_KEY = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"  # Replace with your ConvertKit API key

def fetch_api_data(url, headers=None, retries=3, delay=5):
    """Fetch data from API with retries and error handling."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:  # Rate limit error
                logging.warning(f"Rate limited! Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            response.raise_for_status()  # Raise error for 4xx/5xx responses
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API error on attempt {attempt+1}: {e}")
        time.sleep(delay)
    return None  # Return None if all attempts fail

def get_gumroad_earnings():
    """Fetch earnings from Gumroad API with error handling."""
    url = "https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    
    data = fetch_api_data(url, headers)
    
    if data and "sales" in data:
        try:
            total_earnings = sum(float(sale.get('price', 0)) / 100 for sale in data['sales'])
            return f"💰 Gumroad Earnings: ₹{total_earnings:,.2f}"
        except Exception as e:
            logging.error(f"Error processing Gumroad data: {e}")
            return "❌ Failed to process Gumroad earnings data."
    
    return "❌ Failed to fetch Gumroad earnings."

def get_convertkit_subscribers():
    """Fetch subscriber count from ConvertKit API with error handling."""
    url = f"https://api.convertkit.com/v3/subscribers?api_key={CONVERTKIT_API_KEY}"
    
    data = fetch_api_data(url)
    
    if data and "subscribers" in data:
        try:
            return f"📧 ConvertKit Subscribers: {len(data['subscribers'])} active."
        except Exception as e:
            logging.error(f"Error processing ConvertKit data: {e}")
            return "❌ Failed to process ConvertKit data."
    
    return "❌ Failed to fetch ConvertKit data."

def send_telegram_message():
    """Send daily earnings report to Telegram."""
    logging.info("🚀 Fetching earnings data...")

    gumroad_message = get_gumroad_earnings()
    convertkit_message = get_convertkit_subscribers()

    message = (
        "🚀 Daily Earnings Report\n\n"
        f"{gumroad_message}\n"
        f"{convertkit_message}\n\n"
        "✅ Automated updates sent every day at 7:30 AM IST!"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        logging.info("✅ Telegram message sent successfully!")
    else:
        logging.error(f"❌ Failed to send Telegram message. Response: {response.text}")

# Trigger function for the scheduler
def trigger_scheduled_job():
    """Triggered by the scheduler to send the message."""
    send_telegram_message()

if __name__ == "__main__":
    logging.info("🚀 Bot started...")
    # This is useful for local testing, but your scheduler will handle the actual triggering
    app.run(host="0.0.0.0", port=5000)
