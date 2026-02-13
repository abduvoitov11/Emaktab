import os
import motor.motor_asyncio
import logging

# Loglarni sozlash
logger = logging.getLogger(__name__)

# GitHub Secrets'dan MONGODB_URI ni olish
MONGODB_URI = os.getenv("MONGODB_URI")

# DIQQAT: MongoDB Atlas'da siz yaratgan baza va kolleksiya nomlari
DB_NAME = "emaktab_db" 
COLLECTION_NAME = "accounts"

client = None
db = None
collection = None

def get_db():
    global client, db, collection
    if client is None:
        if not MONGODB_URI:
            logger.error("MONGODB_URI atrof-muhit o'zgaruvchilarida topilmadi (Secrets'ni tekshiring).")
            return None
        try:
            # MongoDB'ga ulanish
            client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            logger.info(f"MongoDB'ga muvaffaqiyatli ulandi: {DB_NAME}")
        except Exception as e:
            logger.error(f"MongoDB'ga ulanishda xato: {e}")
            return None
    return collection

async def get_all_accounts():
    """Bazada mavjud barcha o'quvchilarni olish"""
    coll = get_db()
    if coll is None:
        return []
    try:
        # Bazadagi hamma ma'lumotni massiv sifatida qaytaradi
        cursor = coll.find({})
        return await cursor.to_list(length=200) # Ro'yxat kattaligini hisobga olib 200 gacha ruxsat berdik
    except Exception as e:
        logger.error(f"MongoDB'dan ma'lumot olishda xato: {e}")
        return []

async def add_account(login, password, chat_id=6291811673):
    """Yangi o'quvchi qo'shish yoki parolini yangilash"""
    coll = get_db()
    if coll is None:
        return
    try:
        await coll.update_one(
            {"login": login.strip()},
            {"$set": {
                "password": str(password),
                "chat_id": chat_id
            }},
            upsert=True # Agar login bo'lmasa, yangi qo'shadi
        )
    except Exception as e:
        logger.error(f"Ma'lumot qo'shishda xato: {e}")

async def remove_account(key):
    """Login bo'yicha o'quvchini o'chirish"""
    coll = get_db()
    if coll is None:
        return {'error': "Bazaga ulanish xatosi."}
    
    login_str = str(key).strip()
    try:
        result = await coll.delete_one({"login": login_str})
        if result.deleted_count > 0:
            return {'removed': True, 'login': login_str}
        else:
            return {'error': 'Bunday login topilmadi.'}
    except Exception as e:
        return {'error': f"O'chirishda xato yuz berdi: {e}"}
