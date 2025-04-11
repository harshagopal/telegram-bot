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
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Load Credentials from .env
YOUTUBE_PLAN_A = {
    "client_id": os.getenv("YOUTUBE_PLAN_A_CLIENT_ID"),
    "client_secret": os.getenv("YOUTUBE_PLAN_A_CLIENT_SECRET"),
    "refresh_token": os.getenv("YOUTUBE_PLAN_A_REFRESH_TOKEN"),
    "access_token": os.getenv("YOUTUBE_PLAN_A_ACCESS_TOKEN")
}

YOUTUBE_PLAN_B = {
    "client_id": os.getenv("YOUTUBE_PLAN_B_CLIENT_ID"),
    "client_secret": os.getenv("YOUTUBE_PLAN_B_CLIENT_SECRET"),
    "refresh_token": os.getenv("YOUTUBE_PLAN_B_REFRESH_TOKEN"),
    "access_token": os.getenv("YOUTUBE_PLAN_B_ACCESS_TOKEN")
}

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEEP_AI_API_KEY = os.getenv("DEEP_AI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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
    try:
        logger.info("Attempting to refresh token.")
        creds = Credentials(
            token=credentials.get("access_token"),
            refresh_token=credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        # Force refresh regardless of expiration status
        logger.debug("Forcing token refresh...")
        creds.refresh(Request())
        new_token = creds.token
        credentials["access_token"] = new_token
        logger.info("Token refreshed successfully using google-auth.")
        return creds  # Return the full Credentials object
    except Exception as e:
        logger.error(f"Failed to refresh token: {str(e)}")
        raise RuntimeError(f"Token refresh failed: {str(e)}")
        
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
        print(f"Error generating script: {e}", flush=True)
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
        print(f"Error generating dynamic script: {e}", flush=True)
        return f"Video {video_num}: Something new? discover this #{video_num} now!"

def generate_ai_video(category, video_counts):
    attempts = 0
    max_attempts = 2  # 1 initial + 1 retry

    while attempts < max_attempts:
        try:
            logger.info(f"Starting video generation for category: {category} (Attempt {attempts + 1})")
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

            # Check disk space
            statvfs = os.statvfs('/')
            free_space = statvfs.f_frsize * statvfs.f_bavail / (1024 * 1024)  # Free space in MB
            if free_space < 500:  # Require at least 500MB free
                raise RuntimeError(f"Insufficient disk space: {free_space}MB available")

            # Generate assets
            try:
                logger.debug("Fetching face image from ThisPersonDoesNotExist")
                face_response = requests.get("https://thispersondoesnotexist.com", timeout=5)
                face_response.raise_for_status()
                face_img = Image.open(io.BytesIO(face_response.content)).resize((1920, 2160), Image.LANCZOS)
            except Exception as e:
                logger.error(f"Failed to fetch face: {e}")
                print(f"Error fetching face: {e}", flush=True)
                face_img = Image.new('RGB', (1920, 2160), color='gray')

            # Use Deep AI for background image generation
            try:
                logger.debug("Generating background image with Deep AI")
                bg_response = requests.post(
                    "https://api.deepai.org/api/text2img",
                    data={"text": script},
                    headers={"api-key": DEEP_AI_API_KEY},
                    timeout=30
                )
                bg_response.raise_for_status()
                bg_url = bg_response.json()["output_url"]
                bg_data = requests.get(bg_url, timeout=15).content
                bg_img = Image.open(io.BytesIO(bg_data)).resize((1920, 2160), Image.LANCZOS)
            except Exception as e:
                logger.error(f"Failed to generate background with Deep AI: {e}")
                print(f"Error generating background: {e}", flush=True)
                bg_img = Image.new('RGB', (1920, 2160), color=(200, 200, 255))  # Fallback to light blue

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
                print(f"Error drawing text: {e}", flush=True)

            img_byte_arr = io.BytesIO()
            try:
                logger.debug("Saving final image to byte array")
                final_img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
            except Exception as e:
                logger.error(f"Failed to save image: {e}")
                print(f"Error saving image: {e}", flush=True)
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
                    print(f"Error generating audio: {e}", flush=True)
                    tts = gTTS(text=script, lang='en-us', tld='us', slow=False)
                    tts.save(audio_file)

            try:
                with ThreadPoolExecutor() as executor:
                    executor.submit(generate_audio)
                logger.debug("Creating video clip")
                img_clip = ImageClip(np.array(Image.open(io.BytesIO(img_byte_arr))), duration=30)
                audio_clip = AudioFileClip(audio_file)
                final_clip = img_clip.set_audio(audio_clip)
                final_clip.write_videofile(output_file, codec="libx264", fps=24, bitrate="8000k", logger=None, threads=4)
                logger.info(f"Video successfully created: {output_file}")
                return output_file, script, category, subcategory
            except Exception as e:
                logger.error(f"Video creation failed: {e}")
                print(f"Error creating video: {e}", flush=True)
                if attempts == 0:  # First attempt failed, retry
                    attempts += 1
                    continue
                else:  # Second attempt failed, use placeholder
                    placeholder_script = f"Video {video_num}: What secrets lie hidden? Uncover the mystery #{video_num} now!"
                    return output_file, placeholder_script, category, subcategory

        except Exception as e:
            logger.critical(f"Critical failure in generate_ai_video for {category}: {e}")
            print(f"Critical failure in video generation: {e}", flush=True)
            if attempts == 0:  # First attempt failed, retry
                attempts += 1
                continue
            else:  # Second attempt failed, use placeholder
                placeholder_script = f"Video {video_num}: A journey into the unknown awaits! Explore #{video_num} today!"
                return None, placeholder_script, category, subcategory

    # If all attempts fail, return a default placeholder
    video_num = video_counts[category][random.choice(list(CATEGORIES[category]))] + 1
    placeholder_script = f"Video {video_num}: What wonders will you discover? Dive in #{video_num} now!"
    return None, placeholder_script, category, random.choice(list(CATEGORIES[category]))

def upload_to_youtube(credentials, video_path, title, description, playlist_title=None):
    try:
        logger.info(f"Starting upload for video: {title}")
        max_retries = 5

        # Refresh the token and get credentials
        creds = refresh_token(credentials)

        # Build the service with OAuth2 credentials
        youtube = build('youtube', 'v3', credentials=creds, cache_discovery=False)
        playlist_id = None

        if playlist_title:
            logger.debug(f"Checking playlist ID for {playlist_title}")
            playlist_id = get_playlist_id(youtube, playlist_title)
            if not playlist_id:
                logger.warning(f"Playlist '{playlist_title}' not found, uploading without playlist.")
                print(f"Warning: Playlist {playlist_title} not found", flush=True)

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
                print(f"Video uploaded: {response['id']}", flush=True)

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
                    print(f"Video added to playlist {playlist_title}", flush=True)

                return True, response
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [401, 403]:  # Unauthorized or Forbidden
                    logger.warning(f"Authentication error detected ({e.response.status_code}), refreshing token for attempt {attempt + 1}")
                    print(f"Authentication error, refreshing token", flush=True)
                    creds = refresh_token(credentials)  # Refresh and retry
                    continue
                logger.error(f"Upload attempt {attempt + 1} failed: {e}")
                print(f"Upload failed: {e}", flush=True)
                if attempt == max_retries - 1:
                    return False, str(e)
                time.sleep(0.5 * (2 ** attempt))
    except Exception as e:
        logger.critical(f"Critical failure in upload_to_youtube for {title}: {e}")
        print(f"Critical upload failure: {e}", flush=True)
        return False, str(e)

def send_telegram_notification(subject, body):
    try:
        logger.info(f"Sending Telegram notification: {subject}")
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"{subject}\n\n{body}"
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
        print(f"Telegram notification sent: {subject}", flush=True)
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        print(f"Telegram notification failed: {e}", flush=True)
        return False

def main():
    global category_index
    try:
        deployment_logger.info("Starting deployment and script initialization.")
        logger.info("Main process started.")
        video_counts = load_video_counts()

        while True:
            video_path = None  # Initialize outside try block
            category = None  # Initialize to avoid unbound variable
            subcategory = None
            try:
                category = list(CATEGORIES.keys())[category_index % len(CATEGORIES)]
                logger.info(f"Processing category: {category}")
                print(f"Processing category: {category}", flush=True)
                
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(generate_ai_video, category, video_counts)
                    video_path, script, final_category, final_subcategory = future.result(timeout=300)
                    if video_path is None and "Error" in script:
                        raise ValueError("Video generation failed with placeholder")

                subcategory = final_subcategory if final_category == "Branding & Growth Strategies" and final_subcategory in ["Storytelling & Facts", "Sponsorship & Brand Deals"] else random.choice(CATEGORIES[final_category])
                video_num = video_counts[final_category][subcategory] + 1 if subcategory != "Storytelling & Facts" else video_counts[final_category]["Storytelling & Facts"][final_subcategory] + 1
                title = f"{final_category} - {subcategory} - Video {video_num} - Intriguing Insights"
                description = f"Explore {final_category} and {subcategory} with this engaging update in stunning 4K. No false claims, only verified wisdom!"
                playlist_title = f"{final_category} - {subcategory}"

                logger.info(f"Preparing to upload video: {title}")
                print(f"Preparing to upload: {title}", flush=True)
                success, message = upload_to_youtube(YOUTUBE_PLAN_A, video_path, title, description, playlist_title)
                if not success:
                    logger.warning("Plan A failed, switching to Plan B")
                    print("Plan A failed, switching to Plan B", flush=True)
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
                        print(f"Error updating counts: {e}", flush=True)

                subject = "YouTube Upload " + ("Success" if success else "Failure")
                body = f"Video '{title}' upload {'succeeded' if success else 'failed'}: {message}"
                if not send_telegram_notification(subject, body):
                    logger.error("Failed to send Telegram notification after retries.")
                    print("Failed to send Telegram notification", flush=True)

                category_index += 1
                if category_index >= len(CATEGORIES):
                    all_done = all(all(count >= 100 for count in cat_counts.values()) for cat_counts in video_counts.values() if isinstance(cat_counts, dict))
                    if all_done:
                        logger.info("All original categories completed, continuing with generated ones.")
                        print("All original categories completed", flush=True)
                    category_index = 0

            except (TimeoutError, ValueError) as e:
                logger.error(f"Execution timeout or value error for {category}: {e}")
                print(f"Timeout or value error: {e}", flush=True)
                send_telegram_notification("Execution Error", f"Timeout or value error for {category}: {e}")
            except Exception as e:
                logger.error(f"Main execution failed for {category}: {e}")
                print(f"Main execution failed: {e}", flush=True)
                send_telegram_notification("Critical Error", f"Script failed for {category}: {e}")

            finally:
                if video_path or category:  # Only attempt cleanup if variables are set
                    files_to_clean = []
                    if video_path:
                        files_to_clean.append(video_path)
                    if category and subcategory:
                        files_to_clean.append(f"audio_{category}_{subcategory}.mp3")
                    for file_path in files_to_clean:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                logger.debug(f"Cleaned up file: {file_path}")
                                print(f"Cleaned up file: {file_path}", flush=True)
                            except Exception as e:
                                logger.warning(f"Failed to clean up {file_path}: {e}")
                                print(f"Failed to clean up {file_path}: {e}", flush=True)

            time.sleep(0.1)  # Minimal delay for Overdrive

    except Exception as e:
        logger.critical(f"Critical failure in main loop: {e}")
        print(f"Critical failure: {e}", flush=True)
        send_telegram_notification("Critical Failure", f"Script crashed: {e}")
        deployment_logger.critical(f"Deployment failed: {e}")

if __name__ == "__main__":
    deployment_logger.info("Deployment initialized successfully.")
    print("Deployment initialized successfully", flush=True)
    main()
