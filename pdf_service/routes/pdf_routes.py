import io
import os
from fastapi import APIRouter, Header, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from dependencies import get_premium_tenant_id
from services.pdf_service import PDFDispatcher
from security.utils import generate_doc_id

# Create API router for Premium PDF Services
router = APIRouter(prefix="/pdf", tags=["PDF Services"])

# Instantiate the PDF dispatcher utility
pdf_dispatcher = PDFDispatcher()

# --- Pydantic Data Models ---

class PDFUploadResponse(BaseModel):
    message: str
    task_id: str

class PDFDeleteResponse(BaseModel):
    message: str
    source_id: str

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
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported by this service."
        )

    try:
        source_id = generate_doc_id()

        try:
            pdf_dispatcher.create_document_record(source_id, tenant_id, collection_name, file.filename)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A document named '{file.filename}' already exists in collection '{collection_name}'."
            )

        # Save the uploaded file locally inside the pdf_worker_service context
        upload_dir = os.path.join("data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, f"{source_id}.pdf")
        
        with open(filepath, "wb") as f:
            pdf_data = await file.read()
            f.write(pdf_data)

        # Dispatch the background job to the Celery worker
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

@router.get("/tasks/{task_id}")
def get_pdf_task_status(
    task_id: str,
    tenant_id: int = Depends(get_premium_tenant_id)
):
    """
    Endpoint: Poll the Celery worker for the current status and progress of a PDF upload.
    """
    try:
        status_data = pdf_dispatcher.get_task_status(task_id)
        return status_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving task status: {str(e)}"
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
    doc_name = pdf_dispatcher.get_document_name(source_id, tenant_id, collection_name)
    if not doc_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document source with ID {source_id} not found in collection '{collection_name}'."
        )

    try:
        pdf_dispatcher.delete_document_resources(source_id, tenant_id, collection_name)
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
    try:
        documents = pdf_dispatcher.list_documents(tenant_id, collection_name)
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )

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
    doc_name = pdf_dispatcher.get_document_name(source_id, tenant_id, collection_name)
    if not doc_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document source with ID {source_id} not found in collection '{collection_name}'."
        )

    try:
        return pdf_dispatcher.get_document_chunks(source_id, tenant_id, collection_name, doc_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PDF document chunks: {str(e)}"
        )
