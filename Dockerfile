# Microsoft's official Playwright image (pre-configured with Chromium, Firefox, WebKit, and Xvfb)
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Prevent Python from writing pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Run the Telegram bot inside the Xvfb virtual display
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 -ac & export DISPLAY=:99 && python -u bot.py"]