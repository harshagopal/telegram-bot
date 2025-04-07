import requests
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Constants
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"
CONVERTKIT_API_SECRET = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"

# Determine which summary type to send based on current minute for testing
def get_summary_type():
    minute = datetime.now().minute % 5
    return ["daily", "weekly", "monthly", "quarterly", "yearly"][minute]

# Get ConvertKit subscriber count (past day/week/month/etc.)
def get_convertkit_subscribers(since_date):
    url = f"https://api.convertkit.com/v3/subscribers?api_secret={CONVERTKIT_API_SECRET}&from={since_date.isoformat()}"
    logging.debug(f"ConvertKit URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        subscribers = response.json().get("total_subscribers", 0)
        return subscribers
    except Exception as e:
        logging.error(f"ConvertKit error: {e}")
        return "Error"

# Get Gumroad earnings (past day/week/month/etc.)
def get_gumroad_earnings(since_date):
    url = f"https://api.gumroad.com/v2/sales"
    headers = {"Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"}
    params = {"from": since_date.strftime("%Y-%m-%d")}
    logging.debug(f"Gumroad URL: {url} | Params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        sales = response.json().get("sales", [])
        total_earnings = sum(float(sale.get("price", 0)) / 100 for sale in sales)
        return f"${total_earnings:.2f}"
    except Exception as e:
        logging.error(f"Gumroad error: {e}")
        return "Error"

# Send Telegram message
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    logging.debug(f"Sending Telegram: {payload}")
    response = requests.post(url, data=payload)
    logging.debug(f"Telegram Response: {response.status_code} - {response.text}")

# Determine since_date based on summary type
def get_since_date(summary_type):
    today = datetime.now()
    if summary_type == "daily":
        return today - timedelta(days=1)
    elif summary_type == "weekly":
        return today - timedelta(weeks=1)
    elif summary_type == "monthly":
        return today.replace(day=1)
    elif summary_type == "quarterly":
        month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=month, day=1)
    elif summary_type == "yearly":
        return today.replace(month=1, day=1)
    else:
        return today

# Main Logic
def run_summary():
    summary_type = get_summary_type()
    since_date = get_since_date(summary_type)
    date_str = since_date.strftime("%d-%b-%Y")

    logging.debug(f"Running {summary_type.upper()} summary since {date_str}")

    subscribers = get_convertkit_subscribers(since_date)
    earnings = get_gumroad_earnings(since_date)

    message = (
        f"✅ Update Summary ({summary_type.capitalize()} since {date_str})\n"
        f"- New ConvertKit Subscribers: {subscribers}\n"
        f"- Gumroad Earnings: {earnings}"
    )
    send_telegram_message(message)

if __name__ == "__main__":
    run_summary()
