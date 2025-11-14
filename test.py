from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from src.core.database import Base  # ✅ correct import
from src.models.orders import Cart, CartItem  # import your models

DATABASE_URL="postgresql://ecommerce_mfs3_user:mcuP5dcsxUVIN7fOQHWvxgXIvIwmWUEs@dpg-d3o9m7ili9vc73bv0rjg-a.singapore-postgres.render.com/ecommerce_mfs3"

engine = create_engine(DATABASE_URL)

inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"Existing tables: {existing_tables}")

for table in Base.metadata.sorted_tables:
    if table.name not in existing_tables:
        print(f"Creating missing table: {table.name}")
        try:
            table.create(engine)
            print(f"✅ Table {table.name} created successfully.")
        except SQLAlchemyError as e:
            print(f"❌ Error creating table {table.name}: {e}")

print("All missing tables processed.")
