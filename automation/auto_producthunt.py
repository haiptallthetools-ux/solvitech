import csv
import os
from playwright.async_api import async_playwright
import asyncio
import json
import pandas as pd
import os

import re
current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, 'producthunt.csv')
data_list = pd.read_csv(path)
links = data_list["Selector"].tolist()
links = list(set(links))
traffic_list = data_list["Traffic"].tolist()
print(len(links), "unique links found.")
output_path = os.path.join(current_dir, "producthunt_result2.csv")

# Header cố định
csv_fields = [
    "url","name","traffic","logo","description","rating_value","rating_count",
    "images","thumbnail","authors","price","currency","category","published","modified",
    "image","gen_description","pros","cons", "tags"
]

if not os.path.exists(output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, delimiter=';')
        writer.writeheader()

async def main():
    ws_url = "ws://localhost:9222/devtools/browser/8bf414e8-3a24-4ed5-acf2-c2d83cb167ee"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]

        for link, traffic in zip(links, traffic_list):
            page = await context.new_page()
            try:
                print(f"Processing: {link}")
                await page.goto('https://' + link, timeout=60000, wait_until="load")
                await page.wait_for_timeout(3000)

                json_ld_raw = await page.locator("script[type='application/ld+json']").all_inner_texts()
                for raw in json_ld_raw:
                    if 'description' in raw:
                        ld = json.loads(raw)
                        # logo
                        logo = None
                        logo_locator = page.locator(f"img[alt='{ld.get('name')}']")
                        if await logo_locator.count() > 0:
                            logo = await logo_locator.first.get_attribute("src")
                        # images
                        images = []
                        media_locator = page.locator(f"div[aria-label='{ld.get('name')}'] media")
                        for i in range(await media_locator.count()):
                            src = await media_locator.nth(i).get_attribute("src")
                            if src:
                                images.append(src)
                        gen_desc_locator = page.locator("div[class='styles-module__9XWFJG__markdown !text-16 !text-secondary [&_a]:!text-brand-500']")
                        if await gen_desc_locator.count() > 0:
                            gen_description = await gen_desc_locator.first.inner_text()
                        else:
                            gen_description = None
                        pros_title = await page.query_selector("div:text('Pros')")
                        if pros_title:
                            pros_container = await pros_title.evaluate_handle("el => el.nextElementSibling")

                            tags_el = await pros_container.query_selector_all("div.flex.cursor-pointer")

                            pros = []
                            for tag in tags_el:
                                text = await tag.inner_text()
                                clean = re.sub(r"\s*\([^)]*\)$", "", text)
                                pros.append(clean.strip())
                            print("Tags:", pros)
                        else:
                            pros = []
                            
                        cons_title = await page.query_selector("div:text('Cons')")
                        if cons_title:
                            cons_container = await cons_title.evaluate_handle("el => el.nextElementSibling")

                            tags_el = await cons_container.query_selector_all("div.flex.cursor-pointer")

                            cons = []
                            for tag in tags_el:
                                text = await tag.inner_text()
                                clean = re.sub(r"\s*\([^)]*\)$", "", text)
                                cons.append(clean.strip())
                            print("Tags:", cons)
                        else:
                            cons = []
                        
                        category = page.locator(
            "a.text-14.text-tertiary.group-hover\\:brightness-25"
        )

                        if await category.count() > 0:
                            category_text = await category.all_inner_texts()
                        else:
                            category_text = []

                        print("Category:", category_text)
                        result = {
                            "url": link,
                            "name": ld.get("name"),
                            "traffic": traffic,
                            "logo": logo,
                            "image": images,  # list
                            "description": ld.get("description"),
                            "rating_value": ld.get("aggregateRating", {}).get("ratingValue"),
                            "rating_count": ld.get("aggregateRating", {}).get("ratingCount"),
                            "images": ld.get("screenshot", []),  # list
                            "thumbnail": ld.get("image"),
                            "authors": [a["name"] for a in ld.get("author", [])],  # list
                            "gen_description": gen_description,
                            "pros": pros,
                            "cons": cons,
                            "price": ld.get("offers", {}).get("price"),
                            "currency": ld.get("offers", {}).get("priceCurrency"),
                            "tags": ld.get("applicationCategory"),
                            "category": category_text,
                            "published": ld.get("datePublished"),
                            "modified": ld.get("dateModified"),
                        }
                        # print(result)

                        # safe_result = {k: ';'.join(v) if isinstance(v, list) else v for k, v in result.items()}

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
