import os
import re
import random
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- SET FOR JULY 31 ---
TARGET_DATE = "31"
TARGET_MONTH = "Jul"
TARGET_ISO = "2026-07-31"

THEATER_BASES = {
    "Palazzo (District)": "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    "LUXE (District)": "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779"
}

TARGET_MOVIE = "THE ODYSSEY"  
TARGET_FORMAT = "IMAX"

def send_telegram_alert(msg):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(telegram_url, json=payload, timeout=20)
        if res.status_code == 200:
            print("Telegram alert sent successfully!")
        else:
            print(f"Failed to send Telegram alert: {res.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def get_visible_text(html):
    text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', html, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).upper()

def check_tickets():
    alert_triggered = False
    
    for name, base_url in THEATER_BASES.items():
        print(f"Checking {name}...")
        
        # Randomizer bypasses server caching to ensure it fetches live data
        url = f"{base_url}?date={TARGET_ISO}&showDate={TARGET_ISO}&nocache={random.randint(100000, 999999)}"
        
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                visible_text = get_visible_text(response.text)
                sections = visible_text.split(TARGET_MOVIE)
                valid_ticket_found = False
                
                if len(sections) > 1:
                    for section in sections[1:]:
                        # 1. THE WALL: Find the NEXT movie's certificate (e.g., U/A |, A |)
                        # We skip the first 15 chars so we don't accidentally match The Odyssey's own certificate
                        next_cert = re.search(r'\b(U/A|A|U|UA\d*\+?)\s*\|', section[15:])
                        
                        if next_cert:
                            # 2. Chop the string exactly at the pipe. This deletes the next movie's showtimes entirely!
                            text_chunk = section[:next_cert.start() + 15]
                        else:
                            text_chunk = section[:1500]
                        
                        # 3. STRICT FORWARD PROXIMITY: "IMAX" must appear shortly BEFORE a digital time.
                        # This links the format directly to the showtime and ignores standard 2D times.
                        is_real_imax = re.search(r'IMAX.{0,30}?\d{1,2}:\d{2}\s*(?:AM|PM)', text_chunk)
                        
                        if is_real_imax:
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
