from fastapi import Header, HTTPException, status
from app.services.auth_service import verify_api_key
from app.chroma_manager import ChromaManager

# Shared singleton ChromaManager instance — reused across all routes
db_manager = ChromaManager()


def get_tenant_id(x_api_key: str = Header(..., description="Developer API Key (e.g. lunar_xxxx.xxxx)")) -> int:
    """
    Security dependency to authorize incoming REST requests.
    Validates the provided API key header and extracts the associated tenant_id.
    """
    tenant_id = verify_api_key(x_api_key)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or deactivated API Key. Access denied."
        )
    return tenant_id
