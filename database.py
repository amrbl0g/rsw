from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    student_id = Column(String(10), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    points = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cost_points = Column(Integer, nullable=False)
    stock_quantity = Column(Integer, default=0)
    icon_name = Column(String(255), nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_name = Column(String(255), nullable=False)
    point_change = Column(Integer, nullable=False)  # positive for recycling, negative for purchases
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

# Database setup
# MySQL connection configuration from environment variables
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecovendix")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default products
    db = SessionLocal()
    try:
        # Check if products already exist
        if db.query(Product).count() == 0:
            products = [
                Product(name="Water", cost_points=15, stock_quantity=11, icon_name="water.png"),
                Product(name="Drink", cost_points=25, stock_quantity=15, icon_name="drink.png"),
                Product(name="Soda", cost_points=35, stock_quantity=9, icon_name="soda.png"),
                Product(name="Snacks", cost_points=30, stock_quantity=20, icon_name="Snacks.png"),
                Product(name="Chocolate", cost_points=50, stock_quantity=13, icon_name="chocolate.png"),
                Product(name="Biscuit", cost_points=30, stock_quantity=0, icon_name="biscuit.png"),
            ]
            for product in products:
                db.add(product)
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

