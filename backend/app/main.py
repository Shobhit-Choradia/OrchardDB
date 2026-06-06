import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import init_db
from app.routes import vdb_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize metadata DB schema on application startup
    init_db()
    yield

app = FastAPI(
    title="OrchardDB",
    description="A simple, multi-tenant Vector Database as a Service (VDBaaS) trial wrapping ChromaDB.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(vdb_routes.router, prefix="/api")

# Resolve absolute path to the frontend directories dynamically
current_dir = os.path.dirname(os.path.realpath(__file__))
frontend_dist = os.path.abspath(os.path.join(current_dir, "../../frontend/dist"))
frontend_raw = os.path.abspath(os.path.join(current_dir, "../../frontend"))

# Serve the compiled React 'dist' directory if present (production), otherwise fall back to raw source folder
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    app.mount("/", StaticFiles(directory=frontend_raw, html=True), name="frontend")


