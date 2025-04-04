import logging
import requests
from flask import Flask

# Configure logging with a better format
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask app
app = Flask(__name__)

# Hardcoded values (provided by you)
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"  # Your Telegram bot token
TELEGRAM_CHANNEL_ID = "@aiappsselfcreation"  # Your Telegram channel ID or username
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"  # Your Gumroad access token
CONVERTKIT_API_KEY = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"  # Your ConvertKit API key

def send_telegram_message():
    """Send a simple 'Hi' message to Telegram."""
    logging.info("🚀 Sending message to Telegram...")

    # Message content
    message = "Hi"

    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": message, "parse_mode": "Markdown"}

    try:
        # Send request to Telegram
        response = requests.post(url, json=payload)

        # Check if the message was sent successfully
        if response.status_code == 200:
            logging.info("✅ Telegram message sent successfully!")
        else:
            logging.error(f"❌ Failed to send Telegram message. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error occurred while sending the message: {e}")

def send_gumroad_message():
    """Send a request to the Gumroad API."""
    logging.info("🚀 Sending message to Gumroad...")

    # Gumroad API endpoint for sending data
    url = "https://api.gumroad.com/v2/your_endpoint_here"  # Replace with actual endpoint
    headers = {
        "Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"
    }
    payload = {
        # Add necessary payload parameters here
    }

    try:
        # Send request to Gumroad
        response = requests.post(url, headers=headers, data=payload)

        # Check if the request was successful
        if response.status_code == 200:
            logging.info("✅ Gumroad request sent successfully!")
        else:
            logging.error(f"❌ Failed to send Gumroad request. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error occurred while sending the Gumroad request: {e}")

def send_convertkit_message():
    """Send a request to the ConvertKit API."""
    logging.info("🚀 Sending request to ConvertKit...")

    # ConvertKit API endpoint for sending data
    url = "https://api.convertkit.com/v3/your_endpoint_here"  # Replace with actual endpoint
    params = {
        "api_key": CONVERTKIT_API_KEY,
        # Add necessary parameters here
    }

    try:
        # Send request to ConvertKit
        response = requests.get(url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            logging.info("✅ ConvertKit request sent successfully!")
        else:
            logging.error(f"❌ Failed to send ConvertKit request. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error occurred while sending the ConvertKit request: {e}")

@app.route('/')
def home():
    """Basic route to check if the Flask app is running."""
    return "Bot is up and running!"

if __name__ == "__main__":
    logging.info("🚀 Bot started...")
    # Run Flask app (Railway will handle the port dynamically)
    app.run(host="0.0.0.0", port=5000)
