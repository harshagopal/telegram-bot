import requests
import random
import time
import os
from datetime import datetime
from base64 import b64decode

# --- CONFIGURATION ---
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"
DEEP_AI_API_KEY = "e574a317-d252-477f-9317-d00f71a87c54"
HUGGINGFACE_API_KEY = "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"

CATEGORIES = [
    "Notion Templates", "Digital Planners", "Resume Packs",
    "AI Prompt Collections", "Study Guides / Cheat Sheets"
]

HISTORY_FILE = "history.txt"
CATEGORY_INDEX_FILE = "last_category.txt"

# --- UTILITIES ---
def log(msg): print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def retry_request(func, *args, max_attempts=3, **kwargs):
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2 + attempt * 2)
    raise Exception("All retry attempts failed.")

def load_history():
    return set(open(HISTORY_FILE).read().splitlines()) if os.path.exists(HISTORY_FILE) else set()

def update_history(title):
    with open(HISTORY_FILE, "a") as f:
        f.write(title + "\n")

def get_next_category():
    last = int(open(CATEGORY_INDEX_FILE).read().strip()) if os.path.exists(CATEGORY_INDEX_FILE) else 0
    next_idx = (last + 1) % len(CATEGORIES)
    with open(CATEGORY_INDEX_FILE, "w") as f:
        f.write(str(next_idx))
    return CATEGORIES[next_idx]

# --- AI CONTENT GENERATION ---
def generate_ai_content(category):
    prompt = f"Generate a catchy TITLE, DESCRIPTION, and PRICE in USD for a digital product in: {category}"
    
    # DeepAI
    try:
        res = retry_request(
            requests.post,
            "https://api.deepai.org/api/text-generator",
            data={'text': prompt},
            headers={'api-key': DEEP_AI_API_KEY}
        )
        output = res.json().get("output", "").strip()
        if output: return parse_ai_response(output, category)
    except Exception as e:
        log(f"DeepAI failed: {e}")

    # Hugging Face Falcon
    try:
        res = retry_request(
            requests.post,
            "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct",
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": f"Write a short product title, description, and price for: {category}"}
        )
        output = res.json()[0].get("generated_text", "").strip()
        if output: return parse_ai_response(output, category)
    except Exception as e:
        log(f"HuggingFace Falcon failed: {e}")

    # Fallback (static)
    title = f"{category} Bundle {random.randint(100,999)}"
    desc = f"An essential {category.lower()} pack for immediate use."
    return title, desc + "\n\n⚡ Grab this limited edition drop!", round(random.uniform(5, 25), 2)

def parse_ai_response(output, category):
    parts = output.split('\n')
    title = parts[0][:100].strip() if parts else f"{category} Pack {random.randint(100,999)}"
    desc = "\n".join([line.strip() for line in parts[1:3] if line.strip()])
    if len(desc) < 20:
        desc = f"A power-packed {category.lower()} resource bundle for instant results."
    price = round(random.uniform(5, 25), 2)
    return title, desc + "\n\n⚡ Grab this limited edition drop!", price

# --- AI IMAGE GENERATION ---
def generate_ai_thumbnail():
    prompt = random.choice([
        "Smiling human face professional photo",
        "Elegant minimalist planner cover design",
        "Digital art of vibrant organized workspace"
    ])
    # DeepAI
    try:
        res = retry_request(
            requests.post,
            "https://api.deepai.org/api/text2img",
            data={'text': prompt},
            headers={'api-key': DEEP_AI_API_KEY}
        )
        return res.json().get("output_url")
    except Exception as e:
        log(f"DeepAI image gen failed: {e}")
    
    # Craiyon fallback
    try:
        res = retry_request(
            requests.post,
            "https://backend.craiyon.com/generate",
            json={"prompt": "creative modern digital product display"}
        )
        images = res.json().get("images", [])
        if images:
            return "data:image/png;base64," + images[0]
    except Exception as e:
        log(f"Craiyon fallback failed: {e}")

    # Final fallback
    return "https://via.placeholder.com/600x400?text=Digital+Product"

# --- GUMROAD UPLOAD ---
def create_gumroad_product(title, description, price, thumbnail_url):
    url = "https://api.gumroad.com/v2/products"
    payload = {
        "access_token": GUMROAD_ACCESS_TOKEN,
        "name": title,
        "description": description,
        "price": int(price * 100),
        "published": True
    }

    res = retry_request(requests.post, url, data=payload)
    data = res.json()
    if res.status_code != 200 or "product" not in data:
        raise Exception(f"Gumroad creation failed: {res.text}")
    product_id = data["product"]["id"]

    # Upload thumbnail
    if thumbnail_url.startswith("data:image"):
        img_data = b64decode(thumbnail_url.split(",")[1])
    else:
        img_data = requests.get(thumbnail_url).content

    with open("thumb.jpg", "wb") as f:
        f.write(img_data)

    with open("thumb.jpg", "rb") as img_file:
        retry_request(
            requests.put,
            f"https://api.gumroad.com/v2/products/{product_id}/edit",
            data={"access_token": GUMROAD_ACCESS_TOKEN},
            files={"preview": img_file}
        )

    # Upload dummy product file
    with open("dummy.txt", "w") as f:
        f.write("This is your product. Thank you for purchasing!")

    with open("dummy.txt", "rb") as file:
        retry_request(
            requests.post,
            f"https://api.gumroad.com/v2/products/{product_id}/files",
            data={"access_token": GUMROAD_ACCESS_TOKEN},
            files={"file": file}
        )

    cleanup_temp_files()
    return f"https://gumroad.com/l/{product_id}", thumbnail_url

def cleanup_temp_files():
    for f in ["thumb.jpg", "dummy.txt"]:
        if os.path.exists(f):
            os.remove(f)

# --- TELEGRAM POSTING ---
def send_telegram_message(title, price, url, thumbnail_url=None):
    inr_price = round(price * 83.2, 2)
    caption = f"**{title}**\n\nPrice: ${price} (~₹{inr_price})\n\nLive Now: {url}\n\n🚀 Hurry — this drop won't last!"

    try:
        if thumbnail_url and not thumbnail_url.startswith("data:image"):
            image_bytes = requests.get(thumbnail_url).content
            retry_request(
                requests.post,
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": image_bytes}
            )
        else:
            retry_request(
                requests.post,
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "Markdown"}
            )
    except Exception as e:
        log(f"Telegram message failed: {e}")

# --- MAIN ---
def autopilot():
    log("Started autopilot run.")
    history = load_history()
    category = get_next_category()
    title, desc, price = generate_ai_content(category)

    if title in history:
        log(f"Duplicate title found. Skipping: {title}")
        return

    try:
        thumbnail_url = generate_ai_thumbnail()
        product_url, img_url = create_gumroad_product(title, desc, price, thumbnail_url)
        send_telegram_message(title, price, product_url, img_url)
        update_history(title)
        log(f"SUCCESS: {title} uploaded to Gumroad.")
    except Exception as e:
        log(f"FINAL FAILURE: {e}")

if __name__ == "__main__":
    autopilot()
