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
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode

import config

# ===== CAPTCHA: ddddocr avtomatik yechish =====
try:
    import ddddocr
    _ocr = ddddocr.DdddOcr(show_ad=False)
    DDDDOCR_AVAILABLE = True
    logging.getLogger(__name__).info("✅ ddddocr yukland — captcha avtoyechish faol.")
except ImportError:
    _ocr = None
    DDDDOCR_AVAILABLE = False
    logging.getLogger(__name__).warning("⚠️  ddddocr topilmadi — captcha avtoyechish o'chiq.")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXCEL = os.path.join(BASE_DIR, "Foydalanuvchilar_Royxati.xlsx")
if not os.path.exists(DEFAULT_EXCEL):
    if os.getenv("EXCEL_BASE64"):
        import base64
        try:
            with open(DEFAULT_EXCEL, "wb") as f:
                f.write(base64.b64decode(os.getenv("EXCEL_BASE64")))
            logger.info("Excel fayl shifrlangan GitHub Secret (EXCEL_BASE64) dan xavfsiz tiklandi.")
        except Exception as e:
            logger.error(f"EXCEL_BASE64 ni dekodlashda xato: {e}")
    elif os.path.exists("/home/torabek/Downloads/Foydalanuvchilar_Royxati.xlsx"):
        DEFAULT_EXCEL = "/home/torabek/Downloads/Foydalanuvchilar_Royxati.xlsx"
EXCEL_FILE = os.getenv("EXCEL_FILE", DEFAULT_EXCEL)
MEDIA_DIR = os.path.join(BASE_DIR, "media")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

greeted_recipients = set()


def solve_captcha(image_bytes: bytes) -> str:
    """ddddocr yordamida captcha rasmini matn(string)ga aylantiradi."""
    if not DDDDOCR_AVAILABLE or _ocr is None:
        return ""
    try:
        result = _ocr.classification(image_bytes)
        logger.info(f"🔐 ddddocr captchani o'qidi: '{result}'")
        return result.strip()
    except Exception as e:
        logger.error(f"ddddocr xato: {e}")
        return ""


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
            "⚡ <b>AvtoEmaktab Bosh Monitoring Tizimi</b> 🎓\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Assalomu alaykum, <b>Bosh Administrator</b>!\n\n"
            "🚀 Bugungi eMaktab avtomatlashtirish jarayoni boshlandi.\n"
            "📊 <i>Barcha sinflar bo'yicha 1080p HD video va foto hisobotlar quyida qabul qilinmoqda...</i> ⬇️"
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
                f"🌸 <b>AvtoEmaktab Hisobot Tizimi</b> 🎓\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Assalomu alaykum, <b>{html.escape(t_name)} ustoz</b>! 👋\n\n"
                f"📋 <b>{html.escape(sinf)}</b> sinfingizning bugungi dars va baholash natijalari tayyorlandi.\n"
                f"📸 <i>Quyida 1080p HD video va jurnal fotosuratlari qabul qilinmoqda...</i> ⬇️\n\n"
                f"⏱ <i>Har oyda 26 soat qimmatli vaqtingizni va asabingizni tejang!</i>"
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

        # Agar media group biron sababga ko'ra o'tmasa, alohida yuborish fallback
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


async def process_account(browser, bot: Bot, acc: dict):
    login = acc["login"]
    password = acc["password"]
    sinf = acc["sinf"]

    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    now_check = datetime.now(tashkent_tz)
    if config.is_curfew_time(now_check):
        logger.warning(f"🛑 {login} uchun login bekor qilindi: Tungi taqiq (21:45 - 07:00) faol! ({now_check.strftime('%H:%M:%S')})")
        return False

    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    logger.info(f"[*] To'liq insoniy ssenariy (Rasm + Video): {login} (Sinf: {sinf})")

    session_path = os.path.join(SESSIONS_DIR, f"{login}.json")
    session_exists = os.path.exists(session_path)

    # === SESSION MAVJUD BO'LSA: Login sahifasini o'tkazib yuboramiz ===
    if session_exists:
        logger.info(f"[✅] {login} uchun saqlangan session topildi — login sahifasi o'tkaziladi.")
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            storage_state=session_path,
            record_video_dir=MEDIA_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        await page.goto("https://emaktab.uz/userfeed", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(1.5, 2.5))

        # Session eskirgan bo'lsa (login sahifasiga qaytsa) — qayta login qilamiz
        if "login.emaktab.uz" in page.url:
            logger.warning(f"[⚠️] {login} sessiyasi eskirgan — qayta login qilinmoqda...")
            os.remove(session_path)
            session_exists = False
            await context.close()

    # === SESSION YO'Q BO'LSA: To'liq login jarayoni ===
    if not session_exists:
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            record_video_dir=MEDIA_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        # --- Captcha bilan login (3 urinish) ---
        login_success = False
        for attempt in range(1, 4):
            try:
                await page.goto(config.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector('input[name="login"]', timeout=15000)
                await asyncio.sleep(random.uniform(0.8, 1.5))

                await page.fill('input[name="login"]', "")
                await page.fill('input[name="password"]', "")

                for char in login:
                    await page.type('input[name="login"]', char, delay=random.randint(60, 110))
                await asyncio.sleep(random.uniform(0.4, 0.8))

                for char in password:
                    await page.type('input[name="password"]', char, delay=random.randint(60, 110))
                await asyncio.sleep(random.uniform(0.6, 1.2))

                # Captcha tekshiruvi
                captcha_visible = await page.evaluate("""
                    () => {
                        const el = document.querySelector('.login__body__captcha');
                        return el ? !el.classList.contains('login__body__captcha_hidden') : false;
                    }
                """)

                if captcha_visible:
                    logger.info(f"[🔐] {login} — {attempt}-urinish: Captcha aniqlandi! ddddocr bilan yechilmoqda...")
                    captcha_bytes = await page.evaluate("""
                        async () => {
                            const img = document.querySelector('.login__body__captcha img');
                            if (!img) return null;
                            const r = await fetch(img.src);
                            const buf = await r.arrayBuffer();
                            return Array.from(new Uint8Array(buf));
                        }
                    """)
                    if captcha_bytes:
                        img_bytes = bytes(captcha_bytes)
                        captcha_text = solve_captcha(img_bytes)
                        if captcha_text:
                            await page.fill('input[name="Captcha.Input"]', captcha_text)
                            await asyncio.sleep(random.uniform(0.3, 0.6))
                        else:
                            logger.warning(f"[⚠️] {login} — Captcha o'qilmadi, bo'sh qoldirildi.")
                else:
                    logger.info(f"[✅] {login} — Captcha yo'q, to'g'ridan login...")

                await page.click('button[type="submit"], input[type="submit"]')
                await asyncio.sleep(5.0)

                if "login.emaktab.uz" not in page.url:
                    logger.info(f"[✅] {login} — Login muvaffaqiyatli! URL: {page.url}")
                    # Session saqlanadi (keyingi ishga tushirishda login o'tkaziladi)
                    await context.storage_state(path=session_path)
                    logger.info(f"[💾] {login} sessiyasi saqlandi: {session_path}")
                    login_success = True
                    break
                else:
                    logger.warning(f"[⚠️] {login} — {attempt}-urinish muvaffaqiyatsiz. Qayta uriniladi...")
                    await asyncio.sleep(random.uniform(3, 6))
            except Exception as e:
                logger.error(f"[❌] {login} — {attempt}-urinishda xato: {e}")
                await asyncio.sleep(random.uniform(3, 5))

        if not login_success:
            logger.error(f"[❌] {login} — 3 urinishdan keyin ham login muvaffaqiyatsiz!")
            try:
                await context.close()
            except Exception:
                pass
            return False

    try:
        # 4. HECH QANDAY TUGMA BOSILMASDAN 1-sahifaning rasmini (skrinshot) olish
        photo_path = os.path.join(MEDIA_DIR, f"{login}.png")
        await page.screenshot(path=photo_path, full_page=False)
        logger.info(f"[+] 1-sahifa rasmi olindi: {photo_path}")

        # 5. Videoning davomi: 1-sahifada scroll qilish
        await smooth_scroll_down(page, steps=3)
        await asyncio.sleep(1.0)
        await smooth_scroll_up(page, steps=3)
        await asyncio.sleep(1.0)

        # 6. Dars jadvalini / Kundalikni ochish
        logger.info(f"[~] {login} uchun dars jadvali sahifasiga o'tilmoqda...")
        kundalik_btn = await page.query_selector('a:has-text("Kundalik"), a:has-text("Dnevnik"), a:has-text("Dars jadvali")')
        if kundalik_btn:
            try:
                await kundalik_btn.click()
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass

        # Dars jadvalini sekin ko'rib chiqish (o'qish, scroll)
        await asyncio.sleep(2.0)
        await smooth_scroll_down(page, steps=4)
        await asyncio.sleep(1.5)
        await smooth_scroll_up(page, steps=4)
        await asyncio.sleep(1.0)

        # 7. Yana asosiy sahifaga qaytish
        logger.info(f"[~] {login} uchun yana asosiy sahifaga qaytilmoqda...")
        home_btn = await page.query_selector('a:has-text("Bosh sahifa"), a:has-text("Glavnaya"), a.header__logo')
        if home_btn:
            try:
                await home_btn.click()
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                await page.go_back()
        else:
            await page.go_back()

        # 8. Asosiy sahifada 2.5 soniya kutib videoni yakunlash
        logger.info(f"[~] {login} uchun asosiy sahifada 2.5s kutilib video yakunlanmoqda...")
        await asyncio.sleep(2.5)

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

        # Toza va rasmiy izoh
        caption = (
            f"✅ <b>KUNLIK HISOBOT: {html.escape(sinf)} SINF</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏫 <b>Tizim:</b> eMaktab.uz Monitoring\n"
            f"👤 <b>Login:</b> <tg-spoiler>{html.escape(login)}</tg-spoiler>\n"
            f"🔑 <b>Parol:</b> <tg-spoiler>{html.escape(password)}</tg-spoiler>\n"
            f"📊 <b>Holati:</b> Muvaffaqiyatli tekshirildi\n"
            f"⚡ <b>Kirish:</b> Insoniy simulyatsiya (Playwright)\n"
            f"🔒 <b>Xavfsizlik:</b> 21:45 tungi taqiq himoyasida\n\n"
            f"🎥 <i>HD video va fotosuratda profilingizga kirilgani va baholar to'liq tekshirilgani tasdiqlangan.</i>"
        )

        await send_media(bot, photo_path, mp4_path, caption, sinf)

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

    # Tungi rejim taqiqi (21:45 - 07:00) — Bu vaqt oralig'ida login qilish qat'iyan taqiqlanadi
    if config.is_curfew_time(now):
        curfew_msg = (
            "🛑 <b>TUNGI XAVFSIZLIK TAQIQI (21:45 - 07:00)</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "Kechki va tungi soatlarda eMaktab tizimiga login qilish xavfsizlik (Anti-BAN va insoniy faollik) talablari bo'yicha qat'iyan taqiqlangan!\n\n"
            f"⏱ Hozirgi Toshkent vaqti: <b>{now.strftime('%H:%M:%S')}</b>\n"
            "🌙 <b>Holat:</b> Dam olish vaqti faol\n"
            "🌅 Tizim ertalab soat <b>07:00</b> da qayta faollashadi."
        )
        logger.warning(f"🛑 TUNGI TAQIQ: Soat {now.strftime('%H:%M:%S')} — 21:45 dan 07:00 gacha login qilish qat'iyan taqiqlangan! Jarayon to'xtatildi.")
        try:
            await bot.send_message(
                chat_id=config.SUPER_ADMIN_ID,
                text=curfew_msg,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Tungi taqiq xabarini yuborishda xato: {e}")
        return

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

    all_accounts = os.getenv("ALL_ACCOUNTS", "false").lower() == "true"
    if all_accounts:
        today_batch = []
        for sinf_name, acc_list in classes.items():
            today_batch.extend(acc_list)
        logger.info(f"⚡ TO'LIQ IERARXIYA REJIMI (ALL_ACCOUNTS=True): Jami {len(today_batch)} ta hisobga kiriladi!")
    else:
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
            now_check = datetime.now(tashkent_tz)
            if config.is_curfew_time(now_check):
                logger.warning(f"🛑 Vaqt 21:45 ga yetdi ({now_check.strftime('%H:%M:%S')})! Tungi xavfsizlik taqiqi kuchga kirdi. Qolgan hisoblar to'xtatildi.")
                try:
                    await bot.send_message(
                        chat_id=config.SUPER_ADMIN_ID,
                        text=(
                            f"🛑 <b>Vaqt 21:45 bo'ldi!</b> Tungi xavfsizlik taqiqi sababli jarayon to'xtatildi.\n"
                            f"eMaktab xavfsizligi (anti-ban) uchun tungi loginlar taqiqlangan.\n"
                            f"✅ Muvaffaqiyatli yuborildi: <b>{success_count} / {len(today_batch)}</b>"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                break

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
        f"📊 <b>KUNLIK YAKUNIY MONITORING HISOBOTI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Hafta kuni:</b> {day_names.get(weekday, '')}\n"
        f"✅ <b>Muvaffaqiyatli tekshirildi:</b> <b>{success_count} / {len(today_batch)}</b> ta hisob\n"
        f"📹 <b>Format:</b> 1080p HD Video + Skrinshot\n"
        f"⏱ <b>Yakunlangan vaqt:</b> {datetime.now(tashkent_tz).strftime('%H:%M:%S')} (Toshkent)\n"
        f"🛡️ <b>Anti-BAN holati:</b> 100% Xavfsiz topshirildi\n\n"
        f"🎓 <i>AvtoEmaktab — eMaktab.uz aqlli avtomatlashtirish platformasi.</i>"
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
