import time, argparse
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
    drv.get(LOGIN_URL);                                   time.sleep(1)
    WebDriverWait(drv, 15).until(
        EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
    ).send_keys(USER);                                     time.sleep(1)
    drv.find_element(By.NAME, "Password").send_keys(PASSWD); time.sleep(1)
    drv.find_element(By.CSS_SELECTOR, "button[type='submit']").click(); time.sleep(1)
    WebDriverWait(drv, 15).until(EC.url_contains("/admin"));            time.sleep(1)

def reorder_one(drv, product_id: int, src_pos: int):
    PROD_URL = f"{BASE_URL}/admin/product/edit/{product_id}"
    PIC_SEL  = "#productpictures-grid .picture-item"

    drv.get(PROD_URL);                                    time.sleep(1)
    WebDriverWait(drv, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
    ).click();                                            time.sleep(1)

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
    drv.find_element(By.CSS_SELECTOR, "button.btn-primary[name='save']").click(); time.sleep(1)
    WebDriverWait(drv, 15).until_not(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading")))
    print(f"✅ {product_id}: {src_pos+1}. görsel başa alındı")
    time.sleep(1)

def run_bulk_edits(drv):
    drv.get(BULKEDIT_URL);                                time.sleep(1)

    # ─────────── İŞLEM 1: Etiket Güncelle ───────────
    sel = Select(drv.find_element(By.ID, "SearchInCategoryIds")); time.sleep(1)
    sel.select_by_value("374");                          time.sleep(1)

    buttons = drv.find_elements(By.XPATH, "//span[@class='select2-selection__choice__remove']")
    if len(buttons) > 1:
        buttons[1].click();                              time.sleep(1)

    drv.find_element(By.ID, "search-products").click();  time.sleep(1)

    chk = WebDriverWait(drv, 10).until(
        EC.presence_of_element_located((By.ID, "ProductTag_Update")))
    drv.execute_script("arguments[0].click();", chk);    time.sleep(1)

    Select(drv.find_element(By.ID, "ProductTagId")).select_by_value("144"); time.sleep(1)

    save_btn = WebDriverWait(drv, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "btn-primary")))
    drv.execute_script("arguments[0].click();", save_btn); time.sleep(1)

    # ─────────── İŞLEM 2: Kategori Güncelle ───────────
    sel = Select(drv.find_element(By.ID, "SearchInCategoryIds")); time.sleep(1)
    for cid in ["172", "440", "556", "614", "620"]:
        sel.select_by_value(cid);                      time.sleep(1)

    buttons = drv.find_elements(By.XPATH, "//span[@class='select2-selection__choice__remove']")
    if len(buttons) > 1:
        buttons[1].click();                             time.sleep(1)

    drv.find_element(By.ID, "search-products").click(); time.sleep(1)
    drv.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(1)

    chk = WebDriverWait(drv, 10).until(
        EC.presence_of_element_located((By.ID, "Category_Update")))
    drv.execute_script("arguments[0].click();", chk);   time.sleep(1)

    Select(drv.find_element(By.ID, "CategoryId")).select_by_value("374"); time.sleep(1)
    Select(drv.find_element(By.ID, "CategoryTransactionId")).select_by_value("1"); time.sleep(1)

    save_btn = WebDriverWait(drv, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "btn-primary")))
    drv.execute_script("arguments[0].click();", save_btn); time.sleep(1)

def main(batch_str: str):
    pairs = [
        (int(pid), int(pos) - 1)
        for pid, pos in (p.split(":") for p in batch_str.split(",") if p.strip())
    ]

    drv = init_driver()
    try:
        login(drv)
        for pid, pos in pairs:
            reorder_one(drv, pid, pos)
        run_bulk_edits(drv)
    finally:
        drv.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True,
                        help='ör: "231321:2,235412:5" (virgülle ayrılır)')
    args = parser.parse_args()
    main(args.batch)
