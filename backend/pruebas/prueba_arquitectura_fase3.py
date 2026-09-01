"""
Pruebas Automatizadas de Arquitectura Limpia y Desacoplamiento - Fase 3:
1. Operaciones CRUD y consultas en los repositorios especializados.
2. Tipado estricto con DTOs de Pydantic v2 (from_attributes=True).
3. Inyección de dependencias con FastAPI dependency_overrides.
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.repositorios.base import (
    IRepositorioTriaje,
    IRepositorioPacientes,
    IRepositorioMedicos,
    IRepositorioAuditoria
)
from app.repositorios.dependencias import (
    obtener_repositorio_triaje,
    obtener_repositorio_pacientes,
    obtener_repositorio_medicos,
    obtener_repositorio_auditoria
)
from pruebas.fakes.fakes_repositorios import (
    RepositorioTriajeEnMemoria,
    RepositorioPacientesEnMemoria,
    RepositorioMedicosEnMemoria,
    RepositorioAuditoriaEnMemoria
)
from app.esquemas.dominio import (
    RegistroTriajeDTO,
    PacienteDTO,
    PerfilMedicoDTO,
    EventoAuditoriaDTO,
    ResultadoIADTO
)


# =============================================================================
# 1. PRUEBAS DE REPOSITORIOS ESPECIALIZADOS
# =============================================================================

@pytest.mark.asyncio
async def test_repositorio_triaje_operaciones_crud_y_dtos():
    """Valida el ciclo de vida del triaje en el repositorio retornando DTOs tipados."""
    repo = RepositorioTriajeEnMemoria()
    triaje_id = f"tr-{uuid.uuid4().hex[:8]}"

    datos = {
        "id": triaje_id,
        "codigo_acceso": "MS-TEST1",
        "nombre_paciente": "Juan Pérez",
        "edad": 42,
        "genero": "Masculino",
        "sintomas_brutos": "Dolor abdominal agudo",
        "especialidad_solicitada": "Medicina General",
        "estado": "RECIBIDO"
    }

    # 1. Guardar
    dto_creado = await repo.guardar_triaje(datos)
    assert isinstance(dto_creado, RegistroTriajeDTO)
    assert dto_creado.id == triaje_id
    assert dto_creado.codigo_acceso == "MS-TEST1"

    # 2. Consultar por Código
    dto_obtenido = await repo.obtener_por_codigo("MS-TEST1")
    assert dto_obtenido is not None
    assert dto_obtenido.nombre_paciente == "Juan Pérez"

    # 3. Asignar Médico
    dto_asignado = await repo.asignar_medico(triaje_id, "doc-123")
    assert dto_asignado.medico_asignado_id == "doc-123"
    assert dto_asignado.estado == "EN_CONSULTA"

    # 4. Cerrar Revisión
    dto_cerrado = await repo.cerrar_revision_medica(
        triaje_id=triaje_id,
        medico_id="doc-123",
        notas_medico="Paciente con apendicitis descartada.",
        prioridad_ajustada="VERDE"
    )
    assert dto_cerrado.estado == "REVISADO"
    assert dto_cerrado.notas_medico == "Paciente con apendicitis descartada."
    assert dto_cerrado.prioridad_final == "VERDE"


@pytest.mark.asyncio
async def test_repositorio_pacientes_persistencia_3nf():
    """Valida la gestión de pacientes y su historial clínico en el repositorio de pacientes."""
    repo = RepositorioPacientesEnMemoria()
    paciente_id = str(uuid.uuid4())

    datos_paciente = {
        "id": paciente_id,
        "ci_hash": "hash_ciego_123456",
        "ci_cifrado": "gAAAAABl...",
        "nombre_completo": "María Flores",
        "edad": 28,
        "genero": "Femenino",
        "alergias_medicamentosas": "Penicilina",
        "enfermedades_base": ["Asma"]
    }

    # 1. Crear
    dto = await repo.crear_o_actualizar_paciente(datos_paciente)
    assert isinstance(dto, PacienteDTO)
    assert dto.nombre_completo == "María Flores"
    assert "Asma" in dto.enfermedades_base

    # 2. Consultar por CI Hash
    dto_hash = await repo.obtener_por_ci_hash("hash_ciego_123456")
    assert dto_hash is not None
    assert dto_hash.id == paciente_id

    # 3. Consultar Historial
    historial = await repo.obtener_historial_clinico(paciente_id)
    assert historial["paciente_id"] == paciente_id
    assert historial["total_atenciones"] >= 1


@pytest.mark.asyncio
async def test_repositorio_medicos_gestion_y_catalogo():
    """Valida el listado, creación y agrupación por especialidad médica."""
    repo = RepositorioMedicosEnMemoria()

    medico_datos = {
        "id": "doc-test-99",
        "nombre_completo": "Dr. Fernando Morales",
        "correo": "f.morales@medisinc.bo",
        "especialidad": "Cardiología y Medicina Interna",
        "rol": "MEDICO",
        "esta_activo": True
    }

    # 1. Crear
    dto_med = await repo.crear_medico(medico_datos)
    assert isinstance(dto_med, PerfilMedicoDTO)
    assert dto_med.id == "doc-test-99"

    # 2. Listar
    lista = await repo.listar_medicos(esta_activo=True)
    assert len(lista) == 1
    assert lista[0].nombre_completo == "Dr. Fernando Morales"

    # 3. Agrupación por Especialidad
    catalogo = await repo.obtener_medicos_activos_por_especialidad()
    assert "Cardiología y Medicina Interna" in catalogo
    assert len(catalogo["Cardiología y Medicina Interna"]) == 1


@pytest.mark.asyncio
async def test_repositorio_auditoria_registro_inmutable():
    """Valida el registro inmutable y consulta cronológica en la bitácora de auditoría."""
    repo = RepositorioAuditoriaEnMemoria()

    # 1. Registrar 2 eventos
    ev1 = await repo.registrar_evento(
        usuario_id="doc-123",
        accion="CONSULTA_EXPEDIENTE",
        recurso_id="tr-001",
        direccion_ip="192.168.1.10"
    )
    assert isinstance(ev1, EventoAuditoriaDTO)
    assert ev1.accion == "CONSULTA_EXPEDIENTE"

    await repo.registrar_evento(
        usuario_id="doc-123",
        accion="CIERRE_REVISION_MEDICA",
        recurso_id="tr-001"
    )

    # 2. Listar
    eventos = await repo.listar_eventos(limite=10)
    assert len(eventos) == 2
    # El más reciente primero
    assert eventos[0].accion == "CIERRE_REVISION_MEDICA"


# =============================================================================
# 2. PRUEBA DE INYECCIÓN DE DEPENDENCIAS CON FASTAPI
# =============================================================================

@pytest.mark.asyncio
async def test_inyeccion_dependencias_fastapi_con_overrides():
    """
    Valida que FastAPI resuelva los repositorios mediante Depends y que
    la suite pueda sobreescribir las dependencias limpiamente con dependency_overrides.
    """
    fake_triaje_repo = RepositorioTriajeEnMemoria()
    fake_medicos_repo = RepositorioMedicosEnMemoria()

    # Sobreescribir las dependencias en la app de FastAPI
    app.dependency_overrides[obtener_repositorio_triaje] = lambda: fake_triaje_repo
    app.dependency_overrides[obtener_repositorio_medicos] = lambda: fake_medicos_repo

    try:
        # Pre-cargar un médico en el fake
        await fake_medicos_repo.crear_medico({
            "id": "doc-override-01",
            "nombre_completo": "Dr. Inyectado Override",
            "correo": "override@medisinc.bo",
            "especialidad": "Medicina General",
            "rol": "MEDICO",
            "esta_activo": True
        })

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/triaje/especialidades")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 6
    finally:
        # Limpiar overrides
        app.dependency_overrides.clear()
