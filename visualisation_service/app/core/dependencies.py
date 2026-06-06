from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.security import verify_jwt_token

def get_tenant_id(
    authorization: Optional[str] = Header(None)
) -> int:
    """
    Security dependency to authorize incoming REST requests.
    Validates a JWT Bearer token in the Authorization header.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header."
        )

    auth_str = authorization.strip()

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
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unsupported authentication scheme. Use 'Bearer <JWT>'."
        )
