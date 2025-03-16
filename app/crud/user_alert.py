from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import SessionLocal
from app.models.user_alert import UserAlert
from app.schemas.user_alert import UserAlertCreate
from app.utils import send_email_alert
import yfinance as yf
from celery_config import celery


# Create Alert
async def create_user_alert(db: AsyncSession, alert_data: UserAlertCreate):
    existing_alert = await db.execute(
        select(UserAlert).where(
            UserAlert.email == alert_data.email,
            UserAlert.symbol == alert_data.symbol.upper(),
            UserAlert.target_price == alert_data.target_price,
        )
    )
    if existing_alert.scalar():
        raise HTTPException(status_code=400, detail="Alert already exists")

    alert = UserAlert(
        email=alert_data.email,
        symbol=alert_data.symbol.upper(),
        target_price=alert_data.target_price,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert




# celery = Celery(__name__, broker="redis://redis:6379/0")



@celery.task
def run_price_check():
    # Use a synchronous DB session here since Celery tasks are not async
    with SessionLocal() as db:
        alerts = db.execute(select(UserAlert).where(UserAlert.is_active == True))
        alerts = alerts.scalars().all()

        for alert in alerts:
            stock_data = yf.Ticker(alert.symbol).info
            current_price = stock_data.get("currentPrice")

            print("Checking the price from cleery now")

            if current_price and current_price >= alert.target_price:
                send_email_alert(  # Sync version here
                    alert.email,
                    f"{alert.symbol} Alert!",
                    f"{alert.symbol} has reached ${alert.target_price}!",
                )
                alert.is_active = False
                db.commit()


# @celery.task
# async def run_price_check(db: AsyncSession):
#     alerts = await db.execute(select(UserAlert).where(UserAlert.is_active == True))
#     alerts = alerts.scalars().all()

#     for alert in alerts:
#         stock_data = yf.Ticker(alert.symbol).info
#         current_price = stock_data.get("currentPrice")

#         if current_price and current_price >= alert.target_price:
#             await send_email_alert(
#                 alert.email,
#                 f"{alert.symbol} Alert!",
#                 f"{alert.symbol} has reached ${alert.target_price}!",
#             )
#             alert.is_active = False
#             await db.commit()
