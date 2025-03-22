"""
backend/app/services/token_service.py
------------------
Mục đích:
- Quản lý việc sử dụng token và số lượng request của người dùng.
- Thực thi các giới hạn quota và rate limit.
- Theo dõi và báo cáo thống kê sử dụng.

Chức năng chính:
- Tăng và theo dõi số lượng token đã sử dụng của người dùng theo ngày.
- Kiểm tra quota token còn lại của người dùng.
- Đếm và giới hạn số lượng request API theo ngày.
- Cung cấp API để lấy thống kê sử dụng của người dùng.
- Xử lý exception khi vượt quá giới hạn.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import date
from typing import Dict, Any, Tuple
from app.models.token_usage import TokenUsage, RequestCount
from app.models.user import User
from app.config import TOKEN_QUOTA_PER_USER, DAILY_REQUEST_LIMIT


async def increment_token_usage(db: Session, user_id: int, token_count: int) -> Dict[str, Any]:
    """
    Tăng số lượng token đã sử dụng cho một người dùng.

    Args:
        db (Session): Database session
        user_id (int): ID của người dùng
        token_count (int): Số lượng token sử dụng

    Returns:
        Dict: Thông tin về việc sử dụng token

    Raises:
        HTTPException: Nếu người dùng đã vượt quá quota
    """
    today = date.today()

    # Tìm hoặc tạo record cho ngày hôm nay
    token_usage = db.query(TokenUsage).filter(
        TokenUsage.user_id == user_id,
        TokenUsage.date == today
    ).first()

    if not token_usage:
        token_usage = TokenUsage(user_id=user_id, tokens_used=0, date=today)
        db.add(token_usage)
        db.commit()
        db.refresh(token_usage)

    # Kiểm tra nếu đã vượt quá hạn mức
    if token_usage.tokens_used + token_count > TOKEN_QUOTA_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Token quota exceeded for today"
        )

    # Cập nhật số lượng token đã sử dụng
    token_usage.tokens_used += token_count
    db.commit()
    db.refresh(token_usage)

    return {
        "user_id": user_id,
        "tokens_used": token_usage.tokens_used,
        "token_quota": TOKEN_QUOTA_PER_USER,
        "tokens_remaining": TOKEN_QUOTA_PER_USER - token_usage.tokens_used,
        "date": today
    }


async def check_token_quota(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Kiểm tra quota token của người dùng.

    Args:
        db (Session): Database session
        user_id (int): ID của người dùng

    Returns:
        Dict: Thông tin về quota token
    """
    today = date.today()

    # Tìm record cho ngày hôm nay
    token_usage = db.query(TokenUsage).filter(
        TokenUsage.user_id == user_id,
        TokenUsage.date == today
    ).first()

    tokens_used = token_usage.tokens_used if token_usage else 0

    return {
        "user_id": user_id,
        "tokens_used": tokens_used,
        "token_quota": TOKEN_QUOTA_PER_USER,
        "tokens_remaining": TOKEN_QUOTA_PER_USER - tokens_used,
        "date": today
    }


async def increment_request_count(db: Session, user_id: int) -> Tuple[bool, Dict[str, Any]]:
    """
    Tăng số lượng request đã sử dụng và kiểm tra giới hạn.

    Args:
        db (Session): Database session
        user_id (int): ID của người dùng

    Returns:
        Tuple[bool, Dict]: (Có vượt quá giới hạn không, Thông tin request count)
    """
    today = date.today()

    # Tìm hoặc tạo record cho ngày hôm nay
    request_count = db.query(RequestCount).filter(
        RequestCount.user_id == user_id,
        RequestCount.date == today
    ).first()

    if not request_count:
        request_count = RequestCount(user_id=user_id, request_count=0, date=today)
        db.add(request_count)
        db.commit()
        db.refresh(request_count)

    # Kiểm tra nếu đã vượt quá giới hạn
    if request_count.request_count >= DAILY_REQUEST_LIMIT:
        return False, {
            "user_id": user_id,
            "request_count": request_count.request_count,
            "daily_limit": DAILY_REQUEST_LIMIT,
            "requests_remaining": 0,
            "date": today
        }

    # Tăng số lượng request
    request_count.request_count += 1
    db.commit()
    db.refresh(request_count)

    return True, {
        "user_id": user_id,
        "request_count": request_count.request_count,
        "daily_limit": DAILY_REQUEST_LIMIT,
        "requests_remaining": DAILY_REQUEST_LIMIT - request_count.request_count,
        "date": today
    }


async def get_user_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Lấy thống kê sử dụng của người dùng.

    Args:
        db (Session): Database session
        user_id (int): ID của người dùng

    Returns:
        Dict: Thống kê sử dụng
    """
    # Tổng số token đã sử dụng
    total_tokens = db.query(func.sum(TokenUsage.tokens_used)).filter(
        TokenUsage.user_id == user_id
    ).scalar() or 0

    # Tổng số request
    total_requests = db.query(func.sum(RequestCount.request_count)).filter(
        RequestCount.user_id == user_id
    ).scalar() or 0

    # Thông tin quota hiện tại
    token_quota = await check_token_quota(db, user_id)

    today = date.today()
    request_count = db.query(RequestCount).filter(
        RequestCount.user_id == user_id,
        RequestCount.date == today
    ).first()

    current_requests = request_count.request_count if request_count else 0

    return {
        "user_id": user_id,
        "total_tokens_used": total_tokens,
        "total_requests": total_requests,
        "current_day": {
            "tokens": token_quota,
            "requests": {
                "count": current_requests,
                "limit": DAILY_REQUEST_LIMIT,
                "remaining": DAILY_REQUEST_LIMIT - current_requests
            }
        }
    }