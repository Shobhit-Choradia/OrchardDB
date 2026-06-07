from app.db.postgres import get_db_connection

def verify_paid_tenant(tenant_id: int) -> bool:
    """Verify if a tenant is paid"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT paid_tenant FROM tenants WHERE id = %s", (tenant_id,)
        )
        row = cursor.fetchone()
        return bool(row["paid_tenant"]) if row else False