import sqlite3
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def export_to_excel():
    logging.info("📊 Reading SQLite...")
    conn = sqlite3.connect("scraper.db")

    query = """
        SELECT 
            business_name AS 'Company Name',
            phone AS 'Phone Number',
            website AS 'Website',
            address AS 'Location',
            rating AS 'Rating',
            reviews_count AS 'Reviews',
            years_in_business AS 'Years in Business',
            scraped_at AS 'Date Added'
        FROM leads
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        logging.exception("⚠️ DB is empty! Nothing to export.")
        return

    file_name = "leads_report.xlsx"
    df.to_excel(file_name, index=False, engine='openpyxl')
    
    conn.close()
    logging.info(f"✅ Done! File '{file_name}' is created. Total exported records: {len(df)}")

if __name__ == "__main__":
    export_to_excel()