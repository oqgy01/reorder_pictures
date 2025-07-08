# gorsel_siralama.py
import time, argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────── GİRİŞ BİLGİLERİ ───────────
USER   = "mustafa_kod@haydigiy.com"
PASSWD = "123456"
# ────────────────────────────────────────

# ─────────── URL’LER ───────────
BASE_URL  = "https://www.siparis.haydigiy.com"
LOGIN_URL = f"{BASE_URL}/kullanici-giris/?ReturnUrl=%2Fadmin"
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
    opts.binary_location = "/usr/bin/chromium-browser"
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

def reorder_one(drv, product_id: int, src_pos: int):
    """Belirtilen bir ürünün görselini başa alır."""
    PROD_URL = f"{BASE_URL}/admin/product/edit/{product_id}"
    PIC_SEL  = "#productpictures-grid .picture-item"

    drv.get(PROD_URL)
    time.sleep(1)
    WebDriverWait(drv, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
    ).click()
    time.sleep(1)

    WebDriverWait(drv, 15).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, PIC_SEL)) >= src_pos + 1)
    WebDriverWait(drv, 15).until(
        lambda d: d.execute_script(
            "return $('#productpictures-grid').data('ui-sortable')!==undefined"))

    js = """
    var idx = arguments[0];
    var $list = $('#productpictures-grid');
    var $src  = $list.children('.picture-item').eq(idx);
    $src.insertBefore($list.children('.picture-item').eq(0));
    var s = $list.data('ui-sortable');
    s._trigger('update', null, {item: $src});
    s._trigger('stop');
    return 'ok';
    """
    if drv.execute_script(js, src_pos) != "ok":
        raise RuntimeError(f"sortable trigger failed ({product_id})")

    time.sleep(1)
    drv.find_element(By.CSS_SELECTOR, "button.btn-primary[name='save']").click()
    time.sleep(1)
    WebDriverWait(drv, 15).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading")))
    print(f"✅ {product_id}: {src_pos+1}. görsel başa alındı")
    time.sleep(1)

def main(batch_str: str):
    """Ana fonksiyon: Giriş yapar, döngü işlemlerini yürütür ve çıkar."""
    pairs = [
        (int(pid), int(pos) - 1)
        for pid, pos in (p.split(":") for p in batch_str.split(",") if p.strip())
    ]

    drv = init_driver()
    try:
        login(drv)
        for pid, pos in pairs:
            reorder_one(drv, pid, pos)
        print("\nTüm görsel sıralama işlemleri tamamlandı.")
    finally:
        drv.quit()
        print("Tarayıcı kapatıldı.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Belirtilen ürünlerin görsellerini yeniden sıralar.")
    parser.add_argument("--batch", required=True,
                        help='İşlenecek ürünler. Ör: "231321:2,235412:5" (virgülle ayrılır)')
    args = parser.parse_args()
    main(args.batch)
