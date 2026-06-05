import psycopg
from psycopg.rows import dict_row
from app.core.config import settings

def get_db_connection() -> psycopg.Connection:
    """Returns a Psycopg connection with dict_row enabled."""
    conn = psycopg.connect(settings.DATABASE_URL)
    conn.row_factory = dict_row
    return conn
