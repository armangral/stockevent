from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import gen_new_key
from app.models.user import User
from app.schemas.user import UserCreate, UserCreateWithAdmin
from app.utils import generate_random_password


async def get_all_users(db: AsyncSession):
    query = select(User).where(
        User.is_super_admin.is_(False) | User.is_super_admin.is_(None)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    return users

async def get_all_users_count(db: AsyncSession):
    count = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.is_super_admin.is_(False) | User.is_super_admin.is_(None))
    )
    return count.scalars().first()


async def get_users_logged_in_last_24_hours(db: AsyncSession):
    now = datetime.utcnow()
    twenty_four_hours_ago = now - timedelta(hours=24)

    query = (
        select(func.count())
        .select_from(User)
        .where(User.last_login >= twenty_four_hours_ago)
        .where(User.is_super_admin.is_(False) | User.is_super_admin.is_(None))
    )
    result = await db.execute(query)
    return result.scalar()


async def get_users_logged_in_last_n_days(db: AsyncSession, days: int):
    """
    Fetch the count of users who logged in within the last `days` days.
    """
    now = datetime.utcnow()
    n_days_ago = now - timedelta(days=days)

    query = (
            select(func.count()).select_from(User)
            .where(User.last_login >= n_days_ago)
            .where(User.is_super_admin.is_(False) | User.is_super_admin.is_(None))
    )

    result = await db.execute(query)
    return result.scalar()


# Get a user by ID
async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar()


# Get a user by username
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar()


# Create a new user
async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    password_hash = gen_new_key(user_in.password)
    new_user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        username=user_in.username,
        password=password_hash[0],
        password_salt=password_hash[1],
        is_super_admin = False,
        is_active=False,
    )

    db.add(new_user)
    await db.flush()  # This assigns an ID to the user

    return new_user



# Create a new user
async def create_user_with_admin(db: AsyncSession, user_in: UserCreateWithAdmin) -> User:
    password_hash = gen_new_key(user_in.password)
    new_user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        username=user_in.username,
        password=password_hash[0],
        password_salt=password_hash[1],
        is_super_admin=False,
        is_active=True,
        email_verified=True,

    )

    db.add(new_user)
    await db.flush()  # This assigns an ID to the user

    return new_user


# Update user
async def update_user(db: AsyncSession, user_id: int, new_data: dict) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        for key, value in new_data.items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
    return user


async def update_user_password(db: AsyncSession, user: User, new_password):
    new_pass = gen_new_key(new_password)
    user.password = new_pass[0]
    user.password_salt = new_pass[1]
    await db.flush()
    return user


# # Delete a user
# async def delete_user(db: AsyncSession, user_id: int) -> None:
#     user = await get_user_by_id(db, user_id)
#     if user:
#         await db.delete(user)
#         await db.commit()




async def get_user_by_social_id(
    db: AsyncSession, social_id: str, provider: str
) -> User | None:
    query = select(User).where(
        User.social_id == social_id, User.social_provider == provider
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_social_user(db: AsyncSession, userinfo: dict, provider: str) -> User:
    user = User(
        social_id=userinfo["id"],
        social_provider=provider,
        username=userinfo["email"],
        first_name=userinfo.get("given_name"),
        last_name=userinfo.get("family_name"),
        is_active=True,
        is_super_admin=False,
        password=generate_random_password(16),
        password_salt=generate_random_password(16),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def create_social_user_id_and_provider(db: AsyncSession, userinfo: dict, provider: str) -> User:
    user = User(
        social_id=userinfo["id"],
        social_provider=provider
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: UUID):
    # Check if the user exists
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    return {"message": "User and related data deleted successfully"}