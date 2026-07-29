import os
import re
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TARGET_DATE = "31"
TARGET_MONTH = "Jul"
TARGET_ISO = "2026-07-31"

# 1. Force the URL to the exact date
THEATERS = {
    "Palazzo (District)": f"https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274?date={TARGET_ISO}&showDate={TARGET_ISO}",
    "LUXE (District)": f"https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779?date={TARGET_ISO}&showDate={TARGET_ISO}"
}

# --- FILTERS ---
TARGET_MOVIE = "THE ODYSSEY"  
TARGET_FORMAT = "IMAX"

def send_telegram_alert(msg):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(telegram_url, json=payload, timeout=10, impersonate="chrome")
        if res.status_code == 200:
            print("Telegram alert sent successfully!")
        else:
            print(f"Failed to send Telegram alert: {res.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def get_visible_text(html):
    # 2. Completely delete all <script> and <style> tags and their hidden database contents
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', html, flags=re.IGNORECASE)
    # 3. Strip remaining HTML layout tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # 4. Compress all spaces and make uppercase so it reads like a plain book
    return re.sub(r'\s+', ' ', text).upper()

def check_tickets():
    alert_triggered = False
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                
                # Get only the text a human can actually see on screen
                visible_text = get_visible_text(response.text)
                
                movie_matches = [m.start() for m in re.finditer(TARGET_MOVIE, visible_text)]
                valid_ticket_found = False
                
                # Check the 250 visible characters immediately after the movie title.
                # Because all HTML is gone, 250 chars is a very tight window that won't bleed into other movies.
                for match_index in movie_matches:
                    start = match_index
                    end = min(len(visible_text), match_index + 250)
                    text_chunk = visible_text[start:end]
                    
                    if TARGET_FORMAT in text_chunk:
                        valid_ticket_found = True
                        break 
                
                if valid_ticket_found:
                    send_telegram_alert(f"🚨 TICKET ALERT! {name} has updated {TARGET_FORMAT} showtimes for {TARGET_MOVIE} on {TARGET_DATE} {TARGET_MONTH}! Open app NOW!")
                    alert_triggered = True
                else:
                    print(f"Status 200 OK, but {TARGET_FORMAT} tickets for {TARGET_MOVIE} on {TARGET_DATE} {TARGET_MONTH} not found yet at {name}.")
            else:
                print(f"Blocked (Status {response.status_code}) for {name}.")
        except Exception as e:
            print(f"Fetch failed for {name}: {e}")
            
    if not alert_triggered:
        print("Check completed across all targets.")

if __name__ == "__main__":
    check_tickets()
