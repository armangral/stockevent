import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import http_except
from app.core.auth import decode_jwt
from app.core.db import SessionLocal
from app.crud.user import  get_user_by_username
from app.models.user import User


async def get_session():
    async with SessionLocal() as session:
        yield session
        await session.commit()
        await session.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

jwt_token_header_misc = OAuth2PasswordBearer(
    "/api/v1/auth/login", scheme_name="User login"
)


def verify_access_token(token: str, credentials_exception):
    """
    Verify the access token and extract the user email from it.
    """
    try:
        payload = decode_jwt(token)
        payload_dict = json.loads(payload)
        email: str = payload_dict.get("email")

        if email is None:
            raise credentials_exception

    except PyJWTError:
        raise credentials_exception

    return email


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
):
    """
    Get the current authenticated user based on the access token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate Credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_access_token(token, credentials_exception)
    user = await get_user_by_username(db, email)
    if not user:
        raise http_except.unexpected_error
    return user





async def get_current_active_super_admin(
    user: User = Depends(get_current_user),
):
    if not (user.is_super_admin is True):
        raise http_except.insufficaint_premissions
    return user
