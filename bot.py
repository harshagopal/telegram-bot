import requests
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Constants (Hardcoded for debug run)
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"  # Numeric ID is safer on Railway

def send_telegram_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = "✅ Railway deployment is working! Message sent successfully."

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
    }

    logging.debug(f"Sending to Telegram with payload: {payload}")
    response = requests.post(url, data=payload)
    logging.debug(f"Response code: {response.status_code}")
    logging.debug(f"Response text: {response.text}")

    if response.status_code == 200:
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Failed to send message. Status: {response.status_code}")

if __name__ == "__main__":
    send_telegram_message()
