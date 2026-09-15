import os
import sqlite3
import pytest

os.environ["DB_PATH"] = ":memory:"

from config import EXPORT_FILE


@pytest.fixture
def populated_db(tmp_path):
    """Create a temporary SQLite DB with sample leads data."""
    db_path = str(tmp_path / "test_export.db")
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

    sample_leads = [
        ("Alpha Plumbing", "(214) 555-0001", "https://alpha.com", "Dallas, TX", 4.5, 120, 15),
        ("Beta Electric", "(214) 555-0002", "https://beta.com", "Dallas, TX", 3.0, 45, 8),
        ("Gamma HVAC", "(214) 555-0003", None, "Plano, TX", 5.0, 200, 22),
        ("Delta Roofing", "(214) 555-0004", "https://delta.com", "Frisco, TX", None, None, 3),
        ("Epsilon Painting", "(214) 555-0005", None, "Arlington, TX", 4.0, 80, 10),
        ("Zeta Landscaping", "(214) 555-0006", "https://zeta.com", "Irving, TX", 2.5, 15, 1),
        ("Eta Construction", "(214) 555-0007", "https://eta.com", "McKinney, TX", 4.5, 95, 12),
    ]

    cursor.executemany(
        "INSERT INTO leads (business_name, phone, website, address, rating, reviews_count, years_in_business) VALUES (?, ?, ?, ?, ?, ?, ?)",
        sample_leads
    )
    conn.commit()
    conn.close()

    return db_path


class TestExportToExcel:
    """Verify Excel export logic produces valid output files."""

    def test_export_creates_file(self, populated_db, tmp_path, monkeypatch):
        """Full export should create an xlsx file with all rows."""
        output_file = str(tmp_path / "test_output.xlsx")

        monkeypatch.setattr("export.DB_PATH", populated_db)
        monkeypatch.setattr("export.EXPORT_FILE", output_file)

        from export import export_to_excel
        export_to_excel(limit=None)

        assert os.path.exists(output_file)

    def test_export_respects_limit(self, populated_db, tmp_path, monkeypatch):
        """Limited export should contain only the requested number of rows."""
        import pandas as pd

        output_file = str(tmp_path / "test_limited.xlsx")

        monkeypatch.setattr("export.DB_PATH", populated_db)
        monkeypatch.setattr("export.EXPORT_FILE", output_file)

        from export import export_to_excel
        export_to_excel(limit=3)

        df = pd.read_excel(output_file)
        assert len(df) == 3

    def test_export_column_names(self, populated_db, tmp_path, monkeypatch):
        """Exported file should have human-readable column names."""
        import pandas as pd

        output_file = str(tmp_path / "test_columns.xlsx")

        monkeypatch.setattr("export.DB_PATH", populated_db)
        monkeypatch.setattr("export.EXPORT_FILE", output_file)

        from export import export_to_excel
        export_to_excel(limit=None)

        df = pd.read_excel(output_file)
        expected_columns = {
            "Business Name", "Phone Number", "Website",
            "Address", "Rating", "Reviews Count", "Years in Business"
        }
        assert set(df.columns) >= expected_columns

    def test_export_empty_db_does_not_crash(self, tmp_path, monkeypatch):
        """Exporting from an empty DB should return gracefully, not crash."""
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.execute("""
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

        output_file = str(tmp_path / "empty_output.xlsx")
        monkeypatch.setattr("export.DB_PATH", db_path)
        monkeypatch.setattr("export.EXPORT_FILE", output_file)

        from export import export_to_excel
        export_to_excel(limit=None)

        # File should NOT be created for empty DB
        assert not os.path.exists(output_file)
