import os, time, argparse, colorama
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run(product_id: int, src_pos: int):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--incognito")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    drv = webdriver.Chrome(service=Service(), options=opts)

    BASE   = "https://www.siparis.haydigiy.com"
    LOGIN  = f"{BASE}/kullanici-giris/?ReturnUrl=%2Fadmin"
    PROD   = f"{BASE}/admin/product/edit/{product_id}"
    USER   = os.environ["mustafa_kod@haydigiy.com"]      # GH Secret
    PASSWD = os.environ["123456"]

    picsel = "#productpictures-grid .picture-item"
    try:
        drv.get(LOGIN)
        WebDriverWait(drv, 15).until(
            EC.visibility_of_element_located((By.NAME, "EmailOrPhone"))
        ).send_keys(USER)
        drv.find_element(By.NAME, "Password").send_keys(PASSWD)
        drv.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        WebDriverWait(drv, 15).until(EC.url_contains("/admin"))
        drv.get(PROD)
        WebDriverWait(drv, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "li[data-tab-name='tab-pictures']"))
        ).click()

        WebDriverWait(drv, 15).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, picsel)) >= src_pos + 1
        )
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
            raise RuntimeError("sortable trigger failed")

        time.sleep(1.5)
        drv.find_element(By.CSS_SELECTOR, "button.btn-primary[name='save']").click()
        WebDriverWait(drv, 15).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".k-loading")))

        print(colorama.Fore.GREEN +
              f"Ürün {product_id}: {src_pos+1}. görsel başa alındı." +
              colorama.Style.RESET_ALL)
    finally:
        drv.quit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-id", required=True, type=int)
    ap.add_argument("--src-pos",    required=True, type=int,
                    help="1-den başlar (3 = üçüncü görsel)")
    a = ap.parse_args()
    run(a.product_id, a.src_pos-1)
