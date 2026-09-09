import os
import asyncio
import openpyxl
from playwright.async_api import async_playwright
from telegram import Bot


EXCEL_FILE = "/home/torabek/Downloads/Foydalanuvchilar_Royxati.xlsx"
BOT_TOKEN = "8375587042:AAGfQNUc_3LzpTHBIPsyNHxw8AHfFV9CyXU" # O'zgartirishingiz kerak!
LOGIN_URL = "https://login.emaktab.uz/"
SCREENSHOTS_DIR = "/home/torabek/Desktop/Emaktab_Local/screenshots"

async def run_local_automation():

    bot = Bot(token=BOT_TOKEN)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    print("Excel fayldan ma'lumotlar o'qilmoqda...")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    accounts = []
    # 2-qatordan boshlab o'qish (1-qator sarlavha)
    for row in range(2, ws.max_row + 1):
        login = ws.cell(row=row, column=2).value
        password = ws.cell(row=row, column=3).value
        chat_id = ws.cell(row=row, column=4).value
        
        if login and password and chat_id:
            accounts.append({
                "login": str(login).strip(),
                "password": str(password).strip(),
                "chat_id": int(chat_id)
            })
    
    print(f"Jami {len(accounts)} ta hisob topildi. Dastur ishga tushmoqda...")

    async with async_playwright() as p:
        # Brauzerni ishga tushirish
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        for acc in accounts:
            login = acc['login']
            password = acc['password']
            chat_id = acc['chat_id']
            print(f"[*] {login} hisobiga kirishga urinish...")

            try:
                await page.goto(LOGIN_URL, wait_until="domcontentloaded")
                await page.wait_for_selector('input[name="login"]', timeout=10000)
                await page.fill('input[name="login"]', login)
                await page.fill('input[name="password"]', password)
                
                # Kirish tugmasini bosish
                await page.click('button[type="submit"], input[type="submit"]')
                
                # Tizimga kirishni tasdiqlash uchun kutish
                try:
                    await page.wait_for_selector('text="Chiqish"', timeout=10000)
                except:
                    print(f"[!] {login} uchun 'Chiqish' so'zi topilmadi, baribir rasmga olinadi.")

                print(f"[~] {login} uchun sahifa to`liq yuklanishini 7 soniya kutmoqdamiz...")
                await page.wait_for_timeout(7000)
                # Skrinshot olish
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{login}.png")
                await page.screenshot(path=screenshot_path)
                
                print(f"[+] {login} uchun rasm olindi, Telegramga yuborilmoqda...")
                with open(screenshot_path, 'rb') as photo:
                    await bot.send_photo(chat_id=chat_id, photo=photo, caption=f"eMaktab: {login} profiliga muvaffaqiyatli kirildi.")
                
                # Keyingi hisob uchun brauzerni tozalash
                await page.context.clear_cookies()

            except Exception as e:
                print(f"[-] {login} uchun xatolik yuz berdi: {e}")

        await browser.close()
    print("Barcha vazifalar yakunlandi!")

if __name__ == "__main__":
    asyncio.run(run_local_automation())
