"""
backend/app/database.py
------------------
Mục đích:
- Cấu hình kết nối database cho toàn bộ ứng dụng.
- Cung cấp session và engine SQLAlchemy.
- Khởi tạo bảng trong database.

Chức năng chính:
- Tạo SQLAlchemy engine với cấu hình kết nối PostgreSQL.
- Cấu hình connection pool để tối ưu hiệu suất.
- Tạo session factory để tương tác với database.
- Định nghĩa base class cho các model SQLAlchemy.
- Cung cấp dependency get_db để sử dụng database session trong API.
- Hàm create_tables để khởi tạo schema database.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo engine SQLAlchemy với PostgreSQL
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các model
Base = declarative_base()

# Dependency để có database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Tạo các bảng
def create_tables():
    Base.metadata.create_all(bind=engine)