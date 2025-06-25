"""
Batch reorder script.
Call example:
    python reorder_pictures.py --batch "231321:2,235412:5"
"""

import os, time, argparse
from selenium.webdriver import Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─────────────   SABİT GİRİŞ BİLGİLERİ  ─────────────
USER   = "mustafa_kod@haydigiy.com"
PASSWD = "123456"
# ─────────────────────────────────────────────────────

def setup_driver():
    remote = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--incognito")
    opts.add_argument("--window-size=1920,1080")
    return Remote(command_executor=remote, options=opts)

def login(driver):
    BASE  = "https://www.siparis.haydigiy.com"
    LOGIN = f"{BASE}/kullanici-giris/?ReturnUrl=%2Fadmin"
    driver.get(LOGIN)
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
    ).send_keys(USER)
    driver.find_element(By.NAME, "Password").send_keys(PASSWD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, 15).until(EC.url_contains("/admin"))

def reorder_one(driver, product_id: int, src_pos: int):
    BASE   = "https://www.siparis.haydigiy.com"
    PROD   = f"{BASE}/admin/product/edit/{product_id}"
    PICSEL = "#productpictures-grid .picture-item"

    driver.get(PROD)
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
    ).click()

    WebDriverWait(driver, 15).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, PICSEL)) >= src_pos + 1)
    WebDriverWait(driver, 15).until(
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
    if driver.execute_script(js, src_pos) != "ok":
        raise RuntimeError(f"sortable trigger failed (product {product_id})")

    time.sleep(1.0)
    driver.find_element(By.CSS_SELECTOR, "button.btn-primary[name='save']").click()
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading")))
    print(f"✅ {product_id}: {src_pos+1}. görsel başa alındı")

def main(batch_arg: str):
    """
    batch_arg formatı:
        "231321:2,235412:5"  (virgülle ayrılmış; ürünID:srcPos)
    """
    pairs = []
    for part in batch_arg.split(","):
        pid, pos = part.strip().split(":")
        pairs.append((int(pid), int(pos)-1))   # 0-index’e çevir

    drv = setup_driver()
    try:
        login(drv)
        for pid, pos in pairs:
            reorder_one(drv, pid, pos)
    finally:
        drv.quit()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--batch", required=True,
                   help='ör: "231321:2,235412:5"')
    args = p.parse_args()
    main(args.batch)
