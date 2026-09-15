import sqlite3
import logging
from typing import Optional

import pandas as pd

from config import DB_PATH, EXPORT_FILE


def export_to_excel(limit: Optional[int] = None):
    logging.info("📊 Reading SQLite...")
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM leads"
    params: tuple = ()
    if limit:
        query += " LIMIT ?"
        params = (limit,)
    
    df = pd.read_sql_query(query, conn, params=params)
    df.rename(columns={
        "business_name": "Business Name",
        "phone": "Phone Number",
        "website": "Website",
        "address": "Address",
        "rating": "Rating",
        "reviews_count": "Reviews Count",
        "years_in_business": "Years in Business"
    }, inplace=True)
    
    if df.empty:
        logging.warning("⚠️ DB is empty! Nothing to export.")
        conn.close()
        return

    df.to_excel(EXPORT_FILE, index=False, engine='openpyxl')
    
    conn.close()
    logging.info(f"✅ Done! File '{EXPORT_FILE}' is created. Total exported records: {len(df)}")

if __name__ == "__main__":
    export_to_excel()