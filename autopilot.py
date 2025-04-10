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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# --- AI CONTENT GENERATION USING OPENAI ---
def generate_ai_content(category):
    prompt = f"""
Generate a catchy TITLE, DESCRIPTION, and PRICE in USD for a digital product in this category: {category}.
Format the response like:
Title: ...
Description: ...
Price: ...
"""
    try:
        response = retry_request(
            requests.post,
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        content = safe_json(response)["choices"][0]["message"]["content"]
        return parse_openai_response(content, category)
    except Exception as e:
        print("[OpenAI Error] Falling back with error:", e)
        return fallback_static(category)

def parse_openai_response(content, category):
    try:
        lines = content.strip().split('\n')
        title = next((line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("title:")), f"{category} Pack {random.randint(100,999)}")
        description = next((line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("description:")), f"An ultimate {category.lower()} toolkit.")
        price = next((float(line.split(":", 1)[1].strip().replace("$", "")) for line in lines if line.lower().startswith("price:")), round(random.uniform(5, 25), 2))
        return title, description + "\n\n⚡ Grab this limited edition drop!", round(price, 2)
    except Exception as e:
        print("[Parse Error] Fallback triggered:", e)
        return fallback_static(category)

def fallback_static(category):
    title = f"{category} Pack {random.randint(100,999)}"
    desc = f"A complete {category.lower()} solution to level up your productivity."
    return title, desc + "\n\n⚡ Grab this limited edition drop!", round(random.uniform(5, 25), 2)

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
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1024"}
        )
        return safe_json(response)["data"][0]["url"]
    except Exception as e:
        print("[Image Generation Fallback] Error:", e)
        return "https://via.placeholder.com/1024x1024.png?text=Digital+Product"

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
