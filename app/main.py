from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, diagnostico

from app.services.storage_service import storage_service
from app.services.roboflow_service import roboflow_service
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Backend Alzheimer API",
    description="API para gestión de pacientes con Alzheimer",
    version="1.0.0"
)

# Configurar CORS
origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Solo para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(diagnostico.router)

@app.get("/")
async def root():
    """Endpoint de bienvenida"""
    return {
        "message": "Backend Alzheimer API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
