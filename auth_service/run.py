"""Dev entry point for the Auth Service."""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
