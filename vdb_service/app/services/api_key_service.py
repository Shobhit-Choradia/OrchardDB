import hashlib
from app.db.postgres import get_db_connection

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
