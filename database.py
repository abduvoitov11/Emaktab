import os
import motor.motor_asyncio
import logging

logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "emaktab_bot"
COLLECTION_NAME = "accounts"

client = None
db = None
collection = None

def get_db():
    global client, db, collection
    if client is None:
        if not MONGODB_URI:
            logger.error("MONGODB_URI not found in environment variables.")
            return None
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
    return collection

async def get_all_accounts():
    coll = get_db()
    if coll is None:
        return []
    try:
        cursor = coll.find({})
        return await cursor.to_list(length=100)
    except Exception as e:
        logger.error(f"Error fetching accounts from MongoDB: {e}")
        return []

async def add_account(login, password):
    coll = get_db()
    if coll is None:
        return
    await coll.update_one(
        {"login": login.strip()},
        {"$set": {"password": str(password)}},
        upsert=True
    )

async def remove_account(key):
    """
    Remove account by login (exact match).
    Returns dict with 'removed': bool, 'login': str, or 'error': str.
    """
    coll = get_db()
    if coll is None:
        return {'error': "Database connection error."}
    
    login_str = str(key).strip()
    result = await coll.delete_one({"login": login_str})
    
    if result.deleted_count > 0:
        return {'removed': True, 'login': login_str}
    else:
        return {'error': 'Bunday hisob topilmadi.'}
