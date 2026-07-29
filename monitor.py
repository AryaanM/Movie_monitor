import os
import re
from curl_cffi import requests

# Pull secrets directly from GitHub Actions environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

THEATERS = {
    "Palazzo (District)": "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    "LUXE (District)": "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779"
}

TARGET_DATE = "31"
TARGET_MONTH = "Jul"
TARGET_MONTH_NUM = "07"
TARGET_YEAR = "2026"

# --- FILTERS ---
TARGET_MOVIE = "THE ODYSSEY"  # Set to "SPIDER-MAN" if you prefer
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

def check_tickets():
    alert_triggered = False
    iso_date = f"{TARGET_YEAR}-{TARGET_MONTH_NUM}-{TARGET_DATE}"
    visible_format_1 = f"{TARGET_DATE} {TARGET_MONTH}".upper()
    visible_format_2 = f"{TARGET_MONTH} {TARGET_DATE}".upper()
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            if response.status_code == 200:
                raw_html = response.text
                clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
                clean_text = re.sub(r'\s+', ' ', clean_text).upper()
                
                # Check for all three criteria
                date_found = iso_date in raw_html or visible_format_1 in clean_text or visible_format_2 in clean_text
                movie_found = TARGET_MOVIE in clean_text
                imax_found = TARGET_FORMAT in clean_text
                
                # Require Date AND Movie AND Format
                if date_found and movie_found and imax_found:
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
