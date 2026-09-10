"""
eMaktab Smart Automation — Konfiguratsiya va Ierarxiya
"""
import os

# ==================== 1. IERARXIYA VA FOYDALANUVCHILAR ====================

# Eng katta va asosiy tizim administratori (Barcha sinflar keladi)
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "6291811673"))

# Sinf rahbarlari (Ustozlar): Har bir ustozga faqat o'z sinfining hisobotlari boradi
TEACHERS = {
    "9-B": {
        "name": "Zuhra",
        "chat_id": 896459615
    },
    # Kelajakda qo'shiladigan yangi sinf uchun tayyorlangan o'rin:
    "9-A": {
        "name": "Muhayyo",
        "chat_id": 624782674
    }
}

# ==================== 2. TELEGRAM VA EMAKTAB SOZLAMALARI ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8375587042:AAGfQNUc_3LzpTHBIPsyNHxw8AHfFV9CyXU")
LOGIN_URL = "https://login.emaktab.uz/"

# ==================== 3. QAT'IY CHEKLOVLAR VA ME'YORLAR ====================
# Bir kunda kirishlar soni 11 tadan oshishi qat'iyan taqiqlanadi
DAILY_MAX_ACCOUNTS = 11

# Bitta hisobga bir haftada kirishlar soni bo'yicha maksimal limit
WEEKLY_MAX_PER_ACCOUNT = 4

# ==================== 4. ANTI-BAN VA VAQT SOZLAMALARI ====================
PAGE_LOAD_WAIT_SECONDS = 7    # Ma'lumotlar to'liq ko'rinishi uchun kutish
MIN_HUMAN_PAUSE_SECONDS = 20  # Hisoblar orasidagi minimal insoniy pauza
MAX_HUMAN_PAUSE_SECONDS = 45  # Hisoblar orasidagi maksimal insoniy pauza

# Boshlanishdagi tasodifiy kechikish (jitter) — sekundlarda
MIN_STARTUP_JITTER_SECONDS = 60   # 1 daqiqa
MAX_STARTUP_JITTER_SECONDS = 300  # 5 daqiqa
