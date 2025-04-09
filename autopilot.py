import requests
import random
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
CATEGORY_INDEX_FILE = "last_category.txt"

# --- UTILITY FUNCTIONS ---

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def update_history(title):
    with open(HISTORY_FILE, "a") as f:
        f.write(title + "\n")

def get_next_category():
    last = 0
    if os.path.exists(CATEGORY_INDEX_FILE):
        try:
            last = int(open(CATEGORY_INDEX_FILE).read().strip())
        except:
            last = 0
    next_idx = (last + 1) % len(CATEGORIES)
    with open(CATEGORY_INDEX_FILE, "w") as f:
        f.write(str(next_idx))
    return CATEGORIES[next_idx]

def retry_request(func, *args, max_attempts=3, **kwargs):
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(2 + attempt * 2)
    raise Exception(f"All {max_attempts} attempts failed.")

# --- AI CONTENT GENERATION ---

def generate_ai_content(category):
    prompt = f"Generate a catchy digital product TITLE, DESCRIPTION, and PRICE in USD for the category: {category}. Keep it short and appealing."

    response = retry_request(requests.post,
        "https://api.deepai.org/api/text-generator",
        data={'text': prompt},
        headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'}
    )
    output = response.json().get("output", "")

    parts = output.split('\n')
    title = parts[0][:100].strip() if len(parts) > 0 and len(parts[0].strip()) >= 5 else f"{category} Bundle {random.randint(100, 999)}"
    description = "\n".join([line.strip() for line in parts[1:3] if len(line.strip()) > 0])
    if len(description) < 20:
        description = f"A powerful {category.lower()} pack to boost your productivity instantly."

    price = round(random.uniform(5, 25), 2)

    description += f"\n\n⚡ This {category} drop is available for a limited time. Act now!"

    return title, description, price

# --- AI IMAGE GENERATION ---

def generate_ai_thumbnail():
    prompt = random.choice([
        "Smiling human face professional photo",
        "Aesthetic natural landscape, ultra-realistic",
        "Minimalist digital art with vibrant colors",
        "Creative workspace, high resolution",
        "Elegant digital planner cover design"
    ])
    try:
        response = retry_request(requests.post,
            "https://api.deepai.org/api/text2img",
            data={'text': prompt},
            headers={'api-key': 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'}
        )
        return response.json().get("output_url")
    except:
        return generate_fallback_image()

def generate_fallback_image():
    response = retry_request(requests.post,
        "https://backend.craiyon.com/generate",
        json={"prompt": "A beautiful realistic human photo or nature landscape"}
    )
    images = response.json().get("images", [])
    if not images:
        raise Exception("Craiyon fallback failed")
    return "data:image/png;base64," + images[0]

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
    if res.status_code != 200 or "product" not in res.json():
        raise Exception(f"Gumroad creation failed: {res.text}")
    product_id = res.json()["product"]["id"]

    # Add thumbnail
    if thumbnail_url.startswith("data:image"):
        from base64 import b64decode
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

    # Dummy file
    with open("dummy.txt", "w") as f:
        f.write("This is your digital product.")
    with open("dummy.txt", "rb") as file:
        retry_request(
            requests.post,
            f"https://api.gumroad.com/v2/products/{product_id}/files",
            data={"access_token": GUMROAD_ACCESS_TOKEN},
            files={"file": file}
        )

    return f"https://gumroad.com/l/{product_id}", thumbnail_url

# --- TELEGRAM POSTING ---

def send_telegram_message(title, price, url, thumbnail_url=None):
    inr_price = round(price * 83.2, 2)
    caption = f"**{title}**\n\nPrice: ${price} (~₹{inr_price})\n\nLive Now: {url}\n\n🚀 Hurry — this drop won't last!"

    if thumbnail_url and not thumbnail_url.startswith("data:image"):
        retry_request(
            requests.post,
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
            files={"photo": requests.get(thumbnail_url).content}
        )
    else:
        retry_request(
            requests.post,
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": caption, "parse_mode": "Markdown"}
        )

# --- MAIN AUTOPILOT ---

def autopilot():
    log("Started autopilot run.")
    history = load_history()
    category = get_next_category()
    title, description, price = generate_ai_content(category)

    if title in history:
        log(f"Duplicate title found. Skipping: {title}")
        return

    try:
        thumbnail_url = generate_ai_thumbnail()
        product_url, img_url = create_gumroad_product(title, description, price, thumbnail_url)
        send_telegram_message(title, price, product_url, img_url)
        update_history(title)
        log(f"SUCCESS: Uploaded - {title}")
    except Exception as e:
        log(f"FAILURE: {str(e)}")

if __name__ == "__main__":
    autopilot()
