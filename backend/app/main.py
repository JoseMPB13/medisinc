"""
Módulo Principal de la Aplicación MediSinc-IA Backend (FastAPI).
Inicializa el servidor, configura CORS, monta las rutas de la API v1
y aplica el manejador global de excepciones con sanitización de errores 500.
"""

import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.configuracion import configuracion, settings
from app.api.v1 import api_v1_router

logger = logging.getLogger("medisinc.main")

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="MediSinc-IA API",
    description="Sistema Inteligente de Pre-Triaje Clínico e Inteligencia de Salud",
    version="2.0.0"
)

# Configuración Middleware CORS para comunicación con el Frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montaje de rutas de la API v1
app.include_router(api_v1_router)


# =============================================================================
# Manejador Global de Excepciones No Controladas (Sanitización de Errores 500)
# =============================================================================
@app.exception_handler(Exception)
async def sanitizacion_errores_500(request: Request, exc: Exception):
    """
    Manejador Global de Excepciones No Controladas.
    Sanitiza todos los errores 500 para evitar fugas de información sensible
    (stack traces, consultas SQL, llaves API o variables de entorno).
    Registra el detalle del error en los logs del servidor.
    """
    logger.critical(
        f"[GlobalExceptionHandler] Excepción no controlada en ruta {request.url}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detalle": "Ha ocurrido un error interno en el servidor. Por favor intente más tarde.",
            "detail": "Ha ocurrido un error interno en el servidor. Por favor intente más tarde.",
            "estado": 500,
            "status": 500,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

global_exception_handler = sanitizacion_errores_500


# =============================================================================
# Endpoints Raíz y Verificación de Salud Operativa
# =============================================================================
@app.get("/", tags=["Root"])
async def raiz():
    """
    Endpoint de bienvenida e información del servicio.
    """
    return {
        "aplicacion": "MediSinc-IA Backend",
        "app": "MediSinc-IA Backend",
        "version": "2.0.0",
        "estado": "en_linea",
        "status": "online"
    }

root = raiz


@app.get("/salud", tags=["Salud Operativa"])
@app.get("/health", tags=["Salud Operativa"])
async def salud():
    """
    Endpoint público de verificación de salud para monitores de infraestructura (Docker, Kubernetes, Render).
    """
    return {
        "estado": "operativo",
        "status": "healthy",
        "servicio": "MediSinc-IA API",
        "service": "MediSinc-IA API",
        "entorno": configuracion.ENTORNO,
        "environment": configuracion.ENVIRONMENT,
        "proveedor_ia": configuracion.AI_PROVIDER,
        "ai_provider": configuracion.AI_PROVIDER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

health = salud


@app.get("/api/v1/salud", tags=["Salud Operativa"])
@app.get("/api/v1/health", tags=["Salud Operativa"])
async def chequeo_salud_v1():
    """
    Endpoint de diagnóstico para verificar el estado de la API v1.
    """
    return await salud()

health_check = chequeo_salud_v1
