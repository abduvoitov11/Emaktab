import os
import sys
import html
import asyncio
import random
import logging
import subprocess
from datetime import datetime
import zoneinfo
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


def load_accounts_by_class(file_path: str):
    if not os.path.exists(file_path):
        logger.error(f"Excel fayl topilmadi: {file_path}")
        return {}

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active

    classes = {}
    for r in range(2, ws.max_row + 1):
        login = ws.cell(row=r, column=2).value
        password = ws.cell(row=r, column=3).value
        chat_id = ws.cell(row=r, column=4).value
        sinf = ws.cell(row=r, column=5).value or "9-B"

        if login and password:
            sinf_name = str(sinf).strip().upper()
            if sinf_name not in classes:
                classes[sinf_name] = []
            classes[sinf_name].append({
                "login": str(login).strip(),
                "password": str(password).strip(),
                "chat_id": int(chat_id) if chat_id else config.SUPER_ADMIN_ID,
                "sinf": sinf_name
            })

    total = sum(len(v) for v in classes.values())
    logger.info(f"Excel fayldan {len(classes)} ta sinf bo'yicha jami {total} ta hisob yuklandi.")
    return classes


def generate_weekly_schedule(accounts: list, year: int, week: int):
    rng = random.Random(year * 1000 + week)
    shuffled = list(accounts)
    rng.shuffle(shuffled)

    days = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    counts = {acc["login"]: 0 for acc in accounts}

    active_days = [5, 6, 0, 1, 2, 3] # Shanba(5), Yakshanba(6), Dushanba(0), Seshanba(1), Chorshanba(2), Payshanba(3)

    n = len(shuffled)
    saturday_quota = min(3, n)
    remaining_n = n - saturday_quota
    base_per_day = remaining_n // 5
    rem = remaining_n % 5

    base_dist = {5: saturday_quota}
    for i, d in enumerate([6, 0, 1, 2, 3]):
        base_dist[d] = base_per_day + (1 if i < rem else 0)

    idx = 0
    for d in active_days:
        for _ in range(base_dist[d]):
            if idx < n:
                acc = shuffled[idx]
                days[d].append(acc)
                counts[acc["login"]] += 1
                idx += 1

    for d in active_days:
        current_logins = {acc["login"] for acc in days[d]}
        candidates = [
            acc for acc in accounts
            if acc["login"] not in current_logins and counts[acc["login"]] < config.WEEKLY_MAX_PER_ACCOUNT
        ]
        rng.shuffle(candidates)
        max_extra = 1 if d == 5 else 2
        extra = min(rng.randint(0, max_extra), config.DAILY_MAX_ACCOUNTS - 1 - len(days[d]))
        for acc in candidates[:max(0, extra)]:
            days[d].append(acc)
            counts[acc["login"]] += 1

    return days


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

    for chat_id in recipients:
        # 1. Rasm yuborish
        for attempt in range(3):
            try:
                with open(photo_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                break
            except Exception as e:
                logger.warning(f"Rasm yuborishda xato (urinish {attempt+1}/3): {e}")
                await asyncio.sleep(2)

        # 2. Video yuborish
        for attempt in range(3):
            try:
                with open(video_path, "rb") as video:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        supports_streaming=True
                    )
                break
            except Exception as e:
                logger.warning(f"Video yuborishda xato (urinish {attempt+1}/3): {e}")
                await asyncio.sleep(2)


async def human_scroll_down_and_up(page):
    """Tugmalarni bosmasdan, shu sahifada pastga tushib, yana tepaga qaytish."""
    for _ in range(4):
        scroll_y = random.randint(180, 260)
        await page.mouse.wheel(0, scroll_y)
        await page.mouse.move(random.randint(200, 600), random.randint(200, 500))
        await asyncio.sleep(random.uniform(1.0, 1.5))

    await asyncio.sleep(1.5)

    for _ in range(4):
        scroll_y = random.randint(180, 260)
        await page.mouse.wheel(0, -scroll_y)
        await page.mouse.move(random.randint(200, 600), random.randint(200, 500))
        await asyncio.sleep(random.uniform(0.8, 1.3))

    await asyncio.sleep(1.0)


async def process_account(browser, bot: Bot, acc: dict):
    login = acc["login"]
    password = acc["password"]
    sinf = acc.get("sinf", "9-B")

    os.makedirs(MEDIA_DIR, exist_ok=True)
    logger.info(f"[*] Kirilmoqda (Rasm + Video): {login} (Sinf: {sinf})")

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

        # Insondek terish
        for char in login:
            await page.type('input[name="login"]', char, delay=random.randint(60, 110))
        await asyncio.sleep(0.5)

        for char in password:
            await page.type('input[name="password"]', char, delay=random.randint(60, 110))
        await asyncio.sleep(0.8)

        await page.click('button[type="submit"], input[type="submit"]')

        # 7-8 soniya sahifa to'liq yuklanishini kutish
        logger.info(f"[~] {login} uchun 7.5 soniya sahifa yuklanishi kutilmoqda...")
        await asyncio.sleep(7.5)

        # Boshqa tugmalarni bosmasdan shu sahifada scroll qilib pastga tushib, yana tepaga chiqish
        logger.info(f"[~] {login} uchun sahifada insoniy scroll qilinmoqda...")
        await human_scroll_down_and_up(page)

        # Skrinshot olish
        photo_path = os.path.join(MEDIA_DIR, f"{login}.png")
        await page.screenshot(path=photo_path, full_page=False)

        # Videoni saqlash va yopish
        await page.close()
        raw_video_path = await page.video.path()
        await context.close()

        # MP4 formatga o'tkazish
        mp4_path = os.path.join(MEDIA_DIR, f"{login}.mp4")
        cmd = [
            "ffmpeg", "-y", "-i", raw_video_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            "-movflags", "+faststart", mp4_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Ortiqcha so'zlarsiz, toza va rasmiy izoh
        caption = (
            f"🏫 Sinf: <b>{html.escape(sinf)}</b>\n"
            f"👤 Login: <tg-spoiler>{html.escape(login)}</tg-spoiler>\n"
            f"🔑 Parol: <tg-spoiler>{html.escape(password)}</tg-spoiler>\n"
            f"✅ Holat: Muvaffaqiyatli kirildi"
        )

        await send_media(bot, photo_path, mp4_path, caption, sinf)

        # Tozalash
        if os.path.exists(raw_video_path):
            os.remove(raw_video_path)

        return True
    except Exception as e:
        logger.error(f"[-] {login} bilan ishlashda xatolik: {e}")
        try:
            await context.close()
        except:
            pass
        return False


async def run():
    bot = create_bot()
    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    now = datetime.now(tashkent_tz)
    year, week, weekday_iso = now.isocalendar()
    weekday = weekday_iso - 1

    day_names = {
        0: "Dushanba", 1: "Seshanba", 2: "Chorshanba", 3: "Payshanba",
        4: "Juma", 5: "Shanba", 6: "Yakshanba"
    }
    logger.info(f"Hozirgi vaqt (Toshkent): {now.strftime('%Y-%m-%d %H:%M:%S')}, {day_names.get(weekday, '')}")

    force_run = os.getenv("FORCE_RUN", "false").lower() == "true"
    custom_day = os.getenv("CUSTOM_DAY", "auto").lower()

    if custom_day in ["0", "mon", "dushanba"]:
        weekday = 0
    elif custom_day in ["1", "tue", "seshanba"]:
        weekday = 1
    elif custom_day in ["2", "wed", "chorshanba"]:
        weekday = 2
    elif custom_day in ["3", "thu", "payshanba"]:
        weekday = 3
    elif custom_day in ["4", "fri", "juma"]:
        weekday = 4
    elif custom_day in ["5", "sat", "shanba"]:
        weekday = 5
    elif custom_day in ["6", "sun", "yakshanba"]:
        weekday = 6

    if weekday == 4 and not force_run:
        logger.info("🛑 Bugun JUMA — dam olish kuni. eMaktabga kirish qat'iyan to'xtatildi!")
        return

    enable_jitter = os.getenv("ENABLE_JITTER", "true").lower() == "true"
    if enable_jitter and not force_run:
        jitter = random.randint(config.MIN_STARTUP_JITTER_SECONDS, config.MAX_STARTUP_JITTER_SECONDS)
        logger.info(f"Anti-BAN: Boshlanishdan oldin {jitter} soniya tasodifiy kutilmoqda...")
        await asyncio.sleep(jitter)

    classes = load_accounts_by_class(EXCEL_FILE)
    if not classes:
        logger.error("Hech qanday hisob topilmadi!")
        return

    today_batch = []
    for sinf_name, accounts in classes.items():
        schedule = generate_weekly_schedule(accounts, year, week)
        today_accs = schedule.get(weekday, [])
        today_batch.extend(today_accs)

    if len(today_batch) > config.DAILY_MAX_ACCOUNTS:
        logger.warning(f"Kunlik limit {config.DAILY_MAX_ACCOUNTS} tadan oshmasligi uchun qisqartirildi.")
        today_batch = today_batch[:config.DAILY_MAX_ACCOUNTS]

    logger.info(f"Bugungi ({day_names.get(weekday, '')}) navbatda {len(today_batch)} ta hisob bor.")

    if not today_batch:
        logger.info("Bugun uchun hisoblar belgilanmagan.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        success_count = 0
        for i, acc in enumerate(today_batch, 1):
            logger.info(f"[{i}/{len(today_batch)}] Ishlanmoqda...")
            ok = await process_account(browser, bot, acc)
            if ok:
                success_count += 1

            if i < len(today_batch):
                pause = random.randint(config.MIN_HUMAN_PAUSE_SECONDS, config.MAX_HUMAN_PAUSE_SECONDS)
                logger.info(f"Insoniy pauza: {pause} soniya kutilmoqda...")
                await asyncio.sleep(pause)

        await browser.close()

    summary_msg = (
        f"📊 <b>Bugungi hisobot ({day_names.get(weekday, '')}):</b>\n"
        f"✅ Muvaffaqiyatli tekshirildi: <b>{success_count} / {len(today_batch)}</b> ta hisob (Rasm + Video)\n"
        f"⏱ Vaqt: {datetime.now(tashkent_tz).strftime('%H:%M:%S')}"
    )
    try:
        await bot.send_message(
            chat_id=config.SUPER_ADMIN_ID,
            text=summary_msg,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Xulosa xabarini yuborishda xato: {e}")

    logger.info("Bugungi barcha vazifalar to'liq yakunlandi!")


if __name__ == "__main__":
    asyncio.run(run())
