import os
import re
import json
import random
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

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
        requests.post(telegram_url, json=payload, timeout=20)
        print("Telegram alert sent successfully!")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def check_tickets():
    alert_triggered = False
    
    for name, base_url in THEATERS.items():
        print(f"Checking {name}...")
        url = f"{base_url}&nocache={random.randint(100000, 999999)}"
        
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                
                # 1. Extract the raw Next.js database from the background
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
                
                if not match:
                    print(f"Could not extract database for {name}.")
                    continue
                    
                raw_db = match.group(1).upper()
                
                # 2. SERVER TRAP CHECK: If the target date isn't even in the database, the server served us today's page. Skip it.
                if TARGET_ISO not in raw_db:
                    print(f"Status 200 OK, but {TARGET_FORMAT} tickets for {TARGET_MOVIE} on {TARGET_DATE} {TARGET_MONTH} not found yet at {name}.")
                    continue
                
                # 3. Isolate the exact data block for The Odyssey
                if TARGET_MOVIE in raw_db:
                    sections = raw_db.split(TARGET_MOVIE)
                    valid_ticket_found = False
                    
                    for section in sections[1:]:
                        # Look at the 1500 characters of data specifically assigned to this movie
                        chunk = section[:1500]
                        
                        # The database must explicitly assign the 31st AND IMAX to this exact movie
                        if TARGET_FORMAT in chunk and TARGET_ISO in chunk:
                            valid_ticket_found = True
                            break 
                    
                    if valid_ticket_found:
                        send_telegram_alert(f"🚨 TICKET ALERT! {name} has updated {TARGET_FORMAT} showtimes for {TARGET_MOVIE} on {TARGET_DATE} {TARGET_MONTH}! Open app NOW!")
                        alert_triggered = True
                    else:
                        print(f"Status 200 OK, but {TARGET_FORMAT} tickets for {TARGET_MOVIE} on {TARGET_DATE} {TARGET_MONTH} not found yet at {name}.")
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
