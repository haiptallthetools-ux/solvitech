import csv
import os
from playwright.async_api import async_playwright
import asyncio
import json
import pandas as pd
import os
import time
import re
current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, 'submit.csv')
data_list = pd.read_csv(path)
links = data_list["URL"].tolist()

already_submitted =  os.path.join(current_dir, "done.csv")
done_link = pd.read_csv(already_submitted)
done_links = done_link["url"].tolist()
links = [link for link in links if link not in done_links]
print(len(links), "unique links found.")
output_path = os.path.join(current_dir, "done.csv")

# Header cố định
csv_fields = [
   "url"
]

if not os.path.exists(output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=';')
        writer.writeheader()
##"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\EdgeTempDebug"
async def main():
    ws_url = "ws://localhost:9222/devtools/browser/3739e03d-c8e0-4853-bcf7-4ed92a34b406"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]

        for link in links:
            page = await context.new_page()
            try:
                print(f"Processing: {link}")
                await page.goto("https://search.google.com/search-console?utm_source=about-page&resource_id=https://www.jetcalculator.com/" , timeout=60000, wait_until="load")
                await page.wait_for_timeout(3000)
                selector = 'input[aria-label="Kiểm tra mọi URL trong https://www.jetcalculator.com/"]'
                await page.wait_for_selector(selector)
                box = page.locator(selector)
                await box.click()
                await box.fill(link)
                time.sleep(1)
                await box.press("Enter")
                
                await page.wait_for_timeout(1000)

                button = page.locator(".RveJvd.snByac", has_text="Kiểm tra URL đang hoạt động")
                cancel_popup = page.locator('span.mUIrbf-vQzf8d', has_text="Huỷ")

                await cancel_popup.wait_for(state="detached")
                await button.wait_for(state="visible")
                await page.wait_for_timeout(1000)   
                await button.click()
                await page.wait_for_timeout(1000)   
                     
                done_button  = page.locator(
    'div[role="button"][aria-label="Yêu cầu lập chỉ mụcYêu cầu lại"]',
    has_text="Yêu cầu lập chỉ mục"
).filter(has_text="Yêu cầu lại").filter(has=page.locator(":visible"))



                overlay1 = page.locator("div.uW2Fw-IE5DDf")
                await overlay1.wait_for(state="detached")
                await done_button.wait_for(state="visible")
                await page.wait_for_timeout(1000)        
                await done_button.click()
                await page.locator("span.MMvswb").wait_for(state="visible")
                await page.wait_for_timeout(3000)        

                with open(output_path, "a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow([link])

               



               







            except Exception as e:
                print(f"Error processing {link}: {e}")
            finally:
                await page.close()

        await browser.close()

asyncio.run(main())
