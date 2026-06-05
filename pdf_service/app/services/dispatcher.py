from app.worker.celery_app import celery_app

class PDFDispatcher:
    def dispatch_processing_job(self, filepath: str, document_id: str, filename: str, tenant_id: str, collection_name: str) -> str:
        """
        Sends a message to Redis telling the worker to process the PDF.
        Returns the asynchronous task_id.
        """
        task = celery_app.send_task(
            "process_pdf_task",
            args=[filepath, document_id, filename, str(tenant_id), collection_name]
        )
        return task.id

    def get_task_status(self, task_id: str) -> dict:
        """
        Retrieves the state and progress metadata for a given task ID.
        """
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = {
            "task_id": task_id,
            "state": task_result.state
        }
        
        if task_result.state == 'PROCESSING':
            response['progress'] = task_result.info
        elif task_result.state == 'FAILURE':
            response['error'] = str(task_result.info)
            
        return response
