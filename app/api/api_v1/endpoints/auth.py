
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.crud.invitation import get_valid_invitation_by_token, get_valid_password_invitation_by_token
from app.models.invitation import Invitation
from app.models.invitation_password import InvitationPassword
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdatePassword
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import http_except
from app.api.deps import get_current_user, get_session
from app.core.auth import authenticate_user, generate_jwt
from app.core.config import settings
from app.crud.user import create_user, get_user_by_id, get_user_by_username, update_user_password
from app.utils import send_password_reset_email, send_verification_email

router = APIRouter()


@router.post("/login")
async def user_login(
    data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    if not data.username:
        raise http_except.incorrect_usrnm_passwd
    
    print(data.username)

    user = await get_user_by_username(db, data.username)
    print("user is ",user)
    if not user:
        raise http_except.incorrect_usrnm_passwd

    valid = authenticate_user(db, user, data.password)
    if not valid:
        raise http_except.incorrect_usrnm_passwd
    
    if user.email_verified is False:
        raise http_except.email_not_verified

    if user.is_active is False:
        raise http_except.inactive_user

    jwt_client_access_timedelta = timedelta(
        minutes=settings.CRYPTO_JWT_ACESS_TIMEDELTA_MINUTES
    )
    data_to_be_encoded = {
        "email": user.username,
        "type": "acess_token",
    }

    new_jwt_access = generate_jwt(
        data={"sub": json.dumps(data_to_be_encoded)},
        expires_delta=jwt_client_access_timedelta,
    )

    user.last_login = datetime.now()

    print("user.last_login",user.last_login)

    await db.commit()

    return {"access_token": new_jwt_access, "token_type": "bearer", "is_superadmin":user.is_super_admin}




@router.post("/register", status_code=201)
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):

    # Check if user already exists
    user = await get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the new user
    new_user = await create_user(db, user_in)

    if new_user:
        token = str(new_user.id) + "788"
        expires_at = datetime.utcnow() + timedelta(days=7)
        new_invitation = Invitation(
            email=new_user.username,
            token=token,
            expires_at=expires_at,
        )
        db.add(new_invitation)
        await db.flush()

        try:
            background_tasks.add_task(
                send_verification_email,
                user_in.username,
                token,
                expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            )
        except Exception as e:
            print(f"email not sent. there is an error {e}")


    return {"message": "User has been registered. Please check your email for verification", "user_id": new_user.id}


@router.get("/me", response_model=UserOut)
async def get_user_information(
    db: AsyncSession = Depends(get_session), u=Depends(get_current_user)
):
    user = await get_user_by_id(db, u.id)
    return user


@router.post("/verify-email/{token}")
async def accept_invitation(token: str, db: AsyncSession = Depends(get_session)):
    invitation = await get_valid_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invlid Verification"
        )

    get_user = await get_user_by_username(db, invitation.email)

    if not get_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found or deleted"
        )

    get_user.email_verified = True
    get_user.is_active = True
    await db.commit()

    await db.delete(invitation)
    await db.commit()


@router.patch("/update_password", response_model=None)
async def update_password(
    data: UserUpdatePassword,
    db: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
):


    valid = authenticate_user(db, user, data.old_password)
    if not valid:
        raise http_except.incorrect_usrnm_passwd

    if len(data.new_password) < settings.CRYPTO_MIN_PASSWD_LENGTH:
        raise http_except.short_password
    # Redundat
    user = await update_user_password(db, user, data.new_password)



@router.post("/forgot-password", status_code=200)
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    # Check if user exists
    user = await get_user_by_username(db, username=email)
    if not user:
        # Return success even if email doesn't exist (for security)
        return {"message": "If email exists, password reset instructions will be sent"}

    # Create password reset token
    token = str(user.id) + "788"  # Using same token format as registration
    expires_at = datetime.utcnow() + timedelta(minutes=60)  # 60 minutes expiration

    # Create password reset invitation
    password_reset_invite = InvitationPassword(
        email=user.username,
        token=token,
        expires_at=expires_at,
    )
    db.add(password_reset_invite)
    await db.flush()

    try:
        background_tasks.add_task(
            send_password_reset_email,
            user.username,
            token,
            expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
    except Exception as e:
        print(f"Password reset email not sent. Error: {e}")

    return {"message": "If email exists, password reset instructions will be sent"}


@router.post("/reset-password/{token}", status_code=200)
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_session),
):
    # Verify token and get invitation
    invitation = await get_valid_password_invitation_by_token(
        db, token
    )
    if not invitation:
        raise http_except.invalid_token

    # Get user by email
    user = await get_user_by_username(db, username=invitation.email)
    if not user:
        raise http_except.invalid_token

    # Validate password length
    if len(new_password) < settings.CRYPTO_MIN_PASSWD_LENGTH:
        raise http_except.short_password

    # Update password
    await update_user_password(db, user, new_password)

    # Delete the used invitation
    await db.delete(invitation)
    await db.flush()

    return {"message": "Password has been reset successfully"}