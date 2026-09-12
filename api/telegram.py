"""
AvtoEmaktab — Vercel Serverless Webhook Handler & Billing / Teachers System
Telegram bot uchun webhook endpoint va ustozlar hisob tizimi.
"""
import json
import os
import sys
import logging
import asyncio
import zoneinfo
import urllib.request
import base64
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

# Vercel da loyiha root papkasini sys.path ga qo'shamiz
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application

import config

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WEB_APP_URL = "https://abduvoitov11.github.io/Emaktab/"
ADMIN_USERNAME = "Torabek_Abduvoitov"
ADMIN_PHONE = "+998 94 091 12 19"
ROOT_ID = int(config.ROOT_ID)

TEACHERS_FILE = os.path.join(os.path.dirname(__file__), "..", "teachers.json")
GITHUB_REPO = "abduvoitov11/Emaktab"
# Agar Vercel env'da bo'lsa GitHub PAT o'qiladi (faylni repoda avto-yangilash uchun)
GITHUB_PAT = os.getenv("GITHUB_PAT", "")


# ==================== DATA FUNCTIONS (TEACHERS) ====================

def load_teachers() -> dict:
    try:
        if os.path.exists(TEACHERS_FILE):
            with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading teachers: {e}")
    return {}


def save_teachers_locally(data: dict):
    try:
        with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving teachers locally: {e}")


def sync_teachers_to_github(data: dict):
    """Vercel serverless muhitida o'zgarishni GitHub repoga avtomat commit qilish"""
    if not GITHUB_PAT:
        return
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/teachers.json"
        headers = {
            "Authorization": f"token {GITHUB_PAT}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "AvtoEmaktab-Bot"
        }

        # Faylning hozirgi SHA raqamini olish
        req = urllib.request.Request(url, headers=headers)
        sha = None
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode())
                    sha = body.get("sha")
        except Exception:
            pass

        content_str = json.dumps(data, ensure_ascii=False, indent=2)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": "chore(data): auto-update teachers.json from telegram bot",
            "content": content_b64
        }
        if sha:
            payload["sha"] = sha

        data_bytes = json.dumps(payload).encode("utf-8")
        put_req = urllib.request.Request(url, data=data_bytes, headers=headers, method="PUT")
        with urllib.request.urlopen(put_req) as resp:
            logger.info(f"GitHub sync status: {resp.status}")
    except Exception as e:
        logger.error(f"GitHub sync error: {e}")


# ==================== KLAVIATURALAR ====================

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🌐 Rasmiy Sayt (Web App)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("👤 Mening Hisobim", callback_data="btn_cabinet"),
            InlineKeyboardButton("💰 Tariflar", callback_data="btn_tariffs")
        ],
        [
            InlineKeyboardButton("🛡️ Anti-BAN Xavfsizligi", callback_data="btn_security"),
            InlineKeyboardButton("📊 Tizim Holati", callback_data="btn_status")
        ],
        [
            InlineKeyboardButton("⏱️ 26 Soat Tejamkorlik", callback_data="btn_timesaver"),
            InlineKeyboardButton("👨‍💻 Bog'lanish", callback_data="btn_admin_info")
        ]
    ]
    if user_id == ROOT_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel (Ustozlar)", callback_data="btn_admin_teachers")])

    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🌐 Rasmiy Sayt", web_app=WebAppInfo(url=WEB_APP_URL)),
            InlineKeyboardButton(
                "✍️ Buyurtma Berish",
                url=f"https://t.me/{ADMIN_USERNAME}?text=Assalomu%20alaykum!%20AvtoEmaktab%20xizmati%20bo'yicha%20buyurtma%20bermoqchiman."
            )
        ],
        [InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== MATNLAR ====================

def get_welcome_text(user_first_name: str) -> str:
    return (
        f"🎓 <b>Assalomu alaykum, {user_first_name}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>AvtoEmaktab</b> — eMaktab.uz tizimi uchun aqlli avtomatlashtirish va monitoring rasmiy botiga xush kelibsiz!\n\n"
        f"⚡ <b>Xizmatimiz nima qiladi?</b>\n"
        f"Har kuni dars jadvalingiz tugashi bilanoq o'quvchilar profilingizga insoniy usulda kirilib, jurnallar tekshiriladi hamda shaxsiy Telegramingizga <b>1080p HD video va foto hisoboti</b> yetkaziladi.\n\n"
        f"🛡️ <b>Ishonchli Anti-BAN Himoyasi</b> (Tungi taqiq xavfsizligi)\n"
        f"⏱️ <b>Har oyda 26 soat</b> qimmatli vaqtingizni va asabingizni tejang!\n\n"
        f"<i>Quyidagi tugmalar orqali xizmat bilan to'liq tanishing:</i> ⬇️"
    )


def get_cabinet_text(user_id: int, user_first_name: str) -> str:
    teachers = load_teachers()
    uid_str = str(user_id)

    if uid_str in teachers:
        t = teachers[uid_str]
        name = t.get("name", user_first_name)
        cls = t.get("class", "Aniqlanmagan")
        cnt = t.get("students_count", 0)
        exp = t.get("expires_at", "—")
        status = t.get("status", "active")

        # Qolgan kunlarni hisoblash
        days_left_str = ""
        try:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            today = datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).date()
            delta = (exp_date - today).days
            if delta > 0:
                days_left_str = f"({delta} kun qoldi)"
                status_icon = "🟢 Faol"
            elif delta == 0:
                days_left_str = "(Bugun tugaydi)"
                status_icon = "🟡 Oxirgi kun"
            else:
                days_left_str = f"({abs(delta)} kun oldin tugagan)"
                status_icon = "🔴 To'xtatilgan"
        except Exception:
            status_icon = "🟢 Faol"

        return (
            f"👤 <b>Hurmatli {name} ustoz!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏫 <b>Sinfingiz:</b> {cls} ({cnt} nafar o'quvchi)\n"
            f"📊 <b>Tarif:</b> Sinf Rahbar\n"
            f"⚡ <b>Holati:</b> {status_icon}\n"
            f"📅 <b>Obuna tugash sanasi:</b> {exp} {days_left_str}\n\n"
            f"<i>Hisobingiz bo'yicha hisobotlar dars yakunida avtomatik yuboriladi.</i>"
        )
    else:
        return (
            f"👤 <b>Hurmatli {user_first_name}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Sizning hisobingiz hali tizimga ulanmagan.\n\n"
            f"💡 <b>Ulanish uchun:</b>\n"
            f"Administratorga murojaat qiling va o'z sinfingiz uchun xizmatni faollashtiring.\n\n"
            f"📞 <b>Admin:</b> @{ADMIN_USERNAME}\n"
            f"🆔 <b>Sizning Telegram ID:</b> <code>{user_id}</code>"
        )


def get_tariffs_text() -> str:
    return (
        "💰 <b>AvtoEmaktab Shaffof Tariflari:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⭐ <b>1. SINF RAHBAR (Eng Ommabop):</b>\n"
        "• Narxi: <b>1 000 so'm / 1 o'quvchiga</b>\n"
        "• O'quvchilar soni 50 tadan oshmasligi kerak\n"
        "• Masalan: 30 ta o'quvchi = <b>30 000 so'm / oyiga</b>\n"
        "• Kunlik 1080p HD Video + Rasm hisoboti\n"
        "• Ishonchli Anti-BAN va Tungi Taqiq himoyasi\n"
        "• <i>26 soat qimmatli vaqtingiz tejaladi!</i>\n\n"
        "🏫 <b>2. KATTA PAKET (2 - 5 ta sinf):</b>\n"
        "• Narxi: Kelishilgan narxda (Chegirma bilan)\n"
        "• Har bir ustozga faqat o'z sinfi hisoboti\n"
        "• Alohida guruhlangan Telegram albom\n\n"
        "🏢 <b>3. BUTUN MAKTAB:</b>\n"
        "• Narxi: <b>$240 / oyiga</b> (To'lov O'zR MB kursi bo'yicha so'mda)\n"
        "• 30 tagacha sinflar va ulardagi barcha ota-onalar\n"
        "• To'liq maktab monitoringi va nazorati"
    )


def get_security_text() -> str:
    return (
        "🛡️ <b>Anti-BAN va Tungi Taqiq Xavfsizlik Tizimi:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>21:45 - 07:00 Tungi Taqiq Himoyasi:</b>\n"
        "eMaktab.uz tizimi o'qituvchi va o'quvchilar tungi soatlarda kirmasligini nazorat qiladi. "
        "Shu sababli botimiz soat 21:45 dan 07:00 gacha har qanday kirishni avtomatik to'xtatadi.\n\n"
        "2️⃣ <b>Insoniy Klaviatura Simulyatsiyasi (Playwright):</b>\n"
        "Tizim harflarni robotdek bir zumda emas, inson barmoqlari tezligida (60-110ms tasodifiy kechikish bilan) kiritadi.\n\n"
        "3️⃣ <b>Maxfiylik va Shifrlash:</b>\n"
        "Sizning hisobingiz faqat o'zingizga tegishli bo'lib, uchinchi shaxslarga berilmaydi va "
        "faqat server lokal xotirasida xavfsiz ishlatiladi."
    )


def get_timesaver_text() -> str:
    return (
        "⏱️ <b>Har oyda 26 soat qanday tejaladi?</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Har bir sinf rahbari kuniga o'rtacha <b>50 daqiqa</b> vaqtini:\n"
        "• eMaktab saytiga kirish va yuklanishini kutishga;\n"
        "• 30+ o'quvchining baholari qo'yilganini tekshirishga;\n"
        "• Qolib ketgan darslarni qidirishga sarflaydi.\n\n"
        "📊 <b>Bir oyda:</b> 26 ish kuni × 1 soat = <b>26 soat!</b>\n"
        "Bu 3 dan ortiq to'liq ish kuni degani!\n\n"
        "💡 <b>AvtoEmaktab bilan:</b>\n"
        "Dars tugashi bilanoq shaxsiy Telegramingizga tayyor hisobot keladi. "
        "Siz bu vaqtni dam olishga, o'zingizga va oilangizga bag'ishlaysiz!"
    )


def get_status_text() -> str:
    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    now = datetime.now(tashkent_tz)
    is_curfew = config.is_curfew_time(now)
    if is_curfew:
        status_badge = "🛑 <b>TUNGI TAQIQ FAOL</b> (Dam olish rejimi)"
        status_desc = "21:45 - 07:00 oralig'ida login qilish xavfsizlik yuzasidan to'xtatilgan."
    else:
        status_badge = "🟢 <b>KUNDUZI MONITORING FAOL</b>"
        status_desc = "Jadvallar bo'yicha hisobotlar qabul qilinmoqda."
    return (
        f"📊 <b>AvtoEmaktab Tizim Monitoringi:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Hozirgi Toshkent vaqti: <b>{now.strftime('%H:%M:%S')}</b>\n"
        f"📅 Sana: <b>{now.strftime('%Y-%m-%d')}</b>\n"
        f"⚡ Holat: {status_badge}\n\n"
        f"ℹ️ {status_desc}\n\n"
        f"<i>Xizmat serverlari 24/7 rejimida uzluksiz ishlamoqda.</i>"
    )


def get_admin_info_text() -> str:
    return (
        "👨‍💻 <b>Bog'lanish va Qo'llab-quvvatlash:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Savollaringiz, takliflaringiz yoki yangi sinfni ulash bo'yicha "
        "to'g'ridan-to'g'ri administratorga murojaat qiling:\n\n"
        f"💬 <b>Telegram:</b> @{ADMIN_USERNAME}\n"
        f"📞 <b>Telefon:</b> {ADMIN_PHONE}\n"
        f"🌐 <b>Sayt:</b> {WEB_APP_URL}\n\n"
        "<i>Ish vaqti: 08:00 dan 21:00 gacha har kuni.</i>"
    )


# ==================== UPDATE PROCESSOR ====================

async def process_update(update_data: dict):
    """Telegramdan kelgan JSON update ni qayta ishlaydi"""
    app = Application.builder().token(config.BOT_TOKEN).build()
    await app.initialize()

    update = Update.de_json(update_data, app.bot)

    # ---------- Xabarlar (message) ----------
    if update.message:
        msg = update.message
        text = (msg.text or "").strip()
        user = update.effective_user
        user_id = user.id if user else 0
        name = user.first_name if user else "Hurmatli Ustoz"

        # 1. /start yoki /sayt
        if text.startswith("/start") or text.startswith("/sayt"):
            await msg.reply_text(
                text=get_welcome_text(name),
                reply_markup=get_main_keyboard(user_id),
                parse_mode=ParseMode.HTML
            )

        # 2. /kabinet
        elif text.startswith("/kabinet"):
            await msg.reply_text(
                text=get_cabinet_text(user_id, name),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )

        # 3. /tariflar
        elif text.startswith("/tariflar"):
            await msg.reply_text(
                text=get_tariffs_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )

        # 4. /xavfsizlik
        elif text.startswith("/xavfsizlik"):
            await msg.reply_text(
                text=get_security_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )

        # 5. /status
        elif text.startswith("/status"):
            await msg.reply_text(
                text=get_status_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )

        # 6. /admin
        elif text.startswith("/admin"):
            keyboard = [
                [InlineKeyboardButton("💬 Adminga Yozish", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")]
            ]
            await msg.reply_text(
                text=get_admin_info_text(),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

        # ================= QAT'IY XAVFSIZLIK VA ADMIN BUYRUQLARI =================
        elif any(text.startswith(cmd) for cmd in ["/qosh", "/uzaytir", "/ochir", "/ustozlar", "/admin_panel"]):
            # Agar buyruqni yozgan odam ROOT bo'lmasa -> DARHOL BLOK VA ROOT GA ALERT!
            if user_id != ROOT_ID:
                uname_str = f"@{user.username}" if (user and user.username) else "Mavjud emas"
                now_str = datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).strftime('%Y-%m-%d %H:%M:%S')
                
                # Begona shaxsga ogohlantirish
                await msg.reply_text(
                    "⛔ <b>RUXSAT ETILMAGAN AMAL!</b>
"
                    "Sizda administratorlik huquqi yo'q. Ushbu xatti-harakat va sizning ma'lumotlaringiz xavfsizlik jurnaliga qayd etildi.",
                    parse_mode=ParseMode.HTML
                )
                
                # ROOT ga xavfsizlik hisoboti
                alert_text = (
                    f"🚨 <b>XAVFSIZLIK OGOHLANTIRISHI!</b>
"
                    f"━━━━━━━━━━━━━━━━━━━━━
"
                    f"Begona foydalanuvchi admin buyrug'ini ishlatishga urindi:

"
                    f"👤 <b>Ism:</b> {name}
"
                    f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>
"
                    f"💬 <b>Username:</b> {uname_str}
"
                    f"⌨️ <b>Yozgan buyrug'i:</b> <code>{text}</code>
"
                    f"⏱ <b>Vaqt:</b> {now_str}

"
                    f"🛑 <i>Tizim tomonidan avtomatik ravishda to'xtatildi.</i>"
                )
                try:
                    await app.bot.send_message(chat_id=ROOT_ID, text=alert_text, parse_mode=ParseMode.HTML)
                except Exception as ex:
                    logger.error(f"Failed to alert root: {ex}")
                
                await app.shutdown()
                return

            # Agar bu haqiqiy ROOT bo'lsa:

            # 7. /qosh <TG_ID> <Ism> <Sinf> <Oquvchilar_Soni> <Kun>
            if text.startswith("/qosh"):
                parts = text.split()
                if len(parts) >= 6:
                    target_id = parts[1]
                    t_name = parts[2]
                    t_class = parts[3]
                    try:
                        t_count = int(parts[4])
                        days = int(parts[5])
                    except ValueError:
                        await msg.reply_text("❌ Xato: O'quvchilar soni va kunlar butun son bo'lishi kerak.")
                        await app.shutdown()
                        return

                    today = datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).date()
                    exp_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")

                    teachers = load_teachers()
                    teachers[target_id] = {
                        "name": t_name,
                        "class": t_class,
                        "students_count": t_count,
                        "expires_at": exp_date,
                        "status": "active"
                    }
                    save_teachers_locally(teachers)
                    sync_teachers_to_github(teachers)

                    res_text = (
                        f"✅ <b>Yangi ustoz hisobi qo'shildi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 Ism: <b>{t_name}</b>\n"
                        f"🏫 Sinf: <b>{t_class}</b> ({t_count} o'quvchi)\n"
                        f"🆔 Telegram ID: <code>{target_id}</code>\n"
                        f"📅 Muddat: <b>{exp_date}</b> ({days} kun)\n"
                        f"⚡ Holat: 🟢 Faol"
                    )
                    await msg.reply_text(res_text, parse_mode=ParseMode.HTML)

                    # Ustozga avto xabar
                    try:
                        await app.bot.send_message(
                            chat_id=int(target_id),
                            text=(
                                f"🎉 <b>Assalomu alaykum, {t_name} ustoz!</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━\n"
                                f"Sizning <b>{t_class}</b> sinfingiz uchun AvtoEmaktab monitoring xizmati faollashtirildi!\n\n"
                                f"📅 <b>Amal qilish muddati:</b> {exp_date} gacha ({days} kun)\n\n"
                                f"Hisobingizni tekshirish uchun: /kabinet"
                            ),
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as ex:
                        logger.warning(f"Could not notify teacher {target_id}: {ex}")

                else:
                    help_qosh = (
                        "ℹ️ <b>Yangi hisob qo'shish formati:</b>\n"
                        "<code>/qosh &lt;TG_ID&gt; &lt;Ism&gt; &lt;Sinf&gt; &lt;Oquvchilar_Soni&gt; &lt;Kun&gt;</code>\n\n"
                        "<b>Misol:</b>\n"
                        "<code>/qosh 896459615 Zuhra 9-B 34 30</code>"
                    )
                    await msg.reply_text(help_qosh, parse_mode=ParseMode.HTML)

            # 8. /uzaytir <TG_ID> <Kun>
            elif text.startswith("/uzaytir"):
                parts = text.split()
                if len(parts) >= 3:
                    target_id = parts[1]
                    try:
                        days = int(parts[2])
                    except ValueError:
                        await msg.reply_text("❌ Xato: Kun butun son bo'lishi kerak.")
                        await app.shutdown()
                        return

                    teachers = load_teachers()
                    if target_id in teachers:
                        t = teachers[target_id]
                        curr_exp = t.get("expires_at", "")
                        try:
                            base_date = max(
                                datetime.strptime(curr_exp, "%Y-%m-%d").date(),
                                datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).date()
                            )
                        except Exception:
                            base_date = datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).date()

                        new_exp = (base_date + timedelta(days=days)).strftime("%Y-%m-%d")
                        t["expires_at"] = new_exp
                        t["status"] = "active"

                        save_teachers_locally(teachers)
                        sync_teachers_to_github(teachers)

                        await msg.reply_text(
                            f"✅ <b>{t.get('name')} ustozning obunasi uzaytirildi!</b>\n"
                            f"Yangi tugash sanasi: <b>{new_exp}</b> (+{days} kun)",
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await msg.reply_text(f"❌ Telegram ID: {target_id} topilmadi.")
                else:
                    await msg.reply_text("Format: <code>/uzaytir &lt;TG_ID&gt; &lt;Kun&gt;</code>", parse_mode=ParseMode.HTML)

            # 9. /ustozlar
            elif text.startswith("/ustozlar"):
                teachers = load_teachers()
                if not teachers:
                    await msg.reply_text("Baza bo'sh.")
                else:
                    lines = ["📋 <b>Ulangan Ustozlar Ro'yxati:</b>\n━━━━━━━━━━━━━━━━━━━━━"]
                    for uid, t in teachers.items():
                        lines.append(
                            f"👤 <b>{t.get('name')}</b> ({t.get('class')}) — {t.get('students_count')} o'quvchi\n"
                            f"🆔 <code>{uid}</code> | 📅 {t.get('expires_at')}"
                        )
                    lines.append("\n<i>Yangi qo'shish: /qosh | Uzaytirish: /uzaytir</i>")
                    await msg.reply_text("\n\n".join(lines), parse_mode=ParseMode.HTML)

            # 10. /ochir <TG_ID>
            elif text.startswith("/ochir"):
                parts = text.split()
                if len(parts) >= 2:
                    target_id = parts[1]
                    teachers = load_teachers()
                    if target_id in teachers:
                        removed = teachers.pop(target_id)
                        save_teachers_locally(teachers)
                        sync_teachers_to_github(teachers)
                        await msg.reply_text(f"🗑️ <b>{removed.get('name')}</b> ro'yxatdan o'chirildi.", parse_mode=ParseMode.HTML)
                    else:
                        await msg.reply_text(f"❌ ID {target_id} topilmadi.")

    # ---------- Inline tugmalar (callback_query) ----------
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user
        user_id = user.id if user else 0
        name = user.first_name if user else "Hurmatli Ustoz"

        if data == "btn_main_menu":
            await query.edit_message_text(
                text=get_welcome_text(name),
                reply_markup=get_main_keyboard(user_id),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_cabinet":
            await query.edit_message_text(
                text=get_cabinet_text(user_id, name),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_tariffs":
            await query.edit_message_text(
                text=get_tariffs_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_security":
            await query.edit_message_text(
                text=get_security_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_timesaver":
            await query.edit_message_text(
                text=get_timesaver_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_status":
            await query.edit_message_text(
                text=get_status_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_admin_info":
            keyboard = [
                [InlineKeyboardButton("💬 Adminga Yozish", url=f"https://t.me/{ADMIN_USERNAME}")],
                [InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")]
            ]
            await query.edit_message_text(
                text=get_admin_info_text(),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        elif data == "btn_admin_teachers":
            if user_id != ROOT_ID:
                uname_str = f"@{user.username}" if (user and user.username) else "Mavjud emas"
                now_str = datetime.now(zoneinfo.ZoneInfo("Asia/Tashkent")).strftime('%Y-%m-%d %H:%M:%S')
                alert_text = (
                    f"🚨 <b>XAVFSIZLIK: CALLBACK ATTACK!</b>
"
                    f"Begona foydalanuvchi Admin Panel tugmasini simulyatsiya qilib bosishga urindi!
"
                    f"👤 Ism: {name} (ID: <code>{user_id}</code>, {uname_str})
"
                    f"⏱ Vaqt: {now_str}"
                )
                try:
                    await app.bot.send_message(chat_id=ROOT_ID, text=alert_text, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                await query.answer("⛔ Ruxsat yo'q!", show_alert=True)
                await app.shutdown()
                return
            teachers = load_teachers()
            lines = ["📋 <b>Ulangan Ustozlar Ro'yxati:</b>\n━━━━━━━━━━━━━━━━━━━━━"]
            for uid, t in teachers.items():
                lines.append(
                    f"👤 <b>{t.get('name')}</b> ({t.get('class')}) — {t.get('students_count')} o'quvchi\n"
                    f"🆔 <code>{uid}</code> | 📅 {t.get('expires_at')}"
                )
            lines.append("\n<i>Yangi qo'shish: /qosh\nObunani uzaytirish: /uzaytir</i>")
            await query.edit_message_text(
                text="\n\n".join(lines),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )

    await app.shutdown()


# ==================== VERCEL HTTP HANDLER ====================

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(format % args)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "AvtoEmaktab Webhook & Billing",
            "message": "Bot ishlayapti!"
        }).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode("utf-8"))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_update(update_data))
            finally:
                loop.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as e:
            logger.error(f"Webhook xato: {e}", exc_info=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
