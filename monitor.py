import os
import random
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- TEMP: verify against July 30 where IMAX is confirmed live ---
TARGET_DATE_ISO = "2026-07-30"
TARGET_MOVIE_KEYWORD = "odyssey"   # matched case-insensitively against movie name
TARGET_FORMAT_KEYWORD = "imax"     # matched case-insensitively against scrnFmt

API_URL = "https://www.district.in/gw/consumer/movies/v3/cinema"

THEATERS = {
    "Palazzo": 1022274,
    "LUXE (INOX Phoenix Marketcity)": 1020779,
}

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.district.in/movies/",
    "Origin": "https://www.district.in",
}


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


def check_theater(name, cinema_id):
    params = {
        "meta": 1,
        "reqData": 1,
        "version": 3,
        "site_id": 1,
        "channel": "mweb",
        "child_site_id": 1,
        "platform": "district",
        "cinemaId": cinema_id,
        "date": TARGET_DATE_ISO,
        # cache-buster, harmless if API ignores unknown params
        "_": random.randint(100000, 999999),
    }

    try:
        response = requests.get(
            API_URL, params=params, headers=HEADERS, impersonate="chrome", timeout=15
        )
    except Exception as e:
        print(f"Fetch failed for {name}: {e}")
        return False

    if response.status_code != 200:
        print(f"Blocked/error (Status {response.status_code}) for {name}.")
        return False

    try:
        data = response.json()
    except Exception as e:
        print(f"Could not parse JSON for {name}: {e}")
        return False

    movies = data.get("meta", {}).get("movies", [])
    sessions = data.get("pageData", {}).get("sessions", [])

    # Collect every movie-code (mid) whose name matches our target movie,
    # since the same movie can have multiple entries (one per language/version)
    target_mids = {
        m["id"] for m in movies
        if TARGET_MOVIE_KEYWORD in (m.get("name") or "").lower()
    }

    if not target_mids:
        print(f"{name}: '{TARGET_MOVIE_KEYWORD}' not even listed for {TARGET_DATE_ISO} yet.")
        return False

    matches = [
        s for s in sessions
        if s.get("mid") in target_mids
        and TARGET_FORMAT_KEYWORD in (s.get("scrnFmt") or "").lower()
    ]

    if matches:
        details = "; ".join(
            f"{s['showTime']} ({s.get('audi', '?')}, {s.get('lang', '?')}, {s.get('scrnFmt')})"
            for s in matches
        )
        print(f"{name}: MATCH FOUND -> {details}")
        send_telegram_alert(
            f"🚨 TICKET ALERT! {name} has {TARGET_FORMAT_KEYWORD.upper()} showtimes "
            f"for The Odyssey on {TARGET_DATE_ISO}!\n{details}\nOpen app NOW!"
        )
        return True
    else:
        found_formats = sorted({
            s.get("scrnFmt") for s in sessions if s.get("mid") in target_mids
        })
        print(
            f"{name}: Odyssey is listed ({len(target_mids)} version(s)) but no "
            f"{TARGET_FORMAT_KEYWORD.upper()} yet. Current formats live: {found_formats}"
        )
        return False


def check_tickets():
    alert_triggered = False
    for name, cinema_id in THEATERS.items():
        print(f"Checking {name}...")
        if check_theater(name, cinema_id):
            alert_triggered = True

    if not alert_triggered:
        print("Check completed across all targets. No IMAX yet.")


if __name__ == "__main__":
    check_tickets()
