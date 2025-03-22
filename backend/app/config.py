"""
backend/app/config.py
------------------
Mục đích:
- Tập trung quản lý tất cả các cấu hình của ứng dụng.
- Đọc và cung cấp các biến môi trường cho toàn bộ ứng dụng.
- Định nghĩa các giá trị mặc định cho cấu hình.

Chức năng chính:
- Đọc biến môi trường từ file .env bằng dotenv.
- Cấu hình kết nối API LLM (key, URL, model, max tokens).
- Cấu hình database connection (PostgreSQL).
- Cấu hình JWT cho xác thực (secret key, thời hạn token).
- Cấu hình rate limiting và quota token cho người dùng.
- Khởi tạo đối tượng Reflection để xử lý lịch sử chat.
"""

import os
from dotenv import load_dotenv
from app.utils.reflection import Reflection

# Load biến môi trường
load_dotenv()

# Cấu hình API
API_KEY = os.getenv("api_key_fpt")
GEN_API_URL = os.getenv("api_url_fpt")

# Khởi tạo reflection
REFLECTION = Reflection()

# Cấu hình mô hình
DEFAULT_MODEL = "LLama-3.3-70B-Instruct"
MAX_TOKENS = 800

# Cấu hình Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/aitutor")

#Cấu hình Google
OAUTH_GOOGLE_CLIENT_ID = os.getenv("OAUTH_GOOGLE_CLIENT_ID")
OAUTH_GOOGLE_CLIENT_SECRET = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET")
OAUTH_GOOGLE_REDIRECT_URI = os.getenv("OAUTH_GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

# Cấu hình JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cấu hình Rate Limiting và Token Usage
DAILY_REQUEST_LIMIT = int(os.getenv("DAILY_REQUEST_LIMIT", "100"))  # Giới hạn số request mỗi ngày cho mỗi người dùng
TOKEN_QUOTA_PER_USER = int(os.getenv("TOKEN_QUOTA_PER_USER", "10000"))  # Hạn mức token cho mỗi người dùng