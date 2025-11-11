from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile, Response
from typing import List, Optional, Union
import cloudinary
import cloudinary.uploader
from src.models.products import Product, ProductImage
from src.models.products import Category
from src.schemas.products import AddStockRequest, BulkUploadResponse, BulkUploadRow
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch, generate_bulk_upload_template
from src.utils.functions import generate_slug, generate_simple_sku

class ProductService:
    def __init__(self, db: Session, current_user):
        self.db = db
        self.current_user = current_user

    def list_products(self):
        # Only admin can view all products
        if not self.current_user or self.current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can view all products"
            )

        products = (
            self.db.query(Product)
            .filter(Product.is_deleted == False)
            .all()
        )
        return products

    def get_seller_products(self, seller_id: int):
        if self.current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

        if self.current_user.role == "seller" and self.current_user.id != seller_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own products")

        products = (
            self.db.query(Product)
            .filter(Product.seller_id == seller_id, Product.is_deleted == False)
            .order_by(Product.created_at.desc())
            .all()
        )

        if not products:
            raise HTTPException(status_code=404, detail="No products found for this seller")

        return products

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

        # Process discount price
        discount_value = float(discount_price) if discount_price not in (None, "", "null") else None

        # Generate SKU if not provided
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

        # Upload images
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

    def get_product(self, product_id: int):
        db_product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.is_deleted == False)
            .first()
        )
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return db_product

    def get_products_by_category_name(self, category_name: str):
        category = self.db.query(Category).filter(Category.name.ilike(category_name)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        products = (
            self.db.query(Product)
            .filter(Product.category_id == category.id, Product.is_deleted == False)
            .all()
        )
        if not products:
            raise HTTPException(status_code=404, detail="No products found for this category")

        return products

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

        # Clean helper — convert "", "null", "None", "undefined" → None
        def clean_value(value):
            if value is None:
                return None
            if isinstance(value, str):
                v = value.strip().lower()
                if v in ("", "null", "none", "undefined"):
                    return None
            return value

        # Clean inputs
        name = clean_value(name)
        description = clean_value(description)
        sku = clean_value(sku)
        is_featured = clean_value(is_featured)

        # Handle numeric safely
        try:
            price = float(price) if clean_value(price) is not None else None
        except (ValueError, TypeError):
            price = None

        try:
            discount_price = str(discount_price) if clean_value(discount_price) is not None else None
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

        # Clean valid images
        valid_images = []
        if images:
            for img in images:
                if isinstance(img, UploadFile) and img.filename.strip():
                    valid_images.append(img)
        images = valid_images if valid_images else None

        # Update only valid non-empty fields
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

        # Handle image uploads
        if images:
            self.db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()
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
                        self.db.add(ProductImage(product_id=db_product.id, url=image_url, position=index))
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

        # Reset approval and activation
        db_product.status = "pending"
        db_product.is_active = False

        self.db.commit()
        self.db.refresh(db_product)
        return db_product

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

        # Soft delete instead of actual delete
        db_product.is_deleted = True
        db_product.is_active = False  # also deactivate product

        self.db.commit()
        self.db.refresh(db_product)

        return {"message": f"Product '{db_product.name}' marked as deleted successfully"}

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