from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_async_engine(f"postgresql+asyncpg://{settings.SQLALCHEMY_DATABASE_URI}")

SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


Base = declarative_base()


sync_engine = create_engine(f"postgresql://{settings.SQLALCHEMY_DATABASE_URI}")



# Sync session for Celery
SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)