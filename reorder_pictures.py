"""
reorder_pictures.py
-------------------
Selenium komutlarını uzaktaki (service container) Chrome’a gönderen,
parametreli ve colorama’sız tek dosya sürüm.

Workflow ortamı için:
  - Service container: selenium/standalone-chrome
  - Ortam değişkeni:   SELENIUM_REMOTE_URL="http://localhost:4444/wd/hub"
"""

import os
import time
import argparse
from selenium.webdriver import Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ───────────────  OTOMATİK GİRİŞ BİLGİLERİ  ───────────────
USER   = "mustafa_kod@haydigiy.com"
PASSWD = "123456"
# ───────────────────────────────────────────────────────────

def run(product_id: int, src_pos: int) -> None:
    """src_pos: 0-index (0 = ilk görsel, 2 = üçüncü görsel …)"""
    remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")

    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--headless=new")
    opts.add_argument("--incognito")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    drv = Remote(command_executor=remote_url, options=opts)

    BASE   = "https://www.siparis.haydigiy.com"
    LOGIN  = f"{BASE}/kullanici-giris/?ReturnUrl=%2Fadmin"
    PROD   = f"{BASE}/admin/product/edit/{product_id}"
    PICSEL = "#productpictures-grid .picture-item"

    try:
        # 1) Oturum aç
        drv.get(LOGIN)
        WebDriverWait(drv, 15).until(
            EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
        ).send_keys(USER)
        drv.find_element(By.NAME, "Password").send_keys(PASSWD)
        drv.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 2) Ürün sayfası → Resimler sekmesi
        WebDriverWait(drv, 15).until(EC.url_contains("/admin"))
        drv.get(PROD)
        WebDriverWait(drv, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
        ).click()

        # 3) Resimleri ve sortable nesnesini bekle
        WebDriverWait(drv, 15).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, PICSEL)) >= src_pos + 1)
        WebDriverWait(drv, 15).until(
            lambda d: d.execute_script(
                "return $('#productpictures-grid').data('ui-sortable')!==undefined"))

        # 4) İstenen görseli başa taşı
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
            raise RuntimeError("sortable trigger failed")

        # 5) Kaydet
        time.sleep(1.5)
        drv.find_element(By.CSS_SELECTOR,
                         "button.btn-primary[name='save']").click()
        WebDriverWait(drv, 15).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading")))

        print(f"✅ Ürün {product_id}: {src_pos+1}. görsel başa alındı.")
    finally:
        drv.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-id", required=True, type=int,
                        help="Ürün ID’si (URL sonundaki sayı)")
    parser.add_argument("--src-pos",    required=True, type=int,
                        help="Başa alınacak görsel sıra numarası (1-başlı)")
    args = parser.parse_args()
    run(args.product_id, args.src_pos - 1)  # 0-index’e çevir
