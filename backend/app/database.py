import os
import sqlite3

DB_PATH = os.getenv("METADATA_DB_PATH", "./data/metadata.db")

def get_db_connection() -> sqlite3.Connection:
    """Returns a standard sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables on application startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                paid_tenant BOOLEAN DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP DEFAULT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                source_id TEXT PRIMARY KEY,
                tenant_id INTEGER NOT NULL,
                collection_name TEXT NOT NULL,
                doc_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id), 
                UNIQUE(tenant_id,collection_name,doc_name)
            )
        """)
