from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.postgres import init_db
from app.api import auth_routes, api_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize metadata database tables on startup
    init_db()
    yield

app = FastAPI(
    title="OrchardDB Authentication Service",
    description="Authentication Service for multi-tenant Vector Database as a Service (VDBaaS) trial wrapping ChromaDB.",
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
app.include_router(auth_routes.router, prefix="/api")
app.include_router(api_routes.router, prefix="/api")
