"""
backend/app/services/auth_service.py
------------------
Mục đích:
- Xử lý xác thực và ủy quyền cho người dùng.
- Tạo và xác minh JWT token.
- Xác thực người dùng với OAuth (Google).

Chức năng chính:
- Tạo JWT access token với thời gian hết hạn có thể cấu hình.
- Xác minh JWT token và trích xuất thông tin người dùng.
- Cung cấp dependency get_current_user để bảo vệ các endpoint.
- Xác thực token OAuth từ Google và lấy thông tin người dùng.
- Xử lý các exception khi xác thực thất bại.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.user import User, TokenData
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

from app.database import get_db

# Thêm đoạn này để xử lý hash mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def verify_password(plain_password, hashed_password):
    """Xác minh mật khẩu"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash mật khẩu"""
    return pwd_context.hash(password)


async def authenticate_user(db: Session, email: str, password: str):
    """Xác thực người dùng bằng email và mật khẩu"""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.hashed_password:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Tạo JWT token.

    Args:
        data (dict): Dữ liệu để mã hóa
        expires_delta (timedelta, optional): Thời gian hết hạn

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Lấy người dùng hiện tại từ token.

    Args:
        token (str): JWT token
        db (Session): Database session

    Returns:
        User: Đối tượng người dùng

    Raises:
        HTTPException: Nếu token không hợp lệ
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()

    if user is None:
        raise credentials_exception

    return user


async def verify_google_token(token: str):
    """
    Xác thực token OAuth từ Google.

    Args:
        token (str): Token OAuth từ Google

    Returns:
        dict: Thông tin người dùng từ Google
    """
    # Trong môi trường thực tế, bạn cần thêm logic xác thực token OAuth
    # Đây là một triển khai giả
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from app.config import OAUTH_GOOGLE_CLIENT_ID

    try:
        # Xác thực Google token và lấy thông tin người dùng
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            OAUTH_GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        return {
            "email": idinfo['email'],
            "name": idinfo.get('name', ''),
            "provider": "google"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )