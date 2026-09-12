"""
AvtoEmaktab — Vercel Serverless Webhook Handler
Telegram bot uchun webhook endpoint (Vercel api/ papkasida joylashgan)
Har bir Telegram xabari shu endpoint ga POST so'rov sifatida keladi.
"""
import json
import os
import sys
import logging
import asyncio
import zoneinfo
from datetime import datetime
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


# ==================== KLAVIATURALAR ====================

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🌐 Rasmiy Sayt (Web App)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("💰 Tariflar va Narxlar", callback_data="btn_tariffs"),
            InlineKeyboardButton("🛡️ Anti-BAN Xavfsizligi", callback_data="btn_security")
        ],
        [
            InlineKeyboardButton("⏱️ 26 Soat Tejamkorlik", callback_data="btn_timesaver"),
            InlineKeyboardButton("📊 Tizim Holati", callback_data="btn_status")
        ],
        [InlineKeyboardButton("👨‍💻 Administratorga Yozish", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🌐 Rasmiy Sayt (Web App)", web_app=WebAppInfo(url=WEB_APP_URL)),
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
        f"<i>Quyidagi tugmalar orqali xizmat bilan to'liq tanishing yoki buyurtma bering:</i> ⬇️"
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


# ==================== UPDATE PROCESSOR ====================

async def process_update(update_data: dict):
    """Telegramdan kelgan JSON update ni qayta ishlaydi"""
    app = Application.builder().token(config.BOT_TOKEN).build()
    await app.initialize()

    update = Update.de_json(update_data, app.bot)

    # ---------- Xabarlar (message) ----------
    if update.message:
        msg = update.message
        text = msg.text or ""

        if text.startswith("/start") or text.startswith("/sayt"):
            user = update.effective_user
            name = user.first_name if user else "Hurmatli Ustoz"
            await msg.reply_text(
                text=get_welcome_text(name),
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif text.startswith("/tariflar"):
            await msg.reply_text(
                text=get_tariffs_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif text.startswith("/xavfsizlik"):
            await msg.reply_text(
                text=get_security_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif text.startswith("/status"):
            await msg.reply_text(
                text=get_status_text(),
                reply_markup=get_back_keyboard(),
                parse_mode=ParseMode.HTML
            )
        elif text.startswith("/admin"):
            admin_text = (
                "👨‍💻 <b>Bog'lanish va Qo'llab-quvvatlash:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Savollaringiz, takliflaringiz yoki yangi sinfni ulash bo'yicha "
                "to'g'ridan-to'g'ri administratorga murojaat qiling:\n\n"
                f"💬 <b>Telegram:</b> @{ADMIN_USERNAME}\n"
                f"📞 <b>Telefon:</b> {ADMIN_PHONE}\n"
                f"🌐 <b>Sayt:</b> {WEB_APP_URL}\n\n"
                "<i>Ish vaqti: 08:00 dan 21:00 gacha har kuni.</i>"
            )
            keyboard = [
                [
                    InlineKeyboardButton("💬 Adminga Yozish", url=f"https://t.me/{ADMIN_USERNAME}"),
                    InlineKeyboardButton("📞 Qo'ng'iroq", url="tel:+998940911219")
                ],
                [InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")]
            ]
            await msg.reply_text(
                text=admin_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

    # ---------- Inline tugmalar (callback_query) ----------
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data
        user = update.effective_user
        name = user.first_name if user else "Hurmatli Ustoz"

        if data == "btn_main_menu":
            await query.edit_message_text(
                text=get_welcome_text(name),
                reply_markup=get_main_keyboard(),
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

    await app.shutdown()


# ==================== VERCEL HTTP HANDLER ====================

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function uchun HTTP handler"""

    def log_message(self, format, *args):
        logger.info(format % args)

    def do_GET(self):
        """GET — Webhook tekshiruvi"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "AvtoEmaktab Webhook",
            "message": "Bot ishlayapti!"
        }).encode())

    def do_POST(self):
        """POST — Telegram Webhook xabari"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode("utf-8"))

            logger.info(f"Webhook update: {json.dumps(update_data)[:200]}")

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
            self.send_response(200)  # Telegram qayta urinmasin deb 200 qaytaramiz
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
