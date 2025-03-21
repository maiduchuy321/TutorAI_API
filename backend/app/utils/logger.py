"""
logger.py
---------
Mục đích:
- Cấu hình và cung cấp công cụ logging cho backend.
- Hỗ trợ debug, theo dõi lỗi và ghi log các sự kiện quan trọng trong hệ thống.

Nội dung cần có:
- Thiết lập logging (ví dụ: sử dụng thư viện logging của Python).
- Các hàm hỗ trợ ghi log theo các mức độ (info, warning, error).
"""

import logging

# Cấu hình cơ bản cho logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Tạo logger để sử dụng trong các module khác
logger = logging.getLogger("chatbot_backend")
