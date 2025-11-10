import pytest
from fastapi import UploadFile
from src.utils.bulk_upload import process_upload_file, validate_row, save_products_batch
from src.schemas.products import BulkUploadRow
import pandas as pd
import io
from unittest.mock import MagicMock, patch

@pytest.fixture
def sample_csv_content():
    return """name,description,price,stock,sku,category_id,images
Product1,Description1,10.99,100,SKU001,1,https://example.com/img1.jpg|https://example.com/img2.jpg
Product2,Description2,20.99,200,SKU002,1,https://example.com/img3.jpg
Invalid,,,-50,SKU003,invalid"""

@pytest.fixture
def sample_excel_content():
    df = pd.DataFrame({
        'name': ['Product1', 'Product2', 'Invalid'],
        'description': ['Description1', 'Description2', ''],
        'price': [10.99, 20.99, -10],
        'stock': [100, 200, -50],
        'sku': ['SKU001', 'SKU002', 'SKU003'],
        'category_id': [1, 1, 'invalid'],
        'images': ['https://example.com/img1.jpg|https://example.com/img2.jpg', 'https://example.com/img3.jpg', '']
    })
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer.read()

async def test_process_upload_csv(sample_csv_content):
    # Create mock UploadFile
    file = UploadFile(filename="test.csv")
    file.read = MagicMock(return_value=sample_csv_content.encode())
    
    df = await process_upload_file(file, seller_id=1)
    assert len(df) == 3
    assert list(df.columns) == ['name', 'description', 'price', 'stock', 'sku', 'category_id']

async def test_process_upload_excel(sample_excel_content):
    file = UploadFile(filename="test.xlsx")
    file.read = MagicMock(return_value=sample_excel_content)
    
    df = await process_upload_file(file, seller_id=1)
    assert len(df) == 3
    assert list(df.columns) == ['name', 'description', 'price', 'stock', 'sku', 'category_id']

def test_validate_row():
    valid_row = {
        'name': 'Test Product',
        'description': 'Test Description',
        'price': 10.99,
        'stock': 100,
        'sku': 'SKU001',
        'category_id': 1
    }
    
    is_valid, product = validate_row(valid_row, 1)
    assert is_valid
    assert product.status == "success"
    assert product.error_message is None
    
    invalid_row = {
        'name': '',
        'price': -10,
        'stock': -50,
        'sku': '',
        'category_id': 'invalid'
    }
    
    is_valid, product = validate_row(invalid_row, 2)
    assert not is_valid
    assert product.status == "error"
    assert product.error_message is not None

@pytest.mark.asyncio
async def test_save_products_batch(db_session):
    products = [
        BulkUploadRow(
            name="Test Product",
            description="Test Description",
            price=10.99,
            stock=100,
            sku=f"SKU{i}",
            category_id=1,
            row_number=i,
            status="success"
        )
        for i in range(5)
    ]
    
    success, errors = save_products_batch(db_session, products, seller_id=1, batch_size=2)
    assert len(success) == 5
    assert len(errors) == 0