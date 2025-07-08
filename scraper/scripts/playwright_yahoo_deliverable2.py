import requests
import time
import json
import re
from datetime import datetime, timezone, timedelta

def generate_yahoo_dv2(TARGET_URLS, OUTPUT_FILE, PROXY=None):
    # 1) build 90-day window [now-90d, now)
    now = int(time.time())
    start_ts = now - 90 * 86400
    end_ts   = now

    session = requests.Session()
    if PROXY:
        session.proxies.update({"http": PROXY, "https": PROXY})

    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )

    results = []
    for url in TARGET_URLS:
        # extract symbol
        m = re.search(r"/quote/([^/]+)/history", url)
        if not m:
            results.append({"url": url, "error": "Invalid symbol URL"})
            continue
        symbol = m.group(1)

        api = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1":        start_ts,
            "period2":        end_ts,
            "interval":       "1d",
            "includePrePost": "false"
        }
        headers = {"User-Agent": ua}

        resp = session.get(api, params=params, headers=headers, timeout=30, stream=False)


        try:
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            results.append({"url": url, "error": f"HTTP/JSON error: {e}"})
            continue
        # parse the 90-day history
        chart_data = payload.get("chart", {}).get("result")
        if not chart_data:
            err = payload.get("chart", {}).get("error", {}).get("description", "No data")
            results.append({"url": url, "error": err})
            continue

        result = chart_data[0]
        timestamps = result.get("timestamp", [])
        quote = result["indicators"]["quote"][0]

        rows = []
        for i, ts in enumerate(timestamps):
            rows.append({
                "date":   datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d"),
                "open":   quote["open"][i],
                "high":   quote["high"][i],
                "low":    quote["low"][i],
                "close":  quote["close"][i],
                "volume": quote["volume"][i],
            })

        results.append({
            "url":  url,
            "data": rows,
        })

    # write to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Done – saved to {OUTPUT_FILE}")

