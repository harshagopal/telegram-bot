import json
import requests
from datetime import datetime

# Final Telegram bot credentials
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

# Path to the updates file
UPDATES_FILE = "updates.json"

def load_updates():
    """Load update items from file."""
    try:
        with open(UPDATES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_updates(updates):
    """Write updated items back to file."""
    with open(UPDATES_FILE, "w") as f:
        json.dump(updates, f, indent=2)

def format_message(update):
    """Format Telegram message."""
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p IST")
    return (
        f"*App/Project:* `{update['app']}`\n"
        f"*Update:* {update['update']}\n"
        f"*Time:* _{timestamp}_"
    )

def send_telegram_message(message):
    """Send the formatted message via Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

def main():
    updates = load_updates()
    pending = [u for u in updates if u.get("status") == "pending"]

    if not pending:
        print("No pending updates.")
        return

    for u in pending:
        try:
            msg = format_message(u)
            send_telegram_message(msg)
            u["status"] = "sent"
        except Exception as e:
            print(f"Failed to send update for {u['app']}: {e}")

    save_updates(updates)
    print(f"Sent {len(pending)} update(s).")

if __name__ == "__main__":
    main()
