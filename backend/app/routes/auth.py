"""
backend/app/routes/auth.py
------------------
Mục đích:
- Cung cấp các endpoint API cho việc xác thực.
- Xử lý đăng nhập với Google OAuth.
- Quản lý thông tin người dùng.

Chức năng chính:
- Cung cấp route /api/auth/google để đăng nhập bằng Google.
- Xác minh token OAuth và tạo hoặc cập nhật người dùng trong database.
- Tạo JWT access token cho người dùng đã xác thực.
- Cung cấp route /api/auth/me để lấy thông tin người dùng hiện tại.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.models.user import User, UserCreate, UserResponse, Token, UserLogin
from app.services.auth_service import (
    get_current_user,
    verify_google_token,
    create_access_token,
    get_password_hash,
    authenticate_user
)
from datetime import timedelta
from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OAUTH_GOOGLE_CLIENT_ID,
    OAUTH_GOOGLE_CLIENT_SECRET,
    OAUTH_GOOGLE_REDIRECT_URI
)
from app.database import get_db
import httpx

router = APIRouter()


# Đăng ký tài khoản mới
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Đăng ký tài khoản mới.

    Args:
        user (UserCreate): Thông tin người dùng mới
        db (Session): Database session

    Returns:
        UserResponse: Thông tin người dùng đã tạo
    """
    # Kiểm tra email đã tồn tại chưa
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Tạo người dùng mới
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        provider="email"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


# Đăng nhập với email và mật khẩu
@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Đăng nhập và tạo access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form đăng nhập
        db (Session): Database session

    Returns:
        Token: JWT token
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Đăng nhập với JSON payload (thay vì form)
@router.post("/login", response_model=Token)
async def login_json(
        user_data: UserLogin,
        db: Session = Depends(get_db)
):
    """
    Đăng nhập với JSON payload.

    Args:
        user_data (UserLogin): Thông tin đăng nhập
        db (Session): Database session

    Returns:
        Token: JWT token
    """
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "Bearer"}


# Tạo URL xác thực OAuth Google
@router.get("/google/login")
async def google_login():
    """
    Tạo URL để chuyển hướng người dùng đến trang đăng nhập Google.
    """
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={OAUTH_GOOGLE_CLIENT_ID}"
        "&response_type=code"
        "&scope=openid email profile"
        f"&redirect_uri={OAUTH_GOOGLE_REDIRECT_URI}"
        "&access_type=offline"
    )
    return {"auth_url": auth_url}


# Xử lý callback từ Google
@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Xử lý callback từ Google OAuth và tạo JWT token.

    Args:
        code (str): Authorization code từ Google
        db (Session): Database session

    Returns:
        Token: JWT token
    """
    # Trao đổi code để lấy access token
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": OAUTH_GOOGLE_CLIENT_ID,
        "client_secret": OAUTH_GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": OAUTH_GOOGLE_REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not validate Google credentials"
            )

        token_data = response.json()
        id_token = token_data.get("id_token")

        # Lấy thông tin người dùng từ token
        user_data = await verify_google_token(id_token)

        # Kiểm tra người dùng đã tồn tại chưa
        db_user = db.query(User).filter(User.email == user_data["email"]).first()

        if not db_user:
            # Tạo người dùng mới
            db_user = User(
                email=user_data["email"],
                name=user_data["name"],
                provider="google"
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        # Tạo JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": db_user.email},
            expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}


# Endpoint hiện tại vẫn giữ để hỗ trợ client có token ID Google sẵn
@router.post("/google", response_model=Token)
async def login_with_google(token: str, db: Session = Depends(get_db)):
    """
    Đăng nhập bằng Google OAuth token ID.

    Args:
        token (str): Google OAuth token
        db (Session): Database session

    Returns:
        Token: JWT token
    """
    user_data = await verify_google_token(token)

    # Kiểm tra người dùng đã tồn tại chưa
    db_user = db.query(User).filter(User.email == user_data["email"]).first()

    if not db_user:
        # Tạo người dùng mới
        db_user = User(
            email=user_data["email"],
            name=user_data["name"],
            provider="google"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Tạo JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": db_user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin người dùng hiện tại.

    Args:
        current_user (User): Người dùng hiện tại (từ token)

    Returns:
        UserResponse: Thông tin người dùng
    """
    return current_user