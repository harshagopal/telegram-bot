import requests
import random
import time
import os
from datetime import datetime
from base64 import b64decode
from dotenv import load_dotenv

# --- LOAD .env CONFIGURATION ---
load_dotenv()

GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DEEP_AI_API_KEY = os.getenv("DEEP_AI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

CATEGORIES = [
    "Notion Templates", "Digital Planners", "Resume Packs",
    "AI Prompt Collections", "Study Guides / Cheat Sheets"
]

HISTORY_FILE = "history.txt"
CATEGORY_INDEX_FILE = "last_category.txt"

# --- UTILITY FUNCTIONS ---
def safe_json(response):
    try:
        return response.json()
    except Exception:
        print(f"[safe_json] Failed to parse JSON. Response Text:\n{response.text[:300]}")
        raise

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

def retry_request(func, *args, max_attempts=3, **kwargs):
    for attempt in range(max_attempts):
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"[Retry Attempt {attempt+1}] Error: {e}")
            time.sleep(2 + attempt * 2)
    raise Exception(f"All {max_attempts} attempts failed.")

# --- AI CONTENT GENERATION ---
def generate_ai_content(category):
    prompt = f"Generate a catchy TITLE, DESCRIPTION, and PRICE in USD for a digital product in: {category}"

    try:
        response = retry_request(
            requests.post,
            "https://api.deepai.org/api/text-generator",
            data={'text': prompt},
            headers={'api-key': DEEP_AI_API_KEY}
        )
        output = safe_json(response).get("output", "")
    except Exception as e:
        print("[DeepAI Fallback] Failed with error:", e)
        return fallback_text_falcon(category)

    return parse_ai_response(output, category)

def fallback_text_falcon(category):
    try:
        response = retry_request(
            requests.post,
            "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct",
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={"inputs": f"Write a short, catchy product title, description, and price for: {category}"}
        )
        output = safe_json(response)[0]["generated_text"]
        return parse_ai_response(output, category)
    except Exception as e:
        print("[HuggingFace Fallback] Failed with error:", e)
        title = f"{category} Pack {random.randint(100,999)}"
        desc = f"A complete {category.lower()} solution to level up your productivity."
        return title, desc + "\n\n⚡ Grab this limited edition drop!", round(random.uniform(5, 25), 2)

def parse_ai_response(output, category):
    parts = output.split('\n')
    title = parts[0][:100].strip() if parts and len(parts[0]) >= 5 else f"{category} Pack {random.randint(100,999)}"
    description = "\n".join([line.strip() for line in parts[1:3] if line.strip()])
    if len(description) < 20:
        description = f"A power-packed {category.lower()} resource bundle for instant results."
    price = round(random.uniform(5, 25), 2)

    print("[AI Output] Title:", title)
    print("[AI Output] Description:", description)
    print("[AI Output] Price (USD):", price)
    return title, description + "\n\n⚡ Grab this limited edition drop!", price

# --- AI IMAGE GENERATION ---
def generate_ai_thumbnail():
    prompt = random.choice([
        "Smiling human face professional photo",
        "Elegant minimalist planner cover design",
        "Digital art of vibrant organized workspace"
    ])
    try:
        response = retry_request(
            requests.post,
            "https://api.deepai.org/api/text2img",
            data={'text': prompt},
            headers={'api-key': DEEP_AI_API_KEY}
        )
        image_url = safe_json(response).get("output_url")
        print("[Image] DeepAI Output URL:", image_url)
        return image_url
    except Exception as e:
        print("[DeepAI Image Fallback] Error:", e)
        return generate_fallback_image()

def generate_fallback_image():
    try:
        response = retry_request(
            requests.post,
            "https://backend.craiyon.com/generate",
            json={"prompt": "creative modern digital product display"}
        )
        images = safe_json(response).get("images", [])
        if not images:
            raise Exception("Craiyon fallback failed")
        return "data:image/png;base64," + images[0]
    except Exception as e:
        print("[Craiyon Fallback Failed] Error:", e)
        raise

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
    product_id = safe_json(res)["product"]["id"]

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
    product_url = f"https://gumroad.com/l/{product_id}"
    print("[Gumroad] Product Created:", product_url)
    return product_url, thumbnail_url

def cleanup_temp_files():
    for file in ["thumb.jpg", "dummy.txt"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"[Cleanup] Deleted {file}")

# --- TELEGRAM POSTING ---
def send_telegram_message(title, price, url, thumbnail_url=None):
    inr_price = round(price * 83.2, 2)
    caption = f"**{title}**\n\nPrice: ${price} (~₹{inr_price})\n\nLive Now: {url}\n\n🚀 Hurry — this drop won't last!"

    if thumbnail_url and not thumbnail_url.startswith("data:image"):
        image_content = requests.get(thumbnail_url).content
        retry_request(
            requests.post,
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
            files={"photo": ("thumb.jpg", image_content)}
        )
    else:
        retry_request(
            requests.post,
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "Markdown"}
        )

# --- MAIN DRIVER ---
def autopilot():
    print(f"[{datetime.now()}] Started autopilot run.\n")

    category = get_next_category()
    print("[Category] Selected:", category)

    title, description, price = generate_ai_content(category)

    if title in load_history():
        print("[Skip] Already posted:", title)
        return

    image_url = generate_ai_thumbnail()
    product_url, thumb = create_gumroad_product(title, description, price, image_url)
    send_telegram_message(title, price, product_url, thumb)

    update_history(title)
    print("\n[Success] Product Created and Posted!")

# --- RUN ---
if __name__ == "__main__":
    autopilot()
