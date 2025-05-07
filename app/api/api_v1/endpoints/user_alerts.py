from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.user_alert import UserAlert
from app.schemas.user_alert import UserAlertCreate, UserAlertResponse
from app.crud.user_alert import create_user_alert, run_price_check
from app.api.deps import get_current_user, get_session

router = APIRouter()


@router.get("/", response_model=list[UserAlertResponse])
async def get_user_alerts(
    db: AsyncSession = Depends(get_session),
    user:User=Depends(get_current_user),
):
    result = await db.execute(select(UserAlert).where(UserAlert.email == user.username))
    alerts = result.scalars().all()
    return alerts


@router.post("/", response_model=UserAlertResponse)
async def set_price_alert(
    alert: UserAlertCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return await create_user_alert(db, alert,user.username)


@router.get("/check/")
async def run_check():
    run_price_check.delay()  # Manually trigger the Celery task
    return {"message": "Price check task started"}

