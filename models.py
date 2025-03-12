from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from config import settings

engine = create_engine(settings.DATABASE_URL)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images = relationship("ProductImage", back_populates="product")
    size_charts = relationship("SizeChart", back_populates="product")

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    image_url = Column(String(500), nullable=False)
    is_main = Column(Boolean, default=False)
    
    product = relationship("Product", back_populates="images")

class SizeChart(Base):
    __tablename__ = "size_charts"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    size_info = Column(Text, nullable=False)
    image_url = Column(String(500))
    
    product = relationship("Product", back_populates="size_charts")

class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class CustomerInquiry(Base):
    __tablename__ = "customer_inquiries"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(String(100))
    question = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    staff_notes = Column(Text)

# 데이터베이스 테이블 생성
Base.metadata.create_all(engine) 