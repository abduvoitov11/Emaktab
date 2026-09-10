# eMaktab Smart Automation (eMaktab Avtomatlashtirish Tizimi) 🔐

Ushbu loyiha **eMaktab.uz** (kundalik.com) platformasiga o'quvchilar hisoblari orqali avtomatik kirish, ko'rinish va faollikni ta'minlash, 7 soniya to'liq yuklanishni kutib skrinshot olish va natijalarni Telegram orqali mas'ullarga yetkazish uchun mo'ljallangan avtonom tizimdir.

---

## 🏛 Tizim Ierarxiyasi va Huquqlar

1. 👑 **Bosh Administrator (`6291811673`):**
   * Tizimning to'liq egasi. Barcha sinflar (hozirgi 9-B va kelajakda qo'shiladigan boshqa barcha sinflar)dan olingan barcha skrinshot va hisobotlar doimiy keladi.
2. 👩‍🏫 **Zuhra ustoz (`896459615`):**
   * **9 - B sinf** rahbari. Unga faqat va faqat o'zining 9-B sinf o'quvchilarining skrinshotlari boradi.
3. 👩‍🏫 **Muhayyo ustoz (`624782674`):**
   * Yangi sinf rahbari (zaxirada). Kelgusida yangi sinf qo'shilishi bilan faqat o'z sinfining hisobotlarini oladi.

---

## 📩 Xabarlar formati (Spoiler):
Har bir skrinshot tagida login va parol Telegram'ning nuqtali xiralashtirilgan pardasi (`<tg-spoiler>`) bilan yopiladi. Ustiga bosilganda ochiladi:
```text
🏫 Sinf: 9-B
👤 Login: <tg-spoiler>login</tg-spoiler>
🔑 Parol: <tg-spoiler>parol</tg-spoiler>
✅ Holat: Muvaffaqiyatli kirildi
```

---

## ⏰ Haftalik Ish Jadvali va Cheklovlar (GitHub Actions)

* **Kunlik qat'iy me'yor:** 1 kunda **11 tadan oshiq** hisobga kirilmaydi (har kuni 6–9 tadan hisob).
* **Foydalanuvchi limiti:** Bitta hisobga bir haftada **maksimal 4 martagacha** kirish mumkin (LIMIT: 4).
* **Haftalik qamrov:** Dushanbadan Jumagacha barcha 32 ta o'quvchining har biriga kamida 1 marta (va 2–4 martagacha) kirib chiqiladi.
* **Juma kuni:** Qat'iy qoida bo'yicha **soat 10:00 gacha** hamma narsa to'liq yakunlanadi (08:30 da ishga tushadi).
* **Anti-BAN mexanizmi:**
  * Kunlik ishga tushish vaqtlari har xil soatlarda.
  * Skript boshida 1–5 daqiqalik tasodifiy kutish (jitter).
  * O'quvchilar hisoblari orasida 20–45 soniyalik insoniy tanaffus.

---

## 🚀 Ishga tushirish usullari

### 1. GitHub Actions (Avtomatik — Bulutda)
Kompyuteringiz o'chiq bo'lsa ham GitHub serverlarida avtomatik ishlaydi. 
* Shuningdek, GitHub saytidan **Actions -> eMaktab Smart Scheduler -> Run workflow** tugmasini bosib istalgan payt qo'lda ham tekshirish mumkin.

### 2. Mahalliy kompyuterda (Local)
Agar noutbukingizda qo'lda ishlatmoqchi bo'lsangiz:
```bash
chmod +x ishga_tushirish.sh
./ishga_tushirish.sh
```

---

## 📁 Fayllar tarkibi
- `config.py` — Foydalanuvchilar ierarxiyasi (Admin, Zuhra, Muhayyo), sozlamalar va limitlar
- `cron_runner.py` — Haftalik aqlli taqsimot, anti-ban va ko'p sinfli yuboruvchi asosiy algoritm
- `local_runner.py` — Mahalliy kompyuterda sinov uchun skript
- `ishga_tushirish.sh` — Mahalliy tezkor ishga tushiruvchi
- `Foydalanuvchilar_Royxati.xlsx` — Sinf, Login, Parol va Telegram ID ro'yxati
- `.github/workflows/emaktab_cron.yml` — GitHub Actions avtonom jadvali
- `requirements.txt` — Kerakli kutubxonalar (`playwright`, `openpyxl`, `python-telegram-bot`)
