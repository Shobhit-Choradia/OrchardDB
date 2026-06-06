from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import visualization_routes

app = FastAPI(
    title="OrchardDB Vector Visualisation Service",
    description="Microservice to perform dimensionality reduction (PCA/t-SNE) on high-dimensional vectors stored in ChromaDB.",
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

# Mount routes
app.include_router(visualization_routes.router, prefix="/api")
