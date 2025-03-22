"""
backend/app/main.py
------------------
Mục đích:
- Entry point chính cho ứng dụng FastAPI, khởi tạo và cấu hình toàn bộ ứng dụng.
- Đăng ký các routes, middleware và event handlers.
- Cấu hình CORS để cho phép truy cập từ frontend.

Chức năng chính:
- Khởi tạo đối tượng FastAPI với tiêu đề và mô tả.
- Đăng ký middleware CORS và rate limiting.
- Tích hợp các router từ modules auth và chat.
- Thêm event handler để khởi tạo database khi ứng dụng bắt đầu.
- Cung cấp endpoint root đơn giản cho health check.
- Cấu hình logging để ghi lại thông tin và lỗi.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, chat_routes
from app.middleware.token_middlewave import rate_limit_middleware
from app.database import create_tables
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Tutor API",
    description="API cho ứng dụng AI Tutor dạy lập trình",
    version="0.0.1"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production, nên chỉ định cụ thể domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm middleware rate limiting
app.middleware("http")(rate_limit_middleware)

# Thêm các router
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["Chat"])

@app.get("/")
async def root():
    return {"message": "Welcome to AI Tutor API"}

# Tạo bảng khi khởi động
@app.on_event("startup")
async def startup_event():
    logger.info("Creating database tables if they don't exist...")
    create_tables()
    logger.info("Application startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)