import requests
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Constants (Hardcoded)
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

CONVERTKIT_API_SECRET = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"

# Get date range for yesterday (UTC -5.5)
def get_yesterday_range():
    today = datetime.utcnow() - timedelta(hours=5.5)
    start = datetime(today.year, today.month, today.day) - timedelta(days=1)
    end = datetime(today.year, today.month, today.day)
    return start.isoformat() + "Z", end.isoformat() + "Z"

# Fetch ConvertKit subscriber count
def get_convertkit_subscribers():
    url = f"https://api.convertkit.com/v3/subscribers?api_secret={CONVERTKIT_API_SECRET}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return len(data.get("subscribers", []))
    except Exception as e:
        logging.error(f"ConvertKit Error: {e}")
        return "Error"

# Fetch Gumroad sales total
def get_gumroad_earnings():
    start, end = get_yesterday_range()
    url = f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_ACCESS_TOKEN}&after={start}&before={end}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        sales = response.json().get("sales", [])
        total = sum(float(s.get("price", 0)) / 100 for s in sales)
        return f"${total:.2f}"
    except Exception as e:
        logging.error(f"Gumroad Error: {e}")
        return "Error"

# Send Telegram message
def send_telegram_message(subs, earnings):
    summary_date = (datetime.utcnow() - timedelta(hours=5.5 + 24)).strftime("%d-%b-%Y")
    message = (
        f"✅ Update Summary ({summary_date})\n"
        f"- New ConvertKit Subscribers: {subs}\n"
        f"- Gumroad Earnings: {earnings}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    
    try:
        logging.debug(f"Sending to Telegram with payload: {payload}")
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logging.debug("Telegram message sent.")
    except Exception as e:
        logging.error(f"Telegram Error: {e}")

# Main
if __name__ == "__main__":
    subs = get_convertkit_subscribers()
    earnings = get_gumroad_earnings()
    send_telegram_message(subs, earnings)
