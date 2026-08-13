"""
Módulo Principal de la Aplicación MediSinc-IA Backend.
Inicializa el servidor FastAPI, configura middleware de CORS y define rutas de salud.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Inicialización de la instancia principal de FastAPI
app = FastAPI(
    title="MediSinc-IA API",
    description="API de Pre-Triaje Clínico e Inteligencia de Salud",
    version="1.0.0"
)

# Configuración de CORS para permitir la interacción con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """
    Endpoint base de verificación del servicio.
    Retorna el estado general de la API.
    """
    return {"message": "MediSinc-IA API está en funcionamiento", "status": "online"}
