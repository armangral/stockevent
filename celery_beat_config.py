from celery.schedules import crontab
from celery_config import celery

celery.conf.beat_schedule = {
    "check-prices-every-5-minutes": {
        "task": "app.crud.user_alert.run_price_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}
