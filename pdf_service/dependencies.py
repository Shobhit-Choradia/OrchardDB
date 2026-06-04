import hashlib
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from database import get_db_connection
from security.utils import verify_jwt_token

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

def get_tenant_id(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> int:
    """
    Security dependency to authorize incoming REST requests.
    Validates either a JWT token or an API Key.
    """
    # 1. Handle API Key via x-api-key header
    if x_api_key:
        tenant_id = verify_api_key(x_api_key.strip())
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or deactivated API Key. Access denied."
            )
        return tenant_id

    # 2. Handle Authorization Header (JWT or API key)
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing credentials. Provide 'x-api-key' or 'Authorization' header."
        )

    auth_str = authorization.strip()

    # JWT Bearer Token
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
        except HTTPException as he:
            raise he
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token string."
            )

    # Raw API key in Authorization header
    elif auth_str.lower().startswith("orchard_"):
        tenant_id = verify_api_key(auth_str)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or deactivated API Key. Access denied."
            )
        return tenant_id

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication scheme. Use 'Bearer <JWT>' or 'orchard_<API_KEY>'."
        )

def get_premium_tenant_id(tenant_id: int = Depends(get_tenant_id)) -> int:
    """
    Dependency that authorizes requests and verifies if the tenant has a premium subscription.
    """
    if not verify_paid_tenant(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid subscription required to access Premium PDF Scan & Load features."
        )
    return tenant_id
