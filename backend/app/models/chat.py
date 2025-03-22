"""
backend/app/models/chat.py
------------------
Mục đích:
- Định nghĩa cấu trúc dữ liệu cho cuộc trò chuyện và tin nhắn.
- Xác định mối quan hệ giữa người dùng, cuộc trò chuyện và tin nhắn.
- Cung cấp schema cho request/response của API chat.

Chức năng chính:
- Định nghĩa model SQLAlchemy Conversation với các trường: id, user_id, title, timestamps.
- Định nghĩa model SQLAlchemy Message với các trường: id, conversation_id, role, content, timestamp.
- Thiết lập relationship giữa Conversation và Message.
- Định nghĩa các Pydantic model cho API:
  + MessageBase, MessageCreate, MessageResponse: Schema cho tin nhắn.
  + ConversationBase, ConversationCreate, ConversationResponse: Schema cho cuộc trò chuyện.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

Base = declarative_base()


class Conversation(Base):
    """SQLAlchemy model cho cuộc hội thoại"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Conversation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """SQLAlchemy model cho tin nhắn"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # 'user' hoặc 'assistant'
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


# Pydantic models cho API
class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ConversationBase(BaseModel):
    title: str = "New Conversation"


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True