from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user_alert import UserAlertCreate, UserAlertResponse
from app.crud.user_alert import create_user_alert, run_price_check
from app.api.deps import get_session

router = APIRouter()


@router.post("/", response_model=UserAlertResponse)
async def set_price_alert(
    alert: UserAlertCreate, db: AsyncSession = Depends(get_session)
):
    return await create_user_alert(db, alert)


@router.get("/check/")
async def run_check(db: AsyncSession = Depends(get_session)):
    await run_price_check(db).delay()  # Manually trigger the Celery task
    return {"message": "Price check task started"}
