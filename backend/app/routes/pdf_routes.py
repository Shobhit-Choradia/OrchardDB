import io
from fastapi import APIRouter, Header, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from app.services.auth_service import verify_api_key, verify_paid_tenant
from app.dependencies import db_manager
from app.services import pdf_service
from app.database import get_db_connection

# Create API router for Premium PDF Services
router = APIRouter(prefix="/pdf", tags=["PDF Services"])

# Instantiate the PDF processor utility
pdf_processor = pdf_service.PDFProcessor()

# --- Pydantic Data Models ---

class PDFUploadResponse(BaseModel):
    message: str
    total_chunks: int

class PDFDeleteResponse(BaseModel):
    message: str
    source_id: int

# --- Security Dependency ---

def get_premium_tenant_id(x_api_key: str = Header(..., description="Developer API Key (e.g. lunar_xxxx.xxxx)")) -> int:
    """
    Dependency that authorizes requests and verifies if the tenant has a premium subscription.
    """
    tenant_id = verify_api_key(x_api_key)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or deactivated API Key. Access denied."
        )
    
    # Check if the tenant is active on the premium tier
    if not verify_paid_tenant(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid subscription required to access Premium PDF Scan & Load features."
        )
    return tenant_id

# --- Router Endpoints ---

@router.post("/collections/{collection_name}/upload", response_model=PDFUploadResponse)
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
        # 2. Insert metadata record in SQLite first to generate a unique source_id
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO documents (tenant_id, collection_name, doc_name) VALUES (?, ?, ?)",
                    (tenant_id, collection_name, file.filename)
                )
                conn.commit()
                source_id = cursor.lastrowid

            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A document named '{file.filename}' already exists in collection '{collection_name}'."
                )

        # 3. Read uploaded file bytes asynchronously
        pdf_data = await file.read()
        file_stream = io.BytesIO(pdf_data)

        # 4. Extract and chunk text semantically
        processed_chunks = pdf_processor.extract_text_from_pdf(
            file_stream=file_stream,
            filename=file.filename,
            source_id=source_id
        )

        if not processed_chunks:
            # Clean up the SQLite record if the file was empty/unparseable
            with get_db_connection() as conn:
                conn.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
                conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract any text from the uploaded PDF. It may be scanned or empty."
            )

        # 5. Ingest chunks into tenant's isolated ChromaDB collection
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=collection_name)

        ids = [chunk["id"] for chunk in processed_chunks]
        documents = [chunk["text"] for chunk in processed_chunks]
        metadatas = [chunk["metadata"] for chunk in processed_chunks]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return PDFUploadResponse(
            message=f"Successfully indexed document '{file.filename}' as {len(processed_chunks)} semantically coherent chunks (Source ID: {source_id}).",
            total_chunks=len(processed_chunks)
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
    source_id: int,
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
            "SELECT doc_name FROM documents WHERE source_id = ? AND tenant_id = ? AND collection_name = ?",
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
                "DELETE FROM documents WHERE source_id = ? AND tenant_id = ?",
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
            "SELECT source_id, doc_name, created_at FROM documents WHERE tenant_id = ? AND collection_name = ?",
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
    source_id: int,
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
            "SELECT doc_name FROM documents WHERE source_id = ? AND tenant_id = ? AND collection_name = ?",
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
