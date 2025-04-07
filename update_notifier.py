import requests
import logging

# Telegram Config
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

# Logging Setup
logging.basicConfig(level=logging.INFO)

def send_custom_update(title, message):
    full_message = f"**{title}**\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logging.info("Update sent successfully.")
        else:
            logging.error(f"Telegram Error: {response.text}")
    except Exception as e:
        logging.error(f"Telegram Exception: {e}")

# Example usage
if __name__ == "__main__":
    send_custom_update("APK Ready", "The latest build of Karuneeka Sangha is available:\nhttps://your-link.com")
