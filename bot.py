import logging
import zoneinfo
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

import config

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WEB_APP_URL = "https://abduvoitov11.github.io/Emaktab/"
ADMIN_USERNAME = "Torabek_Abduvoitov"
ADMIN_PHONE = "+998 94 091 12 19"


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Rasmiy Sayt (Web App)",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton("💰 Tariflar va Narxlar", callback_data="btn_tariffs"),
            InlineKeyboardButton("🛡️ Anti-BAN Xavfsizligi", callback_data="btn_security")
        ],
        [
            InlineKeyboardButton("⏱️ 26 Soat Tejamkorlik", callback_data="btn_timesaver"),
            InlineKeyboardButton("📊 Tizim Holati", callback_data="btn_status")
        ],
        [
            InlineKeyboardButton(
                "👨‍💻 Administratorga Yozish",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "🌐 Rasmiy Sayt (Web App)",
                web_app=WebAppInfo(url=WEB_APP_URL)
            ),
            InlineKeyboardButton(
                "✍️ Buyurtma Berish",
                url=f"https://t.me/{ADMIN_USERNAME}?text=Assalomu%20alaykum!%20AvtoEmaktab%20xizmati%20bo'yicha%20buyurtma%20bermoqchiman."
            )
        ],
        [
            InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user else "Hurmatli Ustoz"
    await update.message.reply_text(
        text=get_welcome_text(name),
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def tariflar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
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
    await update.message.reply_text(
        text=text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def xavfsizlik_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡️ <b>Anti-BAN va Tungi Taqiq Xavfsizlik Tizimi:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ <b>21:45 - 07:00 Tungi Taqiq Himoyasi:</b>\n"
        "eMaktab.uz tizimi o'qituvchi va o'quvchilar tungi soatlarda kirmasligini nazorat qiladi. Shu sababli botimiz soat 21:45 dan 07:00 gacha har qanday kirishni avtomatik to'xtatadi.\n\n"
        "2️⃣ <b>Insoniy Klaviatura Simulyatsiyasi (Playwright):</b>\n"
        "Tizim harflarni robotdek bir zumda emas, inson barmoqlari tezligida (60-110ms tasodifiy kechikish bilan) kiritadi.\n\n"
        "3️⃣ <b>Maxfiylik va Shifrlash:</b>\n"
        "Sizning hisobingiz faqat o'zingizga tegishli bo'lib, uchinchi shaxslarga berilmaydi va faqat server lokal xotirasida xavfsiz ishlatiladi."
    )
    await update.message.reply_text(
        text=text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    now = datetime.now(tashkent_tz)
    is_curfew = config.is_curfew_time(now)

    if is_curfew:
        status_badge = "🛑 <b>TUNGI TAQIQ FAOL</b> (Dam olish rejimi)"
        status_desc = "21:45 - 07:00 oralig'ida login qilish xavfsizlik yuzasidan to'xtatilgan."
    else:
        status_badge = "🟢 <b>KUNDUZGI MONITORING FAOL</b>"
        status_desc = "Jadvallar bo'yicha hisobotlar qabul qilinmoqda."

    text = (
        f"📊 <b>AvtoEmaktab Tizim Monitoringi:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Hozirgi Toshkent vaqti: <b>{now.strftime('%H:%M:%S')}</b>\n"
        f"📅 Sana: <b>{now.strftime('%Y-%m-%d')}</b>\n"
        f"⚡ Holat: {status_badge}\n\n"
        f"ℹ️ {status_desc}\n\n"
        f"<i>Xizmat serverlari 24/7 rejimida uzluksiz ishlamoqda.</i>"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=get_back_keyboard(),
        parse_mode=ParseMode.HTML
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👨‍💻 <b>Bog'lanish va Qo'llab-quvvatlash:</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Savollaringiz, takliflaringiz yoki yangi sinfni ulash bo'yicha to'g'ridan-to'g'ri administratorga murojaat qiling:\n\n"
        f"💬 <b>Telegram:</b> @{ADMIN_USERNAME}\n"
        f"📞 <b>Telefon:</b> {ADMIN_PHONE}\n"
        f"🌐 <b>Sayt:</b> {WEB_APP_URL}\n\n"
        "<i>Ish vaqti: 08:00 dan 21:00 gacha har kuni.</i>"
    )
    keyboard = [
        [
            InlineKeyboardButton("💬 Adminga Yozish", url=f"https://t.me/{ADMIN_USERNAME}")
        ],
        [
            InlineKeyboardButton("◀️ Asosiy Menyu", callback_data="btn_main_menu")
        ]
    ]
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = (
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
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.HTML
        )
    elif data == "btn_security":
        text = (
            "🛡️ <b>Anti-BAN va Tungi Taqiq Xavfsizlik Tizimi:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ <b>21:45 - 07:00 Tungi Taqiq Himoyasi:</b>\n"
            "eMaktab.uz tizimi o'qituvchi va o'quvchilar tungi soatlarda kirmasligini nazorat qiladi. Shu sababli botimiz soat 21:45 dan 07:00 gacha har qanday kirishni avtomatik to'xtatadi.\n\n"
            "2️⃣ <b>Insoniy Klaviatura Simulyatsiyasi (Playwright):</b>\n"
            "Tizim harflarni robotdek bir zumda emas, inson barmoqlari tezligida (60-110ms tasodifiy kechikish bilan) kiritadi.\n\n"
            "3️⃣ <b>Maxfiylik va Shifrlash:</b>\n"
            "Sizning hisobingiz faqat o'zingizga tegishli bo'lib, uchinchi shaxslarga berilmaydi va faqat server lokal xotirasida xavfsiz ishlatiladi."
        )
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.HTML
        )
    elif data == "btn_timesaver":
        text = (
            "⏱️ <b>Har oyda 26 soat qanday tejaladi?</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Har bir sinf rahbari kuniga o'rtacha <b>50 daqiqa</b> vaqtini:\n"
            "• eMaktab saytiga kirish va yuklanishini kutishga;\n"
            "• 30+ o'quvchining baholari qo'yilganini tekshirishga;\n"
            "• Qolib ketgan darslarni qidirishga sarflaydi.\n\n"
            "📊 <b>Bir oyda:</b> 26 ish kuni × 1 soat = <b>26 soat!</b>\n"
            "Bu 3 dan ortiq to'liq ish kuni degani!\n\n"
            "💡 <b>AvtoEmaktab bilan:</b>\n"
            "Dars tugashi bilanoq shaxsiy Telegramingizga tayyor hisobot keladi. Siz bu vaqtni dam olishga, o'zingizga va oilangizga bag'ishlaysiz!"
        )
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.HTML
        )
    elif data == "btn_status":
        tashkent_tz = zoneinfo.ZoneInfo("Asia/Tashkent")
        now = datetime.now(tashkent_tz)
        is_curfew = config.is_curfew_time(now)

        if is_curfew:
            status_badge = "🛑 <b>TUNGI TAQIQ FAOL</b> (Dam olish rejimi)"
            status_desc = "21:45 - 07:00 oralig'ida login qilish xavfsizlik yuzasidan to'xtatilgan."
        else:
            status_badge = "🟢 <b>KUNDUZGI MONITORING FAOL</b>"
            status_desc = "Jadvallar bo'yicha hisobotlar qabul qilinmoqda."

        text = (
            f"📊 <b>AvtoEmaktab Tizim Monitoringi:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱ Hozirgi Toshkent vaqti: <b>{now.strftime('%H:%M:%S')}</b>\n"
            f"📅 Sana: <b>{now.strftime('%Y-%m-%d')}</b>\n"
            f"⚡ Holat: {status_badge}\n\n"
            f"ℹ️ {status_desc}\n\n"
            f"<i>Xizmat serverlari 24/7 rejimida uzluksiz ishlamoqda.</i>"
        )
        await query.edit_message_text(
            text=text,
            reply_markup=get_back_keyboard(),
            parse_mode=ParseMode.HTML
        )


def main():
    logger.info("AvtoEmaktab Telegram boti ishga tushirilmoqda...")
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("tariflar", tariflar_command))
    app.add_handler(CommandHandler("xavfsizlik", xavfsizlik_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("sayt", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot tayyor! Polling boshlanmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
