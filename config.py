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
    "3-D": {
        "name": "Muhayyo",
        "chat_id": 624782674
    },
    "3D": {
        "name": "Muhayyo",
        "chat_id": 624782674
    }
}

# ==================== 2. TELEGRAM VA EMAKTAB SOZLAMALARI ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8375587042:AAGfQNUc_3LzpTHBIPsyNHxw8AHfFV9CyXU")
LOGIN_URL = "https://login.emaktab.uz/"

# ==================== 3. QAT'IY CHEKLOVLAR VA ME'YORLAR ====================
DAILY_MAX_ACCOUNTS = 11      # 1 kunda 11 tadan oshiq hisobga kirish qat'iyan taqiqlanadi
WEEKLY_MAX_PER_ACCOUNT = 4  # 1 hisobga 1 haftada maksimal 4 martagacha kirish mumkin

# ==================== 4. ANTI-BAN VA VAQT SOZLAMALARI ====================
PAGE_LOAD_WAIT_SECONDS = 7    # Ma'lumotlar to'liq ko'rinishi uchun kutish
MIN_HUMAN_PAUSE_SECONDS = 20  # Hisoblar orasidagi minimal insoniy pauza
MAX_HUMAN_PAUSE_SECONDS = 45  # Hisoblar orasidagi maksimal insoniy pauza

# Boshlanishdagi tasodifiy kechikish (jitter) — sekundlarda
MIN_STARTUP_JITTER_SECONDS = 60   # 1 daqiqa
MAX_STARTUP_JITTER_SECONDS = 300  # 5 daqiqa

# ==================== 5. TUNGI REJIM VA XAVFSIZLIK (23:00 - 06:00) ====================
# eMaktab.uz tizimida o'quvchilar va o'qituvchilar tungi soatlarda faol bo'lmaydi.
# Tizim xavfsizligi, anti-ban va insoniy xatti-harakat qoidalariga ko'ra
# soat 23:00 dan 06:00 gacha har qanday login urinishi QAT'IYAN TAQIQLANADI!
CURFEW_START_HOUR = 23  # 23:00
CURFEW_END_HOUR = 6     # 06:00


def is_curfew_time(dt=None) -> bool:
    """
    Toshkent vaqti bo'yicha tungi taqiq (23:00 - 06:00) faol ekanligini tekshiradi.
    23:00:00 dan 05:59:59 oralig'ida True, boshqa payt False qaytaradi.
    """
    if dt is None:
        import zoneinfo
        from datetime import datetime
        tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
        dt = datetime.now(tashkent_tz)
    return dt.hour >= CURFEW_START_HOUR or dt.hour < CURFEW_END_HOUR

