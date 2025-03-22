"""
backend/app/middleware/token_middleware.py
------------------
Mục đích:
- Giám sát và kiểm soát tất cả các request đến API.
- Thực thi giới hạn số lượng request theo ngày.
- Thêm thông tin rate limiting vào response header.

Chức năng chính:
- Middleware rate_limit_middleware xử lý mỗi request.
- Bỏ qua kiểm tra cho các endpoint công khai (auth, docs).
- Trích xuất và xác minh JWT token.
- Tăng số lượng request và kiểm tra giới hạn.
- Thêm headers X-Rate-Limit-* vào response.
- Đo thời gian xử lý request và thêm vào header X-Process-Time.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
import time
from app.config import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.services.token_service import increment_request_count
from app.database import get_db


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware để kiểm tra rate limiting.

    Args:
        request (Request): FastAPI request
        call_next: Next middleware function

    Returns:
        Response: FastAPI response
    """
    # Bỏ qua kiểm tra cho một số endpoint
    if request.url.path in ["/api/auth/token", "/api/auth/google", "/docs", "/openapi.json", "/"]:
        return await call_next(request)

    # Trích xuất token JWT từ header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return await call_next(request)

    token = authorization.replace("Bearer ", "")

    try:
        # Giải mã token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if email is None:
            return await call_next(request)

        # Lấy database session
        db = next(get_db())

        # Tìm người dùng
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return await call_next(request)

        # Kiểm tra rate limiting
        is_allowed, request_info = await increment_request_count(db, user.id)

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Daily request limit exceeded",
                    "limit": request_info["daily_limit"],
                    "reset_at": datetime.combine(request_info["date"], datetime.min.time()).timestamp() + 86400
                }
            )

        # Lưu user_id vào request state để sử dụng sau này
        request.state.user_id = user.id

        # Tiếp tục xử lý request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Thêm headers về rate limiting
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Rate-Limit-Limit"] = str(request_info["daily_limit"])
        response.headers["X-Rate-Limit-Remaining"] = str(request_info["requests_remaining"])

        return response

    except JWTError:
        return await call_next(request)
    except Exception as e:
        # Log lỗi nhưng vẫn cho phép request tiếp tục
        print(f"Rate limit middleware error: {e}")
        return await call_next(request)