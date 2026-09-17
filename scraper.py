import asyncio
import re
import logging
import random

import aiosqlite
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup

from config import DB_PATH, SCRAPER_API_KEY


def _build_page_url(base_url: str, page_num: int) -> str:
    """Build paginated URL by appending/replacing ?page=N parameter."""
    if page_num <= 1:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_num}"


async def scrape_directory(url: str, pages: int = 1, progress_callback=None) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        # Clearing db before new parsing
        await db.execute("DELETE FROM leads")
        await db.commit()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
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

            total_cards_found = 0
            total_new_leads = 0

            for page_num in range(1, pages + 1):
                page_url = _build_page_url(url, page_num)
                logging.info(f"🚀 Scraping page {page_num}/{pages}: {page_url}")

                if progress_callback:
                    await progress_callback(f"📄 Scraping page {page_num}/{pages}...")

                # Retry loop for navigation (ScraperAPI proxy can be slow/flaky)
                max_retries = 3
                page_loaded = False
                for attempt in range(1, max_retries + 1):
                    try:
                        await page.goto(page_url, wait_until="load", timeout=120000)
                        # Random human-like delay — gives JS time to render cards
                        await asyncio.sleep(random.uniform(4, 7))
                        await page.wait_for_selector(".result", timeout=30000)
                        page_loaded = True
                        break
                    except Exception as e:
                        logging.warning(f"⚠️ Page {page_num}, attempt {attempt}/{max_retries} failed: {e}")
                        if attempt < max_retries:
                            retry_delay = attempt * 5  # 5s, 10s backoff
                            if progress_callback:
                                await progress_callback(
                                    f"🔄 Page {page_num}/{pages} — retry {attempt + 1}/{max_retries} in {retry_delay}s..."
                                )
                            await asyncio.sleep(retry_delay)

                if not page_loaded:
                    if page_num == 1:
                        # First page failed after all retries — save debug screenshot and abort
                        try:
                            await page.screenshot(path="debug_screenshot.png", full_page=True)
                        except Exception:
                            pass
                        logging.error("⚠️ Cards not found on page 1 after all retries. Screenshot saved to debug_screenshot.png")
                        await browser.close()
                        return {"total_found": 0, "new_added": 0, "pages_scraped": 0}
                    else:
                        # Subsequent page failed — we've likely reached the end
                        logging.info(f"📭 No results on page {page_num} after retries. Stopping pagination.")
                        break

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all("div", class_="result")

                if not cards:
                    logging.info(f"📭 No cards found on page {page_num}. Stopping pagination.")
                    break

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

                total_cards_found += len(cards)
                await db.commit()
                logging.info(f"✅ Page {page_num}: found {len(cards)} cards, {total_new_leads} total unique leads so far")

                # Human-like delay between pages (2-5 seconds)
                if page_num < pages:
                    await asyncio.sleep(random.uniform(2, 5))

            await browser.close()

            return {"total_found": total_cards_found, "new_added": total_new_leads, "pages_scraped": page_num}

if __name__ == "__main__":
    pass