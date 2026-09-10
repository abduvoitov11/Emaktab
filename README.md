# eMaktab Avtomatlashtirish Boti 🔐

Ushbu dastur Excel faylidagi foydalanuvchilar (o'quvchilar/ota-onalar) hisoblariga **eMaktab.uz** platformasi orqali avtomatik tarzda kiradi, 7 soniya sahifaning to'liq yuklanishini kutadi, profil skrinshotini oladi va ko'rsatilgan Telegram ID ga bot orqali yuboradi.

## 🚀 Ishga tushirish

Terminalda quyidagi buyruqni bering:
```bash
chmod +x ishga_tushirish.sh
./ishga_tushirish.sh
```

Skript birinchi marta ishga tushganda avtomatik virtual muhit (`venv`) yaratadi, kerakli kutubxonalarni o'rnatadi va avtomatlashtirish jarayonini boshlaydi.

## 📁 Fayllar tarkibi
- `local_runner.py` — Asosiy avtomatlashtirish kodi (Playwright + Telegram Bot)
- `ishga_tushirish.sh` — Dasturni qulay ishga tushiruvchi skript
- `Foydalanuvchilar_Royxati.xlsx` — Foydalanuvchilar hisoblari (Login, Parol, Telegram ID)
- `requirements.txt` — Kerakli kutubxonalar ro'yxati
