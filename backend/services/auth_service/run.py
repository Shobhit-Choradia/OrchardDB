"""Dev entry point for the Auth Service."""

import uvicorn
from app.config import AUTH_SERVICE_PORT

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=AUTH_SERVICE_PORT, reload=True)
