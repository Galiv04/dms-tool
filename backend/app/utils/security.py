from datetime import datetime, timedelta, timezone
from typing import Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.config import settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash password usando Argon2id"""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password contro hash Argon2id"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """Crea JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str):
    """Verifica JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError:
        return None
