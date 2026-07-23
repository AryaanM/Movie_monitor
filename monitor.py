import os
import re
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

THEATERS = {
    "Palazzo (District)": "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    "LUXE (District)": "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779"
}

TARGET_DATE = "26"  # Test with 26 first, then change to 31!
TARGET_MONTH = "Jul"
TARGET_MONTH_NUM = "07"
TARGET_YEAR = "2026"

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
    
    # 1. The exact backend API date format (e.g., "2026-07-26")
    iso_date = f"{TARGET_YEAR}-{TARGET_MONTH_NUM}-{TARGET_DATE}"
    
    # 2. Visible text formats
    visible_format_1 = f"{TARGET_DATE} {TARGET_MONTH}".upper() # "26 JUL"
    visible_format_2 = f"{TARGET_MONTH} {TARGET_DATE}".upper() # "JUL 26"
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            print(f"HTTP Status Code for {name}: {response.status_code}")
            
            if response.status_code == 200:
                raw_html = response.text
                
                # Strip all HTML tags to read plain text, and compress multiple spaces
                clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
                clean_text = re.sub(r'\s+', ' ', clean_text).upper()
                
                # Check if either the backend ISO date exists, or the cleaned text contains the date
                if iso_date in raw_html or visible_format_1 in clean_text or visible_format_2 in clean_text:
                    send_telegram_alert(f"🚨 IMAX ALERT! {name} has updated showtimes for {TARGET_DATE} {TARGET_MONTH}! Open app NOW!")
                    alert_triggered = True
                else:
                    print(f"Status 200 OK, but exact target date not found on page for {name}.")
            else:
                print(f"Blocked or error (Status {response.status_code}) for {name}.")
                
        except Exception as e:
            print(f"Fetch failed for {name}: {e}")
            
    if not alert_triggered:
        print("Check completed across all targets.")

if __name__ == "__main__":
    check_tickets()
