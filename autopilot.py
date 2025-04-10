import openai
import requests
import random
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
OPENAI_API_KEY = "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"
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

CATEGORIES = [
    "Notion Templates", "Digital Planners", "Resume Packs",
    "AI Prompt Collections", "Study Guides / Cheat Sheets"
]

HISTORY_FILE = "history.txt"
CATEGORY_INDEX_FILE = "last_category.txt"

openai.api_key = OPENAI_API_KEY

# --- UTILITIES ---
def safe_json(response):
    try:
        return response.json()
    except Exception:
        print(f"[safe_json] Failed to parse JSON:\n{response.text[:300]}")
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

# --- AI CONTENT GENERATION (OpenAI) ---
def generate_ai_content(category):
    prompt = f"Create a catchy TITLE, DESCRIPTION, and PRICE in USD for a digital product in: {category}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=200
        )
        content = response['choices'][0]['message']['content']
        return parse_ai_response(content, category)
    except Exception as e:
        print("[OpenAI Text Generation Failed] Error:", e)
        fallback_title = f"{category} Pack {random.randint(100,999)}"
        fallback_desc = f"A complete {category.lower()} solution to level up your productivity."
        return fallback_title, fallback_desc + "\n\n⚡ Grab this limited edition drop!", round(random.uniform(5, 25), 2)

def parse_ai_response(output, category):
    lines = output.strip().split('\n')
    title = lines[0].strip() if lines else f"{category} Pack {random.randint(100,999)}"
    desc = "\n".join([line.strip() for line in lines[1:3] if line.strip()])
    if len(desc) < 20:
        desc = f"A power-packed {category.lower()} resource bundle for instant results."
    price = round(random.uniform(5, 25), 2)
    print("[AI Output] Title:", title)
    print("[AI Output] Description:", desc)
    print("[AI Output] Price (USD):", price)
    return title, desc + "\n\n⚡ Grab this limited edition drop!", price

# --- AI IMAGE GENERATION (DALL·E via OpenAI) ---
def generate_ai_thumbnail():
    prompt = random.choice([
        "Smiling human face professional photo",
        "Elegant minimalist planner cover design",
        "Digital art of vibrant organized workspace"
    ])
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        img_data = requests.get(image_url).content
        with open("thumb.jpg", "wb") as f:
            f.write(img_data)
        print("[Image] OpenAI DALL·E generated.")
        return "thumb.jpg"
    except Exception as e:
        print("[OpenAI Image Generation Failed] Error:", e)
        raise

# --- GUMROAD UPLOAD ---
def create_gumroad_product(title, description, price, thumbnail_path):
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

    with open(thumbnail_path, "rb") as img_file:
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
    return product_url, thumbnail_path

def cleanup_temp_files():
    for file in ["thumb.jpg", "dummy.txt"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"[Cleanup] Deleted {file}")

# --- TELEGRAM POSTING ---
def send_telegram_message(title, price, url, thumbnail_path=None):
    inr_price = round(price * 83.2, 2)
    caption = f"**{title}**\n\nPrice: ${price} (~₹{inr_price})\n\nLive Now: {url}\n\n🚀 Hurry — this drop won't last!"

    if thumbnail_path and os.path.exists(thumbnail_path):
        with open(thumbnail_path, "rb") as img:
            retry_request(
                requests.post,
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": img}
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

    image_path = generate_ai_thumbnail()
    product_url, thumb_path = create_gumroad_product(title, description, price, image_path)
    send_telegram_message(title, price, product_url, thumb_path)

    update_history(title)
    print("\n[Success] Product Created and Posted!")

# --- RUN ---
if __name__ == "__main__":
    autopilot()
