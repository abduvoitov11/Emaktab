#!/bin/bash
cd /home/torabek/Desktop/Emaktab_Local

if [ ! -d "venv" ]; then
    echo "Kutubxonalar o'rnatilmoqda (bu faqat birinchi marta bo'ladi)..."
    python3 -m venv venv
    ./venv/bin/pip install openpyxl playwright python-telegram-bot
    ./venv/bin/playwright install chromium
fi

echo "Dastur ishga tushirilmoqda..."
./venv/bin/python local_runner.py
