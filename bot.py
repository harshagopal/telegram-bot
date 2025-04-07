import requests
import logging
from datetime import datetime, timedelta
from time import sleep

# === Logging Config ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Constants (Hardcoded) ===
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

CONVERTKIT_API_SECRET = "0C9EKl_OG2Q_xC788hz1lEt2p3algRB2q2OvOcrgpHo"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"

# === Retry Wrapper ===
def retry_request(func, name, retries=3, wait=3):
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            logging.warning(f"[{name}] Attempt {attempt} failed: {e}")
            if attempt < retries:
                sleep(wait)
            else:
                logging.error(f"[{name}] All attempts failed.")
                return "N/A"

# === ConvertKit Subscribers Count ===
def fetch_convertkit_subscribers():
    url = "https://api.convertkit.com/v3/subscribers"
    params = {
        "api_secret": CONVERTKIT_API_SECRET
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if "subscribers" not in data:
        raise ValueError("Invalid ConvertKit response structure.")

    subscribers = data["subscribers"]
    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    new_subs_count = 0
    for sub in subscribers:
        created_at = sub.get("created_at")
        if not created_at:
            continue
        created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if created_time > cutoff_time:
            new_subs_count += 1

    return new_subs_count

# === Gumroad Earnings ===
def fetch_gumroad_earnings():
    url = "https://api.gumroad.com/v2/sales"
    headers = {
        "Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}"
    }
    params = {
        "after": (datetime.utcnow() - timedelta(hours=24)).isoformat()
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if "sales" not in data:
        raise ValueError("Invalid Gumroad response structure.")

    total = sum(float(sale.get("price", 0)) / 100 for sale in data["sales"])
    return f"${total:.2f}"

# === Send Telegram Message ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=payload, timeout=10)
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise ValueError(f"Telegram error: {result}")

# === Main ===
def main():
    logging.info("=== Daily Telegram Update Script Started ===")

    # Retry-protected calls
    subs = retry_request(fetch_convertkit_subscribers, "ConvertKit")
    earnings = retry_request(fetch_gumroad_earnings, "Gumroad")

    # Final message
    message = (
        f"✅ Update Summary\n"
        f"- New ConvertKit Subscribers: {subs}\n"
        f"- Gumroad Earnings: {earnings}"
    )

    # Send to Telegram
    try:
        send_telegram_message(message)
        logging.info("[Telegram] Message sent successfully.")
    except Exception as e:
        logging.error(f"[Telegram] Failed to send message: {e}")

    logging.info("=== Script Execution Complete ===")

if __name__ == "__main__":
    main()
