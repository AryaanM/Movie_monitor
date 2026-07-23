import os
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# The exact URLs for Palazzo and LUXE across both platforms
THEATERS = {
    "Palazzo (BookMyShow)": "https://in.bookmyshow.com/cinemas/chen/pvr-palazzothe-nexus-vijaya-mall/buytickets/PVPZ/",
    "LUXE (BookMyShow)": "https://in.bookmyshow.com/cinemas/chen/inox-luxe-phoenix-market-city-velachery/buytickets/INPR/",
    "Palazzo (District)": "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    "LUXE (District)": "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-kolathur-CD1020779"
}

TARGET_DATE = "26"  # Leave as 26 to test the ping
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
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            # impersonate="chrome" perfectly mimics a real browser's network fingerprint to bypass Cloudflare
            response = requests.get(url, impersonate="chrome", timeout=15)
            print(f"HTTP Status Code for {name}: {response.status_code}")
            
            if response.status_code == 200:
                if TARGET_DATE in response.text and TARGET_MONTH in response.text:
                    send_telegram_alert(f"🚨 IMAX ALERT! {name} has updated showtimes for {TARGET_DATE} {TARGET_MONTH}! Open app NOW!")
                    alert_triggered = True
                else:
                    print(f"Status 200 OK, but target date ({TARGET_DATE} {TARGET_MONTH}) not found on page for {name}.")
            else:
                print(f"Blocked or error (Status {response.status_code}) for {name}.")
                
        except Exception as e:
            print(f"Fetch failed for {name}: {e}")
            
    if not alert_triggered:
        print("Check completed across all targets.")

if __name__ == "__main__":
    check_tickets()
