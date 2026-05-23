from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.dependencies import get_tenant_id, db_manager

# Create API router with Prefix and Tags for Swagger documentation grouping
router = APIRouter(prefix="/vdb", tags=["Vector Operations"])

# --- Pydantic Data Schemas ---

class CollectionCreate(BaseModel):
    name: str
    metric: Optional[str] = "cosine"  # Similarity spaces supported by ChromaDB: cosine, l2, or ip

class DocumentUpsert(BaseModel):
    ids: List[str]
    documents: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

class DocumentDelete(BaseModel):
    ids: List[str]

class QueryRequest(BaseModel):
    query_text: str
    n_results: Optional[int] = 5

class CollectionResponse(BaseModel):
    message: str
    collection_name: str
    metric: str

class CollectionListResponse(BaseModel):
    collections: List[str]

class DocumentUpsertResponse(BaseModel):
    message: str
    count: int

class DocumentDeleteResponse(BaseModel):
    message: str
    count: int

class QueryMatch(BaseModel):
    id: str
    document: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    distance: Optional[float] = None

class QueryResponse(BaseModel):
    query: str
    results: List[QueryMatch]

class DocumentsListResponse(BaseModel):
    ids: List[str]
    documents: List[Optional[str]]
    metadatas: List[Optional[Dict[str, Any]]]

class DocumentUpdateResponse(BaseModel):
    message: str
    count: int

# --- Router Endpoints ---

@router.post("/collections", response_model=CollectionResponse)
def create_collection(payload: CollectionCreate, tenant_id: int = Depends(get_tenant_id)):
    """
    Creates a new isolated vector collection for the authenticated developer tenant.
    
    Isolation is achieved by internally prefixing collection names with the tenant_id.
    """
    try:
        db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=payload.name, metric=payload.metric)
        return {
            "message": f"Collection '{payload.name}' initialized successfully.",
            "collection_name": payload.name,
            "metric": payload.metric or "cosine"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create collection: {str(e)}"
        )

@router.get("/collections", response_model=CollectionListResponse)
def list_collections(tenant_id: int = Depends(get_tenant_id)):
    """
    Lists all isolated vector collections owned by the authenticated developer tenant.
    """
    try:
        collections = db_manager.list_scoped_collections(tenant_id=str(tenant_id))
        return CollectionListResponse(collections=collections)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {str(e)}"
        )

@router.delete("/collections/{name}", response_model=CollectionResponse)
def delete_collection(name: str, tenant_id: int = Depends(get_tenant_id)):
    """
    Deletes an entire scoped vector collection and all its embedded contents for this tenant.
    """
    try:
        db_manager.delete_scoped_collection(tenant_id=str(tenant_id), name=name)
        return CollectionResponse(message=f"Collection '{name}' deleted successfully.", collection_name=name, metric="")
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete collection: {str(e)}"
        )

# --- Shared Validation ---

def validate_document_payload(payload: DocumentUpsert):
    """Validates that ids, documents, and metadatas arrays have consistent lengths."""
    if len(payload.ids) != len(payload.documents):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of ids and documents must be equal."
        )
    if payload.metadatas and len(payload.metadatas) != len(payload.ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of metadatas must match the number of documents if provided."
        )

@router.post("/collections/{name}/upsert_documents", response_model=DocumentUpsertResponse)
def upsert_documents(name: str, payload: DocumentUpsert, tenant_id: int = Depends(get_tenant_id)):
    """
    Safely indexes or updates vector documents inside the tenant's isolated collection.
    Automatically handles vector embedding generation using Chroma's default pipeline.
    Args:
        name (str): The name of the collection to upsert documents into.
        payload (DocumentUpsert): A Pydantic model containing the documents to upsert.
        tenant_id (int): The ID of the tenant making the request.
    """

    # 1. Validate payload structure
    validate_document_payload(payload)
    
    # 2. Prevent internal duplicate IDs within the incoming request payload itself
    if len(payload.ids) != len(set(payload.ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload contains duplicate document IDs."
        )

    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        
        # 3. Check if any of the document IDs already exist in this collection to enforce unique IDs
        existing = collection.get(ids=payload.ids)
        if existing and existing.get("ids"):
            duplicate_ids = existing["ids"]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document ID(s) already exist: {', '.join(duplicate_ids)}. Duplicate IDs are not allowed."
            )
            
        # 4. Insert documents to the vector store
        collection.add(
            ids=payload.ids,
            documents=payload.documents,
            metadatas=payload.metadatas
        )
        return {
            "message": f"Successfully indexed {len(payload.ids)} documents.",
            "count": len(payload.ids)
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexing documents: {str(e)}"
        )

@router.delete("/collections/{name}/documents", response_model=DocumentDeleteResponse)
def delete_documents(name: str, payload: DocumentDelete, tenant_id: int = Depends(get_tenant_id)):
    """
    Deletes specific vector documents by their IDs from the tenant's isolated collection.
    Args:
        name (str): The name of the collection to delete documents from.
        payload (DocumentDelete): A Pydantic model containing the IDs of the documents to delete.
        tenant_id (int): The ID of the tenant making the request.
    """
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        collection.delete(ids=payload.ids)
        return {
            "message": f"Successfully deleted {len(payload.ids)} documents.",
            "count": len(payload.ids)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting documents: {str(e)}"
        )

@router.post("/collections/{name}/query", response_model=QueryResponse)
def query_collection(name: str, payload: QueryRequest, tenant_id: int = Depends(get_tenant_id)):
    """
    Performs a semantic similarity search and returns the top matching documents.
    Args:
        name (str): The name of the collection to query.
        payload (QueryRequest): A Pydantic model containing the query text and number of results.
        tenant_id (int): The ID of the tenant making the request.
    """
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        results = collection.query(
            query_texts=[payload.query_text],
            n_results=payload.n_results
        )
        
        # Format the raw ChromaDB results into a user-friendly JSON structure
        formatted_matches = []
        if results and "ids" in results and results["ids"]:
            ids = results["ids"][0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for i in range(len(ids)):
                match = {
                    "id": ids[i],
                    "document": docs[i] if i < len(docs) else None,
                    "metadata": metas[i] if metas and i < len(metas) else None,
                    "distance": distances[i] if distances and i < len(distances) else None
                }
                formatted_matches.append(match)
        
        return {
            "query": payload.query_text,
            "results": formatted_matches
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing similarity query: {str(e)}"
        )

@router.get("/collections/{name}/documents", response_model=DocumentsListResponse)
def get_all_documents(name: str, limit: Optional[int] = 100, tenant_id: int = Depends(get_tenant_id)):
    """
    Retrieves/inspects the indexed documents inside the tenant's isolated vector database.
    Args:
        name (str): The name of the collection to retrieve documents from.
        limit (Optional[int]): The maximum number of documents to retrieve.
        tenant_id (int): The ID of the tenant making the request.
    """
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        results = collection.get(limit=limit)
        return {
            "ids": results.get("ids", []),
            "documents": results.get("documents", []),
            "metadatas": results.get("metadatas", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving collection documents: {str(e)}"
        )

@router.put("/collections/{name}/documents", response_model=DocumentUpdateResponse)
def update_documents(name: str, payload: DocumentUpsert, tenant_id: int = Depends(get_tenant_id)):
    """
    Updates the content/metadata of existing documents and triggers automatic embedding re-generation.
    Args:
        name (str): The name of the collection to update documents in.
        payload (DocumentUpsert): A Pydantic model containing the documents to update.
        tenant_id (int): The ID of the tenant making the request.
    """
    validate_document_payload(payload)

    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        
        # Verify that all document IDs actually exist before attempting an update
        existing = collection.get(ids=payload.ids)
        if not existing or not existing.get("ids") or len(existing["ids"]) != len(payload.ids):
            missing_ids = set(payload.ids) - set(existing.get("ids", []))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cannot update: Document ID(s) do not exist: {', '.join(missing_ids)}"
            )

        collection.update(
            ids=payload.ids,
            documents=payload.documents,
            metadatas=payload.metadatas
        )
        return {
            "message": f"Successfully updated {len(payload.ids)} documents.",
            "count": len(payload.ids)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating documents: {str(e)}"
        )