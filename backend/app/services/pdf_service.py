import os
from celery import Celery
from app.database import get_db_connection
from app.dependencies import db_manager

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_client = Celery("orcharddb_worker", broker=redis_url, backend=redis_url.replace("/0", "/1"))

class PDFDispatcher:
    def dispatch_processing_job(self, filepath: str, document_id: str, filename: str, tenant_id: str, collection_name: str) -> str:
        """
        Sends a message to Redis telling the worker to process the PDF.
        Returns the asynchronous task_id.
        """
        task = celery_client.send_task(
            "process_pdf_task",
            args=[filepath, document_id, filename, str(tenant_id), collection_name]
        )
        return task.id

    def get_task_status(self, task_id: str) -> dict:
        """
        Retrieves the state and progress metadata for a given task ID.
        """
        from celery.result import AsyncResult
        task_result = AsyncResult(task_id, app=celery_client)
        
        response = {
            "task_id": task_id,
            "state": task_result.state
        }
        
        if task_result.state == 'PROCESSING':
            response['progress'] = task_result.info
        elif task_result.state == 'FAILURE':
            response['error'] = str(task_result.info)
            
        return response

    def create_document_record(self, source_id: str, tenant_id: int, collection_name: str, filename: str):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO documents (source_id, tenant_id, collection_name, doc_name) VALUES (%s, %s, %s, %s)",
                (source_id, tenant_id, collection_name, filename)
            )
            conn.commit()

    def get_document_name(self, source_id: str, tenant_id: int, collection_name: str) -> str:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT doc_name FROM documents WHERE source_id = %s AND tenant_id = %s AND collection_name = %s",
                (source_id, tenant_id, collection_name)
            )
            row = cursor.fetchone()
            return row["doc_name"] if row else None

    def delete_document_resources(self, source_id: str, tenant_id: int, collection_name: str):
        # 1. Delete all vectors belonging to this source_id in ChromaDB
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
        collection.delete(where={"source_id": source_id})

        # 2. Clean up the source reference from SQLite metadata
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM documents WHERE source_id = %s AND tenant_id = %s",
                (source_id, tenant_id)
            )
            conn.commit()

    def list_documents(self, tenant_id: int, collection_name: str) -> list:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, doc_name, created_at FROM documents WHERE tenant_id = %s AND collection_name = %s",
                (tenant_id, collection_name)
            )
            rows = cursor.fetchall()
            return [
                {
                    "source_id": row["source_id"],
                    "doc_name": row["doc_name"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

    def get_document_chunks(self, source_id: str, tenant_id: int, collection_name: str, doc_name: str) -> dict:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
        results = collection.get(where={"source_id": source_id})

        formatted_chunks = []
        if results and "ids" in results:
            ids = results["ids"]
            docs = results.get("documents", [])
            metas = results.get("metadatas", [])
            for i in range(len(ids)):
                formatted_chunks.append({
                    "id": ids[i],
                    "text": docs[i] if i < len(docs) else None,
                    "metadata": metas[i] if metas and i < len(metas) else None
                })

        return {
            "source_id": source_id,
            "document_name": doc_name,
            "total_chunks": len(formatted_chunks),
            "chunks": formatted_chunks
        }
