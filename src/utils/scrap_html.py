# import os
# import time
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from src.core.database import SessionLocal
# from src.models import Category

# # ---------- CONFIG ----------
# HTML_DIR = "data/scraped_html"
# os.makedirs(HTML_DIR, exist_ok=True)

# session = SessionLocal()

# # ---------- SELENIUM ----------
# chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--window-size=1920,1080")

# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


# # ---------- GET PRODUCT LINKS ----------
# def get_product_links(search_url, max_pages=2):
#     links = set()
#     driver.get(search_url)

#     for _ in range(max_pages):
#         time.sleep(2)
#         products = driver.find_elements(By.CSS_SELECTOR, "a[href*='/dp/']")
#         for p in products:
#             href = p.get_attribute("href")
#             if href and "/dp/" in href:
#                 links.add(href.split("?")[0])

#         # NEXT PAGE
#         try:
#             driver.find_element(By.CSS_SELECTOR, "li.a-last a").click()
#             time.sleep(2)
#         except:
#             break

#     return list(links)


# # ---------- SAVE HTML ----------
# def save_html(product_url, category_name):
#     driver.get(product_url)
#     time.sleep(3)

#     asin = product_url.split("/dp/")[1].split("/")[0]
#     filename = f"{category_name}_{asin}.html"
#     path = os.path.join(HTML_DIR, filename)

#     with open(path, "w", encoding="utf-8") as f:
#         f.write(driver.page_source)

#     print(f"Saved HTML: {filename}")
#     return path


# # ---------- MAIN SCRAPER ----------
# def run_html_scraper():
#     categories = session.query(Category).filter(
#         Category.is_active == True,
#         Category.name != "Default"
#     ).all()

#     for cat in categories:
#         print(f"\n=== Category: {cat.name} ===")

#         search_url = f"https://www.amazon.in/s?k={cat.name.lower()}"
#         product_links = get_product_links(search_url)

#         for link in product_links:
#             try:
#                 save_html(link, cat.name.lower())
#             except Exception as e:
#                 print(f"Failed: {link} — {e}")

#     driver.quit()
#     session.close()


# if __name__ == "__main__":
#     run_html_scraper()

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from src.core.database import SessionLocal
from src.models import Category

# ---------- CONFIG ----------
HTML_DIR = "data/scraped_products_html"
os.makedirs(HTML_DIR, exist_ok=True)

session = SessionLocal()

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


# ---------- GET PRODUCT LINKS ----------
def get_product_links(search_url, max_pages=2):
    links = set()
    driver.get(search_url)

    for _ in range(max_pages):
        time.sleep(2)
        products = driver.find_elements(By.CSS_SELECTOR, "a[href*='/dp/']")
        for p in products:
            href = p.get_attribute("href")
            if href and "/dp/" in href:
                links.add(href.split("?")[0])

        # NEXT PAGE
        try:
            driver.find_element(By.CSS_SELECTOR, "li.a-last a").click()
            time.sleep(2)
        except:
            break

    return list(links)


# ---------- SAVE HTML ----------
def save_html(product_url, category_name):
    driver.get(product_url)
    time.sleep(3)

    asin = product_url.split("/dp/")[1].split("/")[0]
    filename = f"{category_name}_{asin}.html"
    path = os.path.join(HTML_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)

    print(f"Saved HTML: {filename}")
    return path


# ---------- EXTRACT HIGH QUALITY IMAGES ----------
def extract_hd_images():
    """Extract high-quality Amazon product images"""
    elems = driver.find_elements(By.CSS_SELECTOR, "img[data-a-dynamic-image]")
    urls = []

    for el in elems:
        try:
            raw_json = el.get_attribute("data-a-dynamic-image")
            data = json.loads(raw_json)
            urls.extend(list(data.keys()))
        except:
            continue

    return list(set(urls))  # unique URLs


# ---------- MAIN SCRAPER ----------
def run_scraper():
    # Only scrape Fashion and Sports & Fitness categories
    categories = session.query(Category).filter(
        Category.is_active == True,
        Category.name.in_(["Fashion", "Sports & Fitness"])
    ).all()

    for cat in categories:
        print(f"\n=== Category: {cat.name} ===")
        search_url = f"https://www.amazon.in/s?k={cat.name.replace(' ', '+').lower()}"

        product_links = get_product_links(search_url)

        for link in product_links:
            try:
                # Save HTML
                save_html(link, cat.name.lower())

                # Open product page to extract images
                driver.get(link)
                time.sleep(3)
                hd_images = extract_hd_images()

                if hd_images:
                    print(f"HD Images for {link}:")
                    for img in hd_images:
                        print(img)
                else:
                    print("❌ No HD images found")

            except Exception as e:
                print(f"Failed: {link} — {e}")

    driver.quit()
    session.close()


if __name__ == "__main__":
    run_scraper()