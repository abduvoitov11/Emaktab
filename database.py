import os
import logging
from typing import List, Dict, Optional
from supabase import acreate_client, AsyncClient

# Loglarni sozlash - muammolarni aniqlash uchun muhim
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "accounts"

_client: Optional[AsyncClient] = None

async def get_db() -> Optional[AsyncClient]:
    """
    Supabase async klientini yaratadi va qaytaradi (Singleton).
    """
    global _client
    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("XATO: SUPABASE_URL yoki SUPABASE_KEY topilmadi. Muhit o'zgaruvchilarini tekshiring!")
        return None

    try:
        # URL va Key bilan ulanish
        _client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase bazasiga ulanish muvaffaqiyatli o'rnatildi.")
        return _client
    except Exception as e:
        logger.error(f"Supabase klientini yaratishda texnik xato: {e}")
        return None

async def get_all_accounts() -> List[Dict]:
    """
    Bazadagi barcha foydalanuvchilar ro'yxatini qaytaradi.
    """
    client = await get_db()
    if client is None:
        return []

    try:
        # Barcha qatorlarni tanlab olamiz
        response = await client.table(TABLE_NAME).select("*").execute()
        
        # Supabase-py kutubxonasida ma'lumotlar .data ichida bo'ladi
        accounts = getattr(response, "data", [])
        
        if not accounts:
            logger.warning(f"'{TABLE_NAME}' jadvali bo'sh yoki ma'lumot topilmadi.")
        else:
            logger.info(f"Bazadan {len(accounts)} ta hisob muvaffaqiyatli yuklandi.")
            
        return accounts
    except Exception as e:
        logger.error(f"Ma'lumotlarni olishda xatolik: {e}")
        return []

async def add_account(login: str, password: str, chat_id: int = 6291811673) -> bool:
    """
    Yangi foydalanuvchi qo'shadi yoki mavjudini yangilaydi (Upsert).
    """
    client = await get_db()
    if client is None:
        return False

    try:
        await client.table(TABLE_NAME).upsert(
            {
                "login": login.strip(),
                "password": str(password).strip(),
                "chat_id": chat_id,
            },
            on_conflict="login"  # 'login' ustuni UNIQUE bo'lishi kerak
        ).execute()
        logger.info(f"Hisob saqlandi/yangilandi: {login}")
        return True
    except Exception as e:
        logger.error(f"Upsert jarayonida xato: {e}")
        return False

async def remove_account(login: str) -> bool:
    """
    Login bo'yicha foydalanuvchini o'chiradi.
    """
    client = await get_db()
    if client is None:
        return False

    try:
        response = await client.table(TABLE_NAME).delete().eq("login", login.strip()).execute()
        if response.data:
            logger.info(f"Hisob o'chirildi: {login}")
            return True
        return False
    except Exception as e:
        logger.error(f"O'chirishda xato: {e}")
        return False
