import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routes import auth_routes, api_routes

app = FastAPI(
    title="OrchardDB Authentication Service",
    description="Authentication Service for multi-tenant Vector Database as a Service (VDBaaS) trial wrapping ChromaDB.",
    version="1.0.0"
)

# Enable CORS for frontend accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize metadata SQLite schema on application startup
@app.on_event("startup")
def startup_event():
    init_db()

# Mount routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(api_routes.router, prefix="/api")

