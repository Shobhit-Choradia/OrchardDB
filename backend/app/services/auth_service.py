import hashlib
import secrets
from app.database import get_db_connection

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_tenant(username: str, password: str) -> int:
    """Hashes the password and registers a new developer tenant. Returns tenant_id."""
    password_hash = hash_password(password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tenants (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return cursor.lastrowid

def verify_tenant(username: str, password: str) -> int:
    """Verifies credentials. Returns tenant_id if valid, else None."""
    password_hash = hash_password(password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM tenants WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        row = cursor.fetchone()
        return row["id"] if row else None

def activate_paid_tenant(tenant_id: int) -> bool:
    """Activate a tenant's subscription, setting paid_tenant as 1"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE tenants SET paid_tenant = 1 WHERE id = ?", (tenant_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

def verify_paid_tenant(tenant_id: int) -> bool:
    """Verify if a tenant is paid"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT paid_tenant FROM tenants WHERE id = ?", (tenant_id,)
        )
        row = cursor.fetchone()
        return bool(row["paid_tenant"]) if row else False

def generate_tenant_api_key(tenant_id: int, key_name: str = "Default Key") -> str:
    """Generates a secure API key, stores its hash, and returns the raw key."""
    raw_secret = secrets.token_hex(24)
    prefix = f"lunar_{raw_secret[:6]}"
    raw_key = f"{prefix}.{raw_secret[6:]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name) VALUES (?, ?, ?, ?)",
            (tenant_id, key_hash, prefix, key_name)
        )
        conn.commit()
    return raw_key

def verify_api_key(api_key: str) -> int:
    """Verifies if an API key is active. Returns the tenant_id if valid, else None."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tenant_id FROM api_keys WHERE key_hash = ? AND is_active = 1",
            (key_hash,)
        )
        row = cursor.fetchone()
        return row["tenant_id"] if row else None

def delete_tenant(username: str, password: str) -> bool:
    """Deletes a tenant and all their registered API keys from the SQLite database."""
    tenant_id = verify_tenant(username, password)
    if not tenant_id:
        return False
    with get_db_connection() as conn:
        # Delete related API keys first due to FOREIGN KEY constraints
        conn.execute("DELETE FROM api_keys WHERE tenant_id = ?", (tenant_id,))
        # Delete the tenant record
        conn.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
        conn.commit()
    return True


