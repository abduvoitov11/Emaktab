import os

ROOT_ID = SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "6291811673"))
ROOT_NAME = "root"

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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8375587042:AAGfQNUc_3LzpTHBIPsyNHxw8AHfFV9CyXU")
LOGIN_URL = "https://login.emaktab.uz/"

DAILY_MAX_ACCOUNTS = 11
WEEKLY_MAX_PER_ACCOUNT = 4

PAGE_LOAD_WAIT_SECONDS = 7
MIN_HUMAN_PAUSE_SECONDS = 20
MAX_HUMAN_PAUSE_SECONDS = 45

MIN_STARTUP_JITTER_SECONDS = 60
MAX_STARTUP_JITTER_SECONDS = 300

CURFEW_START_HOUR = 21
CURFEW_START_MINUTE = 45
CURFEW_END_HOUR = 7
CURFEW_END_MINUTE = 0


def is_curfew_time(dt=None) -> bool:
    if dt is None:
        import zoneinfo
        from datetime import datetime
        tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
        dt = datetime.now(tashkent_tz)
    
    current_time = (dt.hour, dt.minute)
    curfew_start = (CURFEW_START_HOUR, CURFEW_START_MINUTE)
    curfew_end = (CURFEW_END_HOUR, CURFEW_END_MINUTE)
    
    return current_time >= curfew_start or current_time < curfew_end


def enforce_curfew_or_die(action_name="Login"):
    if is_curfew_time():
        import zoneinfo
        from datetime import datetime
        tz = zoneinfo.ZoneInfo("Asia/Tashkent")
        now_str = datetime.now(tz).strftime('%H:%M:%S')
        raise PermissionError(
            f"🛑 QAT'IY TUNGI TAQIQ (21:45 - 07:00) KUCHAYTIRILGAN! (Hozirgi vaqt: {now_str})\n"
            f"eMaktab.uz tizimi xavfsizligi va Anti-BAN qoidalariga ko'ra tungi soatlarda '{action_name}' qilish QAT'IYAN TAQIQLANADI!\n"
            f"Tizim faqat ertalab soat 07:00 dan boshlab ishlaydi."
        )


