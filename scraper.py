import asyncio
import re
import logging
import random

import aiosqlite
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup

from config import DB_PATH, SCRAPER_API_KEY


async def scrape_directory(url: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        # Clearing db before new parsing
        await db.execute("DELETE FROM leads")
        await db.commit()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--ignore-certificate-errors'],
                proxy={
                    "server": "http://proxy-server.scraperapi.com:8001",
                    "username": "scraperapi.country=us",
                    "password": SCRAPER_API_KEY
                }
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="America/Chicago",
                ignore_https_errors=True
            )

            page = await context.new_page()
            await stealth_async(page)
            
            logging.info(f"🚀 Entering URL: {url}")
            total_new_leads = 0

            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            # Random human-like delay (3-6 seconds)
            await asyncio.sleep(random.uniform(3, 6))

            try:
                await page.wait_for_selector(".result", timeout=15000)
            except Exception:
                # Save a screenshot so we can see WHY it failed (CAPTCHA, block, changed layout)
                await page.screenshot(path="debug_screenshot.png", full_page=True)
                logging.error("⚠️ Cards not found. Screenshot saved to debug_screenshot.png")
                await browser.close()
                return {"total_found": 0, "new_added": 0}

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.find_all("div", class_="result")

            if not cards:
                await browser.close()
                return {"total_found": 0, "new_added": 0}

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
            await browser.close()

            return {"total_found": len(cards), "new_added": total_new_leads}

if __name__ == "__main__":
    pass