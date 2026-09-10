import os
import sys
import html
import asyncio
import logging
import openpyxl
from playwright.async_api import async_playwright
from telegram import Bot
from telegram.constants import ParseMode

import config

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXCEL = os.path.join(BASE_DIR, "Foydalanuvchilar_Royxati.xlsx")
if not os.path.exists(DEFAULT_EXCEL):
    DEFAULT_EXCEL = "/home/torabek/Downloads/Foydalanuvchilar_Royxati.xlsx"
EXCEL_FILE = os.getenv("EXCEL_FILE", DEFAULT_EXCEL)
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")


async def run_local():
    bot = Bot(token=config.BOT_TOKEN)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print(f"Excel fayldan ma'lumotlar o'qilmoqda: {EXCEL_FILE}...")
    wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    accounts = []
    for r in range(2, ws.max_row + 1):
        login = ws.cell(row=r, column=2).value
        password = ws.cell(row=r, column=3).value
        chat_id = ws.cell(row=r, column=4).value
        sinf = ws.cell(row=r, column=5).value or "9-B"

        if login and password:
            accounts.append({
                "login": str(login).strip(),
                "password": str(password).strip(),
                "chat_id": int(chat_id) if chat_id else config.SUPER_ADMIN_ID,
                "sinf": str(sinf).strip().upper()
            })

    print(f"Jami {len(accounts)} ta hisob topildi. Dastur ishga tushmoqda...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        for acc in accounts:
            login = acc["login"]
            password = acc["password"]
            sinf = acc["sinf"]
            print(f"[*] Kirish: {login} (Sinf: {sinf})...")

            try:
                await page.goto(config.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector('input[name="login"]', timeout=15000)
                await page.fill('input[name="login"]', login)
                await page.fill('input[name="password"]', password)
                await page.click('button[type="submit"], input[type="submit"]')

                try:
                    await page.wait_for_selector('text="Chiqish"', timeout=10000)
                except Exception:
                    pass

                print(f"[~] {login} uchun {config.PAGE_LOAD_WAIT_SECONDS}s kutilmoqda...")
                await page.wait_for_timeout(config.PAGE_LOAD_WAIT_SECONDS * 1000)

                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{login}.png")
                await page.screenshot(path=screenshot_path, full_page=False)

                caption = (
                    f"🏫 Sinf: <b>{html.escape(sinf)}</b>\n"
                    f"👤 Login: <tg-spoiler>{html.escape(login)}</tg-spoiler>\n"
                    f"🔑 Parol: <tg-spoiler>{html.escape(password)}</tg-spoiler>\n"
                    f"✅ Holat: Muvaffaqiyatli kirildi"
                )

                # Qabul qiluvchilar: Super Admin + Sinf rahbari
                recipients = {config.SUPER_ADMIN_ID}
                teacher_info = config.TEACHERS.get(sinf)
                if teacher_info and "chat_id" in teacher_info:
                    recipients.add(int(teacher_info["chat_id"]))

                for cid in recipients:
                    try:
                        with open(screenshot_path, "rb") as photo:
                            await bot.send_photo(
                                chat_id=cid,
                                photo=photo,
                                caption=caption,
                                parse_mode=ParseMode.HTML
                            )
                    except Exception as e:
                        print(f"[-] Telegramga yuborishda xatolik ({cid}): {e}")

                await page.context.clear_cookies()
            except Exception as e:
                print(f"[-] {login} xatosi: {e}")

        await browser.close()
    print("Barcha vazifalar yakunlandi!")


if __name__ == "__main__":
    asyncio.run(run_local())
