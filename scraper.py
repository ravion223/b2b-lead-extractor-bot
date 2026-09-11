import asyncio
import re
import aiosqlite
import logging
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def scrape_yellowpages():
    async with aiosqlite.connect("scraper.db") as db:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )

            page = await browser.new_page()
            
            logging.info("🚀 Entering YellowPages...")
            total_new_leads = 0

            url = f"https://www.yellowpages.com/austin-tx/roofing-contractors"
            await page.goto(url)

            try:
                await page.wait_for_selector(".result", timeout=10000)
            except Exception:
                logging.error("⚠️ Cards not found. Stopping scrapping.")
                return

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            cards = soup.find_all("div", class_="result")

            logging.info(f"✅ Found {len(cards)} cards\n")

            for card in cards:
                # 1. Name and phone number
                name_tag = card.find("a", class_="business-name")
                name = name_tag.text.strip() if name_tag else "No name"

                phone_tag = card.find("div", class_="phones")
                phone = phone_tag.text.strip() if phone_tag else "No phone number"

                # 2. Website
                website = None
                links_tag = card.find("div", class_="links")
                if links_tag:
                    website_tag = card.find("a", class_="track-visit-website")
                    if website_tag:
                        website = website_tag["href"]

                # 3. Address
                locality_tag = card.find("div", class_="locality")
                address = locality_tag.text.strip() if locality_tag else None

                # 4. Years in business
                years_in_business = None
                badges_tag = card.find("div", class_="badges")
                if badges_tag:
                    years_in_business_tag = card.find("div", class_="years-in-business")
                    if years_in_business_tag:
                        count_tag = card.find("div", class_="count")
                        if count_tag and count_tag.text.strip(" Years").isdigit():
                            years_in_business = int(count_tag.text.strip(" Years"))

                # 5. Rating and feedbacks
                rating = None
                reviews_count = None

                rating_tag = card.find("div", class_="ratings")
                if rating_tag:
                    result_rating_tag = rating_tag.find(class_=re.compile(r"result-rating"))
                    if result_rating_tag:
                        class_string = " ".join(result_rating_tag.get("class", [])).lower()

                        rating_map = {
                            "five": 5.0,
                            "four half": 4.5,
                            "four": 4.0,
                            "three half": 3.5,
                            "three": 3.0,
                            "two half": 2.5,
                            "two": 2.0,
                            "one half": 1.5,
                            "one": 1.0
                        }

                        for key, val in rating_map.items():
                            if key in class_string:
                                rating = val
                                break

                    count_span = rating_tag.find("span", class_="count")
                    if count_span:
                        count_text = count_span.text.strip("() ")
                        reviews_count = int(count_text) if count_text.isdigit() else None

                cursor = await db.execute("""
                    INSERT OR IGNORE INTO leads (business_name, phone, website, address, rating, reviews_count, years_in_business)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, phone, website, address, rating, reviews_count, years_in_business))

                if cursor.rowcount > 0:
                    total_new_leads += 1

            await db.commit()
            logging.info(f"\n🎯 Total new leads added: {total_new_leads}")

            await browser.close()
            
if __name__ == "__main__":
    asyncio.run(scrape_yellowpages())