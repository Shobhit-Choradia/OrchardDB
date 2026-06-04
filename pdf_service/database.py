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
