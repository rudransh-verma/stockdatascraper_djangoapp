import asyncio
import random
import os
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from datetime import datetime, timezone

def generate_bigchart_5day(yh_symbol, PROXY=None):
    symbol_stripped = yh_symbol.replace("=X", "")
    # List of common user agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    ]
    # Possible viewport sizes
    VIEWPORTS = [
        {"width": 1280, "height": 720},
        {"width": 1366, "height": 768},
        {"width": 1024, "height": 768},
    ]
    # Possible accept-language headers
    LANGUAGES = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7"]

    async def stealth_page(page):
        # Hide webdriver and common headless indicators
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
        """)

    async def random_delay(steps=1, min_s=0.5, max_s=2.0):
        """Pause for a random number of intervals to mimic variable human behavior"""
        for _ in range(random.randint(1, steps)):
            await asyncio.sleep(random.uniform(min_s, max_s))

    async def run():
        async with async_playwright() as p:
            # Rotate user agent and viewport
            ua = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            lang = random.choice(LANGUAGES)

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--blink-settings=imagesEnabled=false",
                ]
            )

            # Build context arguments dynamically to include proxy if provided
            context_args = {
                "user_agent": ua,
                "viewport": viewport,
                "locale": lang.split(",")[0],
                "extra_http_headers": {"Accept-Language": lang}
            }
            if PROXY:
                context_args["proxy"] = {"server": PROXY}

            context = await browser.new_context(**context_args)

            # Block unnecessary resources
            await context.route(
                "**/*.{png,jpg,jpeg,svg,css,woff,woff2,ttf,otf}",
                lambda route: asyncio.create_task(route.abort())
            )

            page = await context.new_page()
            # Extend timeouts
            page.set_default_navigation_timeout(120000)
            page.set_default_timeout(120000)

            await stealth_page(page)
            await random_delay(2, min_s=1, max_s=4)

            # Navigate
            await page.goto(
                f'https://bigcharts.marketwatch.com/advchart/frames/frames.asp?show=&insttype=Currency&symb={symbol_stripped}',
                timeout=120000,
                wait_until='domcontentloaded'
            )
            await random_delay(3, min_s=1, max_s=5)

            # Interactions with added delays
            actions = [
                ("click", '#time'),
                ("select", ('#time', '3')),
                ("click", '#freq'),
                ("select", ('#freq', '7')),
                ("click", '.chartstyle > a:nth-child(2)'),
                ("select", ('#type', '64')),
                ("click", 'input.drawchart:nth-child(1)')
            ]

            for action, target in actions:
                if action == "click":
                    await page.click(target)
                elif action == "select":
                    sel, val = target
                    await page.select_option(sel, val)
                # randomize delays after each action
                await random_delay(random.randint(1, 3), min_s=0.5, max_s=3)

            # Wait for chart render
            await page.wait_for_load_state('domcontentloaded')
            await random_delay(2, min_s=1, max_s=4)

            # Retrieve image
            img = await page.query_selector('td.padded > img:nth-child(1)')
            src = await img.get_attribute('src')
            response = await context.request.get(src)
            content = await response.body()

            # Derive filename
            parsed = urlparse(src)
            base_name = os.path.splitext(os.path.basename(parsed.path))[0] or 'chart'
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                ext = '.png'

            # Current UTC datetime
            now_utc = datetime.now(timezone.utc)

            # Convert to Unix timestamp
            timestamp = f"{symbol_stripped}-{int(now_utc.timestamp())}-5day-graph"
            global filename
            filename = f"{timestamp}{ext}"


            # Save file
            with open(filename, 'wb') as f:
                f.write(content)
            await browser.close()


    asyncio.run(run())
    return filename
