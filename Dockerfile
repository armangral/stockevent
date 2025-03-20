FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ENV PYTHONUNBUFFERED=1

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libgbm1 \
    libxrender1 \
    libxshmfence1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > /tmp/chrome.deb \
    && apt install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb

# Install ChromeDriver (ensure it matches Chrome's version)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1) && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}.0.5735.90/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

EXPOSE 8000
