# import os
# import uuid
# from bs4 import BeautifulSoup
# from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy import func
# from src.core.database import SessionLocal
# from src.models import Product, Review, ProductImage, Category
# from src.utils.functions import generate_slug, generate_simple_sku

# HTML_DIR = "data/scraped_html"

# # ---------- PARSE PRODUCT ----------
# def scrape_from_html(file_path, seller_id=5):
#     # Use a temporary session just to fetch category_id
#     with SessionLocal() as session:
#         with open(file_path, "r", encoding="utf-8") as f:
#             soup = BeautifulSoup(f, "html.parser")

#         # Name
#         name_tag = soup.find(id="productTitle")
#         name = name_tag.text.strip() if name_tag else None
#         if not name:
#             return None

#         # Price
#         price = 0.0

#         # Try 1: Standard price
#         price_tag = soup.select_one("span.a-price > span.a-offscreen")

#         # Try 2: any offscreen price
#         if not price_tag:
#             price_tag = soup.select_one("span.a-offscreen")

#         # -------- FASHION-SPECIFIC PRICE PARSING --------
#         if (not price_tag or price_tag.text.strip() == "₹0") and "fashion" in file_path.lower():
#             # Fashion pages often store price inside "a-price-whole"
#             fashion_price = soup.select_one("span.a-price-whole")
#             if fashion_price:
#                 try:
#                     price = float(fashion_price.text.replace(",", "").strip())
#                 except:
#                     pass

#         # Convert final price
#         if price_tag and price == 0:
#             try:
#                 price = float(price_tag.text.replace("₹", "").replace(",", "").strip())
#             except:
#                 price = 0.0

#         # Discount Price
#         discount_price = None

#         # Images
#         images = []
#         for i, img in enumerate(soup.select("#altImages img"), start=1):
#             src = img.get("src", "").replace("_SS40_", "_SL1500_")
#             if "images/I" in src:
#                 images.append({"url": src, "position": i})

#         # Reviews
#         reviews = []
#         blocks = soup.select(".review")
#         for b in blocks:
#             try:
#                 reviews.append({
#                     "name": b.select_one(".a-profile-name").text,
#                     "rating": float(b.select_one("i span").text.split(" ")[0]),
#                     "comment": b.select_one(".review-text-content span").text
#                 })
#             except:
#                 continue

#         # Extract category from filename
#         filename = os.path.basename(file_path)
#         category_name = filename.split("_")[0]
#         category = session.query(Category).filter(func.lower(Category.name) == category_name.lower()).first()
#         if not category:
#             print(f"⚠️ Category not found: {category_name}")
#             return None

#         category_id = category.id  # use integer

#         return {
#             "name": name,
#             "price": price,
#             "discount_price": discount_price,
#             "category_id": category_id,
#             "seller_id": seller_id,
#             "slug": f"{generate_slug(name)}-{uuid.uuid4().hex[:8]}",
#             "sku": generate_simple_sku(name),
#             "images": images[:10],
#             "reviews": reviews,
#         }

# # ---------- SAVE TO DB ----------
# def save_product(data):
#     try:
#         # start a new transaction for each product
#         with SessionLocal() as session:
#             with session.begin():
#                 existing = session.query(Product).filter_by(
#                     name=data["name"],
#                     category_id=data["category_id"]
#                 ).first()

#                 if existing:
#                     existing.price = data["price"]
#                     existing.discount_price = data["discount_price"]
#                 else:
#                     existing = Product(
#                         name=data["name"],
#                         price=data["price"],
#                         discount_price=data["discount_price"],
#                         category_id=data["category_id"],
#                         seller_id=data["seller_id"],
#                         slug=data["slug"],
#                         sku=data["sku"],
#                         stock=10
#                     )
#                     session.add(existing)
#                     session.flush()  # get existing.id

#                 for img in data["images"]:
#                     if not session.query(ProductImage).filter_by(product_id=existing.id, url=img["url"]).first():
#                         session.add(ProductImage(
#                             product_id=existing.id,
#                             url=img["url"],
#                             position=img["position"]
#                         ))

#                 for r in data["reviews"]:
#                     if not session.query(Review).filter_by(product_id=existing.id, comment=r["comment"]).first():
#                         session.add(Review(
#                             product_id=existing.id,
#                             name=r["name"],
#                             rating=r["rating"],
#                             comment=r["comment"]
#                         ))

#     except SQLAlchemyError as e:
#         print(f"❌ Error saving {data['name']}: {e}")

# # ---------- PROCESS ALL HTML FILES ----------
# def run_db_saver(preview=False):
#     for file in os.listdir(HTML_DIR):
#         if not file.endswith(".html"):
#             continue

#         file_path = os.path.join(HTML_DIR, file)
#         data = scrape_from_html(file_path)

#         if not data:
#             print(f"⚠️ Skipped: {file}")
#             continue

#         if preview:
#             print("\n==============================")
#             print("FILE:", file)
#             print("==============================")
#             from pprint import pprint
#             pprint(data)
#             print("==============================\n")
#             continue  # do not save

#         save_product(data)
#         print(f"✅ Saved: {data['name']}")

# if __name__ == "__main__":
#     run_db_saver(preview=True)

import os
import uuid
import json
from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from src.core.database import SessionLocal
from src.models import Product, Review, ProductImage, Category
from src.utils.functions import generate_slug, generate_simple_sku

HTML_DIR = "data/scraped_products_html"


# ---------------------------------------------------------
# EXTRACT HD IMAGES FROM HTML (NO SELENIUM NEEDED)
# ---------------------------------------------------------
def extract_hd_images_from_html(soup):
    """
    Extract HD images using data-a-dynamic-image attribute
    Found inside <img> tag inside #imgTagWrapperId
    """
    try:
        img = soup.select_one("#imgTagWrapperId img")
        if not img:
            return []

        data = img.get("data-a-dynamic-image")
        if not data:
            return []

        img_dict = json.loads(data)
        return list(img_dict.keys())  # list of HD image URLs

    except Exception:
        return []


# ---------------------------------------------------------
# PARSE PRODUCT FROM HTML
# ---------------------------------------------------------
def scrape_from_html(file_path, seller_id=5):
    """Extract product details from saved HTML"""

    filename = os.path.basename(file_path)
    category_name = filename.split("_")[0]

    if category_name.lower() not in ["fashion", "sports&fitness", "sports-and-fitness", "sports"]:
        return None

    with SessionLocal() as session:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # ---------- PRODUCT NAME ----------
        name_tag = soup.find(id="productTitle")
        name = name_tag.text.strip() if name_tag else None
        if not name:
            return None

        # ---------- PRICE ----------
        price = 0.0

        # Amazon normal price selector
        price_tag = soup.select_one("span.a-price > span.a-offscreen")
        if not price_tag:
            price_tag = soup.select_one("span.a-offscreen")

        # Whole + fraction
        whole = soup.select_one("span.a-price-whole")
        fraction = soup.select_one("span.a-price-fraction")

        if whole:
            try:
                whole_val = whole.text.replace(",", "").strip()
                frac_val = fraction.text.strip() if fraction else "00"
                price = float(f"{whole_val}.{frac_val}")
            except:
                pass

        # fallback
        if price == 0 and price_tag and price_tag.text.strip():
            try:
                price = float(
                    price_tag.text.replace("₹", "").replace(",", "").strip()
                )
            except:
                price = 0.0

        discount_price = None

        # ---------- HD IMAGES ----------
        images = []
        hd_urls = extract_hd_images_from_html(soup)

        for i, url in enumerate(hd_urls, start=1):
            images.append({"url": url, "position": i})

        # ---------- REVIEWS ----------
        reviews = []
        blocks = soup.select(".review")
        for b in blocks:
            try:
                reviews.append({
                    "name": b.select_one(".a-profile-name").text,
                    "rating": float(b.select_one("i span").text.split(" ")[0]),
                    "comment": b.select_one(".review-text-content span").text
                })
            except:
                continue

        # ---------- CATEGORY ----------
        import re

        raw = filename.split("_")[0].lower()
        normalized = re.sub(r"[^a-z]", "", raw)  # remove spaces, &, -

        # What our categories look like in DB
        valid = {
            "fashion": "fashion",
            "sportsfitness": "sports & fitness",
            "sports": "sports & fitness",
        }

        if normalized not in valid:
            return None

        # get normalized readable DB category name
        final_category = valid[normalized]

        # fetch category FROM DATABASE
        category = session.query(Category).filter(
            func.lower(Category.name) == final_category.lower()
        ).first()

        if not category:
            print(f"⚠️ Category not found in DB: {final_category}")
            return None

        return {
            "name": name,
            "price": price,
            "discount_price": discount_price,
            "category_id": category.id,
            "seller_id": seller_id,
            "slug": f"{generate_slug(name)}-{uuid.uuid4().hex[:8]}",
            "sku": generate_simple_sku(name),
            "images": images[:10],
            "reviews": reviews,
        }


# ---------------------------------------------------------
# SAVE TO DATABASE
# ---------------------------------------------------------
def save_product(data):
    try:
        with SessionLocal() as session:
            with session.begin():
                existing = session.query(Product).filter_by(
                    name=data["name"],
                    category_id=data["category_id"]
                ).first()

                if existing:
                    existing.price = data["price"]
                    existing.discount_price = data["discount_price"]
                else:
                    existing = Product(
                        name=data["name"],
                        price=data["price"],
                        discount_price=data["discount_price"],
                        category_id=data["category_id"],
                        seller_id=data["seller_id"],
                        slug=data["slug"],
                        sku=data["sku"],
                        stock=10
                    )
                    session.add(existing)
                    session.flush()

                # ---------- IMAGES ----------
                for img in data["images"]:
                    if not session.query(ProductImage).filter_by(
                        product_id=existing.id, url=img["url"]
                    ).first():
                        session.add(ProductImage(
                            product_id=existing.id,
                            url=img["url"],
                            position=img["position"]
                        ))

                # ---------- REVIEWS ----------
                for r in data["reviews"]:
                    if not session.query(Review).filter_by(
                        product_id=existing.id, comment=r["comment"]
                    ).first():
                        session.add(Review(
                            product_id=existing.id,
                            name=r["name"],
                            rating=r["rating"],
                            comment=r["comment"]
                        ))

    except SQLAlchemyError as e:
        print(f"❌ Error saving {data['name']}: {e}")


# ---------------------------------------------------------
# PROCESS ALL HTML FILES
# ---------------------------------------------------------
def run_db_saver(preview=False):
    for file in os.listdir(HTML_DIR):
        if not file.endswith(".html"):
            continue

        file_path = os.path.join(HTML_DIR, file)
        data = scrape_from_html(file_path)

        if not data:
            print(f"⚠️ Skipped (not Fashion or Sports & Fitness): {file}")
            continue

        if preview:
            print("\n==============================")
            print("FILE:", file)
            print("==============================")
            from pprint import pprint
            pprint(data)
            print("==============================\n")
            continue

        save_product(data)
        print(f"✅ Saved: {data['name']}")

if __name__ == "__main__":
    run_db_saver(preview=True)
