import json
import os
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

ERROR = "ошибка"
PAGE_TIMEOUT = 25
WAIT_TIMEOUT = 15


def default_user_data_dir() -> Path | None:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"
    return base if base.exists() else None


def list_chrome_profiles(user_data_dir: Path) -> list[str]:
    if not user_data_dir or not user_data_dir.exists():
        return []
    names = []
    for p in user_data_dir.iterdir():
        if not p.is_dir():
            continue
        if p.name != "Default" and not p.name.startswith("Profile"):
            continue
        if (p / "Preferences").exists():
            names.append(p.name)
    names.sort(key=lambda n: (0 if n == "Default" else 1, n))
    return names

"""
def build_driver(
    profile_dir: Path | None,
    profile_name: str = "Default",
    headless: bool = True,
) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if profile_dir is not None:
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument(f"--profile-directory={profile_name}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    return driver

def build_driver(
    profile_dir: Path | None,
    profile_name: str = "Default",
) -> webdriver.Chrome:
    options = Options()

    # УБРАТЬ:
    # options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")

    if profile_dir is not None:
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument(f"--profile-directory={profile_name}")

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    return driver


def build_driver(profile_dir):
    options = Options()

    options.add_argument(
        rf"--user-data-dir={profile_dir}"
    )

    options.add_argument("--remote-debugging-port=9222")

    #options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # убирает баннер automation
    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    # скрывает webdriver
    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    service = Service()

    driver = webdriver.Chrome(
        service=service,
        options=options
    )



    return driver
"""



from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def build_driver(headless: bool = True, disable_media: bool = False) -> webdriver.Chrome:
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # === ВАЖНО: твой реальный selenium профиль ===
    options.add_argument(r"--user-data-dir=C:\selenium_profile")
    options.add_argument("--profile-directory=Profile 1")

    # стабильность
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # убирает automation-баннер
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    # отключение загрузки медиа (фото, видео)
    if disable_media:
        options.add_argument("--blink-settings=imagesEnabled=false,videosEnabled=false")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )

    return driver


def try_open_chrome(
    headless: bool = True,
    disable_media: bool = False,
) -> tuple[bool, str]:
    driver = None
    try:
        driver = build_driver(headless=headless, disable_media=disable_media)
        driver.get("about:blank")
        return True, "Chrome открылся и закрылся успешно"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def clean_price(text: str) -> str:
    digits = re.sub(r"\D", "", text or "")
    return digits or ERROR


def extract_text(driver: webdriver.Chrome, selectors: list[str], wait: WebDriverWait | None = None) -> str:
    if wait is None:
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

    for sel in selectors:
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            text = el.text.strip()
            if text:
                return text
        except TimeoutException:
            continue
        except WebDriverException:
            continue

    for sel in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                text = el.text.strip()
                if text:
                    return text
        except WebDriverException:
            continue

    return ""


def parse_ozon(driver: webdriver.Chrome, url: str) -> dict:
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    title = ERROR
    price = ERROR
    price_card = ERROR

    try:
        title_el = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        title = title_el.text.strip() or ERROR
    except TimeoutException:
        pass

    seller = extract_text(
        driver,
        [
            "span.b35_4_2-b7",
            "span[class*='seller']",
            "div[class*='seller'] span",
            "a[class*='seller'] span",
            "span[class*='brand']",
            "div[class*='brand'] span",
        ],
        wait,
    )

    try:
        card_el = driver.find_element(By.CSS_SELECTOR, "span.tsHeadline600Large")
        price_card = clean_price(card_el.text)
    except WebDriverException:
        price_card = ERROR

    try:
        regular_el = driver.find_element(By.CSS_SELECTOR, "span.pdp_bj")
        price = clean_price(regular_el.text)
    except WebDriverException:
        price = ERROR

    if price == ERROR and price_card != ERROR:
        price = price_card
        price_card = ERROR

    return {"title": title, "seller": seller, "price": price, "price_card": price_card}


def parse_wb(driver: webdriver.Chrome, url: str) -> dict:
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    title = ERROR
    price = ERROR

    try:
        title_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1, h2[class*='productTitle'], [class*='productTitle']")
            )
        )
        title = title_el.text.strip() or ERROR
    except TimeoutException:
        pass

    seller = extract_text(
        driver,
        [
            "span.productHeaderBrandText--ZdMBC",
            "span[class*='productHeaderBrandText']",
            "a[class*='brand']",
            "span[class*='brand']",
            "div[class*='brand'] span",
        ],
        wait,
    )

    try:
        driver.execute_script("window.scrollBy(0, 400);")
    except WebDriverException:
        pass
    time.sleep(2)

    selectors = [
        "ins[class*='priceBlockFinalPrice']",
        "[class*='priceBlockFinalPrice']",
        "[class*='finalPrice']",
        "span[class*='price']",
    ]
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text
            if any(ch.isdigit() for ch in text):
                price = clean_price(text)
                break
        except WebDriverException:
            continue

    return {"title": title, "seller": seller, "price": price, "price_card": ""}


def parse_yandex(driver: webdriver.Chrome, url: str) -> dict:
    driver.get(url)
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    title = ERROR
    price = ERROR
    price_card = ERROR

    try:
        title_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1[data-auto='productCardTitle'], h1[data-additional-zone='title']")
            )
        )
        title = title_el.text.strip() or ERROR
    except TimeoutException:
        pass

    seller = extract_text(
        driver,
        [
            "div[data-zone-name='businessProductBlock'] span.ds-text_weight_bold.ds-text_color_text-primary",
            "div[data-zone-name='businessProductBlock'] span.ds-text.ds-text_weight_bold.ds-text_color_text-primary",
            "div[data-zone-name='businessProductBlock'] span.ds-text_weight_bold",
            "div[data-zone-name='businessProductBlock'] span.ds-text",
            "span.ds-text[class*='ds-text_weight_bold'][class*='ds-text_color_text-primary']",
            "span.ds-text[class*='ds-text_weight_bold']",
        ],
        wait,
    )
    if seller and len(seller) > 15:
        seller = seller[:15]

    try:
        driver.execute_script("window.scrollBy(0, 400);")
    except WebDriverException:
        pass
    time.sleep(1)

    selectors_price = [
        "span.ds-text[class*='ds-text_color_text-secondary'][class*='ds-text_typography_headline']",
        "span.ds-text[class*='headline-4']",
        "span[class*='price']",
    ]
    for sel in selectors_price:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text
            if any(ch.isdigit() for ch in text):
                price = clean_price(text)
                break
        except WebDriverException:
            continue

    selectors_price_card = [
        "span.ds-text[class*='ds-text_color_price-term'][class*='ds-text_typography_headline']",
        "span.ds-text[class*='ds-text_color_price-term']",
        "span[class*='price-card']",
    ]
    for sel in selectors_price_card:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text
            if any(ch.isdigit() for ch in text):
                price_card = clean_price(text)
                break
        except WebDriverException:
            continue

    if price == ERROR and price_card != ERROR:
        price = price_card
        price_card = ERROR

    return {"title": title, "seller": seller, "price": price, "price_card": price_card}


def parse_rows(
    rows: list[dict],
    chrome_user_data: str | None = None,
    chrome_profile: str = "Default",
    headless: bool = True,
    disable_media: bool = False,
) -> list[dict]:
    results = []
    driver = None
    try:
        driver = build_driver(headless=headless, disable_media=disable_media)
        for item in rows:
            row_id = item.get("row") if "row" in item else item.get("id")
            market = (item.get("market") or "").strip().upper()
            url = (item.get("url") or "").strip()

            entry = {"row": row_id, "title": ERROR, "price": ERROR, "price_card": "", "seller": ""}
            if not url:
                results.append(entry)
                continue

            try:
                if market == "OZON":
                    entry.update(parse_ozon(driver, url))
                elif market == "WB":
                    entry.update(parse_wb(driver, url))
                elif market == "YANDEX":
                    entry.update(parse_yandex(driver, url))
                else:
                    entry["title"] = ERROR
                    entry["price"] = ERROR
                    entry["price_card"] = ""
            except Exception:
                entry["title"] = ERROR
                entry["price"] = ERROR
                entry["price_card"] = ERROR if market == "OZON" else ""

            results.append(entry)
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    return results


def process(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    cfg = payload.get("config") or {}
    results = parse_rows(
        payload.get("rows", []),
        chrome_user_data=cfg.get("chrome_user_data"),
        chrome_profile=cfg.get("chrome_profile") or "Default",
        headless=bool(cfg.get("headless", True)),
        disable_media=bool(cfg.get("disable_media", False)),
    )
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"rows": results}, f, ensure_ascii=False, indent=2)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: parse_prices.py <input.json> <output.json>", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    process(input_path, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
