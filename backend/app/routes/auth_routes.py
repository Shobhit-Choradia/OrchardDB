from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCredentials(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(creds: UserCredentials):
    """
    Endpoint to Register a new user and generates an API key for them.
    """

    try:
        user_id = auth_service.register_user(creds.username, creds.password)
        # Immediately generate an API key for the newly registered user
        api_key = auth_service.generate_user_api_key(user_id, "Default Key")
        return {
            "message": "User registered successfully",
            "api_key": api_key
        }
    except Exception as e:
        # Username already exists unique constraint violation, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered or invalid registration data."
        )

@router.post("/login")

def login(creds: UserCredentials):
    """
    Endpoint to Login a user and generates an API key for them.
    """

    user_id = auth_service.verify_user(creds.username, creds.password)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    # Generate a fresh API key for the user upon successful login
    api_key = auth_service.generate_user_api_key(user_id, "Login Key")
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
def delete_user(creds: UserCredentials):
    """
    Endpoint to delete a user.
    """

    if not auth_service.delete_user(creds.username, creds.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to delete user."
        )
    return {
        "message": "User deleted successfully",
        "status" : "200"
    }

