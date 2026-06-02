import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_TOKEN_EXPIRY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_TOKEN_EXPIRY)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_jwt_token(token: str):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None
