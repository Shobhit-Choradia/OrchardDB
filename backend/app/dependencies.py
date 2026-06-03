import hashlib
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from app.services.api_key_service import verify_api_key
from app.chroma_manager import ChromaManager
from app.security.utils import verify_jwt_token

# Shared singleton ChromaManager instance — reused across all routes
db_manager = ChromaManager()

def get_tenant_id(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> int:
    """
    Security dependency to authorize incoming REST requests.
    Validates either a JWT token (in Authorization header) or an API Key (in x-api-key or Authorization header).
    """

    # --- 1. HANDLE SDK/DIRECT CLIENT (x-api-key header) ---
    if x_api_key:
        tenant_id = verify_api_key(x_api_key.strip())
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or deactivated API Key. Access denied."
            )
        return tenant_id

    # --- 2. HANDLE CONSOLE SESSION (Authorization header) ---
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials. Provide 'x-api-key' or 'Authorization' header."
        )
    

    auth_str = authorization.strip()

    # --- CASE 1: HANDLE JWT BEARER TOKEN ---
    if auth_str.lower().startswith("bearer "):
        token = auth_str[7:].strip()
        try:

            token_data = verify_jwt_token(token)
            tenant_id = token_data.get("tenant_id")

            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token claims: missing tenant context."
                )
            return tenant_id
            
        except HTTPException as e:
            raise e
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token string."
            )

    # --- CASE 2: HANDLE RAW API KEY IN AUTHORIZATION ---
    elif auth_str.lower().startswith("orchard_"):
        tenant_id = verify_api_key(auth_str)
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or deactivated API Key. Access denied."
            )
        return tenant_id

    # --- CASE 3: FALLBACK UNKNOWN FORMAT ---
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication scheme. Use 'Bearer <JWT>' or 'orchard_<API_KEY>'."
        )
