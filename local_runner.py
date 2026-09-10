import os
import sys
import html
import asyncio
import random
import logging
import subprocess
import openpyxl
from playwright.async_api import async_playwright
from telegram import Bot, InputMediaPhoto, InputMediaVideo
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
MEDIA_DIR = os.path.join(BASE_DIR, "media")

greeted_recipients = set()


def create_bot():
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0
    )
    return Bot(token=config.BOT_TOKEN, request=request)


async def send_greetings_if_needed(bot: Bot, sinf: str):
    if config.SUPER_ADMIN_ID not in greeted_recipients:
        admin_greeting = (
            "⚡ <b>Assalomu alaykum, Bosh Administrator!</b> 👑✨\n\n"
            "🚀 Bugungi eMaktab monitoring jarayoni boshlandi.\n"
            "📊 <i>Barcha sinflar bo'yicha rasm va videolar quyida qabul qilinmoqda...</i> ⬇️💎"
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
                f"📸 <i>Quyida rasm va videolar qabul qilinmoqda...</i> ⬇️💎"
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


async def send_media(bot: Bot, photo_path: str, video_path: str, caption: str, sinf: str):
    await send_greetings_if_needed(bot, sinf)

    recipients = {config.SUPER_ADMIN_ID}
    teacher_info = config.TEACHERS.get(sinf)
    if teacher_info and "chat_id" in teacher_info:
        recipients.add(int(teacher_info["chat_id"]))

    try:
        with open(photo_path, "rb") as pf:
            photo_bytes = pf.read()
        with open(video_path, "rb") as vf:
            video_bytes = vf.read()
    except Exception as e:
        logger.error(f"Media fayllarni o'qishda xato: {e}")
        return

    for chat_id in recipients:
        sent_group = False
        for attempt in range(3):
            try:
                media_group = [
                    InputMediaPhoto(media=photo_bytes, caption=caption, parse_mode=ParseMode.HTML),
                    InputMediaVideo(media=video_bytes, supports_streaming=True)
                ]
                await bot.send_media_group(chat_id=chat_id, media=media_group)
                sent_group = True
                break
            except Exception as e:
                logger.warning(f"Media group yuborishda xato ({chat_id}, urinish {attempt+1}/3): {e}")
                await asyncio.sleep(2)

        if not sent_group:
            logger.info(f"Media group o'tmadi, alohida yuborilmoqda ({chat_id})...")
            try:
                await bot.send_photo(chat_id=chat_id, photo=photo_bytes, caption=caption, parse_mode=ParseMode.HTML)
                await bot.send_video(chat_id=chat_id, video=video_bytes, supports_streaming=True)
            except Exception as e:
                logger.error(f"Alohida yuborishda ham xato ({chat_id}): {e}")


async def smooth_scroll_down(page, steps=3):
    for _ in range(steps):
        scroll_y = random.randint(180, 260)
        await page.mouse.wheel(0, scroll_y)
        await page.mouse.move(random.randint(200, 700), random.randint(200, 500))
        await asyncio.sleep(random.uniform(1.0, 1.4))


async def smooth_scroll_up(page, steps=3):
    for _ in range(steps):
        scroll_y = random.randint(180, 260)
        await page.mouse.wheel(0, -scroll_y)
        await page.mouse.move(random.randint(200, 700), random.randint(200, 500))
        await asyncio.sleep(random.uniform(0.8, 1.2))


async def run_local():
    bot = create_bot()
    os.makedirs(MEDIA_DIR, exist_ok=True)

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
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        for acc in accounts:
            login = acc["login"]
            password = acc["password"]
            sinf = acc["sinf"]
            print(f"[*] Kirish: {login} (Sinf: {sinf})...")

            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                record_video_dir=MEDIA_DIR,
                record_video_size={"width": 1280, "height": 720}
            )
            page = await context.new_page()

            try:
                await page.goto(config.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector('input[name="login"]', timeout=15000)
                await asyncio.sleep(1.0)

                for char in login:
                    await page.type('input[name="login"]', char, delay=random.randint(60, 110))
                await asyncio.sleep(0.5)

                for char in password:
                    await page.type('input[name="password"]', char, delay=random.randint(60, 110))
                await asyncio.sleep(0.8)

                await page.click('button[type="submit"], input[type="submit"]')

                print(f"[~] {login} uchun 1-sahifa to'liq yuklanishi 6 soniya kutilmoqda...")
                await asyncio.sleep(6.0)

                # HECH QANDAY TUGMA BOSILMASDAN 1-sahifa rasmi olinadi
                photo_path = os.path.join(MEDIA_DIR, f"{login}.png")
                await page.screenshot(path=photo_path, full_page=False)

                await smooth_scroll_down(page, steps=3)
                await asyncio.sleep(1.0)
                await smooth_scroll_up(page, steps=3)
                await asyncio.sleep(1.0)

                # Dars jadvalini ochish
                kundalik_btn = await page.query_selector('a:has-text("Kundalik"), a:has-text("Dnevnik"), a:has-text("Dars jadvali")')
                if kundalik_btn:
                    try:
                        await kundalik_btn.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    except Exception:
                        pass

                await asyncio.sleep(2.0)
                await smooth_scroll_down(page, steps=4)
                await asyncio.sleep(1.5)
                await smooth_scroll_up(page, steps=4)
                await asyncio.sleep(1.0)

                # Qaytish
                home_btn = await page.query_selector('a:has-text("Bosh sahifa"), a:has-text("Glavnaya"), a.header__logo')
                if home_btn:
                    try:
                        await home_btn.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    except Exception:
                        await page.go_back()
                else:
                    await page.go_back()

                print(f"[~] {login} uchun asosiy sahifada 2.5s kutilmoqda...")
                await asyncio.sleep(2.5)

                await page.close()
                raw_video_path = await page.video.path()
                await context.close()

                mp4_path = os.path.join(MEDIA_DIR, f"{login}.mp4")
                cmd = [
                    "ffmpeg", "-y", "-i", raw_video_path,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
                    "-movflags", "+faststart", mp4_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                caption = (
                    f"🏫 Sinf: <b>{html.escape(sinf)}</b>\n"
                    f"👤 Login: <tg-spoiler>{html.escape(login)}</tg-spoiler>\n"
                    f"🔑 Parol: <tg-spoiler>{html.escape(password)}</tg-spoiler>\n"
                    f"✅ Holat: Muvaffaqiyatli kirildi"
                )

                await send_media(bot, photo_path, mp4_path, caption, sinf)

                if os.path.exists(raw_video_path):
                    os.remove(raw_video_path)

            except Exception as e:
                print(f"[-] {login} xatosi: {e}")
                try:
                    await context.close()
                except:
                    pass

        await browser.close()
    print("Barcha vazifalar yakunlandi!")


if __name__ == "__main__":
    asyncio.run(run_local())
