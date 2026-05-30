from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from app.services import api_key_service
from app.dependencies import get_tenant_id

router = APIRouter(prefix="/api_keys", tags=["API_KEYS"])

class APIKeyGenerateRequest(BaseModel):
    name: str = "Default Key"

@router.post("/generate")
def generate(req: APIKeyGenerateRequest = None, tenant_id: int = Depends(get_tenant_id)):
    """
    Endpoint to generate a new API key for the authenticated tenant.
    """
    try:
        key_name = req.name if req and req.name else "Default Key"
        api_key = api_key_service.generate_tenant_api_key(tenant_id, key_name)

        return {
            "message": "API key generated successfully",
            "api_key": api_key
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate API key"
        )


@router.get("/")
def list_keys(tenant_id: int = Depends(get_tenant_id)):
    """
    Endpoint to list all active keys of a user.
    """
    try:
        api_keys = api_key_service.list_tenant_api_keys(tenant_id)
        return api_keys

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to list API keys"
        )

@router.delete("/delete/{key_id}")
def delete_key(key_id: int, tenant_id: int = Depends(get_tenant_id)):
    """
    Endpoint to delete an API key of a user.
    """
    try:
        api_key_service.delete_api_key(tenant_id, key_id)
        return {
            "message": "API key deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete API key"
        )
