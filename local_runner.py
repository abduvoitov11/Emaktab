import os
import sys
import html
import asyncio
import logging
import openpyxl
from playwright.async_api import async_playwright
from telegram import Bot
from telegram.request import HTTPXRequest
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

greeted_recipients = set()


def create_bot():
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    return Bot(token=config.BOT_TOKEN, request=request)


async def send_greetings_if_needed(bot: Bot, sinf: str):
    if config.SUPER_ADMIN_ID not in greeted_recipients:
        admin_greeting = (
            "⚡ <b>Assalomu alaykum, Bosh Administrator!</b> 👑✨\n\n"
            "🚀 Bugungi eMaktab monitoring jarayoni boshlandi.\n"
            "📊 <i>Barcha sinflar bo'yicha hisobotlar quyida qabul qilinmoqda...</i> ⬇️💎"
        )
        try:
            await bot.send_message(
                chat_id=config.SUPER_ADMIN_ID,
                text=admin_greeting,
                parse_mode=ParseMode.HTML
            )
            greeted_recipients.add(config.SUPER_ADMIN_ID)
        except Exception as e:
            logger.error(f"Bosh adminga salom yuborishda xato: {e}")

    teacher_info = config.TEACHERS.get(sinf)
    if teacher_info and "chat_id" in teacher_info:
        t_id = int(teacher_info["chat_id"])
        t_name = teacher_info.get("name", "Ustoz")
        if t_id not in greeted_recipients:
            teacher_greeting = (
                f"🌸 <b>Assalomu alaykum, {html.escape(t_name)} ustoz!</b> 👋✨\n\n"
                f"📋 <b>{html.escape(sinf)}</b> sinfingiz o'quvchilarining eMaktab kundalik ko'rik natijalari tayyorlandi.\n"
                f"📸 <i>Quyida skrinshotlar qabul qilinmoqda...</i> ⬇️💎"
            )
            try:
                await bot.send_message(
                    chat_id=t_id,
                    text=teacher_greeting,
                    parse_mode=ParseMode.HTML
                )
                greeted_recipients.add(t_id)
            except Exception as e:
                logger.error(f"{t_name} ustozga salom yuborishda xato: {e}")


async def run_local():
    bot = create_bot()
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

                await send_greetings_if_needed(bot, sinf)

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
