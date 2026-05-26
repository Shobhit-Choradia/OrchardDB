from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List, Literal
from app.dependencies import get_tenant_id, db_manager
from app.services.visualisation_service import VectorVisualizer

router = APIRouter(prefix="/vdb", tags=["Visualisation"])


class VisualPoint(BaseModel):
    id: str
    x: float
    y: float
    z: float
    document: Optional[str] = None


class VisualizeResponse(BaseModel):
    method: str
    n_docs: int
    points: List[VisualPoint]
    variance_explained: Optional[List[float]] = None
    error: Optional[str] = None


@router.get("/collections/{name}/visualize", response_model=VisualizeResponse)
def get_collection_visualization(
    name: str,
    method: Literal["pca", "tsne"] = "pca",
    tenant_id: int = Depends(get_tenant_id),
):
    # 1. Get the tenant-scoped collection
    try:
        collection = db_manager.get_scoped_collection(tenant_id=str(tenant_id), name=name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' not found: {str(e)}"
        )

    # 2. Run dimensionality reduction
    try:
        visualizer = VectorVisualizer()
        result = visualizer.reduce(collection=collection, method=method)

        return VisualizeResponse(
            method=result["method"],
            n_docs=result["n_docs"],
            points=[VisualPoint(**p) for p in result["points"]],
            variance_explained=result.get("variance_explained"),
            error=result.get("error"),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))