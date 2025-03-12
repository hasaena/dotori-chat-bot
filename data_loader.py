import csv
import os
from database import SessionLocal
from models import Product, ProductImage, FAQ, SizeChart

def load_products_from_csv(csv_file: str):
    """CSV 파일에서 상품 정보를 읽어와 데이터베이스에 저장합니다."""
    db = SessionLocal()
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                product = Product(
                    name=row['name'],
                    description=row['description'],
                    price=int(row['price']),
                    stock=int(row['stock']),
                    category=row['category']
                )
                db.add(product)
                db.commit()
                print(f"상품 추가됨: {product.name}")
    finally:
        db.close()

def load_faqs_from_csv(csv_file: str):
    """CSV 파일에서 FAQ를 읽어와 데이터베이스에 저장합니다."""
    db = SessionLocal()
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                faq = FAQ(
                    question=row['question'],
                    answer=row['answer'],
                    category=row['category']
                )
                db.add(faq)
                db.commit()
                print(f"FAQ 추가됨: {faq.question}")
    finally:
        db.close()

def add_product_image(product_id: int, image_path: str, is_main: bool = False):
    """상품 이미지를 추가합니다."""
    db = SessionLocal()
    try:
        # 실제로는 이미지를 서버에 업로드하고 URL을 저장하는 로직이 필요합니다
        image_url = f"/images/products/{os.path.basename(image_path)}"
        image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            is_main=is_main
        )
        db.add(image)
        db.commit()
        print(f"이미지 추가됨: {image_url}")
    finally:
        db.close()

def add_size_chart(product_id: int, size_info: str, image_path: str = None):
    """사이즈 정보를 추가합니다."""
    db = SessionLocal()
    try:
        size_chart = SizeChart(
            product_id=product_id,
            size_info=size_info
        )
        if image_path:
            # 실제로는 이미지를 서버에 업로드하고 URL을 저장하는 로직이 필요합니다
            size_chart.image_url = f"/images/size_charts/{os.path.basename(image_path)}"
        db.add(size_chart)
        db.commit()
        print(f"사이즈 정보 추가됨: {product_id}")
    finally:
        db.close()

if __name__ == "__main__":
    # 예시 사용법
    # load_products_from_csv("products.csv")
    # load_faqs_from_csv("faqs.csv")
    # add_product_image(1, "path/to/image.jpg", True)
    # add_size_chart(1, "S: 90-95cm\nM: 95-100cm", "path/to/size_chart.jpg") 