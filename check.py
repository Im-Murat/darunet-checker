import os
import requests
from bs4 import BeautifulSoup
import cloudscraper

# 🔹 آدرس محصول
url = "https://darunet.com/product/فلکس-7-یوروویتال/"

# 🔹 تنظیمات تلگرام (از GitHub Secrets)
bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(msg):
    """ارسال پیام به تلگرام"""
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": msg}
    try:
        requests.post(telegram_url, data=params, timeout=10)
    except Exception as e:
        print("⚠️ خطا در ارسال به تلگرام:", e)

def fetch_page():
    """اول با cloudscraper تست می‌کنیم، اگر نشد با requests"""
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=15)
        if response.status_code == 200 and "دارونت" in response.text:
            return response.text
    except Exception as e:
        print("⚠️ cloudscraper جواب نداد:", e)

    # 🔄 Fallback به requests با هدر مرورگر واقعی
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print("❌ requests هم جواب نداد:", e)

    return None

def check_drug():
    """بررسی وضعیت دارو"""
    html = fetch_page()
    if not html:
        return {"available": False, "stock": "مشکل در دریافت صفحه"}

    soup = BeautifulSoup(html, "html.parser")

    # بررسی موجودی
    stock_tag = soup.select_one("p.stock.out-of-stock")
    if stock_tag:
        return {"available": False, "stock": stock_tag.get_text(strip=True)}

    # اگر موجود بود
    price_tag = soup.select_one("ins .woocommerce-Price-amount bdi")
    old_price_tag = soup.select_one("del .woocommerce-Price-amount bdi")

    price = price_tag.get_text(strip=True) if price_tag else "نامشخص"
    old_price = old_price_tag.get_text(strip=True) if old_price_tag else "ندارد"

    return {"available": True, "price": price, "old_price": old_price}

if __name__ == "__main__":
    data = check_drug()
    if data["available"]:
        msg = (
            f"✅ دارو موجود شد!\n"
            f"💰 قیمت: {data['price']}\n"
            f"💵 قیمت اصلی: {data['old_price']}"
        )
        send_telegram(msg)
    else:
        print("❌", data["stock"])

