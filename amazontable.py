from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# --- Define Tables ---
class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True)
    amazon_url = Column(Text, unique=True)
    title = Column(Text)
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="product", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    asin = Column(String, nullable=True) 
class Price(Base):
    __tablename__ = 'prices'
    price_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    price = Column(Text)
    scraped_at = Column(TIMESTAMP, server_default=func.now())
    product = relationship("Product", back_populates="prices")

class Rating(Base):
    __tablename__ = 'ratings'
    rating_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    rating = Column(Text)
    review_count = Column(Integer)
    scraped_at = Column(TIMESTAMP, server_default=func.now())
    product = relationship("Product", back_populates="ratings")

class Image(Base):
    __tablename__ = 'images'
    image_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    image_url = Column(Text)
    product = relationship("Product", back_populates="images")

class Review(Base):
    __tablename__ = 'reviews'
    review_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    reviewer_name = Column(Text)
    review_title = Column(Text)
    review_body = Column(Text)
    review_rating = Column(Text)
    review_date = Column(Text)
    product = relationship("Product", back_populates="reviews")













# --- Connect to PostgreSQL ---
engine = create_engine("postgresql://postgres:9698@localhost:5432/ecommercedb")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()