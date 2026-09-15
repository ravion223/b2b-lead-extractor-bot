import os
import re

os.environ["DB_PATH"] = ":memory:"

from bs4 import BeautifulSoup


# --- HTML fixture: simulates a result card ---
SAMPLE_CARD_HTML = """
<div class="result">
    <a class="business-name" href="/profile/abc">Joe's Plumbing</a>
    <div class="phones">(214) 555-1234</div>
    <div class="links">
        <a class="track-visit-website" href="https://joesplumbing.com">Website</a>
    </div>
    <div class="locality">Dallas, TX 75201</div>
    <div class="badges">
        <div class="years-in-business">
            <div class="count">15</div>
        </div>
    </div>
    <div class="ratings">
        <div class="result-rating four half"></div>
        <span class="count">(87)</span>
    </div>
</div>
"""

SAMPLE_CARD_MINIMAL_HTML = """
<div class="result">
    <a class="business-name" href="/profile/xyz">Bare Minimum LLC</a>
    <div class="phones">(972) 555-0000</div>
</div>
"""

RATING_MAP = {
    "five": 5.0,
    "four half": 4.5,
    "four": 4.0,
    "three half": 3.5,
    "three": 3.0,
    "two half": 2.5,
    "two": 2.0,
    "one half": 1.5,
    "one": 1.0,
}


def parse_card(card):
    """
    Extract lead data from a single BeautifulSoup card element.
    This mirrors the parsing logic in scraper.py without requiring Playwright.
    """
    name_tag = card.find("a", class_="business-name")
    name = name_tag.text.strip() if name_tag else "No name"

    phone_tag = card.find("div", class_="phones")
    phone = phone_tag.text.strip() if phone_tag else "No phone number"

    website = None
    links_tag = card.find("div", class_="links")
    if links_tag:
        website_tag = card.find("a", class_="track-visit-website")
        if website_tag:
            website = website_tag["href"]

    locality_tag = card.find("div", class_="locality")
    address = locality_tag.text.strip() if locality_tag else None

    years_in_business = None
    badges_tag = card.find("div", class_="badges")
    if badges_tag:
        years_in_business_tag = card.find("div", class_="years-in-business")
        if years_in_business_tag:
            count_tag = card.find("div", class_="count")
            if count_tag and count_tag.text.strip(" Years").isdigit():
                years_in_business = int(count_tag.text.strip(" Years"))

    rating = None
    reviews_count = None
    rating_tag = card.find("div", class_="ratings")
    if rating_tag:
        result_rating_tag = rating_tag.find(class_=re.compile(r"result-rating"))
        if result_rating_tag:
            class_string = " ".join(result_rating_tag.get("class", [])).lower()
            for key, val in RATING_MAP.items():
                if key in class_string:
                    rating = val
                    break

        count_span = rating_tag.find("span", class_="count")
        if count_span:
            count_text = count_span.text.strip("() ")
            reviews_count = int(count_text) if count_text.isdigit() else None

    return {
        "name": name,
        "phone": phone,
        "website": website,
        "address": address,
        "years_in_business": years_in_business,
        "rating": rating,
        "reviews_count": reviews_count,
    }


class TestScraperParsing:
    """Test the HTML parsing logic in isolation (no Playwright, no network)."""

    def test_full_card_parsing(self):
        soup = BeautifulSoup(SAMPLE_CARD_HTML, "html.parser")
        card = soup.find("div", class_="result")
        result = parse_card(card)

        assert result["name"] == "Joe's Plumbing"
        assert result["phone"] == "(214) 555-1234"
        assert result["website"] == "https://joesplumbing.com"
        assert result["address"] == "Dallas, TX 75201"
        assert result["years_in_business"] == 15
        assert result["rating"] == 4.5
        assert result["reviews_count"] == 87

    def test_minimal_card_parsing(self):
        soup = BeautifulSoup(SAMPLE_CARD_MINIMAL_HTML, "html.parser")
        card = soup.find("div", class_="result")
        result = parse_card(card)

        assert result["name"] == "Bare Minimum LLC"
        assert result["phone"] == "(972) 555-0000"
        assert result["website"] is None
        assert result["address"] is None
        assert result["years_in_business"] is None
        assert result["rating"] is None
        assert result["reviews_count"] is None

    def test_no_cards_found(self):
        soup = BeautifulSoup("<div class='empty-page'></div>", "html.parser")
        cards = soup.find_all("div", class_="result")
        assert len(cards) == 0

    def test_rating_map_coverage(self):
        """Ensure all rating classes are correctly mapped."""
        for rating_class, expected_value in RATING_MAP.items():
            html = f"""
            <div class="result">
                <a class="business-name">Test Co</a>
                <div class="phones">(000) 000-0000</div>
                <div class="ratings">
                    <div class="result-rating {rating_class}"></div>
                    <span class="count">(10)</span>
                </div>
            </div>
            """
            soup = BeautifulSoup(html, "html.parser")
            card = soup.find("div", class_="result")
            result = parse_card(card)
            assert result["rating"] == expected_value, f"Failed for class '{rating_class}'"
