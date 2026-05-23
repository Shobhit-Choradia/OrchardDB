from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.auth_service import verify_api_key
from app.chroma_manager import ChromaManager

router = APIRouter(prefix="/vdb", tags=["Vector Operations"])
db_manager = ChromaManager()

# Security dependency to authorize requests using the API Key
def get_tenant_id(x_api_key: str = Header(..., description="Developer API Key (e.g. lunar_xxxx.xxxx)")) -> int:
    tenant_id = verify_api_key(x_api_key)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or deactivated API Key. Access denied."
        )
    return tenant_id

# --- Pydantic Schemas ---

class CollectionCreate(BaseModel):
    name: str
    metric: Optional[str] = "cosine"  # cosine, l2, or ip

class DocumentUpsert(BaseModel):
    ids: List[str]
    documents: List[str]
    metadatas: Optional[List[Dict[str, Any]]] = None

class DocumentDelete(BaseModel):
    ids: List[str]

class QueryRequest(BaseModel):
    query_text: str
    n_results: Optional[int] = 5

# --- Router Endpoints ---

@router.post("/collections")
def create_collection(payload: CollectionCreate, tenant_id: int = Depends(get_tenant_id)):
    """Creates a new isolated vector collection for the authenticated developer."""
    try:
        db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=payload.name, metric=payload.metric)
        return {"message": f"Collection '{payload.name}' initialized successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create collection: {str(e)}"
        )

@router.get("/collections")
def list_collections(tenant_id: int = Depends(get_tenant_id)):
    """Lists all collections created by the authenticated developer."""
    try:
        collections = db_manager.list_scoped_collections(tenant_id=str(tenant_id))
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {str(e)}"
        )

@router.delete("/collections/{name}")
def delete_collection(name: str, tenant_id: int = Depends(get_tenant_id)):
    """Deletes an entire scoped vector collection and all its indexed contents."""
    try:
        db_manager.delete_scoped_collection(tenant_id=str(tenant_id), name=name)
        return {"message": f"Collection '{name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete collection: {str(e)}"
        )

@router.post("/collections/{name}/documents")
def add_documents(name: str, payload: DocumentUpsert, tenant_id: int = Depends(get_tenant_id)):
    """Adds or updates documents (generating embeddings automatically via Chroma's default pipeline)."""
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
    
    # 1. Prevent internal duplicate IDs within the request payload itself
    if len(payload.ids) != len(set(payload.ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload contains duplicate document IDs."
        )

    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        
        # 2. Check if any of the document IDs already exist in this collection
        existing = collection.get(ids=payload.ids)
        if existing and existing.get("ids"):
            duplicate_ids = existing["ids"]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document ID(s) already exist: {', '.join(duplicate_ids)}. Duplicate IDs are not allowed."
            )
            
        collection.add(
            ids=payload.ids,
            documents=payload.documents,
            metadatas=payload.metadatas
        )
        return {"message": f"Successfully indexed {len(payload.ids)} documents."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexing documents: {str(e)}"
        )

@router.delete("/collections/{name}/documents")
def delete_documents(name: str, payload: DocumentDelete, tenant_id: int = Depends(get_tenant_id)):
    """Deletes specific documents by their IDs within the scoped collection."""
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        collection.delete(ids=payload.ids)
        return {"message": f"Successfully deleted {len(payload.ids)} documents."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting documents: {str(e)}"
        )

@router.post("/collections/{name}/query")
def query_collection(name: str, payload: QueryRequest, tenant_id: int = Depends(get_tenant_id)):
    """Performs a semantic similarity search and returns the top matches."""
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        results = collection.query(
            query_texts=[payload.query_text],
            n_results=payload.n_results
        )
        # Format ChromaDB response dynamically for simple client consumption
        formatted_matches = []
        if results and "ids" in results and results["ids"]:
            # Retrieve the list of list values
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

@router.get("/collections/{name}/documents")
def get_all_documents(name: str, limit: Optional[int] = 100, tenant_id: int = Depends(get_tenant_id)):
    """Inspects/gets documents inside the collection to see what is currently in the database."""
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

@router.put("/collections/{name}/documents")
def update_documents(name: str, payload: DocumentUpsert, tenant_id: int = Depends(get_tenant_id)):
    """Updates existing documents and automatically re-generates their vector embeddings."""
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

    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
        
        # Check if the document IDs actually exist first
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
        return {"message": f"Successfully updated {len(payload.ids)} documents."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating documents: {str(e)}"
        )

