import sqlite3
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def export_to_excel(limit=None):
    logging.info("📊 Reading SQLite...")
    conn = sqlite3.connect("scraper.db")

    query = "SELECT * FROM leads"
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn)
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
        logging.exception("⚠️ DB is empty! Nothing to export.")
        return

    file_name = "leads_report.xlsx"
    df.to_excel(file_name, index=False, engine='openpyxl')
    
    conn.close()
    logging.info(f"✅ Done! File '{file_name}' is created. Total exported records: {len(df)}")

if __name__ == "__main__":
    export_to_excel()