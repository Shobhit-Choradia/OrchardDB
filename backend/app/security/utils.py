import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import secrets
import jwt
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_TOKEN_EXPIRY = os.getenv("JWT_TOKEN_EXPIRY")

# Safe conversion for token expiry with fallback
try:
    JWT_TOKEN_EXPIRY = int(JWT_TOKEN_EXPIRY)
except ValueError:
    JWT_TOKEN_EXPIRY = 60

# 1. Initialize OAuth2 scheme (Points to your login endpoint url, e.g., "/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==========================================
# 1. PASSWORD HASHING & VERIFICATION (BCRYPT)
# ==========================================

def hash_password(password: str) -> str:
    """Hashes a plaintext password securely using native bcrypt."""
    # Convert string to bytes, generate salt, and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash string."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ==========================================
# 2. JWT TOKEN GENERATION & VERIFICATION
# ==========================================

def create_jwt_token(data: dict) -> str:
    """Generates a secure JWT token with an expiration time."""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Input Data",
        )

    try:
        payload = data.copy()
        expiry_delta = datetime.now(timezone.utc) + timedelta(
            minutes=JWT_TOKEN_EXPIRY
        )
        payload.update({"exp": expiry_delta})
        encoded_jwt = jwt.encode(payload, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}",
        )


def verify_jwt_token(token: str) -> dict:
    """Decodes and verifies the JWT Token and returns the payload."""
    try:
        payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Error during token verification",
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency to extract and validate the token from incoming requests."""
    return verify_jwt_token(token)


def generate_doc_id() -> str:
    """Generates random secure and unique document ID for PDF documents."""
    return secrets.token_urlsafe(8)[:10]
