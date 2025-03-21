"""
config.py
---------
Mục đích:
- Quản lý các cấu hình chung của backend, chẳng hạn như cấu hình server, database, và các biến môi trường.
- Tách biệt cấu hình ra khỏi code chính để dễ bảo trì và tùy chỉnh theo từng môi trường (development, testing, production).

Nội dung cần có:
- Đọc biến môi trường (sử dụng os.environ hoặc thư viện như python-decouple).
- Định nghĩa các cấu hình: HOST, PORT, DEBUG, DATABASE_URL, API keys, ...
- Có thể sử dụng Pydantic settings cho cấu hình có kiểu dữ liệu.
"""
import os
from dotenv import load_dotenv
from ..app.models.reflection import Reflection

# Nạp biến môi trường từ .env file
load_dotenv()

# Cấu hình API
API_KEY = os.getenv("api_key_fpt")
GEN_API_URL = os.getenv("api_url_fpt")

# Khởi tạo reflection
REFLECTION = Reflection()

# Cấu hình mô hình
DEFAULT_MODEL = "LLama-3.3-70B-Instruct"
MAX_TOKENS = 800

# Cấu hình server
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1", "t"]
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# import os
# from pydantic import BaseSettings
#
#
# class Settings(BaseSettings):
#     # Cấu hình server
#     HOST: str = os.getenv("HOST", "0.0.0.0")
#     PORT: int = int(os.getenv("PORT", 8000))
#     DEBUG: bool = os.getenv("DEBUG", "True") == "True"
#
#     # Cấu hình database
#     # DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
#
#     # Cấu hình LLM
#     FPT_API_KEY: str = os.getenv("FPT_API_KEY")
#     FPT_API_URL: str = os.getenv("FPT_API_URL")
#
#     # Cấu hình Langfuse
#     LANGFUSE_SECRET_KEY: str = os.environ["LANGFUSE_SECRET_KEY"]
#     LANGFUSE_PUBLIC_KEY: str = os.environ["LANGFUSE_PUBLIC_KEY"]
#     LANGFUSE_HOST: str = os.environ["LANGFUSE_HOST"]
#
#     class Config:
#         env_file = ".env"
#
#
# # Khởi tạo cấu hình toàn cục
# settings = Settings()
