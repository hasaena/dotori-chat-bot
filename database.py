from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import settings
from models import Base, Product, ProductImage, SizeChart, FAQ, CustomerInquiry

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_product_info(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
                "images": [img.image_url for img in product.images],
                "size_charts": [{
                    "size_info": chart.size_info,
                    "image_url": chart.image_url
                } for chart in product.size_charts]
            }
        return None
    finally:
        db.close()

def get_faqs(category: str = None):
    db = SessionLocal()
    try:
        query = db.query(FAQ)
        if category:
            query = query.filter(FAQ.category == category)
        return query.all()
    finally:
        db.close()

def create_customer_inquiry(customer_id: str, question: str):
    db = SessionLocal()
    try:
        inquiry = CustomerInquiry(
            customer_id=customer_id,
            question=question
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        return inquiry
    finally:
        db.close()

def get_pending_inquiries():
    db = SessionLocal()
    try:
        return db.query(CustomerInquiry).filter(
            CustomerInquiry.status == "pending"
        ).all()
    finally:
        db.close() 