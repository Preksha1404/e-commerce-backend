from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from amazontable import Base, Product, Price, Image, Review  # Removed Rating if unused
import time
import inspect

# -------------------- DATABASE SETUP --------------------
engine = create_engine("postgresql://postgres:9698@localhost:5432/ecommercedb")
Session = sessionmaker(bind=engine)
session = Session()

# -------------------- SELENIUM SETUP --------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# -------------------- FUNCTIONS --------------------
def scroll_to_bottom():
    """Scroll to bottom to load lazy content"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_product_links(category_url, max_pages=5):
    """Collect product URLs from a category/search page"""
    product_links = set()
    driver.get(category_url)
    for page in range(max_pages):
        time.sleep(2)
        links = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
        for link in links:
            href = link.get_attribute("href")
            if href and "/dp/" in href:
                product_links.add(href.split("?")[0])  # Remove query params
        # Go to next page
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
            next_btn.click()
            time.sleep(2)
        except:
            break
    return list(product_links)


def safe_create_product(**kwargs):
    """Create Product safely ignoring invalid fields"""
    valid_keys = inspect.signature(Product.__init__).parameters.keys()
    clean_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
    return Product(**clean_kwargs)


def scrape_product(product_url, n_images=10, max_review_pages=3):
    """Scrape single product page"""
    driver.get(product_url)
    time.sleep(3)
    scroll_to_bottom()

    # --- Title ---
    title_tag = driver.find_elements(By.ID, "productTitle")
    title = title_tag[0].text.strip() if title_tag else "No title found"

    # --- Price ---
    price_tag = driver.find_elements(By.CSS_SELECTOR, "span.a-price-whole")
    price = price_tag[0].text.strip() if price_tag else "No price found"

    # --- ASIN ---
    asin = None
    try:
        asin_input = driver.find_element(By.ID, "ASIN")
        asin = asin_input.get_attribute("value")
    except:
        asin = None

    # --- Images ---
    images = []
    img_tags = driver.find_elements(By.CSS_SELECTOR, "img[src]")
    for img in img_tags:
        src = img.get_attribute("src")
        if "images/I" in src and src not in images:
            images.append(src)
        if len(images) >= n_images:
            break

    # --- Reviews ---
    reviews = []
    for page in range(max_review_pages):
        review_blocks = driver.find_elements(By.CSS_SELECTOR, ".review")
        for block in review_blocks:
            try:
                name = block.find_element(By.CSS_SELECTOR, ".a-profile-name").text
                title_r = block.find_element(By.CSS_SELECTOR, ".review-title span").text
                body = block.find_element(By.CSS_SELECTOR, ".review-text-content span").text
                rating = block.find_element(By.CSS_SELECTOR, ".review-rating span").text
                date = block.find_element(By.CSS_SELECTOR, ".review-date").text
                reviews.append({
                    "reviewer_name": name,
                    "review_title": title_r,
                    "review_body": body,
                    "review_rating": rating,
                    "review_date": date
                })
            except:
                continue
        # Next review page
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "li.a-last a")
            next_btn.click()
            time.sleep(2)
        except:
            break

    # --- Insert/Update DB ---
    existing_product = session.query(Product).filter_by(amazon_url=product_url).first()
    if existing_product:
        print(f"⚠️ Product exists, updating: {title}")
        existing_product.title = title
        existing_product.prices.append(Price(price=price))
        existing_product.images = [Image(image_url=i) for i in images]
        existing_review_texts = {r.review_body for r in existing_product.reviews}
        for r in reviews:
            if r["review_body"] not in existing_review_texts:
                existing_product.reviews.append(Review(**r))
    else:
        print(f"🆕 Inserting new product: {title}")
        # ✅ safe create ignores asin if not supported
        product = safe_create_product(title=title, amazon_url=product_url, asin=asin)
        product.prices.append(Price(price=price))
        for i in images:
            product.images.append(Image(image_url=i))
        for r in reviews:
            product.reviews.append(Review(**r))
        session.add(product)

    session.commit()
    print(f"✅ Saved: {title} | Price: {price} | Images: {len(images)} | Reviews: {len(reviews)} | ASIN: {asin}")


# -------------------- MAIN LOOP --------------------
category_urls = [
    "https://www.amazon.in/s?k=accessories",
    "https://www.amazon.in/s?k=electricalappliances",
    "https://www.amazon.in/s?k=gadgets",
    "https://www.amazon.in/s?k=books"
]

all_product_links = []
for cat_url in category_urls:
    links = get_product_links(cat_url, max_pages=10)
    all_product_links.extend(links)

# Remove duplicates
all_product_links = list(set(all_product_links))

# Scrape all products
for url in all_product_links:
    try:
        scrape_product(url, n_images=10, max_review_pages=3)
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")

driver.quit()
