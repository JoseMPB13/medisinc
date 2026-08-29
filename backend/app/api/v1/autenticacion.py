"""
Alias y re-exportación en español del enrutador de autenticación.
"""
from app.api.v1.auth import router, login_personal_medico, EsquemaCredencialesEntrada, EsquemaRespuestaAutenticacion

__all__ = ["router", "login_personal_medico", "EsquemaCredencialesEntrada", "EsquemaRespuestaAutenticacion"]
