import os
import uuid
from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from src.core.database import SessionLocal
from src.models import Product, Review, ProductImage, Category
from src.utils.functions import generate_slug, generate_simple_sku

HTML_DIR = "data/scraped_html"

# ---------- PARSE PRODUCT ----------
def scrape_from_html(file_path, seller_id=95):
    # Use a temporary session just to fetch category_id
    with SessionLocal() as session:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Name
        name_tag = soup.find(id="productTitle")
        name = name_tag.text.strip() if name_tag else None
        if not name:
            return None

        # Price
        try:
            whole = soup.select_one("span.a-price-whole").text.replace(",", "")
            frac = soup.select_one("span.a-price-fraction").text
            price = float(f"{whole}.{frac}")
        except:
            price = 0.0

        # Discount Price
        try:
            old_p = soup.select_one("span.a-text-price span.a-offscreen").text
            discount_price = float(old_p.replace("₹", "").replace(",", "").strip())
        except:
            discount_price = None

        # Images
        images = []
        for i, img in enumerate(soup.select("#altImages img"), start=1):
            src = img.get("src", "").replace("_SS40_", "_SL1500_")
            if "images/I" in src:
                images.append({"url": src, "position": i})

        # Reviews
        reviews = []
        blocks = soup.select("div[data-hook='review']")
        for b in blocks:
            try:
                reviews.append({
                    "name": b.select_one(".a-profile-name").text,
                    "rating": float(b.select_one("i span").text.split(" ")[0]),
                    "comment": b.select_one(".review-text-content span").text
                })
            except:
                continue

        # Extract category from filename
        filename = os.path.basename(file_path)
        category_name = filename.split("_")[0]
        category = session.query(Category).filter(func.lower(Category.name) == category_name.lower()).first()
        if not category:
            print(f"⚠️ Category not found: {category_name}")
            return None

        category_id = category.id  # use integer

        return {
            "name": name,
            "price": price,
            "discount_price": discount_price,
            "category_id": category_id,
            "seller_id": seller_id,
            "slug": f"{generate_slug(name)}-{uuid.uuid4().hex[:8]}",
            "sku": generate_simple_sku(name),
            "images": images[:10],
            "reviews": reviews,
        }

# ---------- SAVE TO DB ----------
def save_product(data):
    try:
        # start a new transaction for each product
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
                    session.flush()  # get existing.id

                for img in data["images"]:
                    if not session.query(ProductImage).filter_by(product_id=existing.id, url=img["url"]).first():
                        session.add(ProductImage(
                            product_id=existing.id,
                            url=img["url"],
                            position=img["position"]
                        ))

                for r in data["reviews"]:
                    if not session.query(Review).filter_by(product_id=existing.id, comment=r["comment"]).first():
                        session.add(Review(
                            product_id=existing.id,
                            name=r["name"],
                            rating=r["rating"],
                            comment=r["comment"]
                        ))

    except SQLAlchemyError as e:
        print(f"❌ Error saving {data['name']}: {e}")

# ---------- PROCESS ALL HTML FILES ----------
def run_db_saver(preview=False):
    for file in os.listdir(HTML_DIR):
        if not file.endswith(".html"):
            continue

        file_path = os.path.join(HTML_DIR, file)
        data = scrape_from_html(file_path)

        if not data:
            print(f"⚠️ Skipped: {file}")
            continue

        if preview:
            print("\n==============================")
            print("FILE:", file)
            print("==============================")
            from pprint import pprint
            pprint(data)
            print("==============================\n")
            continue  # do not save

        save_product(data)
        print(f"✅ Saved: {data['name']}")

if __name__ == "__main__":
    run_db_saver(preview=True)

