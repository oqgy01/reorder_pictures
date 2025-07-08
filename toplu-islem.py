# toplu_duzenleme.py
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ─────────── GİRİŞ BİLGİLERİ ───────────
USER   = "mustafa_kod@haydigiy.com"
PASSWD = "123456"
# ────────────────────────────────────────

# ─────────── URL’LER ───────────
BASE_URL     = "https://www.siparis.haydigiy.com"
LOGIN_URL    = f"{BASE_URL}/kullanici-giris/?ReturnUrl=%2Fadmin"
BULKEDIT_URL = f"{BASE_URL}/admin/product/bulkedit/"
# ───────────────────────────────

def init_driver():
    """Tarayıcıyı (WebDriver) başlatır ve ayarlarını yapar."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--incognito")
    opts.add_argument("--window-size=1920,1080")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    # GitHub runner’da Chromium yolu; lokalde gerekmez
    # opts.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(service=Service(), options=opts)

def login(drv):
    """Admin paneline giriş yapar."""
    drv.get(LOGIN_URL)
    time.sleep(1)
    WebDriverWait(drv, 15).until(
        EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
    ).send_keys(USER)
    time.sleep(1)
    drv.find_element(By.NAME, "Password").send_keys(PASSWD)
    time.sleep(1)
    drv.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    WebDriverWait(drv, 15).until(EC.url_contains("/admin"))
    print("Giriş yapıldı.")
    time.sleep(1)

def run_bulk_edits(drv):
    """Toplu etiket ve kategori güncelleme işlemlerini yapar."""
    drv.get(BULKEDIT_URL)
    print("Toplu düzenleme sayfasına gidildi.")
    time.sleep(1)

    # ─────────── İŞLEM 1: Etiket Güncelle ───────────
    print("İşlem 1: Etiket güncelleme başlıyor...")
    sel = Select(drv.find_element(By.ID, "SearchInCategoryIds"))
    time.sleep(1)
    sel.select_by_value("374")
    time.sleep(1)

    buttons = drv.find_elements(By.XPATH, "//span[@class='select2-selection__choice__remove']")
    if len(buttons) > 1:
        buttons[1].click()
        time.sleep(1)

    drv.find_element(By.ID, "search-products").click()
    time.sleep(1)

    chk = WebDriverWait(drv, 10).until(
        EC.presence_of_element_located((By.ID, "ProductTag_Update")))
    drv.execute_script("arguments[0].click();", chk)
    time.sleep(1)

    Select(drv.find_element(By.ID, "ProductTagId")).select_by_value("144")
    time.sleep(1)

    save_btn = WebDriverWait(drv, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "btn-primary")))
    drv.execute_script("arguments[0].click();", save_btn)
    time.sleep(2) # Kaydetme sonrası bekleme
    print("✅ Etiket güncelleme tamamlandı.")

    # ─────────── İŞLEM 2: Kategori Güncelle ───────────
    print("\nİşlem 2: Kategori güncelleme başlıyor...")
    sel = Select(drv.find_element(By.ID, "SearchInCategoryIds"))
    time.sleep(1)
    for cid in ["172", "440", "556", "614", "620"]:
        sel.select_by_value(cid)
        time.sleep(1)

    buttons = drv.find_elements(By.XPATH, "//span[@class='select2-selection__choice__remove']")
    if len(buttons) > 1:
        buttons[1].click()
        time.sleep(1)

    drv.find_element(By.ID, "search-products").click()
    time.sleep(1)
    drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

    chk = WebDriverWait(drv, 10).until(
        EC.presence_of_element_located((By.ID, "Category_Update")))
    drv.execute_script("arguments[0].click();", chk)
    time.sleep(1)

    Select(drv.find_element(By.ID, "CategoryId")).select_by_value("374")
    time.sleep(1)
    Select(drv.find_element(By.ID, "CategoryTransactionId")).select_by_value("1")
    time.sleep(1)

    save_btn = WebDriverWait(drv, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "btn-primary")))
    drv.execute_script("arguments[0].click();", save_btn)
    time.sleep(2) # Kaydetme sonrası bekleme
    print("✅ Kategori güncelleme tamamlandı.")


def main():
    """Ana fonksiyon: Giriş yapar, toplu işlemleri yürütür ve çıkar."""
    drv = init_driver()
    try:
        login(drv)
        run_bulk_edits(drv)
        print("\nTüm toplu düzenleme işlemleri tamamlandı.")
    finally:
        drv.quit()
        print("Tarayıcı kapatıldı.")


if __name__ == "__main__":
    main()
