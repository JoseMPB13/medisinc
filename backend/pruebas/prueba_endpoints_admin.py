"""
Banco de Pruebas Automatizadas para el Portal de Administración y Gobernanza en Español.
Verifica:
1. Control de acceso estricto RBAC (HTTP 403 Forbidden ante roles no autorizados).
2. Consulta de métricas cuantitativas globales (/api/v1/admin/estadisticas).
3. Alta y listado de personal médico (/api/v1/admin/medicos).
4. Consulta inalterable de la bitácora de auditoría (/api/v1/admin/registros-auditoria).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.seguridad import crear_token_jwt


def _cabecera_auth(rol: str = "ADMIN") -> dict:
    token = crear_token_jwt({
        "id": "admin-01" if rol == "ADMIN" else "doc-med-general-01",
        "sub": "admin-01" if rol == "ADMIN" else "doc-med-general-01",
        "rol": rol,
        "correo": f"{rol.lower()}@medisinc.bo",
        "nombre_completo": f"Usuario {rol}",
        "esta_activo": True
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_bloqueo_roles_no_autorizados():
    """
    Verifica que un usuario con rol MEDICO sea rechazado con HTTP 403 Forbidden
    al intentar acceder a rutas exclusivas de Administrador.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        resp = await cliente.get(
            "/api/v1/admin/estadisticas",
            headers=_cabecera_auth("MEDICO")
        )
        assert resp.status_code == 403
        assert "Se requieren privilegios de Administrador" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_admin_consulta_metricas():
    """
    Verifica que un ADMIN autenticado pueda consultar las métricas agregadas del centro de salud.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        resp = await cliente.get(
            "/api/v1/admin/estadisticas",
            headers=_cabecera_auth("ADMIN")
        )
        assert resp.status_code == 200
        datos = resp.json()
        assert "total_triajes" in datos
        assert "casos_rojo_urgente" in datos or "urgent_red_cases" in datos
        assert "casos_revisados" in datos or "reviewed_cases" in datos
        assert "medicos_activos" in datos or "active_doctors" in datos


@pytest.mark.asyncio
async def test_admin_crear_y_listar_medicos():
    """
    Verifica el flujo de creación de una cuenta de médico y su posterior listado.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        # 1. Crear nuevo médico
        payload_medico = {
            "nombre_completo": "Dra. Valeria Saucedo",
            "correo": "valeria.saucedo@medisinc.bo",
            "especialidad": "Emergencias Pediátricas",
            "password": "Password123!",
            "rol": "MEDICO"
        }
        resp_crear = await cliente.post(
            "/api/v1/admin/medicos",
            json=payload_medico,
            headers=_cabecera_auth("ADMIN")
        )
        assert resp_crear.status_code == 201
        medico_creado = resp_crear.json()
        nombre = medico_creado.get("nombre_completo") or medico_creado.get("full_name")
        rol = medico_creado.get("rol") or medico_creado.get("role")
        esta_activo = medico_creado.get("esta_activo") if "esta_activo" in medico_creado else medico_creado.get("is_active")

        assert nombre == "Dra. Valeria Saucedo"
        assert rol == "MEDICO"
        assert esta_activo is True
        doc_id = medico_creado["id"]

        # 2. Listar médicos y verificar presencia
        resp_listar = await cliente.get(
            "/api/v1/admin/medicos",
            headers=_cabecera_auth("ADMIN")
        )
        assert resp_listar.status_code == 200
        medicos = resp_listar.json()
        assert any(
            m.get("id") == doc_id or m.get("correo") == "valeria.saucedo@medisinc.bo" or m.get("email") == "valeria.saucedo@medisinc.bo"
            for m in medicos
        )


@pytest.mark.asyncio
async def test_admin_consulta_bitacora_auditoria():
    """
    Verifica la consulta de la bitácora inalterable de auditoría.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        resp = await cliente.get(
            "/api/v1/admin/registros-auditoria",
            headers=_cabecera_auth("ADMIN")
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert isinstance(logs, list)
        if len(logs) > 0:
            assert "accion" in logs[0] or "action" in logs[0]
            assert "fecha_hora" in logs[0] or "timestamp" in logs[0]


@pytest.mark.asyncio
async def test_admin_actualizar_medico():
    """
    Verifica la actualización de datos y estado de actividad de un médico.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        payload_update = {
            "especialidad": "Jefe de Emergencias Pediátricas",
            "esta_activo": False
        }
        resp = await cliente.put(
            "/api/v1/admin/medicos/doc-01",
            json=payload_update,
            headers=_cabecera_auth("ADMIN")
        )
        assert resp.status_code == 200
        actualizado = resp.json()
        assert actualizado.get("especialidad") == "Jefe de Emergencias Pediátricas" or actualizado.get("specialty") == "Jefe de Emergencias Pediátricas"
        assert actualizado.get("esta_activo") is False or actualizado.get("is_active") is False


@pytest.mark.asyncio
async def test_admin_historial_pacientes():
    """
    Verifica la consulta del historial de pacientes recibidos.
    """
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://testserver") as cliente:
        resp = await cliente.get(
            "/api/v1/admin/pacientes/historial",
            headers=_cabecera_auth("ADMIN")
        )
        assert resp.status_code == 200
        datos = resp.json()
        assert "total" in datos
        assert "records" in datos or "registros" in datos


