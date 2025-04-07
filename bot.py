import requests
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Telegram Constants (Hardcoded for now, replace with Railway Env Vars if needed)
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"  # Or numeric ID: "-1002610167772"

# Dummy data fetchers
def get_dummy_convertkit_subscribers():
    logging.debug("Fetching dummy ConvertKit subscribers")
    return 5

def get_dummy_gumroad_earnings():
    logging.debug("Fetching dummy Gumroad earnings")
    return 124.95

# Message sender
def send_telegram_message(subscribers, earnings):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = (
        "✅ Update Summary\n"
        f"- New ConvertKit Subscribers: {subscribers}\n"
        f"- Gumroad Earnings: ${earnings:.2f}"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
    }

    logging.debug(f"Sending to Telegram with payload: {payload}")
    response = requests.post(url, data=payload)
    logging.debug(f"Response code: {response.status_code}")
    logging.debug(f"Response text: {response.text}")

    if response.status_code == 200:
        print("✅ Telegram message sent successfully!")
    else:
        print(f"❌ Telegram message failed. Status: {response.status_code}")

# Main execution
if __name__ == "__main__":
    logging.info("Starting Telegram Update Bot")
    subscribers = get_dummy_convertkit_subscribers()
    earnings = get_dummy_gumroad_earnings()
    send_telegram_message(subscribers, earnings)
