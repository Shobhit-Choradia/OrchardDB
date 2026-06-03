import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("orcharddb_worker", broker=REDIS_URL, backend=REDIS_URL.replace("/0", "/1"), include=["tasks"])

celery_app.conf.update(
    task_track_started = True,
    task_acks_late = True,
    worker_prefetch_multiplier = 1,
    task_time_limit = 300,
    result_expires = 1800,
    accept_content = ['json', 'msgpack'],
    task_serializer = 'json',
    result_serializer = 'json',
)
