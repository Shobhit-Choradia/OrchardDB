from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "orcharddb_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL.replace("/0", "/1"),
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    result_expires=1800,
    accept_content=['json', 'msgpack'],
    task_serializer='json',
    result_serializer='json',
)
