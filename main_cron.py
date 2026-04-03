import os
import asyncio
import logging
import socket
from telegram import Bot
from dotenv import load_dotenv

# Import local modules
import automation
import database

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
ADMIN_ID = int(os.getenv("ADMIN_ID", "6291811673"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")

async def run_cron():
    """
    Main entry point for the one-shot cron job.
    """
    if not BOT_TOKEN:
        logger.error("Set TELEGRAM_BOT_TOKEN or BOT_TOKEN environment variable.")
        return

    bot = Bot(token=BOT_TOKEN)

    logger.info("Starting eMaktab cron job...")

    # DNS/Network retry logic for Errno -5 (Temporary failure in name resolution)
    max_retries = 5
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            socket.gethostbyname('api.telegram.org')
            break
        except socket.gaierror as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"DNS resolution failed (attempt {attempt+1}/{max_retries}): {e}. "
                    f"Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"DNS resolution failed after {max_retries} attempts. Exiting.")
                return

    try:
        results = await automation.run_all_screenshots()

        if not results:
            logger.info("No accounts processed.")
            await bot.send_message(chat_id=ADMIN_ID, text="Cron: No accounts found in database.")
            return

        for r in results:
            if 'path' in r:
                try:
                    with open(r['path'], 'rb') as photo:
                        await bot.send_photo(
                            chat_id=ADMIN_ID,
                            photo=photo,
                            caption=f"eMaktab: {r['login']}"
                        )
                    # os.remove(r['path'])  # Screenshot'ni o'chirish (ixtiyoriy)
                except Exception as e:
                    logger.error(f"Failed to send photo for {r['login']}: {e}")
                    await bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"Screenshot failed for {r['login']}: {e}"
                    )
            else:
                logger.error(f"Login failed for {r['login']}: {r.get('error')}")
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"Login failed for {r['login']}: {r.get('error', 'Unknown error')}"
                )

        logger.info("Cron job completed successfully.")

    except Exception as e:
        logger.error(f"Unexpected error in cron job: {e}")
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=f"Cron error: {str(e)}")
        except Exception:
            pass

async def main():
    try:
        await run_cron()
    finally:
        # Supabase async client ni yopish — event loop xatosining oldini oladi
        if database._client is not None:
            await database._client.aclose()
            logger.info("Supabase client yopildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Critical error: {e}")
