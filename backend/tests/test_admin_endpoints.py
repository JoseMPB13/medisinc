"""
Banco de Pruebas Automatizadas para el Portal de Administración (Rol ADMIN).
Verifica:
1. Control de acceso estricto (403 Forbidden ante roles no autorizados).
2. Obtención de métricas globales (/admin/stats).
3. CRUD de personal médico (/admin/doctors).
4. Historial histórico de pacientes (/admin/patients/history).
5. Consulta de la bitácora inalterable (/admin/audit-logs).
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_admin_forbidden_for_non_admin():
    """
    Verifica que un usuario con rol DOCTOR sea rechazado con HTTP 403 Forbidden
    al intentar acceder a las rutas reservadas para Administrador.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"X-User-Role": "DOCTOR"}
        )
        assert resp.status_code == 403
        assert "Se requieren privilegios de Administrador" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_admin_stats_access():
    """
    Verifica que un ADMIN autenticado pueda consultar las métricas agregadas del centro de salud.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"X-User-Role": "ADMIN"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_triages" in data
        assert "urgent_red_cases" in data
        assert "reviewed_cases" in data
        assert "active_doctors" in data
        assert "average_attention_time_min" in data


@pytest.mark.asyncio
async def test_admin_create_and_list_doctors():
    """
    Verifica el flujo de creación de un nuevo profesional médico y su listado subsiguiente.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Crear nuevo médico
        new_doc_payload = {
            "full_name": "Dr. Carlos Saucedo",
            "email": "carlos.saucedo@medisinc.bo",
            "specialty": "Cardiología y Triage de Urgencias",
            "password": "Password123!",
            "role": "DOCTOR"
        }
        create_resp = await client.post(
            "/api/v1/admin/doctors",
            json=new_doc_payload,
            headers={"X-User-Role": "ADMIN"}
        )
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        assert created_data["full_name"] == "Dr. Carlos Saucedo"
        assert created_data["role"] == "DOCTOR"
        assert created_data["is_active"] is True
        doc_id = created_data["id"]

        # 2. Listar doctores y verificar presencia
        list_resp = await client.get(
            "/api/v1/admin/doctors",
            headers={"X-User-Role": "ADMIN"}
        )
        assert list_resp.status_code == 200
        doctors = list_resp.json()
        assert any(d["id"] == doc_id or d["email"] == "carlos.saucedo@medisinc.bo" for d in doctors)


@pytest.mark.asyncio
async def test_admin_update_doctor():
    """
    Verifica la actualización de datos y estado activo/inactivo de un médico por el Administrador.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        update_payload = {
            "specialty": "Jefe de Emergencias Pediátricas",
            "is_active": False
        }
        resp = await client.put(
            "/api/v1/admin/doctors/doc-01",
            json=update_payload,
            headers={"X-User-Role": "ADMIN"}
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["specialty"] == "Jefe de Emergencias Pediátricas"
        assert updated["is_active"] is False


@pytest.mark.asyncio
async def test_admin_patient_history():
    """
    Verifica la consulta del historial integral de pacientes (actuales y anteriores con filtros).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(
            "/api/v1/admin/patients/history",
            headers={"X-User-Role": "ADMIN"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "records" in data
        assert isinstance(data["records"], list)


@pytest.mark.asyncio
async def test_admin_audit_logs():
    """
    Verifica la consulta de la bitácora inalterable AUDIT_LOG.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get(
            "/api/v1/admin/audit-logs",
            headers={"X-User-Role": "ADMIN"}
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert isinstance(logs, list)
        assert len(logs) > 0
        assert "action" in logs[0]
        assert "timestamp" in logs[0]
