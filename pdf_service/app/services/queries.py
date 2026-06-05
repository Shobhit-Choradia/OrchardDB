import hashlib
from typing import Optional
from app.db.postgres import get_db_connection
from app.db.chroma import ChromaManager

db_manager = ChromaManager()

def verify_api_key(api_key: str) -> Optional[int]:
    """Verifies if an API key is active. Returns the tenant_id if valid, else None."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tenant_id FROM api_keys WHERE key_hash = %s AND is_active = 1",
            (key_hash,)
        )
        row = cursor.fetchone()
        return row["tenant_id"] if row else None

def verify_paid_tenant(tenant_id: int) -> bool:
    """Verify if a tenant is paid/premium tier."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT paid_tenant FROM tenants WHERE id = %s", (tenant_id,)
        )
        row = cursor.fetchone()
        return bool(row["paid_tenant"]) if row else False

def create_document_record(source_id: str, tenant_id: int, collection_name: str, filename: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (source_id, tenant_id, collection_name, doc_name) VALUES (%s, %s, %s, %s)",
            (source_id, tenant_id, collection_name, filename)
        )
        conn.commit()

def get_document_name(source_id: str, tenant_id: int, collection_name: str) -> str:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_name FROM documents WHERE source_id = %s AND tenant_id = %s AND collection_name = %s",
            (source_id, tenant_id, collection_name)
        )
        row = cursor.fetchone()
        return row["doc_name"] if row else None

def delete_document_resources(source_id: str, tenant_id: int, collection_name: str):
    # 1. Delete all vectors belonging to this source_id in ChromaDB
    collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
    collection.delete(where={"source_id": source_id})

    # 2. Clean up the source reference from relational metadata
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM documents WHERE source_id = %s AND tenant_id = %s",
            (source_id, tenant_id)
        )
        conn.commit()

def list_documents(tenant_id: int, collection_name: str) -> list:
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

def get_document_chunks(source_id: str, tenant_id: int, collection_name: str, doc_name: str) -> dict:
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
