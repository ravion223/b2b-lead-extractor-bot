# B2B Lead Extractor Pipeline

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](#)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.4+-2CA5E0.svg)](https://aiogram.dev/)
[![Playwright](https://custom-icon-badges.demolab.com/badge/Playwright-2EAD33?logo=playwright&logoColor=fff)](#)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff)](#)

> A production-ready asynchronous Telegram bot and Data Engineering pipeline that dynamically extracts, structures, and exports B2B leads from major US business directories.

<div align="center">
  <img width="100%" alt="Image" src="https://github.com/user-attachments/assets/bb4cdf1c-d2eb-4d19-b9dd-7462f83c2da2" />
</div>

## Overview

This project solves the bottleneck of manual B2B lead generation. It combines a robust web scraper built with Playwright and ScraperAPI with a seamless Telegram Bot UI (Aiogram FSM). The scraper supports **multi-page pagination** (user-configurable, 1–10 pages) with automatic retry logic for proxy resilience. The architecture follows a strict Separation of Concerns: the scraping engine extracts raw data into SQLite, while the bot handles user states, freemium business logic, and Excel report generation.

## Core Features & Architecture

- **ScraperAPI Proxy Integration:** Routes all requests through ScraperAPI's rotating proxy infrastructure, bypassing Cloudflare and other anti-bot systems. Runs in headless mode for optimal performance.
- **Multi-Page Pagination:** Users specify how many pages to scrape (1–10) via the Telegram bot. Each page is scraped sequentially with human-like delays between requests.
- **Automatic Retry Mechanism:** Each page navigation retries up to 3 times with exponential backoff (5s, 10s), handling transient proxy failures gracefully. Real-time progress updates are sent to the user in Telegram.
- **Separation of Concerns (ETL Pattern):** The scraper strictly handles data extraction and SQLite population, while the bot layer independently manages freemium limitations (e.g., exporting only 5 rows for free users) without altering the raw database.
- **Dynamic State Management:** Built with Aiogram's Finite State Machine (FSM) to handle concurrent user sessions, process URL and page count inputs across multiple steps, and gracefully manage edge cases during long-running scraping tasks.
- **Containerized Infrastructure:** Fully packaged using the official Microsoft Playwright Docker image, guaranteeing flawless OS-level dependency resolution and out-of-the-box execution on any cloud provider.

## 🛠 Tech Stack Details

- **Frontend/UI:** Telegram Bot API (Aiogram 3.x)
- **Web Scraping:** Playwright (headless), ScraperAPI (proxy), BeautifulSoup4
- **Data Processing:** Pandas, OpenPyXL
- **Database:** SQLite (`aiosqlite`)
- **Infrastructure:** Docker

## ⚙️ Local Setup (Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/b2b-lead-extractor.git
   cd b2b-lead-extractor
   ```
2. **Set up Environment Variables:**
   Create a .env file in the root directory (ensure it uses LF line endings, not CRLF) and add your Telegram Bot Token:
   ```bash
   BOT_TOKEN=your_telegram_bot_token_here
   SCRAPER_API_KEY=your_scraper_api_key_here
   ```
3. **Build and Run the Pipeline:**
   ```bash
   docker compose up --build
   ```
