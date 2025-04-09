import requests
import random
import json
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
GUMROAD_ACCESS_TOKEN = "2Ot9MDcaOCiQkPZF0vfjGaqIkQEl9NsKmm8Ouzgq29A"
GUMROAD_USER_ID = "harshag24"
TELEGRAM_BOT_TOKEN = "7903820907:AAHEwfUQEZMrwkG-bU8kCFZ0fJOAUTDGUuA"
TELEGRAM_CHAT_ID = "@aiappsselfcreation"

CATEGORIES = [
    "Notion Templates",
    "Digital Planners",
    "Resume Packs",
    "AI Prompt Collections",
    "Study Guides / Cheat Sheets"
]

HISTORY_FILE = "history.txt"

# --- UTILITY FUNCTIONS ---

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def update_history(title):
    with open(HISTORY_FILE, "a") as f:
        f.write(title + "\n")

def get_next_category():
    idx_file = "last_category.txt"
    last = 0
    if os.path.exists(idx_file):
        with open(idx_file, "r") as f:
            last = int(f.read().strip())
    next_idx = (last + 1) % len(CATEGORIES)
    with open(idx_file, "w") as f:
        f.write(str(next_idx))
    return CATEGORIES[next_idx]

def generate_ai_content(category):
    # Use HuggingFace inference API or replicate for free GPT-J
    prompt = f"Generate a SEO-optimized, intriguing digital product title, description, and price in USD for category: {category}"
    response = requests.post(
        "https://api.deepai.org/api/text-generator",
        data={'text': prompt},
        headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'}  # Free DeepAI key
    )
    output = response.json().get("output", "")
    parts = output.split('\n')
    title = parts[0][:100].strip() if len(parts) > 0 else f"{category} Pack {random.randint(100,999)}"
    description = "\n".join(parts[1:3]).strip() if len(parts) > 2 else f"A premium {category.lower()} bundle to boost your productivity."
    price = round(random.uniform(5, 25), 2)
    return title, description, price

def generate_ai_thumbnail():
    prompt = random.choice([
        "Smiling human face professional photo",
        "Aesthetic natural landscape, ultra-realistic",
        "Minimalist digital art with vibrant colors",
        "Creative workspace, high resolution",
        "Elegant digital planner cover design"
    ])
    response = requests.post(
        "https://api.deepai.org/api/text2img",
        data={'text': prompt},
        headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'}
    )
    return response.json().get("output_url")

def create_gumroad_product(title, description, price, thumbnail_url):
    url = "https://api.gumroad.com/v2/products"
    payload = {
        "access_token": GUMROAD_ACCESS_TOKEN,
        "name": title,
        "description": description,
        "price": int(price * 100),  # in cents
        "published": True
    }
    res = requests.post(url, data=payload)
    if res.status_code != 200 or "product" not in res.json():
        raise Exception(f"Gumroad creation failed: {res.text}")
    product_id = res.json()["product"]["id"]

    # Add thumbnail
    img = requests.get(thumbnail_url).content
    with open("thumb.jpg", "wb") as f:
        f.write(img)
    with open("thumb.jpg", "rb") as img_file:
        requests.put(f"https://api.gumroad.com/v2/products/{product_id}/edit",
            data={"access_token": GUMROAD_ACCESS_TOKEN},
            files={"preview": img_file}
        )

    # Add a dummy file to satisfy Gumroad
    with open("dummy.txt", "w") as f:
        f.write("This is your digital product.")
    with open("dummy.txt", "rb") as file:
        requests.post(
            f"https://api.gumroad.com/v2/products/{product_id}/files",
            data={"access_token": GUMROAD_ACCESS_TOKEN},
            files={"file": file}
        )

    product_url = f"https://gumroad.com/l/{product_id}"
    return product_url

def send_telegram_message(title, price, url):
    inr_price = round(price * 83.2, 2)
    text = f"**{title}**\n\nPrice: ${price} (~₹{inr_price})\n\nLive Now: {url}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    )

# --- MAIN AUTOPILOT FUNCTION ---

def autopilot():
    history = load_history()
    category = get_next_category()
    title, description, price = generate_ai_content(category)

    if title in history:
        print(f"Duplicate title skipped: {title}")
        return

    try:
        thumbnail_url = generate_ai_thumbnail()
        product_url = create_gumroad_product(title, description, price, thumbnail_url)
        send_telegram_message(title, price, product_url)
        update_history(title)
        print(f"Uploaded: {title}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    autopilot()
