import requests
import pytz
from datetime import datetime
import logging

# Constants
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"
CONVERTKIT_API_SECRET = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"

# Logging
logging.basicConfig(level=logging.INFO)

def fetch_convertkit_subscribers(since_date):
    url = f"https://api.convertkit.com/v3/subscribers?api_secret={CONVERTKIT_API_SECRET}&from_date={since_date}"
    try:
        response = requests.get(url)
        data = response.json()
        return len(data.get("subscribers", []))
    except Exception as e:
        logging.error(f"Error fetching ConvertKit data: {e}")
        return "Error"

def fetch_gumroad_earnings(since_date):
    url = f"https://api.gumroad.com/v2/sales?access_token={GUMROAD_ACCESS_TOKEN}&since={since_date}"
    try:
        response = requests.get(url)
        data = response.json()
        total = sum(float(sale["price"]) / 100 for sale in data.get("sales", []))
        return f"${total:.2f}"
    except Exception as e:
        logging.error(f"Error fetching Gumroad data: {e}")
        return "Error"

def get_summary_types():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    minute = now.minute
    summary_types = []

    if 0 <= minute < 5:
        summary_types.append("daily")
    elif 5 <= minute < 10:
        summary_types.append("weekly")
    elif 10 <= minute < 15:
        summary_types.append("monthly")
    elif 15 <= minute < 20:
        summary_types.append("quarterly")
    elif 20 <= minute < 25:
        summary_types.append("yearly")

    return summary_types, now

def get_start_date(summary_type, now):
    if summary_type == "daily":
        return (now.replace(hour=0, minute=0, second=0)).strftime("%Y-%m-%d")
    elif summary_type == "weekly":
        start = now - timedelta(days=now.weekday())
        return start.strftime("%Y-%m-%d")
    elif summary_type == "monthly":
        return now.replace(day=1).strftime("%Y-%m-%d")
    elif summary_type == "quarterly":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        return now.replace(month=quarter_start_month, day=1).strftime("%Y-%m-%d")
    elif summary_type == "yearly":
        return now.replace(month=1, day=1).strftime("%Y-%m-%d")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Message sent successfully.")
        else:
            logging.error(f"Failed to send message: {response.text}")
    except Exception as e:
        logging.error(f"Telegram send error: {e}")

def main():
    summary_types, now = get_summary_types()
    if not summary_types:
        logging.info("No summary due at this time.")
        return

    for summary_type in summary_types:
        start_date = get_start_date(summary_type, now)
        ck_count = fetch_convertkit_subscribers(start_date)
        gumroad_earnings = fetch_gumroad_earnings(start_date)

        message = (
            f"✅ Update Summary ({summary_type.capitalize()} since {start_date})\n"
            f"- New ConvertKit Subscribers: {ck_count}\n"
            f"- Gumroad Earnings: {gumroad_earnings}"
        )
        send_telegram_message(message)

if __name__ == "__main__":
    main()
