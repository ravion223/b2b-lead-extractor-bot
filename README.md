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

This project solves the bottleneck of manual B2B lead generation. It combines a robust headless-resistant web scraper built with Playwright with a seamless Telegram Bot UI (Aiogram FSM). The architecture follows a strict Separation of Concerns: the scraping engine blindly extracts raw data into SQLite, while the bot handles user states, freemium business logic, and Excel report generation.

## Core Features & Architecture

- **Headless-Resistant Scraping:** Utilizes a containerized `Xvfb` virtual display approach to run Playwright in `headless=False` mode, bypassing basic anti-bot systems (like Cloudflare) that block standard headless requests.
- **Separation of Concerns (ETL Pattern):** The scraper strictly handles data extraction and SQLite population, while the bot layer independently manages freemium limitations (e.g., exporting only 5 rows for free users) without altering the raw database.
- **Dynamic State Management:** Built with Aiogram's Finite State Machine (FSM) to handle concurrent user sessions, process dynamic URL inputs, and gracefully manage edge cases during long-polling scraping tasks.
- **Containerized Infrastructure:** Fully packaged using the official Microsoft Playwright Docker image, guaranteeing flawless OS-level dependency resolution and out-of-the-box execution on any cloud provider.

## 🛠 Tech Stack Details

- **Frontend/UI:** Telegram Bot API (Aiogram 3.x)
- **Web Scraping:** Playwright, BeautifulSoup4
- **Data Processing:** Pandas, OpenPyXL
- **Database:** SQLite (`aiosqlite`)
- **Infrastructure:** Docker, Xvfb (Virtual Framebuffer)

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
   ```
3. **Build the Docker Image:**
   ```bash
   docker build -t usa-lead-extractor .
   ```
4. **Run the Container:**
   ```bash
   docker run -it --rm --name brio-bot --env-file .env usa-lead-extractor
   ```
