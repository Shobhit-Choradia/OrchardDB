from app.security.utils import hash_password, verify_password
from app.database import get_db_connection

def register_tenant(username: str, password: str) -> int:
    """Hashes the password using bcrypt and registers a new developer tenant. Returns tenant_id."""

    password_hash = hash_password(password)
    with get_db_connection() as conn:

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tenants (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, password_hash)
        )
        row = cursor.fetchone()
        conn.commit()
        return row["id"]


def verify_tenant(username: str, password: str) -> int:
    """Verifies credentials using bcrypt. Returns tenant_id if valid, else None."""
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM tenants WHERE username = %s",
            (username,)
        )
        row = cursor.fetchone()
        return row["id"] if row and verify_password(password, row["password_hash"]) else None


def activate_paid_tenant(tenant_id: int) -> bool:
    """Activate a tenant's subscription, setting paid_tenant as 1"""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE tenants SET paid_tenant = TRUE WHERE id = %s", (tenant_id,)
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
            "SELECT paid_tenant FROM tenants WHERE id = %s", (tenant_id,)
        )
        row = cursor.fetchone()
        return bool(row["paid_tenant"]) if row else False


def delete_tenant(username: str, password: str) -> bool:
    """Deletes a tenant and all their registered API keys from the SQLite database."""
    
    tenant_id = verify_tenant(username, password)
    if not tenant_id:
        return False

    with get_db_connection() as conn:

        conn.execute("DELETE FROM api_keys WHERE tenant_id = %s", (tenant_id,))
        conn.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
        conn.commit()
    return True