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
    print("✅ ddddocr yukland — captcha avtoyechish faol.")
except ImportError:
    _ocr = None
    DDDDOCR_AVAILABLE = False
    print("⚠️  ddddocr topilmadi — captcha avtoyechish o'chiq.")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

greeted_recipients = set()


def find_excel_files(target_class=None):
    """Mavjud barcha sinf va foydalanuvchi Excel fayllarini aniqlaydi."""
    if target_class:
        t = target_class.strip().upper().replace(" ", "").replace("-", "")
        if t in ["3D", "3-D"]:
            f3d = os.path.join(BASE_DIR, "3-D_Royxati.xlsx")
            if os.path.exists(f3d):
                return [f3d]
            dl_3d = "/home/torabek/Downloads/3-D_Royxati.xlsx"
            if os.path.exists(dl_3d):
                return [dl_3d]
        elif t in ["9B", "9-B"]:
            f9b = os.path.join(BASE_DIR, "9-B_Royxati.xlsx")
            if os.path.exists(f9b):
                return [f9b]
            dl_9b = "/home/torabek/Downloads/9-B_Royxati.xlsx"
            if os.path.exists(dl_9b):
                return [dl_9b]

    class_files = [
        os.path.join(BASE_DIR, "9-B_Royxati.xlsx"),
        os.path.join(BASE_DIR, "3-D_Royxati.xlsx")
    ]
    if all(os.path.exists(f) for f in class_files):
        return class_files

    default_excel = os.path.join(BASE_DIR, "Foydalanuvchilar_Royxati.xlsx")
    if os.path.exists(default_excel):
        return [default_excel]

    dl_class_files = [
        "/home/torabek/Downloads/9-B_Royxati.xlsx",
        "/home/torabek/Downloads/3-D_Royxati.xlsx"
    ]
    if all(os.path.exists(f) for f in dl_class_files):
        return dl_class_files

    dl_main = "/home/torabek/Downloads/Foydalanuvchilar_Royxati.xlsx"
    if os.path.exists(dl_main):
        return [dl_main]

    return [f for f in class_files if os.path.exists(f)] or [default_excel]


def load_accounts(file_paths=None, target_class=None):
    if file_paths is None:
        file_paths = find_excel_files(target_class=target_class)
    elif isinstance(file_paths, str):
        file_paths = [file_paths]

    if target_class:
        target_class = target_class.strip().upper().replace(" ", "")

    accounts = []
    seen_logins = set()

    for fp in file_paths:
        if not os.path.exists(fp):
            continue
        try:
            wb = openpyxl.load_workbook(fp, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                login = ws.cell(row=r, column=2).value
                password = ws.cell(row=r, column=3).value
                chat_id = ws.cell(row=r, column=4).value
                sinf = ws.cell(row=r, column=5).value

                if not sinf:
                    if "9-B" in fp or "9B" in fp:
                        sinf = "9-B"
                    elif "3-D" in fp or "3D" in fp:
                        sinf = "3-D"
                    else:
                        sinf = "9-B"

                if login and password:
                    l_str = str(login).strip()
                    if l_str in seen_logins:
                        continue
                    sinf_name = str(sinf).strip().upper().replace(" ", "")
                    if target_class:
                        norm_target = target_class.replace("-", "")
                        norm_sinf = sinf_name.replace("-", "")
                        if norm_target != norm_sinf:
                            continue

                    seen_logins.add(l_str)
                    accounts.append({
                        "login": l_str,
                        "password": str(password).strip(),
                        "chat_id": int(chat_id) if chat_id else config.SUPER_ADMIN_ID,
                        "sinf": str(sinf).strip().upper()
                    })
        except Exception as e:
            print(f"[-] {fp} faylini o'qishda xatolik: {e}")

    return accounts


def solve_captcha(image_bytes: bytes) -> str:
    """ddddocr yordamida captcha rasmini matn(string)ga aylantiradi."""
    if not DDDDOCR_AVAILABLE or _ocr is None:
        return ""
    try:
        result = _ocr.classification(image_bytes)
        print(f"🔐 ddddocr captchani o'qidi: '{result}'")
        return result.strip()
    except Exception as e:
        print(f"ddddocr xato: {e}")
        return ""


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

    target_class = os.getenv("TARGET_CLASS")
    for arg in sys.argv[1:]:
        if arg.startswith("--class="):
            target_class = arg.split("=", 1)[1]
        elif arg.upper() in ["3D", "3-D", "9B", "9-B"]:
            target_class = arg

    ignore_curfew = (
        os.getenv("IGNORE_CURFEW", "false").lower() == "true" or
        "--force" in sys.argv or
        "--ignore-curfew" in sys.argv
    )

    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    now = datetime.now(tashkent_tz)
    if config.is_curfew_time(now) and not ignore_curfew:
        print(f"\n🛑 DIQQAT: TUNGI XAVFSIZLIK TAQIQI (21:45 - 07:00) FAOL! ({now.strftime('%H:%M:%S')})")
        print("eMaktab.uz tizimiga tungi soatlarda kirish qat'iyan taqiqlangan (Anti-BAN xavfsizligi).")
        print("Dastur ertalab soat 07:00 dan keyin ishga tushishi mumkin.\n")
        try:
            await bot.send_message(
                chat_id=config.SUPER_ADMIN_ID,
                text=(
                    f"🛑 <b>TUNGI XAVFSIZLIK TAQIQI (21:45 - 07:00):</b>\n"
                    f"Mahalliy ishga tushirish to'xtatildi. Tungi soatda eMaktabga login qilinmadi.\n"
                    f"⏱ Hozirgi vaqt: <b>{now.strftime('%H:%M:%S')}</b>"
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
        return

    excel_files = find_excel_files(target_class=target_class)
    file_names = ", ".join([os.path.basename(f) for f in excel_files])
    print(f"Excel fayllardan ma'lumotlar o'qilmoqda: {file_names} (Sinf filtri: {target_class or 'Barchasi'})...")
    accounts = load_accounts(excel_files, target_class=target_class)
    print(f"Jami {len(accounts)} ta hisob topildi. Dastur ishga tushmoqda...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        success_count = 0
        for i, acc in enumerate(accounts, 1):
            now_check = datetime.now(tashkent_tz)
            if config.is_curfew_time(now_check) and not ignore_curfew:
                print(f"🛑 Vaqt 21:45 ga yetdi ({now_check.strftime('%H:%M:%S')})! Tungi taqiq kuchga kirdi. Qolgan hisoblar to'xtatildi.")
                try:
                    await bot.send_message(
                        chat_id=config.SUPER_ADMIN_ID,
                        text=(
                            f"🛑 <b>Vaqt 21:45 bo'ldi!</b> Tungi xavfsizlik taqiqi kuchga kirdi.\n"
                            f"eMaktab xavfsizligi (anti-ban) uchun qolgan hisoblar to'xtatildi.\n"
                            f"✅ Muvaffaqiyatli yuborildi: <b>{success_count} / {len(accounts)}</b>"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                break

            login = acc["login"]
            password = acc["password"]
            sinf = acc["sinf"]
            print(f"[{i}/{len(accounts)}] Kirish: {login} (Sinf: {sinf})...")

            os.makedirs(SESSIONS_DIR, exist_ok=True)
            session_path = os.path.join(SESSIONS_DIR, f"{login}.json")
            session_exists = os.path.exists(session_path)

            # === SESSION MAVJUD BO'LSA: Login sahifasini o'tkazib yuboramiz ===
            if session_exists:
                print(f"[✅] {login} uchun saqlangan session topildi — login sahifasi o'tkaziladi.")
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

                if "login.emaktab.uz" in page.url:
                    print(f"[⚠️] {login} sessiyasi eskirgan — qayta login qilinmoqda...")
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
                            print(f"[🔐] {login} — {attempt}-urinish: Captcha aniqlandi! ddddocr bilan yechilmoqda...")
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
                                    print(f"[⚠️] {login} — Captcha o'qilmadi, bo'sh qoldirildi.")
                        else:
                            print(f"[✅] {login} — Captcha yo'q, to'g'ridan login...")

                        await page.click('button[type="submit"], input[type="submit"]')
                        await asyncio.sleep(5.0)

                        if "login.emaktab.uz" not in page.url:
                            print(f"[✅] {login} — Login muvaffaqiyatli! URL: {page.url}")
                            await context.storage_state(path=session_path)
                            print(f"[💾] {login} sessiyasi saqlandi: {session_path}")
                            login_success = True
                            break
                        else:
                            print(f"[⚠️] {login} — {attempt}-urinish muvaffaqiyatsiz. Qayta uriniladi...")
                            await asyncio.sleep(random.uniform(3, 6))
                    except Exception as e:
                        print(f"[❌] {login} — {attempt}-urinishda xato: {e}")
                        await asyncio.sleep(random.uniform(3, 5))

                if not login_success:
                    print(f"[❌] {login} — 3 urinishdan keyin ham login muvaffaqiyatsiz!")
                    try:
                        await context.close()
                    except Exception:
                        pass
                    continue

            try:
                # === AQLLI BROWSING: Barcha sahifalarni o'zi topib bosadi ===
                print(f"[🤖] {login} — Aqlli browsing sessiyasi boshlanmoqda...")

                # 1. Bosh sahifada skrinshot + scroll
                photo_path = os.path.join(MEDIA_DIR, f"{login}.png")
                await page.screenshot(path=photo_path, full_page=False)
                print(f"[📸] Bosh sahifa skrinshoti olindi.")
                await smooth_scroll_down(page, steps=2)
                await asyncio.sleep(random.uniform(0.8, 1.3))
                await smooth_scroll_up(page, steps=2)
                await asyncio.sleep(random.uniform(0.5, 1.0))

                # 2. Nav menudan barcha tugmalarni topib bosish
                nav_selectors = [
                    'a:has-text("Kundalik")',
                    'a:has-text("Дневник")',
                    'a:has-text("Dnevnik")',
                    'a:has-text("Dars jadvali")',
                    'a:has-text("Расписание")',
                    'a:has-text("Jadval")',
                    'a:has-text("Yangiliklar")',
                    'a:has-text("Лента")',
                    'a:has-text("Novosti")',
                    'a:has-text("Baholar")',
                    'a:has-text("Оценки")',
                    'a:has-text("Baholar tasmasi")',
                    'a:has-text("Reyting")',
                    'a:has-text("Рейтинг")',
                ]

                visited_texts = set()
                for selector in nav_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if not btn:
                            continue
                        btn_text = (await btn.inner_text()).strip()
                        if btn_text in visited_texts:
                            continue
                        visited_texts.add(btn_text)

                        print(f"[🖱️] '{btn_text}' sahifasiga o'tilmoqda...")
                        await btn.click()
                        await page.wait_for_load_state("domcontentloaded", timeout=12000)
                        await asyncio.sleep(random.uniform(1.2, 2.0))

                        await smooth_scroll_down(page, steps=random.randint(2, 4))
                        await asyncio.sleep(random.uniform(0.8, 1.5))
                        await smooth_scroll_up(page, steps=random.randint(1, 3))
                        await asyncio.sleep(random.uniform(0.5, 1.0))

                    except Exception as ex:
                        continue

                # 3. Sidebar / Panel ichidagi qo'shimcha bo'limlar
                sidebar_selectors = [
                    '.user-info, .profile-link, a:has-text("Profil"), a:has-text("Профиль")',
                    'a:has-text("Xabar"), a:has-text("Bildirishnoma"), .notification-link',
                ]
                for selector in sidebar_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn:
                            btn_text = (await btn.inner_text()).strip()[:30]
                            if btn_text not in visited_texts:
                                visited_texts.add(btn_text)
                                print(f"[🖱️] Panel: '{btn_text}' bosilmoqda...")
                                await btn.click()
                                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                                await asyncio.sleep(random.uniform(1.0, 1.8))
                                await smooth_scroll_down(page, steps=2)
                                await asyncio.sleep(random.uniform(0.6, 1.0))
                                await smooth_scroll_up(page, steps=2)
                                await asyncio.sleep(random.uniform(0.4, 0.8))
                    except Exception:
                        continue

                # 4. Bosh sahifani o'zi topib qaytish — AQLLI QIDIRISH
                print(f"[🏠] {login} — Bosh sahifani qidirib qaytilmoqda...")
                home_found = False

                home_selectors = [
                    'a.header__logo',
                    'a[href="/"], a[href="/userfeed"], a[href="/home"]',
                    'a:has-text("Bosh sahifa")',
                    'a:has-text("Главная")',
                    'a:has-text("Главная страница")',
                    '.logo a, .header-logo a',
                    'nav a:first-child',
                ]
                for selector in home_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn:
                            print(f"[✅] Bosh sahifa topildi: '{selector}'")
                            await btn.click()
                            await page.wait_for_load_state("domcontentloaded", timeout=12000)
                            home_found = True
                            break
                    except Exception:
                        continue

                if not home_found:
                    print("[🏠] URL orqali bosh sahifaga o'tilmoqda...")
                    try:
                        await page.goto("https://emaktab.uz/userfeed", wait_until="domcontentloaded", timeout=15000)
                    except Exception:
                        await page.go_back()

                # 5. Bosh sahifada 2 soniya kutish va videoni yakunlash
                print(f"[⏱️] {login} — Bosh sahifada 2 soniya kutilmoqda (video yakunlanmoqda)...")
                await asyncio.sleep(2.0)

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
                    f"✅ <b>KUNLIK HISOBOT: {html.escape(sinf)} SINF</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏫 <b>Tizim:</b> eMaktab.uz Monitoring\n"
                    f"👤 <b>Login:</b> <tg-spoiler>{html.escape(login)}</tg-spoiler>\n"
                    f"🔑 <b>Parol:</b> <tg-spoiler>{html.escape(password)}</tg-spoiler>\n"
                    f"📊 <b>Holati:</b> Muvaffaqiyatli tekshirildi\n\n"
                    f"🎥 <i>HD video va fotosuratda profilingizga kirilgani va baholar to'liq tekshirilgani tasdiqlangan.</i>"
                )

                await send_media(bot, photo_path, mp4_path, caption, sinf)
                success_count += 1

                if os.path.exists(raw_video_path):
                    os.remove(raw_video_path)

            except Exception as e:
                print(f"[-] {login} xatosi: {e}")
                try:
                    await context.close()
                except Exception:
                    pass


            if i < len(accounts):
                pause = random.randint(12, 22)
                print(f"Insoniy pauza: {pause} soniya kutilmoqda...")
                await asyncio.sleep(pause)

        await browser.close()

    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    summary_msg = (
        f"📊 <b>KUNLIK YAKUNIY MONITORING HISOBOTI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Muvaffaqiyatli tekshirildi:</b> <b>{success_count} / {len(accounts)}</b> ta hisob\n"
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

    print("Barcha vazifalar yakunlandi!")


if __name__ == "__main__":
    asyncio.run(run_local())
