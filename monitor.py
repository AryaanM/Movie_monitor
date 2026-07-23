import os
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

THEATERS = {
    "Palazzo (District)": "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    "LUXE (District)": "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779"
}

TARGET_DATE = "31"  
TARGET_MONTH = "Jul"

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
    
    # Check for exact date phrases rather than isolated numbers and words
    valid_date_formats = [
        f"{TARGET_DATE} {TARGET_MONTH}",       # "31 Jul"
        f"{TARGET_DATE} {TARGET_MONTH}y",      # "31 July"
        f"{TARGET_MONTH} {TARGET_DATE}",       # "Jul 31"
        f"{TARGET_DATE}-{TARGET_MONTH}"        # "31-Jul"
    ]
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, impersonate="chrome", timeout=15)
            print(f"HTTP Status Code for {name}: {response.status_code}")
            
            if response.status_code == 200:
                text = response.text
                
                # Check if ANY of the exact date strings exist in the HTML
                if any(fmt in text for fmt in valid_date_formats):
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
