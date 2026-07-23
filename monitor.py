import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Target page or API endpoint to monitor
URL = "https://www.pvrcinemas.com/" 

def send_telegram_alert(msg):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(telegram_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending alert: {e}")

def check_tickets():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        
        # Customize this condition based on what appears when the date/shows drop
        if response.status_code == 200 and "26 Jul" in response.text:
            send_telegram_alert("🚨 IMAX TICKETS LIVE! Check PVR / INOX App immediately!")
            print("Alert sent successfully!")
        else:
            print("No tickets detected yet.")
            
    except Exception as e:
        print(f"Fetch failed: {e}")

if __name__ == "__main__":
    check_tickets()
