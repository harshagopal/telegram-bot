import os
import time
import random
import requests
import logging
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import numpy as np
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import threading

# Configure logging with detailed format for diagnostics
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Stream to stdout for Railway logs
        logging.FileHandler('/app/logs/runtime.log')  # File for persistence
    ]
)
logger = logging.getLogger(__name__)

# Deployment-specific logger
deployment_logger = logging.getLogger('deployment')
deployment_logger.setLevel(logging.INFO)
deployment_logger.addHandler(logging.FileHandler('/app/logs/deployment.log'))

# Hardcoded Credentials
GMAIL_CREDENTIALS = {
    "client_id": "350046852277-da896jddcm7jgoj0q0vrk0v9shjor7l9.apps.googleusercontent.com",
    "client_secret": "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",
    "refresh_token": "1//04YhiuDNDBo7hCgYIARAAGAQSNwF-L9IrFoIEFuLh3GNwFmtquTehRyqMYTbrJ4IMdbvyi2ftwDe2msc1pJajj31qqcGf-vkOMUw",
    "access_token": "ya29.a0AZYkNZiDJRxO57M_X84FVSojtJ5UYoJGklg2f0emuv30dZw99z67RoOOL3uGguar_FiTLV0jI8nvbS8phCWAhVyy3i0EVBoAZ7FLqE-0gRwZNt1r4U-AlqzbLGkqeKph8LkoNIluqzHFa-Pr9HsAB9nW1U4DZoQzT5wXlZOpaCgYKAeQSARESFQHGX2MipFjyraPrmoyni6rRFwNn6w0175"
}

YOUTUBE_PLAN_A = {
    "client_id": "160820889531-n0esqor00kr79stf7trkdul7b67acabs.apps.googleusercontent.com",
    "client_secret": "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",
    "refresh_token": "1//04Ro32jYbn3SCCgYIARAAGAQSNwF-L9Ir7GzQ52vy3useymmO7uNMdCAu14Zk6cB3AYsE2k4njH4vrkp71xTB16jb4NY3DmCMlSQ",
    "access_token": "ya29.a0AZYkNZjd8CJIFhpcA_3ASQmNgaTsIUvRE3l0PdqzOEa3bH7uPR9KKS3LPJhIgF-BMO1csv8fC_GiJjSU6gfxfdaKRLmeo3VA2P55rCMZzO9qxt0FJfJzGqofwplRYVRRS0Ex0_EhBL6nxXu6mR2ewwdfN5Mti-vQiOVaq77YaCgYKATMSARESFQHGX2MiJW9UvVKTCuLqSADHamyzJg0175"
}

YOUTUBE_PLAN_B = {
    "client_id": "802931507603-9v48iiq95n6i46sjtv92t7gb095vm0mb.apps.googleusercontent.com",
    "client_secret": "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",
    "refresh_token": "1//0gCR50xfYuhpwCgYIARAAGBASNwF-L9IrSI_7QFRouzS9c69z32TDXDIvCOrBuMS_hafP05cnE-iTBaHHVJKKOY-z1uTlK8_NtxA",
    "access_token": "ya29.a0AZYkNZjsQnIU6XU-ceDhBMGBmlbBJ7crzhenXOHFDxc1isciqVE3sa-Ap6t0bfwXjVRV9JXaE26fet4HTnmFSz2zhlB_d_G_pvRn5mFnAsZNcrgMpcApuyX46czkUmAOK-irDaHGAxSpSdpZrJLFBcvmy7LyOBTDJirXvUAnaCgYKAc0SARESFQHGX2MipnMetkuyNtkF-dbd75iIzg0175"
}

# ElevenLabs API Key
ELEVENLABS_API_KEY = "sk_50a5f87e18e0150ab0cd71e703c0e08561deef6e7d0db668"

# Main Categories and Their Subcategories
CATEGORIES = {
    "Motivation & Success": ["Motivation & Success Stories"],
    "Tech & Innovation": ["Tech News & AI Updates"],
    "Finance & Investments": ["Finance & Stock Market Tips"],
    "Health & Wellness": ["Relaxing Music & Meditation"],
    "Branding & Growth Strategies": ["Storytelling & Facts", "Sponsorship & Brand Deals"],
    "Productivity & Self-Improvement": ["Side Hustle You Can Start For Free", "Learning New Skills with AI", "Best Free Software for Work & Study", "Time Management & Productivity Hacks"],
    "Content Creation & Social Media Growth": ["Best Affiliate Marketing Strategies", "Blogging & SEO for Maximum Traffic", "AI Tools for Content Creation", "Instagram, Twitter, LinkedIn Automation", "YouTube Growth & Monetization"],
    "Digital Products Monetization": ["Print-on-Demand & Dropshipping", "Best Marketplaces to Sell Digital Products", "How to Sell Templates & Digital Assets", "Ebooks & Online Courses"],
    "Business & Finance": ["Freelancing & Remote Work", "Personal Finance & Investment Tips", "Cryptocurrency & Blockchain Basics", "Stock Market & Trading Insights", "Passive Income Strategies"],
    "Tech & Gadgets": ["AI Tools & SaaS Platforms", "Software & Tool Comparisons", "Best Tech Deals & Discounts", "Unboxing & First Impressions", "Reviews and Ratings"],
    "Software Development": ["Cloud Computing & DevOps", "AI & Machine Learning Projects", "Mobile App Development", "Web Development", "Python", "Java"]
}

# Subcategories under "Storytelling & Facts" (under "Branding & Growth Strategies")
STORYTELLING_SUBTOPICS = {
    "Upanishads": ["All 108 mentioned", "Detailed summaries for 10 prominent ones"],
    "Vedas": ["Each Veda covered individually", "Summary for the most influential"],
    "Agamas": ["Core principles", "Temple architecture", "Rituals"],
    "Puranas": ["Standalone stories from each Purana", "Summary of major Puranas (e.g., Bhagavata, Vishnu, Shiva)"],
    "Ramayana Perspectives": ["Rama’s perspective", "Sita’s perspective", "Lakshmana’s perspective", "Ravana’s perspective", "Hanuman’s perspective", "Key morals and cultural wisdom"],
    "Mahabharata Perspectives": ["Krishna’s perspective", "Yudhishthira/Dharmaraya’s perspective", "Bhima’s perspective", "Bhishma’s perspective", "Duryodhana’s perspective", "Moral interpretations"],
    "Teachings of Spiritual Masters": ["Adi Shankaracharya", "Ramanujacharya", "Madhvacharya"],
    "Sanatana Dharma vs Science vs World Cultures": ["Analogies with Greek, Egyptian, Mesopotamian, Chinese, Mayan, etc.", "Evidence-backed insights only", "Avoidance of controversial or biased conclusions"],
    "Influence of Sanatana Dharma on the World": ["Over 30 topics (e.g., yoga, philosophy, mathematics, astronomy, etc.)"],
    "Ancient Legends & Rare Facts": ["Fascinating, lesser-known stories with verified sources"],
    "Moral Stories": ["Short, impactful lessons from Indian epics and folklore"],
    "Sanatana Dharma Today": ["Modern relevance", "Global impact", "Philosophical depth"]
}

# Video count tracking file
VIDEO_COUNTS_FILE = "/app/video_counts.json"

# Load or initialize video counts
def load_video_counts():
    try:
        deployment_logger.info("Starting to load video counts from file.")
        if os.path.exists(VIDEO_COUNTS_FILE):
            with open(VIDEO_COUNTS_FILE, 'r') as f:
                counts = json.load(f)
                deployment_logger.info(f"Successfully loaded video counts from {VIDEO_COUNTS_FILE}.")
                return counts
        counts = {cat: {sub: 0 for sub in subs} for cat, subs in CATEGORIES.items()}
        counts["Branding & Growth Strategies"]["Storytelling & Facts"] = {sub: 0 for sub in STORYTELLING_SUBTOPICS}
        counts["Generated Categories"] = {}
        with open(VIDEO_COUNTS_FILE, 'w') as f:
            json.dump(counts, f)
            deployment_logger.info(f"Initialized and saved default video counts to {VIDEO_COUNTS_FILE}.")
        return counts
    except Exception as e:
        deployment_logger.error(f"Failed to load or create video_counts.json: {e}")
        logger.error(f"Fallback to default video counts due to error: {e}")
        return {cat: {sub: 0 for sub in subs} for cat, subs in CATEGORIES.items()}  # Fallback to default

def save_video_counts(counts):
    try:
        with open(VIDEO_COUNTS_FILE, 'w') as f:
            json.dump(counts, f)
            logger.info(f"Successfully saved video counts to {VIDEO_COUNTS_FILE}.")
    except Exception as e:
        logger.error(f"Failed to save video_counts.json: {e}")

# AI-like category generator
def generate_new_category(existing_categories):
    try:
        themes = ["Science", "History", "Art", "Nature", "Technology", "Culture", "Philosophy", "Adventure", "Health", "Education"]
        descriptors = ["Insights", "Chronicles", "Explorations", "Discoveries", "Trends", "Stories", "Breakthroughs", "Journeys"]
        new_category = f"{random.choice(themes)} {random.choice(descriptors)}"
        while new_category in existing_categories:
            new_category = f"{random.choice(themes)} {random.choice(descriptors)}"
        logger.info(f"Generated new category: {new_category}")
        return new_category
    except Exception as e:
        logger.error(f"Failed to generate new category: {e}")
        return f"NewCategory_{int(time.time())}"  # Fallback

def generate_new_subcategories(category):
    try:
        sub_themes = ["Basics", "Advanced", "History", "Future", "Tips", "Secrets", "Myths", "Facts", "Innovations", "Lessons"]
        new_subs = [f"{category.split()[0]} {sub}" for sub in random.sample(sub_themes, 5)]
        logger.info(f"Generated new subcategories for {category}: {new_subs}")
        return new_subs
    except Exception as e:
        logger.error(f"Failed to generate new subcategories for {category}: {e}")
        return [f"{category.split()[0]} Fallback{sub}" for sub in range(5)]

# Global counter for round-robin
category_index = 0
lock = threading.Lock()

def refresh_token(credentials):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting token refresh, attempt {attempt + 1}/{max_retries}")
            url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "refresh_token": credentials["refresh_token"],
                "grant_type": "refresh_token"
            }
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            new_token = response.json()["access_token"]
            credentials["access_token"] = new_token
            logger.info("Token refreshed successfully.")
            return new_token
        except (requests.exceptions.RequestException, KeyError) as e:
            logger.error(f"Token refresh attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.critical("Max retries reached for token refresh, proceeding with last known token.")
                return credentials["access_token"]  # Fallback to last known token
            time.sleep(0.5 * (2 ** attempt))

def get_playlist_id(youtube, playlist_title):
    try:
        logger.info(f"Checking playlist ID for {playlist_title}")
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50
        )
        response = request.execute()
        for item in response.get('items', []):
            if item['snippet']['title'] == playlist_title:
                logger.info(f"Found playlist ID for {playlist_title}: {item['id']}")
                return item['id']
        logger.warning(f"Playlist {playlist_title} not found.")
        return None
    except Exception as e:
        logger.error(f"Failed to get playlist ID for {playlist_title}: {e}")
        return None

def generate_unique_script(category, subcategory, sub_subcategory, video_num):
    try:
        logger.info(f"Generating script for {category}/{subcategory}/{sub_subcategory}, video #{video_num}")
        intros = [
            f"Video {video_num}: Curious about", f"Video {video_num}: Ever wondered", f"Video {video_num}: What if",
            f"Video {video_num}: Dive into", f"Video {video_num}: Explore", f"Video {video_num}: Uncover"
        ]
        actions = [
            "discover this intriguing insight", "unveil this hidden truth", "learn this intuitive lesson",
            "explore this fascinating fact", "dig into this curious tale", "master this engaging concept"
        ]
        endings = [
            f"#{video_num} today!", f"#{video_num} now!", f"#{video_num} with us!", f"in this stunning reveal #{video_num}!"
        ]

        if category == "Branding & Growth Strategies" and subcategory == "Storytelling & Facts":
            specifics = {
                "Upanishads": f"the Upanishads’ wisdom on {sub_subcategory} #{video_num}",
                "Vedas": f"the Vedas’ secrets about {sub_subcategory} #{video_num}",
                "Agamas": f"Agamas’ principles of {sub_subcategory} #{video_num}",
                "Puranas": f"the Puranas’ stories on {sub_subcategory} #{video_num}",
                "Ramayana Perspectives": f"a Ramayana perspective on {sub_subcategory} #{video_num}",
                "Mahabharata Perspectives": f"a Mahabharata insight on {sub_subcategory} #{video_num}",
                "Teachings of Spiritual Masters": f"a teaching by {sub_subcategory} #{video_num}",
                "Sanatana Dharma vs Science vs World Cultures": f"Sanatana Dharma’s comparison with {sub_subcategory} #{video_num}",
                "Influence of Sanatana Dharma on the World": f"Sanatana Dharma’s impact on {sub_subcategory} #{video_num}",
                "Ancient Legends & Rare Facts": f"an ancient legend about {sub_subcategory} #{video_num}",
                "Moral Stories": f"a moral lesson from {sub_subcategory} #{video_num}",
                "Sanatana Dharma Today": f"Sanatana Dharma’s {sub_subcategory} today #{video_num}"
            }
            return f"{random.choice(intros)} {specifics[subcategory]}? {random.choice(actions)} {random.choice(endings)}"
        else:
            specifics = {
                "Motivation & Success Stories": f"success strategies in {subcategory} #{video_num}",
                "Tech News & AI Updates": f"tech updates on {subcategory} #{video_num}",
                "Finance & Stock Market Tips": f"financial tips for {subcategory} #{video_num}",
                "Relaxing Music & Meditation": f"wellness techniques in {subcategory} #{video_num}",
                "Sponsorship & Brand Deals": f"branding strategies for {subcategory} #{video_num}",
                "Side Hustle You Can Start For Free": f"free side hustles like {subcategory} #{video_num}",
                "Learning New Skills with AI": f"AI skills in {subcategory} #{video_num}",
                "Best Free Software for Work & Study": f"software for {subcategory} #{video_num}",
                "Time Management & Productivity Hacks": f"productivity tips for {subcategory} #{video_num}",
                "Best Affiliate Marketing Strategies": f"affiliate strategies in {subcategory} #{video_num}",
                "Blogging & SEO for Maximum Traffic": f"SEO techniques for {subcategory} #{video_num}",
                "AI Tools for Content Creation": f"AI tools for {subcategory} #{video_num}",
                "Instagram, Twitter, LinkedIn Automation": f"social media automation for {subcategory} #{video_num}",
                "YouTube Growth & Monetization": f"YouTube growth in {subcategory} #{video_num}",
                "Print-on-Demand & Dropshipping": f"digital sales in {subcategory} #{video_num}",
                "Best Marketplaces to Sell Digital Products": f"marketplaces for {subcategory} #{video_num}",
                "How to Sell Templates & Digital Assets": f"selling strategies for {subcategory} #{video_num}",
                "Ebooks & Online Courses": f"content creation for {subcategory} #{video_num}",
                "Freelancing & Remote Work": f"remote work tips for {subcategory} #{video_num}",
                "Personal Finance & Investment Tips": f"investment advice for {subcategory} #{video_num}",
                "Cryptocurrency & Blockchain Basics": f"crypto basics in {subcategory} #{video_num}",
                "Stock Market & Trading Insights": f"trading insights for {subcategory} #{video_num}",
                "Passive Income Strategies": f"passive income in {subcategory} #{video_num}",
                "AI Tools & SaaS Platforms": f"AI platforms for {subcategory} #{video_num}",
                "Software & Tool Comparisons": f"software comparisons for {subcategory} #{video_num}",
                "Best Tech Deals & Discounts": f"tech deals in {subcategory} #{video_num}",
                "Unboxing & First Impressions": f"first impressions of {subcategory} #{video_num}",
                "Reviews and Ratings": f"reviews for {subcategory} #{video_num}",
                "Cloud Computing & DevOps": f"cloud solutions in {subcategory} #{video_num}",
                "AI & Machine Learning Projects": f"AI projects for {subcategory} #{video_num}",
                "Mobile App Development": f"app development in {subcategory} #{video_num}",
                "Web Development": f"web tech for {subcategory} #{video_num}",
                "Python": f"Python skills in {subcategory} #{video_num}",
                "Java": f"Java expertise in {subcategory} #{video_num}"
            }
            return f"{random.choice(intros)} {specifics[subcategory]}? {random.choice(actions)} {random.choice(endings)}"
    except Exception as e:
        logger.error(f"Failed to generate script for {category}/{subcategory}: {e}")
        print(f"Error generating script: {e}", flush=True)  # Force stdout for Railway
        return f"Video {video_num}: Explore something new? discover this #{video_num} now!"

def generate_dynamic_script(category, subcategory, sub_subcategory, video_num):
    try:
        logger.info(f"Generating dynamic script for {category}/{subcategory}/{sub_subcategory}, video #{video_num}")
        intros = [
            f"Video {video_num}: Curious about", f"Video {video_num}: Ever wondered", f"Video {video_num}: What if"
        ]
        actions = [
            "discover this intriguing insight", "unveil this hidden truth", "learn this intuitive lesson"
        ]
        return f"{random.choice(intros)} {subcategory.lower()} in {category.lower()} with focus on {sub_subcategory.lower()}? {random.choice(actions)} #{video_num} now!"
    except Exception as e:
        logger.error(f"Failed to generate dynamic script for {category}/{subcategory}: {e}")
        print(f"Error generating dynamic script: {e}", flush=True)  # Force stdout for Railway
        return f"Video {video_num}: Something new? discover this #{video_num} now!"
def generate_ai_video(category, video_counts):
    try:
        logger.info(f"Starting video generation for category: {category}")
        with lock:
            subcategory = random.choice(list(CATEGORIES[category]))
            if category == "Branding & Growth Strategies" and subcategory == "Storytelling & Facts":
                sub_subcategory = random.choice(list(STORYTELLING_SUBTOPICS.keys()))
                detail = random.choice(STORYTELLING_SUBTOPICS[sub_subcategory])
                video_num = video_counts[category][subcategory][sub_subcategory] + 1
                logger.debug(f"Video number for {category}/{subcategory}/{sub_subcategory}: {video_num}")
                if video_num >= 100:
                    new_cat = generate_new_category(list(CATEGORIES.keys()) + list(video_counts["Generated Categories"].keys()))
                    if new_cat not in video_counts["Generated Categories"]:
                        video_counts["Generated Categories"][new_cat] = {sub: 0 for sub in generate_new_subcategories(new_cat)}
                    category, subcategory, sub_subcategory = new_cat, random.choice(list(video_counts["Generated Categories"][new_cat].keys())), 0
                    script = generate_dynamic_script(category, subcategory, "new topic", video_num)
                    logger.info(f"Switched to new category: {new_cat}")
                else:
                    script = generate_unique_script(category, subcategory, detail, video_num)
            else:
                video_num = video_counts[category][subcategory] + 1
                logger.debug(f"Video number for {category}/{subcategory}: {video_num}")
                if video_num >= 100:
                    new_cat = generate_new_category(list(CATEGORIES.keys()) + list(video_counts["Generated Categories"].keys()))
                    if new_cat not in video_counts["Generated Categories"]:
                        video_counts["Generated Categories"][new_cat] = {sub: 0 for sub in generate_new_subcategories(new_cat)}
                    category, subcategory = new_cat, random.choice(list(video_counts["Generated Categories"][new_cat].keys()))
                    script = generate_dynamic_script(category, subcategory, "new topic", video_num)
                    logger.info(f"Switched to new category: {new_cat}")
                else:
                    script = generate_unique_script(category, subcategory, "general", video_num)

        output_file = f"video_{category.replace(' ', '_')}_{subcategory.replace(' ', '_')}_{int(time.time())}.mp4"
        logger.info(f"Output file generated: {output_file}")

        # Generate assets with high-quality, human-like elements
        try:
            logger.debug("Fetching face image from ThisPersonDoesNotExist")
            face_response = requests.get("https://thispersondoesnotexist.com", timeout=5)
            face_response.raise_for_status()
            face_img = Image.open(io.BytesIO(face_response.content)).resize((1920, 2160), Image.LANCZOS)
        except Exception as e:
            logger.error(f"Failed to fetch face: {e}")
            print(f"Error fetching face: {e}", flush=True)  # Force stdout for Railway
            face_img = Image.new('RGB', (1920, 2160), color='gray')

        try:
            logger.debug("Generating background image with Craiyon")
            bg_response = requests.post("https://backend.craiyon.com/generate", json={"prompt": script}, timeout=15)
            bg_response.raise_for_status()
            bg_url = bg_response.json()["images"][0]
            bg_data = requests.get(bg_url, timeout=15).content
            bg_img = Image.open(io.BytesIO(bg_data)).resize((1920, 2160), Image.LANCZOS)
        except Exception as e:
            logger.error(f"Failed to generate background: {e}")
            print(f"Error generating background: {e}", flush=True)  # Force stdout for Railway
            bg_img = Image.new('RGB', (1920, 2160), color=(200, 200, 255))

        final_img = Image.new('RGB', (3840, 2160))
        final_img.paste(bg_img, (0, 0))
        final_img.paste(face_img, (1920, 0))
        try:
            logger.debug("Drawing text on final image")
            draw = ImageDraw.Draw(final_img)
            font = ImageFont.truetype("arial.ttf", 40) if os.path.exists("arial.ttf") else ImageFont.load_default()
            draw.text((20, 20), script[:50] + "...", fill='white', font=font)
        except Exception as e:
            logger.error(f"Failed to draw text on image: {e}")
            print(f"Error drawing text: {e}", flush=True)  # Force stdout for Railway

        img_byte_arr = io.BytesIO()
        try:
            logger.debug("Saving final image to byte array")
            final_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            print(f"Error saving image: {e}", flush=True)  # Force stdout for Railway
            img_byte_arr = io.BytesIO(Image.new('RGB', (3840, 2160), color='gray').tobytes())

        audio_file = f"audio_{category}_{subcategory}.mp3"

        def generate_audio():
            try:
                logger.debug(f"Generating audio for {category}/{subcategory}")
                headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
                voice_data = {"text": script, "voice_id": "21m00Tcm4TlvDq8ikWAM"}  # Rachel voice
                voice_response = requests.post("https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM", headers=headers, json=voice_data, timeout=15)
                voice_response.raise_for_status()
                with open(audio_file, "wb") as f:
                    f.write(voice_response.content)
            except Exception as e:
                logger.error(f"ElevenLabs voice failed: {e}")
                print(f"Error generating audio: {e}", flush=True)  # Force stdout for Railway
                tts = gTTS(text=script, lang='en-us', tld='us', slow=False)
                tts.save(audio_file)

        try:
            with ThreadPoolExecutor() as executor:
                executor.submit(generate_audio)
            logger.debug("Creating video clip")
            img_clip = ImageClip(np.array(Image.open(io.BytesIO(img_byte_arr))), duration=30)
            audio_clip = AudioFileClip(audio_file)
            final_clip = img_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_file, codec="libx264", fps=30, bitrate="50000k", logger=None, threads=4)
            logger.info(f"Video successfully created: {output_file}")
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            print(f"Error creating video: {e}", flush=True)  # Force stdout for Railway
            raise

        with lock:
            try:
                logger.debug(f"Updating video count for {category}/{subcategory}")
                if category == "Branding & Growth Strategies" and subcategory == "Storytelling & Facts":
                    video_counts[category][subcategory][sub_subcategory] = video_num
                else:
                    video_counts[category][subcategory] = video_num
                save_video_counts(video_counts)
            except Exception as e:
                logger.error(f"Failed to update video counts: {e}")
                print(f"Error updating video counts: {e}", flush=True)  # Force stdout for Railway

        return output_file, script, category, subcategory
    except Exception as e:
        logger.critical(f"Critical failure in generate_ai_video for {category}: {e}")
        print(f"Critical failure in video generation: {e}", flush=True)  # Force stdout for Railway
        return None, f"Error Video {video_num}", category, subcategory

def upload_to_youtube(credentials, video_path, title, description, playlist_title=None):
    try:
        logger.info(f"Starting upload for video: {title}")
        max_retries = 5
        youtube = build('youtube', 'v3', developerKey=credentials["access_token"], cache_discovery=False)
        playlist_id = None

        if playlist_title:
            logger.debug(f"Checking playlist ID for {playlist_title}")
            playlist_id = get_playlist_id(youtube, playlist_title)
            if not playlist_id:
                logger.warning(f"Playlist '{playlist_title}' not found, uploading without playlist.")
                print(f"Warning: Playlist {playlist_title} not found", flush=True)  # Force stdout for Railway
                playlist_id = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"Upload attempt {attempt + 1}/{max_retries} for {title}")
                request_body = {
                    "snippet": {
                        "title": title,
                        "description": description + "\n\nAffiliate Links: [Check our partners at example.com/affiliate]\nSponsorships: Contact harshagmisc@gmail.com for collaborations!",
                        "tags": [title.replace(" ", "_"), "Sanatana Dharma", "Indian Philosophy"],
                        "categoryId": "22"
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }
                if playlist_id:
                    request_body["snippet"]["playlistId"] = playlist_id

                request = youtube.videos().insert(
                    part="snippet,status",
                    body=request_body,
                    media_body=MediaFileUpload(video_path)
                )
                response = request.execute(num_retries=5)
                logger.info(f"Video uploaded successfully: {response['id']}")
                print(f"Video uploaded: {response['id']}", flush=True)  # Force stdout for Railway

                if playlist_id:
                    logger.debug(f"Adding video to playlist {playlist_title}")
                    playlist_item_body = {
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": response['id']
                            }
                        }
                    }
                    playlist_request = youtube.playlistItems().insert(
                        part="snippet",
                        body=playlist_item_body
                    ).execute()
                    logger.info(f"Video added to playlist {playlist_title}: {playlist_request['id']}")
                    print(f"Video added to playlist {playlist_title}", flush=True)  # Force stdout for Railway

                return True, response
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.warning(f"401 error detected, refreshing token for attempt {attempt + 1}")
                    print(f"401 error, refreshing token", flush=True)  # Force stdout for Railway
                    refresh_token(credentials)
                    continue
                logger.error(f"Upload attempt {attempt + 1} failed: {e}")
                print(f"Upload failed: {e}", flush=True)  # Force stdout for Railway
                if attempt == max_retries - 1:
                    return False, str(e)
                time.sleep(0.5 * (2 ** attempt))
    except Exception as e:
        logger.critical(f"Critical failure in upload_to_youtube for {title}: {e}")
        print(f"Critical upload failure: {e}", flush=True)  # Force stdout for Railway
        return False, str(e)

def send_gmail_notification(credentials, subject, body):
    try:
        logger.info(f"Sending Gmail notification: {subject}")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                url = "https://www.googleapis.com/gmail/v1/users/me/messages/send"
                headers = {"Authorization": f"Bearer {credentials['access_token']}", "Content-Type": "application/json"}
                message = {"raw": base64.urlsafe_b64encode(f"Subject: {subject}\n\n{body}".encode()).decode()}
                response = requests.post(url, headers=headers, json=message, timeout=5)
                response.raise_for_status()
                logger.info("Gmail notification sent successfully.")
                print(f"Gmail notification sent: {subject}", flush=True)  # Force stdout for Railway
                return True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.warning(f"401 error detected, refreshing token for Gmail attempt {attempt + 1}")
                    print(f"401 error for Gmail, refreshing token", flush=True)  # Force stdout for Railway
                    refresh_token(credentials)
                    continue
                logger.error(f"Gmail notification attempt {attempt + 1} failed: {e}")
                print(f"Gmail notification failed: {e}", flush=True)  # Force stdout for Railway
                if attempt == max_retries - 1:
                    return False
                time.sleep(0.5 * (2 ** attempt))
    except Exception as e:
        logger.critical(f"Critical failure in send_gmail_notification: {e}")
        print(f"Critical Gmail failure: {e}", flush=True)  # Force stdout for Railway
        return False

def main():
    global category_index
    try:
        deployment_logger.info("Starting deployment and script initialization.")
        logger.info("Main process started.")
        video_counts = load_video_counts()

        while True:
            try:
                category = list(CATEGORIES.keys())[category_index % len(CATEGORIES)]
                logger.info(f"Processing category: {category}")
                print(f"Processing category: {category}", flush=True)  # Force stdout for Railway
                
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(generate_ai_video, category, video_counts)
                    video_path, script, final_category, final_subcategory = future.result(timeout=300)  # 5-minute timeout
                    if video_path is None:
                        raise ValueError("Video generation failed")

                subcategory = final_subcategory if final_category == "Branding & Growth Strategies" and final_subcategory in ["Storytelling & Facts", "Sponsorship & Brand Deals"] else random.choice(CATEGORIES[final_category])
                video_num = video_counts[final_category][subcategory] + 1 if subcategory != "Storytelling & Facts" else video_counts[final_category]["Storytelling & Facts"][final_subcategory] + 1
                title = f"{final_category} - {subcategory} - Video {video_num} - Intriguing Insights"
                description = f"Explore {final_category} and {subcategory} with this engaging update in stunning 4K. No false claims, only verified wisdom!"
                playlist_title = f"{final_category} - {subcategory}"

                logger.info(f"Preparing to upload video: {title}")
                print(f"Preparing to upload: {title}", flush=True)  # Force stdout for Railway
                success, message = upload_to_youtube(YOUTUBE_PLAN_A, video_path, title, description, playlist_title)
                if not success:
                    logger.warning("Plan A failed, switching to Plan B")
                    print("Plan A failed, switching to Plan B", flush=True)  # Force stdout for Railway
                    success, message = upload_to_youtube(YOUTUBE_PLAN_B, video_path, title, description, playlist_title)

                with lock:
                    try:
                        if final_category == "Branding & Growth Strategies" and final_subcategory == "Storytelling & Facts":
                            video_counts[final_category]["Storytelling & Facts"][final_subcategory] += 1
                        else:
                            video_counts[final_category][subcategory] += 1
                        save_video_counts(video_counts)
                    except Exception as e:
                        logger.error(f"Failed to update counts for {final_category}/{subcategory}: {e}")
                        print(f"Error updating counts: {e}", flush=True)  # Force stdout for Railway

                subject = "YouTube Upload " + ("Success" if success else "Failure")
                body = f"Video '{title}' upload {'succeeded' if success else 'failed'}: {message}"
                if not send_gmail_notification(GMAIL_CREDENTIALS, subject, body):
                    logger.error("Failed to send Gmail notification after retries.")
                    print("Failed to send Gmail notification", flush=True)  # Force stdout for Railway

                category_index += 1
                if category_index >= len(CATEGORIES):
                    all_done = all(all(count >= 100 for count in cat_counts.values()) for cat_counts in video_counts.values() if isinstance(cat_counts, dict))
                    if all_done:
                        logger.info("All original categories completed, continuing with generated ones.")
                        print("All original categories completed", flush=True)  # Force stdout for Railway
                    category_index = 0

            except (TimeoutError, ValueError) as e:
                logger.error(f"Execution timeout or value error for {category}: {e}")
                print(f"Timeout or value error: {e}", flush=True)  # Force stdout for Railway
                send_gmail_notification(GMAIL_CREDENTIALS, "Execution Error", f"Timeout or value error for {category}: {e}")
            except Exception as e:
                logger.error(f"Main execution failed for {category}: {e}")
                print(f"Main execution failed: {e}", flush=True)  # Force stdout for Railway
                send_gmail_notification(GMAIL_CREDENTIALS, "Critical Error", f"Script failed for {category}: {e}")

            finally:
                try:
                    for file in [video_path, f"audio_{category}_{subcategory}.mp3"]:
                        if os.path.exists(file):
                            os.remove(file)
                            logger.debug(f"Cleaned up file: {file}")
                            print(f"Cleaned up file: {file}", flush=True)  # Force stdout for Railway
                except Exception as e:
                    logger.warning(f"Failed to clean up {file}: {e}")
                    print(f"Failed to clean up {file}: {e}", flush=True)  # Force stdout for Railway

            time.sleep(0.1)  # Minimal delay for Overdrive

    except Exception as e:
        logger.critical(f"Critical failure in main loop: {e}")
        print(f"Critical failure: {e}", flush=True)  # Force stdout for Railway
        send_gmail_notification(GMAIL_CREDENTIALS, "Critical Failure", f"Script crashed: {e}")
        deployment_logger.critical(f"Deployment failed: {e}")

if __name__ == "__main__":
    deployment_logger.info("Deployment initialized successfully.")
    print("Deployment initialized successfully", flush=True)  # Force stdout for Railway
    main()
