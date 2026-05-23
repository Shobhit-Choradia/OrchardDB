import hashlib
import secrets
from app.database import get_db_connection

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str) -> int:
    """Hashes the password and registers a new developer. Returns user_id."""
    password_hash = hash_password(password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return cursor.lastrowid

def verify_user(username: str, password: str) -> int:
    """Verifies credentials. Returns user_id if valid, else None."""
    password_hash = hash_password(password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        row = cursor.fetchone()
        return row["id"] if row else None

def generate_user_api_key(user_id: int, key_name: str = "Default Key") -> str:
    """Generates a secure API key, stores its hash, and returns the raw key."""
    raw_secret = secrets.token_hex(24)
    prefix = f"lunar_{raw_secret[:6]}"
    raw_key = f"{prefix}.{raw_secret[6:]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO api_keys (user_id, key_hash, key_prefix, name) VALUES (?, ?, ?, ?)",
            (user_id, key_hash, prefix, key_name)
        )
        conn.commit()
    return raw_key

def verify_api_key(api_key: str) -> int:
    """Verifies if an API key is active. Returns the user_id (tenant_id) if valid, else None."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM api_keys WHERE key_hash = ? AND is_active = 1",
            (key_hash,)
        )
        row = cursor.fetchone()
        return row["user_id"] if row else None

def delete_user(username: str, password: str) -> bool:
    """Deletes a user and all their registered API keys from the SQLite database."""
    user_id = verify_user(username, password)
    if not user_id:
        return False
    with get_db_connection() as conn:
        # Delete related API keys first due to FOREIGN KEY constraints
        conn.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
        # Delete the user record
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    return True

