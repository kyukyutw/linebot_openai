'''
#!/bin/bash

# 安裝必要的包
apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# 下載和安裝Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable
rm -rf /var/lib/apt/lists/*

# 下載和安裝ChromeDriver
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm chromedriver_linux64.zip
mv chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver

# 設置環境變量
export DISPLAY=:99
'''
# 使用適當的基礎映像
FROM python:3.9-slim

# 安裝必要的包
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# 下載和安裝Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 下載和安裝ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` \
    && wget -N https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver

# 設置環境變量
ENV DISPLAY=:99

# 將你的應用代碼拷貝到容器中
COPY . /app

# 安裝Python依賴
RUN pip install -r /app/requirements.txt

# 設置工作目錄
WORKDIR /app

# 運行應用
CMD ["python", "app.py"]