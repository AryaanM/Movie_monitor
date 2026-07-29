import os
import re
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- STRICTLY SET FOR JULY 31 ---
TARGET_DATE = "30"
TARGET_MONTH = "Jul"
TARGET_ISO = "2026-07-30"

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

def check_tickets():
    alert_triggered = False
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                
                # 1. Kill the JSON database by deleting <script> tags, but KEEP the HTML buttons and links
                html_no_scripts = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ', response.text, flags=re.IGNORECASE).upper()
                
                movie_matches = [m.start() for m in re.finditer(TARGET_MOVIE, html_no_scripts)]
                valid_ticket_found = False
                
                for match_index in movie_matches:
                    # 2. Grab a larger 2,500-char window because HTML tags take up space
                    start = match_index
                    end = min(len(html_no_scripts), match_index + 2500)
                    html_chunk = html_no_scripts[start:end]
                    
                    # 3. DATE LOCK: The button links MUST contain the Target Date, proving it didn't redirect to today
                    if TARGET_FORMAT in html_chunk and TARGET_ISO in html_chunk:
                        
                        # 4. Now that we know it's the right day, strip the HTML to look for the time block
                        plain_text_chunk = re.sub(r'<[^>]+>', ' ', html_chunk)
                        plain_text_chunk = re.sub(r'\s+', ' ', plain_text_chunk)
                        
                        has_real_time = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)', plain_text_chunk)
                        is_empty_state = re.search(r'(NO SHOW|NOT AVAILABLE|NO TICKETS|CURRENTLY NOT)', plain_text_chunk)
                        
                        if has_real_time and not is_empty_state:
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
