"""Centralized configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── JWT Settings ──────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_TOKEN_EXPIRY = int(os.getenv("JWT_TOKEN_EXPIRY", "60"))  # minutes

# ── Database ──────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# ── Service ───────────────────────────────────────────────────
AUTH_SERVICE_PORT = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
