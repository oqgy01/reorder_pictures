"""
Liste parametresiyle toplu sıralama.

Çağrı örneği
    python reorder_pictures.py --batch "231321:2,235412:5"
"""

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


def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--incognito")
    opts.add_argument("--window-size=1920,1080")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    # GitHub runner’daki Chromium binari
    opts.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(service=Service(), options=opts)


def login(drv):
    BASE  = "https://www.siparis.haydigiy.com"
    LOGIN = f"{BASE}/kullanici-giris/?ReturnUrl=%2Fadmin"

    drv.get(LOGIN)
    WebDriverWait(drv, 15).until(
        EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
    ).send_keys(USER)
    drv.find_element(By.NAME, "Password").send_keys(PASSWD)
    drv.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(drv, 15).until(EC.url_contains("/admin"))


def reorder_one(drv, product_id: int, src_pos: int):
    BASE   = "https://www.siparis.haydigiy.com"
    PROD   = f"{BASE}/admin/product/edit/{product_id}"
    PICSEL = "#productpictures-grid .picture-item"

    drv.get(PROD)
    WebDriverWait(drv, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
    ).click()

    WebDriverWait(drv, 15).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, PICSEL)) >= src_pos + 1
    )
    WebDriverWait(drv, 15).until(
        lambda d: d.execute_script(
            "return $('#productpictures-grid').data('ui-sortable')!==undefined")
    )

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
        raise RuntimeError(`sortable trigger failed (${product_id})`)

    time.sleep(1.0)
    drv.find_element(By.CSS_SELECTOR, "button.btn-primary[name='save']").click()
    WebDriverWait(drv, 15).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading"))
    )
    print(f"✅ {product_id}: {src_pos+1}. görsel başa alındı")


def main(batch_str: str):
    # "231321:2,235412:5"  →  [(231321,1), (235412,4)]
    pairs = [
        (int(pid), int(pos) - 1)
        for pid, pos in (p.split(":") for p in batch_str.split(",") if p.strip())
    ]

    drv = init_driver()
    try:
        login(drv)
        for pid, pos in pairs:
            reorder_one(drv, pid, pos)
    finally:
        drv.quit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True,
                    help='ör: "231321:2,235412:5" (virgülle ayrılır)')
    args = ap.parse_args()
    main(args.batch)
