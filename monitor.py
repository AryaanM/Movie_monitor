import os
import requests

# Fetch secrets configured in your GitHub Repository Secrets
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Direct session pages for Chennai IMAX locations
THEATERS = {
    "Palazzo (Nexus Vijaya)": "https://www.pvrcinemas.com/cinemasessions/Chennai/PVR-Palazzo-The-Nexus-Vijaya-Mall/388",
    "LUXE (Phoenix Marketcity)": "https://www.pvrcinemas.com/cinemasessions/Chennai/INOX-Luxe-Phoenix-Market-City,-Velachery--(formerly-Jazz-Cinemas)Chennai/320"
}

def send_telegram_alert(msg):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(telegram_url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram alert delivered successfully!")
        else:
            print(f"Failed to send Telegram alert: {res.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def check_tickets():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    alert_triggered = False
    
    for name, url in THEATERS.items():
        print(f"Checking {name}...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            # Checks if both '31' and 'Jul' appear on the specific theater's schedule
            if response.status_code == 200 and "31" in response.text and "Jul" in response.text:
                send_telegram_alert(f"🚨 IMAX ALERT! {name} has updated showtimes for July 31st! Open PVR app NOW!")
                alert_triggered = True
            else:
                print(f"Status {response.status_code}: No July 31 tickets detected for {name}.")
                
        except Exception as e:
            print(f"Fetch failed for {name}: {e}")
            
    if not alert_triggered:
        print("Check completed across all targets. No new slots found.")

if __name__ == "__main__":
    check_tickets()
