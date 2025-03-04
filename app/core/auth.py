from datetime import datetime, timedelta

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_key
from app.models.user import User

JWT_SECRET = settings.CRYPTO_JWT_SECRET
JWT_ALGO = settings.CRYPTO_JWT_ALGO



def generate_jwt(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(settings.CRYPTO_JWT_DEFAULT_TIMEDELTA_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)
    return encoded_jwt


def authenticate_user(db: AsyncSession, user: User, password: str):
    if not user:
        return False
    return verify_key(password, user.password_salt, user.password)


def decode_jwt(jwt_token: str):
    payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=JWT_ALGO)
    return payload.get("sub")  # Sub dictionary key holds data we encoded


def init_auth():
    return True
