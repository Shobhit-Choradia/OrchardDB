from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from app.services import auth_service
from app.core.dependencies import get_tenant_id
from app.core.security import create_jwt_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TenantCredentials(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(creds: TenantCredentials):
    """
    Endpoint to Register a new developer tenant.
    """
    try:
        tenant_id = auth_service.register_tenant(creds.username, creds.password)

        token = create_jwt_token(data = {"tenant_id" : tenant_id, "username" : creds.username})
        return {
            "message": "Tenant registered successfully",
            "token" : token
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
    
    # Generate a fresh token for the tenant upon successful login
    token = create_jwt_token(data = {"tenant_id" : tenant_id, "username" : creds.username})
    
    return {
        "message": "Login successful",
        "token" : token
    }

@router.get("/status")
def get_status(tenant_id: int = Depends(get_tenant_id)):
    """
    Checks the premium subscription status of the authenticated tenant.
    """
    is_premium = auth_service.verify_paid_tenant(tenant_id)
    return {"is_premium": is_premium}

@router.post("/upgrade")
def upgrade_to_premium(tenant_id: int = Depends(get_tenant_id)):
    """
    Simulates a payment/upgrade by upgrading the authenticated tenant to the premium tier.
    """
    success = auth_service.activate_paid_tenant(tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found or upgrade failed."
        )
    return {
        "message": "Congratulations! Your developer account has been upgraded to OrchardDB Premium Tier.",
        "is_premium": True
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
