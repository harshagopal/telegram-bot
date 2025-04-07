import requests
import logging
from datetime import datetime, timedelta
import pytz

# Logging setup
logging.basicConfig(level=logging.INFO)

# Constants (hardcoded)
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"
CONVERTKIT_API_SECRET = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"

# Function to detect which summaries to send
def get_summary_types():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
    summary_types = []

    if now.hour == 2:
        summary_types.append("daily")

        if now.weekday() == 0:  # Monday
            summary_types.append("weekly")
        
        if now.day == 1:
            summary_types.append("monthly")

            if now.month in [1, 4, 7, 10]:  # Quarterly start
                summary_types.append("quarterly")
            
            if now.month == 1:
                summary_types.append("yearly")
    
    return summary_types, now

def fetch_convertkit_subscribers(since_date):
    url = f"https://api.convertkit.com/v3/subscribers"
    params = {
        "api_secret": CONVERTKIT_API_SECRET,
        "from_date": since_date.isoformat()
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return len(response.json().get("subscribers", []))
        else:
            logging.error(f"ConvertKit Error: {response.text}")
            return 0
    except Exception as e:
        logging.error(f"ConvertKit Exception: {e}")
        return 0

def fetch_gumroad_earnings(since_date):
    url = "https://api.gumroad.com/v2/sales"
    params = {
        "access_token": GUMROAD_ACCESS_TOKEN,
        "since": since_date.strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            sales = response.json().get("sales", [])
            return sum(float(sale.get("price", 0)) / 100 for sale in sales)
        else:
            logging.error(f"Gumroad Error: {response.text}")
            return 0.0
    except Exception as e:
        logging.error(f"Gumroad Exception: {e}")
        return 0.0

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Message sent successfully.")
        else:
            logging.error(f"Telegram Error: {response.text}")
    except Exception as e:
        logging.error(f"Telegram Exception: {e}")

def get_since_date(now, summary_type):
    if summary_type == "daily":
        return now - timedelta(days=1)
    elif summary_type == "weekly":
        return now - timedelta(weeks=1)
    elif summary_type == "monthly":
        return now.replace(day=1) - timedelta(days=1)
    elif summary_type == "quarterly":
        quarter_start_month = (now.month - 1) // 3 * 3 + 1
        start = datetime(now.year, quarter_start_month, 1, tzinfo=now.tzinfo)
        return start - timedelta(days=1)
    elif summary_type == "yearly":
        return datetime(now.year, 1, 1, tzinfo=now.tzinfo) - timedelta(days=1)

def main():
    summary_types, now = get_summary_types()
    for s_type in summary_types:
        since_date = get_since_date(now, s_type)
        subs = fetch_convertkit_subscribers(since_date)
        earnings = fetch_gumroad_earnings(since_date)

        msg = (
            f"✅ Update Summary ({s_type.capitalize()} since {since_date.strftime('%d-%b-%Y')})\n"
            f"- New ConvertKit Subscribers: {subs}\n"
            f"- Gumroad Earnings: ${earnings:.2f}"
        )
        send_telegram_message(msg)

if __name__ == "__main__":
    main()
