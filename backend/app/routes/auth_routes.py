from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TenantCredentials(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(creds: TenantCredentials):
    """
    Endpoint to Register a new developer tenant and generates an API key for them.
    """
    try:
        tenant_id = auth_service.register_tenant(creds.username, creds.password)
        # Immediately generate an API key for the newly registered tenant
        api_key = auth_service.generate_tenant_api_key(tenant_id, "Default Key")
        return {
            "message": "Tenant registered successfully",
            "api_key": api_key
        }
    except Exception as e:
        # Username already exists unique constraint violation, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered or invalid registration data."
        )

@router.post("/login")
def login(creds: TenantCredentials):
    """
    Endpoint to Login a tenant and generates a fresh API key for them.
    """
    tenant_id = auth_service.verify_tenant(creds.username, creds.password)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    # Generate a fresh API key for the tenant upon successful login
    api_key = auth_service.generate_tenant_api_key(tenant_id, "Login Key")
    return {
        "message": "Login successful",
        "api_key": api_key
    }

@router.get("/health")
def health():
    """
    Endpoint to check the health of the authentication service.
    """
    return {
        "message": "Authentication service is healthy",
        "status" : "200"
    }

@router.delete("/delete")
def delete_tenant(creds: TenantCredentials):
    """
    Endpoint to delete a tenant and clean up their credentials.
    """
    if not auth_service.delete_tenant(creds.username, creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to delete tenant."
        )
    return {
        "message": "Tenant deleted successfully",
        "status" : "200"
    }


