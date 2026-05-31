from app.database import get_db_connection
from app.security.utils import get_password_hash, verify_password
import psycopg

def register_tenant(username: str, password: str) -> int:
    hashed_password = get_password_hash(password)
    with get_db_connection() as conn:
        try:
            row = conn.execute(
                "INSERT INTO tenants (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, hashed_password)
            ).fetchone()
            conn.commit()
            return row["id"]
        except psycopg.IntegrityError:
            raise Exception("Username already exists")

def verify_tenant(username: str, password: str):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM tenants WHERE username = %s", (username,)
        ).fetchone()
        if row and verify_password(password, row["password_hash"]):
            return row["id"]
        return None

def verify_paid_tenant(tenant_id: int) -> bool:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT paid_tenant FROM tenants WHERE id = %s", (tenant_id,)
        ).fetchone()
        return bool(row["paid_tenant"]) if row else False

def activate_paid_tenant(tenant_id: int) -> bool:
    with get_db_connection() as conn:
        res = conn.execute(
            "UPDATE tenants SET paid_tenant = TRUE WHERE id = %s RETURNING id", (tenant_id,)
        ).fetchone()
        conn.commit()
        return bool(res)

def delete_tenant(username: str, password: str) -> bool:
    tenant_id = verify_tenant(username, password)
    if not tenant_id:
        return False
    with get_db_connection() as conn:
        conn.execute("DELETE FROM api_keys WHERE tenant_id = %s", (tenant_id,))
        conn.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
        conn.commit()
        return True
