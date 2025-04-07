import json
import requests
from datetime import datetime

# Telegram config
BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
CHAT_ID = "@aiappsselfcreation"
UPDATES_FILE = "updates.json"

def load_updates():
    with open(UPDATES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_update_message(updates):
    message = "**Development Progress Updates**\n\n"

    for app, entries in updates.items():
        # Filter only non-completed items
        pending = [entry for entry in entries if entry["status"].lower() != "completed"]
        if not pending:
            continue

        message += f"**{app.replace('_', ' ').title()}**\n"
        for entry in pending:
            title = entry.get("title", "Untitled Task")
            details = entry.get("details", "")
            status = entry.get("status", "Unknown")
            timestamp = entry.get("timestamp", "")
            timestamp_fmt = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M") if timestamp else "N/A"

            message += f"• {title} [{status}] - {timestamp_fmt}\n  - {details}\n"
        message += "\n"

    return message.strip()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Telegram send failed: {response.text}")

def main():
    updates = load_updates()
    message = format_update_message(updates)
    
    if message.strip():
        send_telegram_message(message)
    else:
        print("No pending updates to send.")

if __name__ == "__main__":
    main()
