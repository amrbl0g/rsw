from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, text
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
    student_id = Column(Integer, unique=True, nullable=False, index=True)
    password = Column(Integer, nullable=False)
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
# Prefer a full DATABASE_URL (as provided by Railway), otherwise assemble from available MySQL pieces.

def _build_mysql_url(prefix: str) -> str | None:
    """Construct a MySQL URL from env parts. Returns None if host or database missing."""
    user = os.getenv(f"{prefix}MYSQL_USER") or os.getenv(f"{prefix}MYSQLUSERNAME")
    password = os.getenv(f"{prefix}MYSQL_PASSWORD") or os.getenv(f"{prefix}MYSQLPASSWORD") or ""
    host = os.getenv(f"{prefix}MYSQL_HOST") or os.getenv(f"{prefix}MYSQLHOST")
    port = os.getenv(f"{prefix}MYSQL_PORT") or os.getenv(f"{prefix}MYSQLPORT") or "3306"
    database = os.getenv(f"{prefix}MYSQL_DATABASE") or os.getenv(f"{prefix}MYSQLDATABASE")
    if not host or not database:
        return None
    user = user or "root"
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

database_url = os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL")
if not database_url:
    # Try common Railway variable names without DATABASE_URL
    database_url = _build_mysql_url(prefix="")

if database_url:
    # SQLAlchemy needs the pymysql driver prefix for MySQL URLs
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    SQLALCHEMY_DATABASE_URL = database_url
else:
    # Last resort fallback to localhost dev defaults
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost:3306/ecovendix"

# Log a minimal connection summary for debugging (no password).
_dbg_host = SQLALCHEMY_DATABASE_URL.split("@")[-1].split("/")[0]
_dbg_db = SQLALCHEMY_DATABASE_URL.rsplit("/", 1)[-1]
print(f"[database] Using MySQL at {_dbg_host}, db={_dbg_db}")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_password_column():
    """Migrate password_hash column to password column"""
    try:
        with engine.begin() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                # Table doesn't exist yet, migration not needed
                return
            
            # Check if password_hash column exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users'
                AND COLUMN_NAME = 'password_hash'
            """))
            has_old_column = result.fetchone()[0] > 0
            
            if has_old_column:
                # Check if password column already exists
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'users'
                    AND COLUMN_NAME = 'password'
                """))
                has_new_column = result.fetchone()[0] > 0
                
                if not has_new_column:
                    # Add new password column with default value
                    conn.execute(text("ALTER TABLE users ADD COLUMN password INT DEFAULT 1234"))
                
                # Drop old password_hash column
                conn.execute(text("ALTER TABLE users DROP COLUMN password_hash"))
                print("Migration completed: password_hash -> password")
    except Exception as e:
        print(f"Migration warning: {e}")
        # Continue anyway - table might not exist yet

def migrate_student_id_column():
    """Migrate student_id column from VARCHAR to INT"""
    try:
        with engine.begin() as conn:
            # Check if users table exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users'
            """))
            table_exists = result.fetchone()[0] > 0
            
            if not table_exists:
                # Table doesn't exist yet, migration not needed
                return
            
            # Check current column type
            result = conn.execute(text("""
                SELECT DATA_TYPE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'users'
                AND COLUMN_NAME = 'student_id'
            """))
            column_info = result.fetchone()
            
            if column_info and column_info[0] in ['varchar', 'char', 'text']:
                # Convert VARCHAR to INT
                # First, ensure all values are numeric (they should be based on validation)
                conn.execute(text("ALTER TABLE users MODIFY COLUMN student_id INT"))
                print("Migration completed: student_id VARCHAR -> INT")
    except Exception as e:
        print(f"Migration warning: {e}")
        # Continue anyway - table might not exist yet or already migrated

def init_db():
    # Run migrations first
    migrate_password_column()
    migrate_student_id_column()
    
    Base.metadata.create_all(bind=engine)
    
    # Seed default products
    db = SessionLocal()
    try:
        # Check if products already exist
        if db.query(Product).count() == 0:
            products = [
                Product(name="Water", cost_points=15, stock_quantity=0, icon_name="water.png"),
                Product(name="Drink", cost_points=25, stock_quantity=0, icon_name="drink.png"),
                Product(name="Soda", cost_points=35, stock_quantity=0, icon_name="soda.png"),
                Product(name="Snacks", cost_points=30, stock_quantity=0, icon_name="Snacks.png"),
                Product(name="Chocolate", cost_points=50, stock_quantity=0, icon_name="chocolate.png"),
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

