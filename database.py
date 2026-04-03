import os
import logging
from supabase import acreate_client, AsyncClient

# Loglarni sozlash
logger = logging.getLogger(__name__)

# GitHub Secrets'dan Supabase ma'lumotlarini olish
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

TABLE_NAME = "accounts"

# Async Supabase client (lazily initialized)
_client: AsyncClient | None = None


async def get_db() -> AsyncClient | None:
    """Supabase async client singleton."""
    global _client
    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error(
            "SUPABASE_URL yoki SUPABASE_KEY topilmadi. "
            "GitHub Secrets'ni tekshiring."
        )
        return None

    try:
        _client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase'ga muvaffaqiyatli ulandi.")
        return _client
    except Exception as e:
        logger.error(f"Supabase'ga ulanishda xato: {e}")
        return None


async def get_all_accounts() -> list[dict]:
    """Bazadagi barcha o'quvchilarni qaytaradi."""
    client = await get_db()
    if client is None:
        return []
    try:
        response = await client.table(TABLE_NAME).select("*").execute()
        # response.data — list of dicts with keys: id, login, password, chat_id
        return response.data or []
    except Exception as e:
        logger.error(f"Supabase'dan ma'lumot olishda xato: {e}")
        return []


async def add_account(login: str, password: str, chat_id: int = 6291811673) -> None:
    """
    Yangi o'quvchi qo'shadi yoki mavjud loginni yangilaydi (upsert).
    Supabase upsert uchun PRIMARY KEY yoki UNIQUE constraint kerak
    (accounts jadvalidagi 'login' ustunida UNIQUE bo'lishi shart).
    """
    client = await get_db()
    if client is None:
        return
    try:
        await (
            client.table(TABLE_NAME)
            .upsert(
                {
                    "login": login.strip(),
                    "password": str(password),
                    "chat_id": chat_id,
                },
                on_conflict="login",   # UNIQUE ustun nomi
            )
            .execute()
        )
        logger.info(f"Hisob qo'shildi/yangilandi: {login.strip()}")
    except Exception as e:
        logger.error(f"Ma'lumot qo'shishda xato: {e}")


async def remove_account(key: str) -> dict:
    """Login bo'yicha o'quvchini o'chiradi."""
    client = await get_db()
    if client is None:
        return {"error": "Bazaga ulanish xatosi."}

    login_str = str(key).strip()
    try:
        response = (
            await client.table(TABLE_NAME)
            .delete()
            .eq("login", login_str)
            .execute()
        )
        # response.data — o'chirilgan qatorlar ro'yxati
        if response.data:
            return {"removed": True, "login": login_str}
        else:
            return {"error": "Bunday login topilmadi."}
    except Exception as e:
        return {"error": f"O'chirishda xato yuz berdi: {e}"}
