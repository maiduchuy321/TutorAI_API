"""
backend/app/models/token_usage.py
------------------
Mục đích:
- Theo dõi và quản lý việc sử dụng token và số lượng request của người dùng.
- Hỗ trợ tính năng rate limiting và quota token.
- Cung cấp cấu trúc dữ liệu cho thống kê sử dụng.

Chức năng chính:
- Định nghĩa model SQLAlchemy TokenUsage để theo dõi số token đã dùng theo ngày.
- Định nghĩa model SQLAlchemy RequestCount để đếm số request theo ngày.
- Đảm bảo mỗi người dùng chỉ có một bản ghi cho mỗi ngày bằng unique constraint.
- Định nghĩa Pydantic model TokenUsageResponse và RequestCountResponse cho API response.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

Base = declarative_base()

class TokenUsage(Base):
    """SQLAlchemy model để theo dõi việc sử dụng token"""
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tokens_used = Column(Integer, default=0)
    date = Column(Date, default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Đảm bảo mỗi người dùng chỉ có một record cho mỗi ngày
    __table_args__ = (UniqueConstraint('user_id', 'date', name='unique_user_date'),)

class RequestCount(Base):
    """SQLAlchemy model để theo dõi số lượng request"""
    __tablename__ = "request_count"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request_count = Column(Integer, default=0)
    date = Column(Date, default=func.current_date())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Đảm bảo mỗi người dùng chỉ có một record cho mỗi ngày
    __table_args__ = (UniqueConstraint('user_id', 'date', name='unique_user_request_date'),)

# Pydantic models cho API
class TokenUsageResponse(BaseModel):
    user_id: int
    tokens_used: int
    token_quota: int
    tokens_remaining: int
    date: date

    class Config:
        orm_mode = True

class RequestCountResponse(BaseModel):
    user_id: int
    request_count: int
    daily_limit: int
    requests_remaining: int
    date: date

    class Config:
        orm_mode = True