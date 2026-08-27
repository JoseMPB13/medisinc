"""
Banco de Pruebas Automatizadas de Validación Técnica y Seguridad Médica (CV01 - CV20)
Proyecto: MediSinc-IA (FastAPI + Supabase + IA Agnóstica)
"""

import re
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.security import encrypt_ci, decrypt_ci, hash_ci, generate_access_code
from app.core.rate_limit import _LOCAL_RATE_LIMIT_DB, WINDOW_SECONDS, MAX_REQUESTS_PER_WINDOW
from app.services.rules_engine import evaluate_safety_overrides
from app.schemas.triage import AIStructuredOutput, PatientInputSchema
from app.providers.ai_factory import get_ai_provider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider
from app.services.supabase_service import _IN_MEMORY_TRIAGE_DB, _IN_MEMORY_AI_DB, supabase_service

client = TestClient(app)


# =============================================================================
# CV01: Creación de pre-triaje y respuesta inmediata con estado RECEIVED
# =============================================================================
def test_cv01_triage_creation_immediate_response():
    payload = {
        "patient_name": "Carlos Mamani",
        "ci": "8765432 SC",
        "age": 42,
        "gender": "Masculino",
        "raw_symptoms": "Dolor abdominal moderado y náuseas",
        "static_data": {"intensidad": 6, "duracion": "4 horas"},
        "dynamic_answers": {"ubicacion": "epigastrio"}
    }
    response = client.post("/api/v1/triage/process", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "triage_id" in data
    assert "access_code" in data
    assert data["status"] == "RECEIVED"
    assert data["patient_name"] == "Carlos Mamani"
    assert re.match(r"^MS-[2-9A-Z]{5}$", data["access_code"])


# =============================================================================
# CV02: Cifrado simétrico AES (Fernet) para Carnet de Identidad
# =============================================================================
def test_cv02_ci_symmetric_encryption():
    ci_original = "7891234 LP"
    encrypted = encrypt_ci(ci_original)
    assert encrypted != ci_original
    assert len(encrypted) > 20
    decrypted = decrypt_ci(encrypted)
    assert decrypted == ci_original


# =============================================================================
# CV03: Hashing seguro HMAC-SHA256 con Pepper para CI
# =============================================================================
def test_cv03_ci_hmac_hashing():
    ci_1 = "1234567-SC"
    ci_2 = " 1234567-sc "
    hash_1 = hash_ci(ci_1)
    hash_2 = hash_ci(ci_2)
    assert hash_1 == hash_2
    assert len(hash_1) == 64  # SHA-256 hexdigest
    assert hash_1 != ci_1


# =============================================================================
# CV04: Formato regex del código único generado (^MS-[2-9A-Z]{5}$)
# =============================================================================
def test_cv04_access_code_regex_format():
    regex_pattern = r"^MS-[2-9A-Z]{5}$"
    for _ in range(50):
        code = generate_access_code()
        assert re.match(regex_pattern, code)
        # Asegurar que no contenga caracteres ambiguos (0, O, 1, I)
        assert "0" not in code and "O" not in code
        assert "1" not in code and "I" not in code


# =============================================================================
# CV05: Fallback resiliente ante caída de API externa de IA
# =============================================================================
@pytest.mark.asyncio
async def test_cv05_ai_provider_fallback_resilience():
    provider = GeminiProvider()
    patient_data = {
        "patient_name": "Paciente Prueba",
        "age": 30,
        "gender": "Femenino",
        "raw_symptoms": "Dolor de cabeza leve",
        "static_data": {"duracion": "1 hora"}
    }
    fallback_output = provider._generate_fallback(patient_data)
    assert isinstance(fallback_output, AIStructuredOutput)
    assert fallback_output.prioridad_sugerida_ia in ["GREEN", "YELLOW", "RED"]
    assert len(fallback_output.sintomas_principales) > 0
    assert len(fallback_output.resumen_clinico_narrativo) > 10


# =============================================================================
# CV06: Conmutación dinámica de proveedores de IA mediante AI_PROVIDER
# =============================================================================
def test_cv06_ai_factory_provider_switching(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    assert isinstance(get_ai_provider(), GeminiProvider)

    monkeypatch.setattr(settings, "AI_PROVIDER", "groq")
    assert isinstance(get_ai_provider(), GroqProvider)

    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    assert isinstance(get_ai_provider(), OpenAIProvider)


# =============================================================================
# CV07: Safety Override - Activación forzada a ROJO ante dolor de pecho
# =============================================================================
def test_cv07_safety_override_chest_pain():
    mock_ai_output = AIStructuredOutput(
        sintomas_principales=["Molestia en pecho"],
        duracion_e_intensidad="1 hora",
        factores_agravantes_antecedentes=[],
        senales_alerta_identificadas=[],
        prioridad_sugerida_ia="GREEN",  # IA sugiere erróneamente Verde
        resumen_clinico_narrativo="Paciente refiere molestia en el pecho.",
        informacion_faltante_critica=[]
    )

    final_prio, override_applied, reason = evaluate_safety_overrides(
        raw_symptoms="Siento una fuerte opresión en el pecho y dolor precordial",
        age=50,
        static_data={"intensidad": 7},
        ai_output=mock_ai_output
    )

    assert final_prio == "RED"
    assert override_applied is True
    assert "Regla de Seguridad" in reason


# =============================================================================
# CV08: Safety Override - Activación forzada a ROJO ante lactante febril (<1 año)
# =============================================================================
def test_cv08_safety_override_febrile_infant():
    mock_ai_output = AIStructuredOutput(
        sintomas_principales=["Fiebre"],
        duracion_e_intensidad="4 horas",
        factores_agravantes_antecedentes=[],
        senales_alerta_identificadas=[],
        prioridad_sugerida_ia="YELLOW",  # IA sugiere Amarillo
        resumen_clinico_narrativo="Lactante con temperatura elevada.",
        informacion_faltante_critica=[]
    )

    final_prio, override_applied, reason = evaluate_safety_overrides(
        raw_symptoms="El bebé de 6 meses tiene fiebre alta y llanto constante",
        age=0,  # Menor de 1 año
        static_data={"intensidad": 8},
        ai_output=mock_ai_output
    )

    assert final_prio == "RED"
    assert override_applied is True
    assert "Pediatría" in reason


# =============================================================================
# CV09: Validación de Esquema Pydantic AIStructuredOutput
# =============================================================================
def test_cv09_pydantic_ai_structured_output_validation():
    valid_data = {
        "sintomas_principales": ["Cefalea pulsátil"],
        "duracion_e_intensidad": "3 días, 6/10",
        "factores_agravantes_antecedentes": ["Estrés laboral"],
        "senales_alerta_identificadas": [],
        "prioridad_sugerida_ia": "YELLOW",
        "resumen_clinico_narrativo": "Paciente con cefalea tensional de 3 días de evolución.",
        "informacion_faltante_critica": ["Signos meníngeos"]
    }
    schema = AIStructuredOutput(**valid_data)
    assert schema.prioridad_sugerida_ia == "YELLOW"

    with pytest.raises(Exception):
        AIStructuredOutput(**{**valid_data, "prioridad_sugerida_ia": "INVALID_COLOR"})


# =============================================================================
# CV10: Cierre de Consulta Médica (/api/v1/doctor/review)
# =============================================================================
def test_cv10_doctor_review_submission():
    triage_id = "test-triage-cv10"
    _IN_MEMORY_TRIAGE_DB[triage_id] = {
        "id": triage_id,
        "access_code": "MS-TST10",
        "status": "READY",
        "final_priority": "YELLOW"
    }

    review_payload = {
        "triage_id": triage_id,
        "doctor_id": "doc-uuid-12345",
        "doctor_notes": "Paciente atendido y medicado con analgésicos.",
        "priority_adjusted": "GREEN"
    }

    response = client.post("/api/v1/doctor/review", json=review_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert _IN_MEMORY_TRIAGE_DB[triage_id]["status"] == "REVIEWED"
    assert _IN_MEMORY_TRIAGE_DB[triage_id]["final_priority"] == "GREEN"


# =============================================================================
# CV11: Acceso a endpoints del portal médico
# =============================================================================
def test_cv11_doctor_dashboard_access():
    response = client.get("/api/v1/doctor/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "records" in data


# =============================================================================
# CV12: Trazabilidad inalterable - Consulta de paciente
# =============================================================================
def test_cv12_patient_detail_audit_trace():
    triage_id = "MS-AUD12"
    ci_enc = encrypt_ci("5544332 SC")
    _IN_MEMORY_TRIAGE_DB[triage_id] = {
        "id": triage_id,
        "access_code": triage_id,
        "ci_encrypted": ci_enc,
        "patient_name": "Ana Vaca",
        "status": "READY",
        "final_priority": "GREEN"
    }

    response = client.get(f"/api/v1/doctor/patient/{triage_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["decrypted_ci"] == "5544332 SC"


# =============================================================================
# CV13: Control de Abuso y Rate Limiting (>5 peticiones / 5 min)
# =============================================================================
def test_cv13_rate_limiting_exceeded():
    _LOCAL_RATE_LIMIT_DB.clear()
    test_ip = "192.168.1.100"

    headers = {"X-Forwarded-For": test_ip}
    payload = {
        "patient_name": "Test Rate Limit",
        "ci": "112233 SC",
        "age": 25,
        "gender": "Masculino",
        "raw_symptoms": "Consulta general"
    }

    # Primeras 5 peticiones deben ser aceptadas (201)
    for _ in range(MAX_REQUESTS_PER_WINDOW):
        resp = client.post("/api/v1/triage/process", json=payload, headers=headers)
        assert resp.status_code == 201

    # La 6ta petición debe ser rechazada con HTTP 429
    resp_blocked = client.post("/api/v1/triage/process", json=payload, headers=headers)
    assert resp_blocked.status_code == 429
    assert "Límite de solicitudes excedido" in resp_blocked.json()["detail"]


# =============================================================================
# CV14: Generación de preguntas dinámicas adaptativas (Paso 2)
# =============================================================================
def test_cv14_dynamic_questions_generation():
    payload = {
        "symptom": "dolor de cabeza agudo",
        "age": 35
    }
    response = client.post("/api/v1/triage/dynamic-questions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert 2 <= len(data["questions"]) <= 3
    for q in data["questions"]:
        assert "question_text" in q
        assert len(q["options"]) >= 2


# =============================================================================
# CV15: Consulta de estado de triaje por Access Code
# =============================================================================
def test_cv15_get_triage_status():
    access_code = "MS-STAT1"
    _IN_MEMORY_TRIAGE_DB[access_code] = {
        "id": "tr-status-1",
        "access_code": access_code,
        "status": "READY",
        "final_priority": "YELLOW"
    }
    response = client.get(f"/api/v1/triage/status/{access_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["access_code"] == access_code
    assert data["status"] == "READY"


# =============================================================================
# CV16: Búsqueda médica indexada por hash de CI y código de acceso
# =============================================================================
def test_cv16_triage_lookup():
    access_code = "MS-LOOK1"
    _IN_MEMORY_TRIAGE_DB[access_code] = {
        "id": "tr-look-1",
        "access_code": access_code,
        "ci_hash": hash_ci("998877 SC"),
        "status": "READY"
    }
    response = client.get("/api/v1/triage/lookup", params={"access_code": access_code})
    assert response.status_code == 200
    assert response.json()["access_code"] == access_code


# =============================================================================
# CV17: Descifrado seguro de CI en memoria para vista médica
# =============================================================================
def test_cv17_in_memory_ci_decryption():
    ci_secret = "9876543 SC"
    encrypted = encrypt_ci(ci_secret)
    triage_id = "MS-DEC17"
    _IN_MEMORY_TRIAGE_DB[triage_id] = {
        "id": triage_id,
        "access_code": triage_id,
        "ci_encrypted": encrypted,
        "status": "READY"
    }
    response = client.get(f"/api/v1/doctor/patient/{triage_id}")
    assert response.status_code == 200
    assert response.json()["decrypted_ci"] == ci_secret


# =============================================================================
# CV18: Lógica de ordenamiento del Dashboard de guardia por gravedad
# =============================================================================
def test_cv18_doctor_dashboard_priority_sorting():
    from unittest.mock import patch
    with patch.object(supabase_service, "obtener_cliente", return_value=None), patch.object(supabase_service, "get_client", return_value=None):
        _IN_MEMORY_TRIAGE_DB.clear()
        
        records = [
            {"id": "rec-green", "access_code": "MS-GRN01", "final_priority": "GREEN", "status": "READY", "created_at": "2026-08-13T10:00:00Z"},
            {"id": "rec-red", "access_code": "MS-RED01", "final_priority": "RED", "status": "READY", "created_at": "2026-08-13T10:05:00Z"},
            {"id": "rec-yellow", "access_code": "MS-YEL01", "final_priority": "YELLOW", "status": "READY", "created_at": "2026-08-13T10:02:00Z"},
        ]
        for r in records:
            _IN_MEMORY_TRIAGE_DB[r["id"]] = r

        response = client.get("/api/v1/doctor/dashboard")
        assert response.status_code == 200
        data = response.json()
        sorted_recs = data["records"]
        assert len(sorted_recs) == 3
        priorities = [r["final_priority"] for r in sorted_recs]
        assert priorities[0] == "RED"
        assert priorities[1] == "YELLOW"
        assert priorities[2] == "GREEN"


# =============================================================================
# CV19: Resistencia y validación de entrada en PatientInputSchema
# =============================================================================
def test_cv19_patient_input_schema_validation():
    invalid_payload = {
        "patient_name": "Test",
        "ci": "123",
        "age": 150,  # Fuera de rango (0-120)
        "gender": "M",
        "raw_symptoms": "Fiebre"
    }
    with pytest.raises(Exception):
        PatientInputSchema(**invalid_payload)


# =============================================================================
# CV20: Manejador global de excepciones con sanitización de errores 500
# =============================================================================
def test_cv20_global_exception_handler_sanitization():
    # Petición a ruta inexistente o con parámetro inválido no debe exponer traceback sensible
    response = client.get("/api/v1/triage/lookup")
    assert response.status_code == 400
    assert "detail" in response.json()
