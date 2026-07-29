import os
import re
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- STRICTLY SET FOR JULY 31 ---
TARGET_DATE = "31"
TARGET_MONTH = "Jul"
TARGET_ISO = "2026-07-31"

THEATERS = {
    "Palazzo (District)": f"https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274?date={TARGET_ISO}&showDate={TARGET_ISO}",
    "LUXE (District)": f"https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779?date={TARGET_ISO}&showDate={TARGET_ISO}"
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
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                visible_text = get_visible_text(response.text)
                
                movie_matches = [m.start() for m in re.finditer(TARGET_MOVIE, visible_text)]
                valid_ticket_found = False
                
                for match_index in movie_matches:
                    start = match_index
                    # Expanded window slightly to capture full showtime blocks
                    end = min(len(visible_text), match_index + 350)
                    text_chunk = visible_text[start:end]
                    
                    # 1. Look for IMAX
                    has_imax = TARGET_FORMAT in text_chunk
                    
                    # 2. STRICT TIME: Must be a digital time immediately followed by AM or PM
                    has_real_time = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)', text_chunk)
                    
                    # 3. EMPTY STATE KILLER: Ensure the page isn't just saying "No Shows Available"
                    is_empty_state = re.search(r'(NO SHOW|NOT AVAILABLE|NO TICKETS|CURRENTLY NOT)', text_chunk)
                    
                    if has_imax and has_real_time and not is_empty_state:
                        # BLACK BOX DEBUGGER: Prints exactly what tricked the script
                        print(f"\n--- 🚨 SYSTEM TRIGGERED ON THIS TEXT BLOCK 🚨 ---")
                        print(f"{text_chunk}")
                        print(f"-------------------------------------------------\n")
                        
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
