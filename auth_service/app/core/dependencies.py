from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_tenant_id(token: str = Depends(oauth2_scheme)) -> int:
    payload = decode_jwt_token(token)
    if payload is None or "tenant_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["tenant_id"]
