import secrets
import hashlib
from app.db.postgres import get_db_connection

def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_tenant_api_key(tenant_id: int, key_name: str) -> str:
    # Generate a random 32-byte key and hex encode it
    raw_key = secrets.token_hex(32)
    # Prefix could be standard e.g. "sk-" or "orchard-"
    api_key = f"orchard-{raw_key}"
    
    key_hash = _hash_key(api_key)
    key_prefix = api_key[:12] # Save prefix for identification
    
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name) 
               VALUES (%s, %s, %s, %s)""",
            (tenant_id, key_hash, key_prefix, key_name)
        )
        conn.commit()
    
    return api_key

def list_tenant_api_keys(tenant_id: int):
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, key_prefix, name, created_at, is_active FROM api_keys WHERE tenant_id = %s AND deleted_at IS NULL",
            (tenant_id,)
        ).fetchall()
        return rows

def delete_api_key(tenant_id: int, key_id: int):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE api_keys SET deleted_at = CURRENT_TIMESTAMP, is_active = 0 WHERE id = %s AND tenant_id = %s",
            (key_id, tenant_id)
        )
        conn.commit()
