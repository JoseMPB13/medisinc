"""
Enrutador Principal Centralizado de la API v1 de MediSinc-IA.
"""

from fastapi import APIRouter, Depends
from app.core.limite_peticiones import verificar_limite_peticiones
from app.api.v1.triaje import router as triaje_router
from app.api.v1.medico import router as medico_router
from app.api.v1.administracion import router as admin_router
from app.api.v1.auth import router as auth_router

# Enrutador principal API v1
api_v1_router = APIRouter(prefix="/api/v1")

# Inclusión de sub-enrutadores en español
api_v1_router.include_router(auth_router)
api_v1_router.include_router(triaje_router)
api_v1_router.include_router(medico_router)
api_v1_router.include_router(admin_router)

# Aliases de compatibilidad para endpoints legacy (/triage, /doctor)
# Se registran con los mismos handlers para asegurar 100% de interoperabilidad
triage_router_alias = APIRouter(prefix="/triage", tags=["Triaje Clínico (Legacy)"])
doctor_router_alias = APIRouter(prefix="/doctor", tags=["Portal Médico (Legacy)"])

# Importar handlers para montaje en alias
from app.api.v1.triaje import procesar_triaje, consultar_estado_triaje, buscar_triaje, generar_preguntas_dinamicas_api
from app.api.v1.medico import obtener_panel_medico, obtener_detalle_paciente, registrar_revision_medica

triage_router_alias.add_api_route("/process", procesar_triaje, methods=["POST"], status_code=201, dependencies=[Depends(verificar_limite_peticiones)])
triage_router_alias.add_api_route("/procesar", procesar_triaje, methods=["POST"], status_code=201, dependencies=[Depends(verificar_limite_peticiones)])
triage_router_alias.add_api_route("/dynamic-questions", generar_preguntas_dinamicas_api, methods=["POST"])
triage_router_alias.add_api_route("/preguntas-dinamicas", generar_preguntas_dinamicas_api, methods=["POST"])
triage_router_alias.add_api_route("/status/{identifier}", consultar_estado_triaje, methods=["GET"])
triage_router_alias.add_api_route("/estado/{identificador}", consultar_estado_triaje, methods=["GET"])
triage_router_alias.add_api_route("/lookup", buscar_triaje, methods=["GET"])
triage_router_alias.add_api_route("/buscar", buscar_triaje, methods=["GET"])

doctor_router_alias.add_api_route("/dashboard", obtener_panel_medico, methods=["GET"])
doctor_router_alias.add_api_route("/panel", obtener_panel_medico, methods=["GET"])
doctor_router_alias.add_api_route("/patient/{triage_id}", obtener_detalle_paciente, methods=["GET"])
doctor_router_alias.add_api_route("/paciente/{triaje_id}", obtener_detalle_paciente, methods=["GET"])
doctor_router_alias.add_api_route("/review", registrar_revision_medica, methods=["POST"])
doctor_router_alias.add_api_route("/revisar", registrar_revision_medica, methods=["POST"])

api_v1_router.include_router(triage_router_alias)
api_v1_router.include_router(doctor_router_alias)

__all__ = ["api_v1_router"]
