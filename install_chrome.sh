#!/bin/bash

# Script para instalar Chrome e ChromeDriver no Render
# Baseado no buildpack do Chrome para Heroku

set -e

echo "🔧 Instalando Google Chrome e ChromeDriver..."

# Atualizar lista de pacotes
apt-get update

# Instalar dependências necessárias
apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    x11vnc \
    fluxbox \
    wmctrl \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    libnss3 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

# Adicionar chave GPG do Google
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adicionar repositório do Chrome
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Atualizar e instalar Chrome
apt-get update
apt-get install -y google-chrome-stable

# Verificar instalação do Chrome
google-chrome --version

# Instalar ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
echo "Chrome version: $CHROME_VERSION"

# Baixar ChromeDriver compatível
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%.*}")
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver

# Verificar instalação do ChromeDriver
chromedriver --version

echo "✅ Chrome e ChromeDriver instalados com sucesso!"
