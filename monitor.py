import os
import json
import time
import requests
from bs4 import BeautifulSoup

# ---- Configuration (set via environment variables) ----
URL = os.environ.get(
    "CROUS_URL",
    "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=7.1819535_43.7607635_7.323912_43.6454189&locationName=Nice",
)
NTFY_TOPIC = os.environ["NTFY_TOPIC"]  # required - your secret ntfy.sh topic name
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))  # seconds between checks
MAX_RUNTIME = int(os.environ.get("MAX_RUNTIME", str(5 * 3600 + 45 * 60)))  # 5h45m, then exit cleanly
STATE_FILE = os.environ.get("STATE_FILE", "seen_listings.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def load_seen():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=0)


def fetch_listings():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # The site uses the French DSFR "fr-card" component for each listing.
    cards = soup.find_all("div", class_=lambda c: c and "fr-card" in c.split())

    listings = []
    for card in cards:
        link = card.find("a")
        name = link.get_text(strip=True) if link else card.get_text(strip=True)
        href = link.get("href") if link and link.get("href") else ""
        if href and href.startswith("/"):
            href = "https://trouverunlogement.lescrous.fr" + href
        listings.append((name, href))
    return listings


def notify(title, message, url=None):
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": "urgent",
        "Tags": "house,rotating_light",
    }
    if url:
        headers["Click"] = url
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
    except Exception as e:
        print("Failed to send notification:", e)


def main():
    seen = load_seen()
    start = time.time()
    print(f"Monitoring started for: {URL}")
    print(f"Already known listings in state file: {len(seen)}")

    # Quick heartbeat so you know the bot is alive when it (re)starts.
    if os.environ.get("SEND_STARTUP_PING", "0") == "1":
        notify("CROUS bot started", "Watcher is running.")

    while time.time() - start < MAX_RUNTIME:
        try:
            listings = fetch_listings()
            current_keys = {f"{name}||{href}" for name, href in listings}
            new_keys = current_keys - seen

            if listings:
                print(f"[{time.strftime('%H:%M:%S')}] {len(listings)} listing(s) currently on page.")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No listings (Aucun logement trouvé).")

            if new_keys:
                for key in new_keys:
                    name, href = key.split("||", 1)
                    print("NEW LISTING:", name, href)
                    notify(
                        "🏠 Logement CROUS disponible !",
                        f"{name}\n{href or URL}",
                        url=href or URL,
                    )
                seen |= new_keys
                save_seen(seen)

            # Clean up: if the page is empty, reset state so a listing that
            # reappears later is treated as "new" and triggers a notification again.
            if not listings and seen:
                seen = set()
                save_seen(seen)

        except Exception as e:
            print("Error during check:", e)

        time.sleep(CHECK_INTERVAL)

    print("Max runtime reached, exiting cleanly (next scheduled run will resume).")


if __name__ == "__main__":
    main()
