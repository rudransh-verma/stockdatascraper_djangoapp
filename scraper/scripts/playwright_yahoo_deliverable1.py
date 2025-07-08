import requests, time, json, re
from datetime import datetime, timezone, timedelta

def generate_yahoo_dv1(TARGET_URLS, OUTPUT_FILE, PROXY=None):
    # 1) compute yesterday’s UTC-midnight once
    today_mid = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_mid = today_mid - timedelta(days=1)
    ts = int(yesterday_mid.timestamp())      # UNIX seconds for 00:00 UTC yesterday
    date_str = yesterday_mid.strftime("%Y-%m-%d")

    session = requests.Session()
    if PROXY:
        session.proxies.update({"http": PROXY, "https": PROXY})

    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/115.0.0.0 Safari/537.36")

    results = []
    for url in TARGET_URLS:
        m = re.search(r"/quote/([^/]+)/history", url)
        if not m:
            results.append({"url": url, "error": "Invalid symbol URL"})
            continue
        symbol = m.group(1)

        api = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1":        ts,
            "period2":        ts + 86400,
            "interval":       "1d",
            "includePrePost": "false"
        }
        headers = {"User-Agent": ua}

        # stream=False but resp.raw is still populated

        resp = session.get(api, params=params, headers=headers, timeout=30, stream=False)


        try:
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            results.append({"url": url, "error": f"HTTP/JSON error: {e}"})
            continue



        result = data.get("chart", {}).get("result")
        if not result or not result[0].get("timestamp"):
            err = data.get("chart", {}).get("error", {}).get("description", "No data")
            results.append({"url": url, "error": err})
            continue

        quote = result[0]["indicators"]["quote"][0]

        # Build our forced row for “yesterday”:
        row = {
            "timestamp_utc": ts,
            "date_utc":      date_str,
            "open":   quote["open"][0],
            "high":   quote["high"][0],
            "low":    quote["low"][0],
            "close":  quote["close"][0],
            "volume": quote["volume"][0],
        }

        results.append({
            "url":  url,
            "data": row,
        })

    # save JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)

    # echo to console

    print(f"✅ Done – saved to {OUTPUT_FILE}")
