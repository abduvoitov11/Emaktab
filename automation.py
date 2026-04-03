import os
import asyncio
import re
import logging
import time
from playwright.async_api import async_playwright
from database import get_all_accounts

logger = logging.getLogger(__name__)

LOGIN_URL = "https://login.emaktab.uz/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


async def login_and_screenshot(login: str, password: str) -> dict:
    """
    Bitta hisob uchun eMaktab.uz ga kiradi va screenshot saqlaydi.
    """
    browser = None
    try:
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()

            try:
                await page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
            except Exception as e:
                await browser.close()
                return {"error": f"Aloqa xatosi: {str(e)}", "login": login}

            # Input elementlarini topish
            login_input = page.get_by_label("Login").or_(
                page.locator('input[type="text"], input[name="login"]').first
            )
            password_input = page.get_by_label("Parol").or_(
                page.locator('input[type="password"]').first
            )
            submit_btn = (
                page.get_by_role("button", name="Tizimga kiring")
                .or_(page.locator('button:has-text("Tizimga kiring"), input[type="submit"]'))
                .first
            )

            await login_input.first.wait_for(state="visible", timeout=15000)
            await login_input.first.fill(login)
            await password_input.first.fill(password)
            await submit_btn.first.click(force=True)

            # Login jarayonini kutish
            await asyncio.sleep(5)
            
            # Muvaffaqiyatli kirishni tekshirish
            try:
                success_locator = page.get_by_text("Chiqish").or_(page.get_by_text("BUGUN"))
                await success_locator.first.wait_for(state="visible", timeout=15000)
            except:
                pass

            await page.wait_for_load_state("networkidle")

            # Fayl nomini tayyorlash
            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", login)
            timestamp = int(time.time() * 1000)
            screenshot_path = os.path.join(
                SCREENSHOTS_DIR, f"emaktab_{safe_name}_{timestamp}.png"
            )
            
            await page.screenshot(path=screenshot_path, full_page=False)
            await browser.close()
            return {"path": screenshot_path, "login": login}

    except Exception as err:
        if browser:
            await browser.close()
        return {"error": str(err), "login": login}


async def run_all_screenshots() -> list[dict]:
    """Bazadagi barcha hisoblar uchun screenshot oladi."""
    accounts = await get_all_accounts()
    results = []

    if not accounts:
        logger.warning("Bazada hisoblar topilmadi.")
        return results

    for acc in accounts:
        # Supabase dict kalitlari
        login = acc.get("login", "").strip()
        password = acc.get("password", "").strip()

        if not login or not password:
            continue

        res = await login_and_screenshot(login, password)
        results.append(res)

    return results


async def run_all_screenshots_and_notify(bot, chat_id: int) -> None:
    """Screenshots olib Telegram orqali yuboradi."""
    results = await run_all_screenshots()

    for r in results:
        if "path" in r:
            try:
                with open(r["path"], "rb") as photo:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=f"eMaktab: {r['login']}",
                    )
            except Exception as e:
                await bot.send_message(chat_id=chat_id, text=f"Yuborishda xato: {e}")
        else:
            # XATOLIK TUZATILGAN JOY: Noma'lum xato so'zidagi backslash olib tashlandi
            error_msg = r.get('error', 'Nomalum xato')
            await bot.send_message(
                chat_id=chat_id,
                text=f"Login xatosi ({r['login']}): {error_msg}",
            )

if __name__ == "__main__":
    asyncio.run(run_all_screenshots())
