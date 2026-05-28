import os
from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_client = Celery("orcharddb_worker", broker=redis_url, backend=redis_url)

class PDFDispatcher:
    def dispatch_processing_job(self, filepath: str, document_id: str, filename: str, tenant_id: str, collection_name: str) -> str:
        """
        Sends a message to Redis telling the worker to process the PDF.
        Returns the asynchronous task_id.
        """
        # We use send_task because we don't want to import the actual task code into the API
        task = celery_client.send_task(
            "process_pdf_task",
            args=[filepath, document_id, filename, str(tenant_id), collection_name]
        )
        return task.id
