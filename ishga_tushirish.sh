#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "Kutubxonalar o'rnatilmoqda (bu faqat birinchi marta bo'ladi)..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    ./venv/bin/playwright install chromium
fi

echo "Dastur ishga tushirilmoqda..."
./venv/bin/python local_runner.py
