from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, desc
from sqlalchemy.sql import func as sql_func
from fastapi import HTTPException, status, UploadFile, Response
from typing import List, Optional, Union, Dict
import cloudinary
import cloudinary.uploader
from src.models.products import Product, ProductImage
from src.models.products import Category
from src.models.review import Review
from src.schemas.products import AddStockRequest, BulkUploadResponse, BulkUploadRow
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch, generate_bulk_upload_template
from src.utils.functions import generate_slug, generate_simple_sku, generate_unique_slug

class ProductService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    # ==================== OPTIMIZATION HELPERS ====================
    
    def _base_product_query(self, eager_load: bool = True):
        """
        Base query with optional eager loading for images and category
        Eager loaded product images and category
        """
        query = self.db.query(Product)
        if eager_load:
            query = query.options(
                selectinload(Product.images),
                joinedload(Product.category)
            )
        return query

    def _attach_ratings_bulk(self, products: List[Product]) -> List[Product]:
        """Efficiently attach ratings to multiple products in a single query"""
        if not products:
            return products
        
        product_ids = [p.id for p in products]
        
        # Single query to get all ratings instead of N queries
        ratings = (
            self.db.query(Review.product_id, func.avg(Review.rating).label('avg'))
            .filter(Review.product_id.in_(product_ids))
            .group_by(Review.product_id)
            .all()
        )
        
        ratings_map: Dict[int, float] = {r.product_id: float(r.avg) for r in ratings}
        
        for product in products:
            product.average_rating = ratings_map.get(product.id)
        
        return products

    def get_average_rating(self, product_id: int):
        """Single product rating - kept for single product queries"""
        avg_rating = (
            self.db.query(func.avg(Review.rating))
            .filter(Review.product_id == product_id)
            .scalar()
        )
        return float(avg_rating) if avg_rating else None

    # ==================== LIST PRODUCTS (ADMIN) ====================
    
    def list_products(self):
        """Admin only: List all products"""
        if not self.current_user or self.current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view all products"
            )

        products = (
            self._base_product_query()
            .filter(Product.is_deleted == False)
            .order_by(Product.created_at.desc())
            .all()
        )
        return self._attach_ratings_bulk(products)

    # ==================== LIST APPROVED PRODUCTS ====================
    
    def list_approved_products(self):
        """Public: List approved products"""
        products = (
            self._base_product_query()
            .filter(
                Product.status == "approved",
                Product.is_active == True,
                Product.is_deleted == False
            )
            .order_by(Product.created_at.desc())
            .all()
        )
        return self._attach_ratings_bulk(products)

    # ==================== SELLER PRODUCTS ====================
    
    def get_seller_products(self, seller_id: int):
        """Get seller's products"""
        if not self.current_user or self.current_user.role != "seller":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sellers can view their products"
            )

        if self.current_user.role == "seller" and self.current_user.id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own products"
            )

        products = (
            self._base_product_query()
            .filter(Product.seller_id == seller_id, Product.is_deleted == False)
            .order_by(Product.created_at.desc())
            .all()
        )
        return self._attach_ratings_bulk(products)

    # ==================== GET SINGLE PRODUCT ====================
    
    def get_product(self, product_id: int):
        """Get single product by ID"""
        db_product = (
            self._base_product_query()
            .filter(Product.id == product_id, Product.is_deleted == False)
            .first()
        )
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        db_product.average_rating = self.get_average_rating(product_id)
        return db_product

    # ==================== CATEGORY PRODUCTS ====================
    
    def get_products_by_category_name(self, category_name: str):
        """Get products by category name"""
        category = self.db.query(Category).filter(Category.name.ilike(category_name)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        products = (
            self._base_product_query()
            .filter(
                Product.category_id == category.id,
                Product.is_deleted == False,
                Product.status == "approved",
                Product.is_active == True
            )
            .order_by(Product.created_at.desc())
            .all()
        )
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found for this category")
        
        return self._attach_ratings_bulk(products)

    # ==================== NEW ARRIVALS ====================
    
    def get_new_arrivals(self):
        """Get latest 2 products per category - OPTIMIZED using window function"""
        # Subquery with row_number() window function to rank products per category

        row_num = (
            sql_func.row_number()
            .over(
                partition_by=Product.category_id,
                order_by=desc(Product.created_at)
            )
            .label('row_num')
        )
        
        subq = (
            self.db.query(Product.id, row_num)
            .filter(
                Product.is_deleted == False,
                Product.status == "approved",
                Product.is_active == True
            )
            .subquery()
        )
        
        # Get product IDs where row_num <= 2 (top 2 per category)
        product_ids = (
            self.db.query(subq.c.id)
            .filter(subq.c.row_num <= 2)
            .all()
        )
        product_ids = [pid[0] for pid in product_ids]
        
        if not product_ids:
            return []
        
        # Fetch full products with eager loading
        products = (
            self._base_product_query()
            .filter(Product.id.in_(product_ids))
            .order_by(Product.created_at.desc())
            .all()
        )
        
        return self._attach_ratings_bulk(products)

    # ==================== SEARCH PRODUCTS ====================
    
    def search_products(self, query: str, status_filter: Optional[str] = None):
        """Search products"""
        base_query = (
            self._base_product_query()
            .filter(Product.is_deleted == False)
        )
        
        is_admin = self.current_user and self.current_user.role == "admin"
        if is_admin and status_filter:
            base_query = base_query.filter(Product.status == status_filter)
        elif not is_admin:
            base_query = base_query.filter(
                Product.status == "approved",
                Product.is_active == True
            )
        
        search_term = f"%{query}%"
        products = (
            base_query.filter(
                (Product.name.ilike(search_term)) |
                (Product.description.ilike(search_term)) |
                (Product.sku.ilike(search_term))
            )
            .order_by(Product.created_at.desc())
            .limit(100)  # Add reasonable limit for performance
            .all()
        )
        return self._attach_ratings_bulk(products)

    # ==================== CREATE PRODUCT ====================
    
    async def create_product(
        self,
        name: str,
        description: Optional[str],
        price: float,
        discount_price: Optional[str],
        stock: int,
        sku: Optional[str],
        category_id: int,
        is_featured: bool,
        images: List[UploadFile],
    ):
        if self.current_user.role != "seller":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers can create products")

        discount_value = float(discount_price) if discount_price not in (None, "", "null") else None
        sku_value = sku.strip() if sku and sku.strip() else generate_simple_sku(name)

        db_product = Product(
            name=name,
            description=description,
            price=price,
            discount_price=discount_value,
            stock=stock,
            sku=sku_value,
            category_id=category_id,
            slug=generate_slug(name),
            seller_id=self.current_user.id,
            is_active=False,
            is_featured=is_featured,
            status="pending",
        )

        self.db.add(db_product)
        self.db.commit()
        self.db.refresh(db_product)

        for index, image in enumerate(images, start=1):
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {image.filename}")

            try:
                upload_result = cloudinary.uploader.upload(
                    image.file,
                    folder=f"seller_{self.current_user.id}/products/{db_product.id}",
                    overwrite=True,
                )
                image_url = upload_result.get("secure_url")
                db_image = ProductImage(product_id=db_product.id, url=image_url, position=index)
                self.db.add(db_image)

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    # ==================== UPDATE PRODUCT ====================
    
    async def update_product(
        self,
        product_id: int,
        name: Optional[str],
        description: Optional[str],
        price: Optional[float],
        discount_price: Optional[float],
        stock: Optional[int],
        sku: Optional[str],
        category_id: Optional[int],
        is_featured: Optional[bool],
        images: Optional[Union[List[UploadFile], List[str]]],
    ):
        if self.current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Only sellers can update products")

        db_product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.seller_id == self.current_user.id)
            .first()
        )
        
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")

        def clean_value(value):
            if value is None:
                return None
            if isinstance(value, str):
                v = value.strip().lower()
                if v in ("", "null", "none", "undefined"):
                    return None
            return value

        name = clean_value(name)
        description = clean_value(description)
        sku = clean_value(sku)

        try:
            price = float(price) if clean_value(price) is not None else None
        except (ValueError, TypeError):
            price = None

        try:
            discount_price = float(discount_price) if clean_value(discount_price) is not None else None
        except (ValueError, TypeError):
            discount_price = None

        try:
            stock = int(stock) if clean_value(stock) is not None else None
        except (ValueError, TypeError):
            stock = None

        try:
            category_id = int(category_id) if clean_value(category_id) is not None else None
        except (ValueError, TypeError):
            category_id = None

        if isinstance(is_featured, str):
            is_featured = is_featured.lower() == "true"

        form_fields = {
            "name": name,
            "description": description,
            "price": price,
            "discount_price": discount_price,
            "stock": stock,
            "sku": sku,
            "category_id": category_id,
            "is_featured": is_featured,
        }
        for key, value in form_fields.items():
            if value is not None:
                setattr(db_product, key, value)

        if images:
            self.db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()
            self.db.flush()

            for index, image in enumerate(images, start=1):
                if not image.content_type.startswith("image/"):
                    raise HTTPException(status_code=400, detail=f"Invalid file type: {image.filename}")

                try:
                    upload_result = cloudinary.uploader.upload(
                        image.file,
                        folder=f"seller_{self.current_user.id}/products/{db_product.id}",
                        overwrite=True,
                    )
                    image_url = upload_result.get("secure_url")
                    if image_url:
                        new_image = ProductImage(
                            product_id=db_product.id,
                            url=image_url,
                            position=index
                        )
                        self.db.add(new_image)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

        db_product.status = "pending"
        db_product.is_active = False

        self.db.commit()
        self.db.refresh(db_product)

        db_product.images = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == db_product.id)
            .order_by(ProductImage.position)
            .all()
        )

        return db_product

    # ==================== DELETE PRODUCT ====================
    
    def delete_product(self, product_id: int):
        db_product = self.db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )

        if db_product.seller_id != self.current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product"
            )

        db_product.is_deleted = True
        db_product.is_active = False

        self.db.commit()
        self.db.refresh(db_product)

        return {"message": f"Product '{db_product.name}' marked as deleted successfully"}

    # ==================== ADD STOCK ====================
    
    def add_product_stock(self, product_id: int, stock_data: AddStockRequest):
        if self.current_user.role != "seller":
            raise HTTPException(status_code=403, detail="Only sellers can add stock")

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product.seller_id != self.current_user.id:
            raise HTTPException(status_code=403, detail="You can only update your own products")

        product.stock = (product.stock or 0) + stock_data.quantity

        self.db.commit()
        self.db.refresh(product)
        return product

    # ==================== UPDATE STATUS ====================
    
    def update_product_status(self, product_id: int, status_value: str):
        if self.current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update product status")

        db_product = self.db.query(Product).filter(Product.id == product_id).first()

        if not db_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id} not found")

        if status_value not in ["approved", "rejected"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be either 'approved' or 'rejected'")

        db_product.status = status_value
        db_product.is_active = True if status_value == "approved" else False

        self.db.commit()
        self.db.refresh(db_product)
        return db_product

    # ==================== BULK UPLOAD ====================
    
    def download_bulk_upload_template(self):
        template = generate_bulk_upload_template()
        return Response(
            content=template,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=bulk_upload_template.csv"},
        )

    async def bulk_upload_products(self, file: UploadFile):
        if self.current_user.role != "seller":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers can upload products")

        try:
            df = await process_upload_file(file, self.current_user.id)

            validated_products: List[BulkUploadRow] = []
            errors: List[BulkUploadRow] = []

            for index, row in df.iterrows():
                is_valid, product = validate_row(row, index + 2)
                if is_valid:
                    validated_products.append(product)
                else:
                    errors.append(product)

            if validated_products:
                success_records, batch_errors = save_products_batch(self.db, validated_products, self.current_user.id)

                if batch_errors:
                    first_msg = None
                    for err in batch_errors:
                        if hasattr(err, "error_message") and err.error_message:
                            first_msg = err.error_message
                            break
                        if isinstance(err, dict) and err.get("error_message"):
                            first_msg = err.get("error_message")
                            break
                    if not first_msg:
                        row_info = getattr(batch_errors[0], "row_number", None) or (
                            batch_errors[0].get("row_number") if isinstance(batch_errors[0], dict) else None
                        )
                        first_msg = f"Bulk upload failed: {len(batch_errors)} rows failed. First failure at row {row_info or 'unknown'}."
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=first_msg)

                errors.extend(batch_errors)
            else:
                success_records = []

            response_payload = BulkUploadResponse(
                total_records=len(df),
                successful_records=len(success_records),
                failed_records=len(errors),
                errors=errors,
                success_records=success_records,
            )
            if len(success_records) == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response_payload.model_dump())

            return response_payload

        except Exception as e:
            msg = str(e).splitlines()[0] if str(e) else "Bulk upload failed"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)