from datetime import datetime, timedelta
import json
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import http_except
from app.api.deps import (
    get_current_active_super_admin,

    get_session,
)

from app.core.auth import authenticate_user, generate_jwt
from app.crud.property import delete_property
from app.crud.user import (
    create_user_with_admin,
    delete_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
)

from app.models.invitation import Invitation
from app.models.user import UserRole


from app.schemas.user import UserCreateWithAdmin, UserOut, UserOutForadmin
from app.core.config import settings
from app.utils import send_verification_email, send_welcome_email

router = APIRouter()


# Get all users
@router.get("/users", response_model=list[UserOutForadmin])
async def fetch_all_users(
    db: AsyncSession = Depends(get_session),
    # admin=Depends(get_current_active_super_admin),
):
    users = await get_all_users(db)
    if not users:
        return []
    return users


# # Get all users count
# @router.get("/users/count")
# async def fetch_all_users_count(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     count = await get_all_users_count(db)
#     return {"all_users_count": count}


# # Get number of users logged in within the last 24 hours
# @router.get("/users/logged_in_last_24_hours")
# async def fetch_users_logged_in_last_24_hours(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     count = await get_users_logged_in_last_24_hours(db)
#     return {"users_logged_in_last_24_hours": count}


# @router.get("/users/logged_in_last_7_days")
# async def fetch_users_logged_in_last_7_days(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     """
#     Route to get the number of users logged in within the last 7 days.
#     """
#     count = await get_users_logged_in_last_n_days(db, days=7)
#     return {"users_logged_in_last_7_days": count}


# @router.get("/users/logged_in_last_28_days")
# async def fetch_users_logged_in_last_28_days(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     """
#     Route to get the number of users logged in within the last 28 days.
#     """
#     count = await get_users_logged_in_last_n_days(db, days=28)
#     return {"users_logged_in_last_28_days": count}


@router.post("/users")
async def create_new_user(
    user_in: UserCreateWithAdmin,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    # admin=Depends(get_current_active_super_admin),
):
    user = await get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await create_user_with_admin(db, user_in)

    if new_user:

        try:
            background_tasks.add_task(
                send_welcome_email,
                user_in.username,
                user_in.password
            )
        except Exception as e:
            print(f"email not sent. there is an error {e}")

    await db.commit()
    return {"msg": "User created successfully"}


@router.post("/login")
async def user_login(
    data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    if not data.username:
        raise http_except.incorrect_usrnm_passwd

    print(data.username)

    user = await get_user_by_username(db, data.username)
    print("user is ", user)
    if not user:
        raise http_except.incorrect_usrnm_passwd

    valid = authenticate_user(db, user, data.password)
    if not valid:
        raise http_except.incorrect_usrnm_passwd

    if user.is_active is False:
        raise http_except.inactive_user

    if user.role != UserRole.SUPER_ADMIN:
        raise http_except.incorrect_usrnm_passwd


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

    print("user.last_login", user.last_login)

    await db.commit()

    return {
        "access_token": new_jwt_access,
        "token_type": "bearer",
        "is_superadmin": user.is_super_admin,
        "role": user.role,
    }


# # Set the status of user as active
@router.put("/users/activate/{user_id}")
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    # admin=Depends(get_current_active_super_admin),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    user.email_verified = True
    await db.commit()
    return {"msg": "User activated successfully"}


# Set the status of user as inactive
@router.put("/users/deactivate/{user_id}")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    # admin=Depends(get_current_active_super_admin),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()
    return {"msg": "User deactivated successfully"}


@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
   
):
    """
    Delete a user and all related data.
    """
    return await delete_user(db, user_id)



@router.delete("/properties/{property_id}")
async def delete_property_endpoint(
    property_id: str,
    db: AsyncSession = Depends(get_session),
    # admin=Depends(get_current_active_super_admin),  # Uncomment if admin authentication is required
):
    """
    Delete a specific property by its ID and clean up its associations.
    """
    success = await delete_property(db, property_id)
    if not success:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": f"Property with ID {property_id} successfully deleted"}


# @router.get("/properties/active_count")
# async def fetch_active_listings_count(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     """
#     Route to get the count of active property listings.
#     """
#     count = await get_active_listings_count(db)
#     return {"active_listings_count": count}


# @router.get("/properties/insufficient_data_count")
# async def fetch_insufficient_data_listings_count(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     """
#     Route to get the count of listings with insufficient data.
#     """
#     count = await get_insufficient_data_listings_count(db)
#     return {"insufficient_data_listings_count": count}


# @router.get("/properties/updated_count")
# async def fetch_updated_listings_count(
#     db: AsyncSession = Depends(get_session),
#     admin=Depends(get_current_active_super_admin),
# ):
#     """
#     Route to get the count of property listings updated in the last `days` days.
#     """
#     count = await get_updated_listings_count(db)
#     return {"updated_listings_count": count}


