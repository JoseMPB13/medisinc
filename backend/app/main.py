"""
Módulo Principal de la Aplicación MediSinc-IA Backend (FastAPI).
Inicializa el servidor, configura CORS, monta las rutas de la API v1
y aplica el manejador global de excepciones con sanitización de errores.
"""

import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_v1_router

logger = logging.getLogger("medisinc.main")

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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador Global de Excepciones No Controladas.
    Sanitiza todos los errores 500 para evitar fugas de información sensible
    (stack traces, consultas SQL, llaves API o variables de entorno).
    Registra el detalle del error en los logs del servidor.
    """
    logger.critical(f"[GlobalExceptionHandler] Excepción no controlada en ruta {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ha ocurrido un error interno en el servidor. Por favor intente más tarde.",
            "status": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


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
