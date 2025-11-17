from playwright.async_api import async_playwright
import asyncio
import json
import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

URL = "https://www.producthunt.com/products/giggl"

def launch_opera():
    opera_path = r"C:\Users\Admin\AppData\Local\Programs\Opera GX\122.0.5643.178\opera.exe"
    profile_path = r"C:\opera-profile-ph"

    subprocess.Popen([
        opera_path,
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_path}",
    ])

    print("Opera GX launched")
    time.sleep(2)

async def main():
    launch_opera()

    ws_url = "ws://localhost:9222/devtools/browser/d18a3011-8ad7-428e-aec6-1d5bfe5068fe"

    async with async_playwright() as p:
        print("Connecting via WebSocket…")
        browser = await p.chromium.connect_over_cdp(ws_url)

        context = browser.contexts[0]
        page = await context.new_page()

        await page.goto(URL, timeout=0)
        await page.wait_for_timeout(5000)

        json_ld_raw = await page.locator("script[type='application/ld+json']").all_inner_texts()
        for raw in json_ld_raw:
            if 'description' in raw:
                ld = json.loads(raw)
                result = {
                    "name": ld.get("name"),
                    "description": ld.get("description"),
                    "rating_value": ld.get("aggregateRating", {}).get("ratingValue"),
                    "rating_count": ld.get("aggregateRating", {}).get("ratingCount"),
                    "images": ld.get("screenshot", []),
                    "thumbnail": ld.get("image"),
                    "authors": [a["name"] for a in ld.get("author", [])],
                    "price": ld.get("offers", {}).get("price"),
                    "currency": ld.get("offers", {}).get("priceCurrency"),
                    "category": ld.get("applicationCategory"),
                    "published": ld.get("datePublished"),
                    "modified": ld.get("dateModified"),
                }

                print("Ket qua:", result) 

asyncio.run(main())
