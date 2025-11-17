from playwright.async_api import async_playwright
import asyncio
import subprocess
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')
typo = input(str("Nhập type: "))
if typo == '1':
    URL = 'https://semr.muatoolseo.com/analytics/organic/pages/?filter=%7B%22search%22%3A%22%22%2C%22intentPositions%22%3A%5B%5D%2C%22advanced%22%3A%7B%220%22%3A%7B%22inc%22%3Atrue%2C%22fld%22%3A%22tf%22%2C%22cri%22%3A%22%3E%22%2C%22val%22%3A49%7D%2C%221%22%3A%7B%22inc%22%3Atrue%2C%22fld%22%3A%22url%22%2C%22cri%22%3A%22containing%22%2C%22val%22%3A%22%2Fproducts%2F%22%7D%7D%7D&db=us&q=https%3A%2F%2Fwww.producthunt.com%2F&searchType=domain'
elif typo == '2':
    URL = 'https://semr.muatoolseo.com/analytics/organic/pages/?filter=%7B%22search%22%3A%22%22%2C%22intentPositions%22%3A%5B%5D%2C%22advanced%22%3A%7B%220%22%3A%7B%22inc%22%3Atrue%2C%22fld%22%3A%22tf%22%2C%22cri%22%3A%22%3E%22%2C%22val%22%3A49%7D%2C%221%22%3A%7B%22inc%22%3Atrue%2C%22fld%22%3A%22url%22%2C%22cri%22%3A%22containing%22%2C%22val%22%3A%22%2Fposts%2F%22%7D%7D%7D&db=us&q=https%3A%2F%2Fwww.producthunt.com%2F&searchType=domain'
elif typo == '3':
    URL = "https://semr.muatoolseo.com/analytics/organic/pages/?db=ca&q=https%3A%2F%2Fwww.producthunt.com%2F&searchType=domain"

def launch_opera():
    opera_path = r"C:\Users\Admin\AppData\Local\Programs\Opera GX\122.0.5643.178\opera.exe"
    profile_path = r"C:\opera-profile-ph"

    subprocess.Popen([  # Khởi chạy Opera GX
        opera_path,
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_path}",
    ])

    print("Opera GX launched")
    time.sleep(5)  # Thêm thời gian để Opera mở xong

async def main():
    # launch_opera()

    ws_url = "ws://localhost:9222/devtools/browser/2509863c-de67-46d3-9549-68cdb921a613"

    async with async_playwright() as p:
        print("Connecting via WebSocket…")
        browser = await p.chromium.connect_over_cdp(ws_url)
        context = browser.contexts[0]
        page = await context.new_page()

        await page.goto(URL, timeout=0)
        await page.wait_for_timeout(5000)
        await page.locator('button[placeholder="Select option"]').click()
        
        # Lấy tất cả các phần tử có selector "div[data-ui-name='Select.Option']"
        regions = await page.locator('div[data-ui-name="Select.Option"]').all()

        value_list = []
        for region in regions:
            value = await region.get_attribute('value')
            value_list.append(value)

        print(value_list)
        

        for value in value_list:
            url = URL.replace("db=us", f"db={value}") if 'db=us' in URL else URL
            print(f"Navigating to {url}")
            await page.goto(url, timeout=0)  
            await page.wait_for_timeout(5000)  

            selectors = await page.locator("div[data-ui-name='Link.Text']").all_inner_texts()
            print("Selectors:", selectors)
            traffics = await page.locator("span[data-at='display-number']").all_inner_texts()
            traffics = traffics[0::2]
            print("Traffics:", traffics)
            
            count= await page.locator('//span[text()="Next"]').count()
            if count > 0:
                await page.locator('//span[text()="Next"]').click()
            else:
                continue

asyncio.run(main())
