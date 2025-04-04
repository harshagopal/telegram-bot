import requests

# Replace with your bot's token and your channel's ID directly in the script
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"  # Hardcoded token
TELEGRAM_CHANNEL_ID = "@aiappsselfcreation"  # Hardcoded channel ID

# Send a message to the Telegram channel
def send_telegram_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": "Hi",  # Message you want to send
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Error: {response.text}")

if __name__ == "__main__":
    send_telegram_message()
