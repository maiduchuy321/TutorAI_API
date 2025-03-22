"""
backend/app/models/user.py
------------------
Mục đích:
- Định nghĩa các model liên quan đến người dùng cho cả SQLAlchemy (ORM) và Pydantic (API).
- Xác định cấu trúc bảng 'users' trong database.
- Cung cấp schema cho request/response của API xác thực.

Chức năng chính:
- Định nghĩa model SQLAlchemy User với các trường: id, email, name, provider, created_at.
- Định nghĩa các Pydantic model cho API:
  + UserBase: Mô hình cơ bản với email.
  + UserCreate: Kế thừa từ UserBase, thêm name và provider.
  + UserResponse: Schema cho API response với đầy đủ thông tin người dùng.
  + Token và TokenData: Schema liên quan đến JWT authentication.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

Base = declarative_base()


class User(Base):
    """SQLAlchemy model cho người dùng"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String, nullable=True)  # Nullable vì người dùng Google OAuth không cần password
    provider = Column(String)  # 'google', 'email', etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic models cho API
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    name: str
    provider: str

    class Config:
        from_attributes = True  # Thay thế cho orm_mode=True trong Pydantic v2


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None