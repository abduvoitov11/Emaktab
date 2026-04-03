import os
import logging
from supabase import acreate_client, AsyncClient

# Loglarni sozlash
logger = logging.getLogger(__name__)

# Muhit o'zgaruvchilari (Environment Variables)
# MUHIM: Railway yoki GitHub Secrets-da ushbu nomlar aniq bo'lishi shart
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TABLE_NAME = "accounts"

_client: AsyncClient | None = None

async def get_db() -> AsyncClient | None:
    """Supabase async client singleton."""
    global _client
    if _client is not None:
        return _client

    # URL va KEY borligini tekshirish
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL yoki SUPABASE_KEY topilmadi! Muhit o'zgaruvchilarini tekshiring.")
        return None

    try:
        # Client yaratishda xatolik yuz bersa tutib qolamiz
        _client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase'ga muvaffaqiyatli ulandi.")
        return _client
    except Exception as e:
        logger.error(f"Supabase klientini yaratishda xato: {e}")
        return None

async def get_all_accounts() -> list[dict]:
    """Bazadagi barcha o'quvchilarni qaytaradi."""
    client = await get_db()
    if client is None:
        return []
    try:
        # execute() natijasini tekshirish
        result = await client.table(TABLE_NAME).select("*").execute()
        
        # Supabase-py yangi versiyalarida ma'lumot .data ichida bo'ladi
        if hasattr(result, 'data'):
            return result.data or []
        return []
    except Exception as e:
        logger.error(f"Ma'lumot olishda xato: {e}")
        return []

async def add_account(login: str, password: str, chat_id: int = 6291811673) -> bool:
    """Yangi o'quvchi qo'shadi yoki mavjudini yangilaydi."""
    client = await get_db()
    if client is None:
        return False
    try:
        await client.table(TABLE_NAME).upsert(
            {
                "login": login.strip(),
                "password": str(password),
                "chat_id": chat_id,
            },
            on_conflict="login"
        ).execute()
        logger.info(f"Muvaffaqiyatli saqlandi: {login}")
        return True
    except Exception as e:
        logger.error(f"Upsert xatosi: {e}")
        return False
