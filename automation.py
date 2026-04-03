import os
import asyncio
import re
import logging
import time
from playwright.async_api import async_playwright
# database.py dan get_all_accounts funksiyasini chaqiramiz
try:
    from database import get_all_accounts
except ImportError:
    # Test qilish uchun agar database.py bo'lmasa
    async def get_all_accounts(): return []

logger = logging.getLogger(__name__)

LOGIN_URL = "https://login.emaktab.uz/"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")

async def login_and_screenshot(login: str, password: str) -> dict:
    """Bitta hisob uchun eMaktab.uz ga kiradi va screenshot saqlaydi."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        # Brauzerni ishga tushirish
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            # 1. Sahifaga o'tish
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            
            # 2. Login va Parolni kiritish (aniqroq selectorlar bilan)
            await page.wait_for_selector('input[name="login"]', timeout=20000)
            await page.fill('input[name="login"]', login)
            await page.fill('input[name="password"]', password)
            
            # 3. Tugmani bosish
            # eMaktabda odatda submit input yoki button bo'ladi
            await page.click('input[type="submit"], button[type="submit"]')

            # 4. Login jarayonini kutish (Sahifa o'zgarishini kutamiz)
            # "Chiqish" yoki "Profil" so'zi chiqishini kutish eng ishonchli usul
            try:
                await page.wait_for_selector('text="Chiqish"', timeout=20000)
            except:
                logger.warning(f"{login} uchun 'Chiqish' tugmasi ko'rinmadi, baribir screenshot olaman.")

            # Fayl nomini tayyorlash
            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", login)
            timestamp = int(time.time() * 1000)
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"emaktab_{safe_name}_{timestamp}.png")
            
            # Screenshot olish
            await page.screenshot(path=screenshot_path, full_page=False)
            return {"path": screenshot_path, "login": login}

        except Exception as e:
            logger.error(f"Xato yuz berdi ({login}): {str(e)}")
            return {"error": str(e), "login": login}
        finally:
            await browser.close()

async def run_all_screenshots() -> list[dict]:
    """Bazadagi barcha hisoblar uchun screenshot oladi."""
    # MUHIM: database.py dagi funksiyani kutamiz
    accounts = await get_all_accounts()
    results = []

    if not accounts:
        logger.warning("Bazada hisoblar topilmadi. Database ulanishini tekshiring!")
        return results

    for acc in accounts:
        # Supabase-dan kelayotgan JSON kalitlarini tekshiring
        u_login = acc.get("login", "").strip()
        u_pass = acc.get("password", "").strip()

        if not u_login or not u_pass:
            continue

        res = await login_and_screenshot(u_login, u_pass)
        results.append(res)
    
    return results

# Telegram xabarnoma qismi o'zgarishsiz qoladi...
