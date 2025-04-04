import requests

BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
CHAT_ID = "668831071"
MESSAGE = "Hello, this is an automated message from my Telegram bot!"

def send_message():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": MESSAGE}
    response = requests.post(url, data=data)
    return response.json()

if __name__ == "__main__":
    send_message()
