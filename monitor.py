import os
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

THEATERS = {
    "Palazzo (Nexus Vijaya)": "https://www.pvrcinemas.com/cinemasessions/Chennai/PVR-Palazzo-The-Nexus-Vijaya-Mall/388",
    "LUXE (Phoenix Marketcity)": "https://www.pvrcinemas.com/cinemasessions/Chennai/INOX-Luxe-Phoenix-Market-City,-Velachery--(formerly-Jazz-Cinemas)Chennai/320"
}

TARGET_DATE = "26"  # Keep as 26 for testing
TARGET_MONTH = "Jul"

def send_telegram_alert(msg):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
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
            # impersonate="chrome" perfectly mimics a real browser's network fingerprint
            response = requests.get(url, impersonate="chrome", timeout=15)
            print(f"HTTP Status Code for {name}: {response.status_code}")
            
            if response.status_code == 200:
                if TARGET_DATE in response.text and TARGET_MONTH in response.text:
                    send_telegram_alert(f"🚨 IMAX ALERT! {name} has updated showtimes for {TARGET_DATE} {TARGET_MONTH}! Open PVR app NOW!")
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
