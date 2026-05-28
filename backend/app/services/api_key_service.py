import secrets
import hashlib
from app.database import get_db_connection


def generate_tenant_api_key(tenant_id: int, key_name: str = "Default Key") -> str:
    """Generates a secure API key, stores its hash, and returns the raw key."""

    raw_secret = secrets.token_hex(24)
    prefix = f"orchard_{raw_secret[:6]}"
    raw_key = f"{prefix}.{raw_secret[6:]}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    with get_db_connection() as conn:

        conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, key_prefix, name, created_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)",
            (tenant_id, key_hash, prefix, key_name)
        )
        conn.commit()
    return raw_key


def list_tenant_api_keys(tenant_id: int) -> dict[str, list]:
    """ Lists all the keys owned by specific tenant"""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, key_prefix, created_at FROM api_keys WHERE tenant_id = %s AND is_active = 1",
            (tenant_id,)
        )
     
        return {
            "keys": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "key_prefix": row["key_prefix"],
                    "created_at": row["created_at"]
                }
                for row in cursor.fetchall()
            ]
        }


def verify_api_key(api_key: str) -> int:
    """Verifies if an API key is active. Returns the tenant_id if valid, else None."""

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    with get_db_connection() as conn:

        cursor = conn.cursor()
        cursor.execute(
            "SELECT tenant_id FROM api_keys WHERE key_hash = %s AND is_active = 1",
            (key_hash,)
        )
        row = cursor.fetchone()
        return row["tenant_id"] if row else None


def delete_api_key(tenant_id: int, key_id: int) -> dict[str, str]:
    """Delete an api key. """

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE api_keys SET is_active = 0, deleted_at = CURRENT_TIMESTAMP WHERE id = %s AND tenant_id = %s",
            (key_id, tenant_id)
        )
        conn.commit()
        return {"message": "API key deleted successfully"}

