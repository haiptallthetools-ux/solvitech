import csv
import os
from playwright.async_api import async_playwright
import asyncio
import json
import pandas as pd
import os
from urllib.parse import urlparse

import re
current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, 'g2.csv')
data_list = pd.read_csv(path)
links = data_list["URL"].tolist()
links = list(set(links))
traffic_list = data_list["Traffic"].tolist()
print(len(links), "unique links found.")
output_path = os.path.join(current_dir, "g2_result2.csv")

# Header cố định
csv_fields = [
    "url",
    "price",
    "price_monthly",
    "price_yearly",  
    "name",
    "logo",
    "rating_value",
    "rating_count",
    "website",
    "description",
    "image",
    "traffic",
    "reviews",
]



async def get_all_attributes(page, selector, attr):
    locator = page.locator(selector)
    values = []

    for i in range(await locator.count()):
        val = await locator.nth(i).get_attribute(attr)
        if val:
            values.append(val)

    return values

if not os.path.exists(output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=';')
        writer.writeheader()

async def main():
    ws_url = "ws://localhost:9222/devtools/browser/3a079dc0-9020-4bbd-9211-e812c219e2d7"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]

        for link, traffic in zip(links, traffic_list):
            sect = link.split("/")[-1]
            if sect != 'reviews':
                if '/competitors' in link:
                    link  = link.replace("/competitors", "")
                link = link.replace(sect, "reviews")
            page = await context.new_page()
            try:
                
                print(f"Processing: {link}")
                await page.goto( link, wait_until="load")
                # await page.wait_for_timeout(3000)
                name = await page.locator(
                    "meta[property='og:title']"
                ).get_attribute("content")     
                name = name.replace("The G2 on ", "")
                logo = await page.locator("img[title='Product Avatar Image']").nth(0).get_attribute("src")
                rating_value = await page.locator("meta[name='twitter:data2']").get_attribute("value")
                rating_value = rating_value.replace(" ⭐", "")
                rating_count = await page.locator("meta[itemprop='reviewCount']").get_attribute("content")
                webcheck = page.locator("meta[itemprop='url']")
                website = await webcheck.first.get_attribute("content") if await webcheck.count() else None
                website = urlparse(website).netloc if website else None
                description = await page.locator("p[itemprop='description']").nth(0).inner_text()
                image = await get_all_attributes(
    page,
    f"img[title='{name} provided thumbnail']",
    "src"
)
                price_cols = {}

                def push(col, value):
                    price_cols.setdefault(col, []).append(value)

                specs = page.locator('[itemprop="priceSpecification"]')

                for i in range(await specs.count()):
                    spec = specs.nth(i)

                    async def get(prop):
                        el = spec.locator(f'meta[itemprop="{prop}"]')
                        return await el.get_attribute("content") if await el.count() else None

                    price = await get("price")
                    if not price:
                        continue

                    unit = await get("unitText")
                    freq = None
                    if unit:
                        unit = unit.lower()
                        if "month" in unit:
                            freq = "monthly"
                        elif "year" in unit:
                            freq = "yearly"

                    col_name = f"price_{freq}" if freq else "price"

                    push(col_name, {
                        "plan_name": await get("name"),
                        "price": float(price),
                        "currency": await get("priceCurrency"),
                        "trial_days": None
                    })
                reviews = await page.locator('div[itemprop="name"] > div').all_inner_texts()
                result = {
                    "url": link,
                    "name": name,
                    "logo": logo,
                    "rating_value": rating_value,
                    "rating_count": rating_count,
                    "website": website,
                    "description": description,
                    "image": ",".join(image),
                    "traffic": traffic,
                    "reviews": reviews,
                    "price": price_cols.get("price", []),
                    "price_monthly": price_cols.get("price_monthly", []),
                    "price_yearly": price_cols.get("price_yearly", []),
                }
                with open(output_path, mode="a", encoding="utf-8-sig", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=';')
                            writer.writerow(result)

                print("Saved:", result["url"])


                
                

               

            except Exception as e:
                print(f"Error processing {link}: {e}")
            finally:
                await page.close()

        await browser.close()

asyncio.run(main())
