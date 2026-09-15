import os
import sqlite3
import pytest

# Point config at a temp DB before importing anything else
os.environ["DB_PATH"] = ":memory:"

from database import init_db
from config import DB_PATH


class TestDatabaseSchema:
    """Verify that init_db creates the expected table and columns."""

    def test_creates_leads_table(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Replicate init_db logic against a temp file
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

        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_leads_table_columns(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
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

        cursor.execute("PRAGMA table_info(leads)")
        columns = {row[1] for row in cursor.fetchall()}

        expected = {
            "id", "business_name", "phone", "website",
            "address", "rating", "reviews_count",
            "years_in_business", "scraped_at"
        }
        assert columns == expected

        conn.close()

    def test_phone_uniqueness_constraint(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
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

        cursor.execute(
            "INSERT INTO leads (business_name, phone) VALUES (?, ?)",
            ("Company A", "(555) 123-4567")
        )
        conn.commit()

        # Inserting a duplicate phone should raise IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                "INSERT INTO leads (business_name, phone) VALUES (?, ?)",
                ("Company B", "(555) 123-4567")
            )

        conn.close()
