"""
Módulo Principal de la Aplicación MediSinc-IA Backend (FastAPI).
Inicializa el servidor, configura CORS e incluye los routers de la API v1.
"""

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_v1_router

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="MediSinc-IA API",
    description="API de Pre-Triaje Clínico e Inteligencia de Salud",
    version="1.0.0"
)

# Configuración Middleware CORS para permitir solicitudes desde el Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas centralizadas de API v1
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint de bienvenida e información del servicio.
    """
    return {
        "app": "MediSinc-IA Backend",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Endpoint de diagnóstico para verificar el estado de la API y la configuración de entorno.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "ai_provider": settings.AI_PROVIDER,
        "timestamp": datetime.utcnow().isoformat()
    }
