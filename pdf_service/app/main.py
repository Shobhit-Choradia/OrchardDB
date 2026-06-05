from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import pdf_routes

app = FastAPI(
    title="OrchardDB PDF Processing Service",
    description="Microservice to parse, chunk, embed, and store PDF files in ChromaDB.",
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

# Mount routers
app.include_router(pdf_routes.router, prefix="/api")
