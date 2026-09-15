import os
import logging

from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")

# --- Paths ---
DB_PATH = os.getenv("DB_PATH", "scraper.db")
EXPORT_FILE = "leads_report.xlsx"

# --- Business Logic ---
FREE_TIER_LIMIT = 5

# --- Logging (single setup for the entire app) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
