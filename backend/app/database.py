import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

def get_db_connection() -> psycopg.Connection:
    """Returns a Psycopg connection with dict_row enabled."""
    conn = psycopg.connect(DB_URL)
    conn.row_factory = dict_row
    return conn

def init_db():
    """Initializes the database tables on application startup."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                paid_tenant BOOLEAN DEFAULT FALSE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
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
