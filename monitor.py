import os
import re
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

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

def check_tickets():
    alert_triggered = False
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                raw_html = response.text.upper()
                
                body_html = re.sub(r'<HEAD.*?>.*?</HEAD>', '', raw_html, flags=re.DOTALL)
                sections = body_html.split(TARGET_MOVIE)
                valid_ticket_found = False
                
                for section in sections[1:]:
                    chunk = section[:1500]
                    
                    # THE FIX: Removed TARGET_ISO from this check since the URL already handles the date
                    if TARGET_FORMAT in chunk and ":" in chunk:
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
