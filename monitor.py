import os
import random
import string
import time
from curl_cffi import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- TEMP: verify against July 30 where IMAX is confirmed live ---
TARGET_DATE_ISO = "2026-07-30"
TARGET_MOVIE_KEYWORD = "odyssey"   # matched case-insensitively against movie name
TARGET_FORMAT_KEYWORD = "imax"     # matched case-insensitively against scrnFmt

API_URL = "https://www.district.in/gw/consumer/movies/v3/cinema"

# name -> (cinemaId, theater page URL, slug used for ?fromdate referer)
THEATERS = {
    "Palazzo": (
        1022274,
        "https://www.district.in/movies/pvr-palazzo-the-nexus-vijaya-mall-chennai-in-chennai-CD1022274",
    ),
    "LUXE (INOX Phoenix Marketcity)": (
        1020779,
        "https://www.district.in/movies/inox-phoenix-market-city-formerly-jazz-cinemas-velachery-chennai-in-chennai-CD1020779",
    ),
}

COMMON_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "api_source": "district",
    "x-app-type": "ed_mweb",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "priority": "u=1, i",
}


def make_guest_token():
    # Mirrors the pattern seen in real traffic: <ms_timestamp>_<big_random_int>_<base36_random>
    ts = int(time.time() * 1000)
    big_rand = random.randint(10 ** 17, 10 ** 18 - 1)
    tail = "".join(random.choices(string.ascii_lowercase + string.digits, k=11))
    return f"{ts}_{big_rand}_{tail}"


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


def check_theater(name, cinema_id, page_url):
    session = requests.Session()

    # Step 1: visit the real theater page first so Akamai + district.in set
    # their normal cookies (ak_bmsc, bm_sv, AKA_A2, etc.) on this session,
    # exactly like a browser would before it fires the API call.
    try:
        session.get(
            f"{page_url}?fromdate={TARGET_DATE_ISO}",
            impersonate="chrome",
            timeout=15,
        )
    except Exception as e:
        print(f"Bootstrap page load failed for {name}: {e}")
        return False

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
    }

    headers = dict(COMMON_HEADERS)
    headers["Referer"] = f"{page_url}?fromdate={TARGET_DATE_ISO}"
    headers["x-guest-token"] = make_guest_token()

    # Step 2: now call the actual data API within the same session (cookies carry over)
    try:
        response = session.get(
            API_URL, params=params, headers=headers, impersonate="chrome", timeout=15
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
    for name, (cinema_id, page_url) in THEATERS.items():
        print(f"Checking {name}...")
        if check_theater(name, cinema_id, page_url):
            alert_triggered = True

    if not alert_triggered:
        print("Check completed across all targets. No IMAX yet.")


if __name__ == "__main__":
    check_tickets()
