import io
import os
from fastapi import APIRouter, Header, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from app.services.auth_service import verify_paid_tenant
from app.dependencies import db_manager, get_tenant_id
from app.services import pdf_service
from app.database import get_db_connection
from app.security.utils import generate_doc_id
# Create API router for Premium PDF Services
router = APIRouter(prefix="/pdf", tags=["PDF Services"])

# Instantiate the PDF dispatcher utility
pdf_dispatcher = pdf_service.PDFDispatcher()

# --- Pydantic Data Models ---

class PDFUploadResponse(BaseModel):
    message: str
    task_id: str

class PDFDeleteResponse(BaseModel):
    message: str
    source_id: str

# --- Security Dependency ---

def get_premium_tenant_id(tenant_id: int = Depends(get_tenant_id)) -> int:
    """
    Dependency that authorizes requests and verifies if the tenant has a premium subscription.
    """
    # Check if the tenant is active on the premium tier
    if not verify_paid_tenant(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid subscription required to access Premium PDF Scan & Load features."
        )
    return tenant_id

# --- Router Endpoints ---

@router.post("/collections/{collection_name}/upload", response_model=PDFUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    collection_name: str,
    file: UploadFile = File(...),
    tenant_id: int = Depends(get_premium_tenant_id)
):
    """
    Endpoint: Uploads, processes, chunks, and indexes a PDF document 
    into the developer tenant's isolated vector collection.
    
    All chunks are tracked in SQLite and indexed in ChromaDB with source metadatas.
    Args:
        collection_name (str): The name of the collection to upload the PDF to.
        file (UploadFile): The PDF file to upload.
        tenant_id (int): The ID of the tenant making the request.
    """

    # 1. Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported by this service."
        )

    try:
        # Generate a unique source_id first
        source_id = generate_doc_id()

        # 2. Insert metadata record in SQLite first to generate a unique source_id
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO documents (source_id, tenant_id, collection_name, doc_name) VALUES (%s, %s, %s, %s)",
                    (source_id, tenant_id, collection_name, file.filename)
                )
                conn.commit()

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A document named '{file.filename}' already exists in collection '{collection_name}'."
                )

        # 3. Save the uploaded file to the shared volume
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, f"{source_id}.pdf")
        
        with open(filepath, "wb") as f:
            pdf_data = await file.read()
            f.write(pdf_data)

        # 4. Dispatch the background job to the Celery worker
        task_id = pdf_dispatcher.dispatch_processing_job(
            filepath=os.path.abspath(filepath),
            document_id=source_id,
            filename=file.filename,
            tenant_id=str(tenant_id),
            collection_name=collection_name
        )

        return PDFUploadResponse(
            message=f"Document '{file.filename}' is being processed in the background (Source ID: {source_id}).",
            task_id=task_id
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading and processing PDF: {str(e)}"
        )

@router.delete("/collections/{collection_name}/documents/{source_id}", response_model=PDFDeleteResponse)
def delete_pdf(
    collection_name: str,
    source_id: str,
    tenant_id: int = Depends(get_premium_tenant_id)
):
    """
    Endpoint: Deletes all vector chunks and SQLite references belonging 
    to a specific uploaded PDF source.
    """
    # 1. Verify that the document source exists and belongs to the authenticated tenant
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_name FROM documents WHERE source_id = %s AND tenant_id = %s AND collection_name = %s",
            (source_id, tenant_id, collection_name)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document source with ID {source_id} not found in collection '{collection_name}'."
            )
        doc_name = row["doc_name"]

    try:
        # 2. Delete all vectors belonging to this source_id in ChromaDB
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
        collection.delete(where={"source_id": source_id})

        # 3. Clean up the source reference from SQLite metadata
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM documents WHERE source_id = %s AND tenant_id = %s",
                (source_id, tenant_id)
            )
            conn.commit()

        return PDFDeleteResponse(
            message=f"Successfully deleted document '{doc_name}' and all associated vector chunks.",
            source_id=source_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting PDF document resources: {str(e)}"
        )


@router.get("/collections/{collection_name}/documents")
def list_pdf_documents(
    collection_name: str,
    tenant_id: int = Depends(get_premium_tenant_id)
):
    """
    Endpoint: Lists all tracked PDF sources uploaded to this collection.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT source_id, doc_name, created_at FROM documents WHERE tenant_id = %s AND collection_name = %s",
            (tenant_id, collection_name)
        )
        rows = cursor.fetchall()
        
    return {
        "documents": [
            {
                "source_id": row["source_id"],
                "doc_name": row["doc_name"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    }


@router.get("/collections/{collection_name}/documents/{source_id}")
def get_pdf_documents(
    collection_name: str,
    source_id: str,
    tenant_id: int = Depends(get_premium_tenant_id)
):
    """
    Endpoint: Retrieves all processed text chunks and associated metadata
    belonging strictly to a specific uploaded PDF source.
    """
    # 1. Verify that the document source exists and belongs to this tenant in SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT doc_name FROM documents WHERE source_id = %s AND tenant_id = %s AND collection_name = %s",
            (source_id, tenant_id, collection_name)
        )

        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document source with ID {source_id} not found in collection '{collection_name}'."
            )
        doc_name = row["doc_name"]

    try:
        # 2. Retrieve all vectors from ChromaDB filtered by source_id
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)
        results = collection.get(where={"source_id": source_id})

        # 3. Format the raw ChromaDB output into a clean, readable structure
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDF document chunks: {str(e)}"
        )
