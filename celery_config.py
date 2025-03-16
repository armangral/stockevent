from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["app.crud.user_alert"],
)

celery.conf.update(
    task_routes={
        "app.crud.user_alert.*": {"queue": "default"},
    },
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-prices-every-1-minutes": {
            "task": "app.crud.user_alert.run_price_check",
            "schedule": crontab(minute="*/1"),
        }
    },
    result_backend="redis://redis:6379/0",  # Ensures Beat schedule is also tracked in Redis
)

if __name__ == "__main__":
    celery.start()
