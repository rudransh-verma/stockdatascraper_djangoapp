import asyncio
import random
import json
from playwright.async_api import async_playwright
import cloudscraper
import requests
import time
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

def generate_wi_dv3(URLS, OUTPUT_FILE, PROXY=None):
    for url in URLS:
        # Configure scraper with or without proxy
        if PROXY:
            scr = cloudscraper.create_scraper()
            scr.proxies = {
                'http': PROXY,
                'https': PROXY,
            }
        else:
            scr = cloudscraper.create_scraper()

        # Fetch HTML content
        resp = scr.get(url, timeout=60)
        html = resp.text

        # Parse table
        soup = BeautifulSoup(html, "html.parser")
        rows = []
        for tr in soup.select("#w1-container table tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            if any(cells):
                rows.append(cells)

        # Pivot to columns
        headers = rows[0]
        columns = {h: [] for h in headers}
        for row in rows[1:]:
            for i, v in enumerate(row):
                if i < len(headers):
                    columns[headers[i]].append(v)

        result = {
            "url": url,
            "columns": columns,
        }

        # Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([result], f, indent=2, ensure_ascii=False)

        print(f"URL: {url}")
        print("✅ Saved to", OUTPUT_FILE)
