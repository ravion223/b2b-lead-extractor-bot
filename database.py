import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def init_db():
    conn = sqlite3.connect("scraper.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            phone TEXT UNIQUE,
            website TEXT,
            address TEXT,
            rating REAL,
            reviews_count INTEGER,
            years_in_business INTEGER,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    
    logging.info("database 'scraper.db' and table 'leads' successfully created!")

if __name__ == "__main__":
    init_db()