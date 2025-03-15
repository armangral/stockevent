from celery import Celery

celery = Celery(
    "worker",
    broker="redis://redis_stockevent:6379/0",  # Use service name in Docker Compose as hostname
    backend="redis://redis_stockevent:6379/0",
    include=["app.crud.user_alert"],
)

celery.conf.update(
    task_routes={
        "app.crud.user_alert.*": {"queue": "default"},
    },
    timezone="UTC",
    enable_utc=True,
)

if __name__ == "__main__":
    celery.start()
