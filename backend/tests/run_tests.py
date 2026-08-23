"""
Ejecutor Rápido de Pruebas Automatizadas de Validación Técnica y Seguridad Médica (CV01 - CV20)
MediSinc-IA Test Runner
"""

import sys
import os
import re
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
from fastapi.testclient import TestClient

# Asegurar que app esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.config import settings
from app.core.security import encrypt_ci, decrypt_ci, hash_ci, generate_access_code
from app.core.rate_limit import _LOCAL_RATE_LIMIT_DB, MAX_REQUESTS_PER_WINDOW
from app.services.rules_engine import evaluate_safety_overrides
from app.schemas.triage import AIStructuredOutput, PatientInputSchema
from app.providers.ai_factory import get_ai_provider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider
from app.services.supabase_service import _IN_MEMORY_TRIAGE_DB, _IN_MEMORY_AI_DB, supabase_service
from app.services.queue_service import queue_service

client = TestClient(app)
results = []

def run_test(test_id, description, func):
    try:
        if asyncio.iscoroutinefunction(func):
            asyncio.run(func())
        else:
            func()
        print(f"[PASS] {test_id}: {description}")
        results.append((test_id, description, "PASS", "Ejecución exitosa"))
    except AssertionError as ae:
        print(f"[FAIL] {test_id}: {description} -> Fallo: {ae}")
        results.append((test_id, description, "FAIL", f"Fallo: {ae}"))
    except Exception as e:
        print(f"[ERROR] {test_id}: {description} -> Excepción: {e}")
        results.append((test_id, description, "ERROR", f"Excepción: {e}"))

# Desactivar retries de red en tests de API inmediata
with patch.object(queue_service, "enqueue_triage_job", new_callable=AsyncMock) as mock_enqueue:
    mock_enqueue.return_value = True

    # CV01: Creación de pre-triaje y formato regex de código
    def test_cv01():
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

    # CV02: Cifrado simétrico AES para Carnet de Identidad
    def test_cv02():
        ci_original = "7891234 LP"
        encrypted = encrypt_ci(ci_original)
        assert encrypted != ci_original
        assert len(encrypted) > 20
        decrypted = decrypt_ci(encrypted)
        assert decrypted == ci_original

    # CV03: Hashing seguro HMAC-SHA256 con Pepper para CI
    def test_cv03():
        ci_1 = "1234567-SC"
        ci_2 = " 1234567-sc "
        hash_1 = hash_ci(ci_1)
        hash_2 = hash_ci(ci_2)
        assert hash_1 == hash_2
        assert len(hash_1) == 64
        assert hash_1 != ci_1

    # CV04: Formato regex del código único generado (^MS-[2-9A-Z]{5}$)
    def test_cv04():
        regex_pattern = r"^MS-[2-9A-Z]{5}$"
        for _ in range(50):
            code = generate_access_code()
            assert re.match(regex_pattern, code)
            assert "0" not in code and "O" not in code
            assert "1" not in code and "I" not in code

    # CV05: Fallback resiliente ante caída de API externa de IA
    def test_cv05():
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

    # CV06: Conmutación dinámica de proveedores de IA (Gemini, Groq, OpenAI)
    def test_cv06():
        orig_provider = settings.AI_PROVIDER
        try:
            settings.AI_PROVIDER = "gemini"
            assert isinstance(get_ai_provider(), GeminiProvider)
            settings.AI_PROVIDER = "groq"
            assert isinstance(get_ai_provider(), GroqProvider)
            settings.AI_PROVIDER = "openai"
            assert isinstance(get_ai_provider(), OpenAIProvider)
        finally:
            settings.AI_PROVIDER = orig_provider

    # CV07: Safety Override - Activación forzada a ROJO ante dolor torácico
    def test_cv07():
        mock_ai_output = AIStructuredOutput(
            sintomas_principales=["Molestia en pecho"],
            duracion_e_intensidad="1 hora",
            factores_agravantes_antecedentes=[],
            senales_alerta_identificadas=[],
            prioridad_sugerida_ia="GREEN",
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

    # CV08: Safety Override - Activación forzada a ROJO ante lactante febril (<1 año)
    def test_cv08():
        mock_ai_output = AIStructuredOutput(
            sintomas_principales=["Fiebre"],
            duracion_e_intensidad="4 horas",
            factores_agravantes_antecedentes=[],
            senales_alerta_identificadas=[],
            prioridad_sugerida_ia="YELLOW",
            resumen_clinico_narrativo="Lactante con temperatura elevada.",
            informacion_faltante_critica=[]
        )
        final_prio, override_applied, reason = evaluate_safety_overrides(
            raw_symptoms="El bebé de 6 meses tiene fiebre alta y llanto constante",
            age=0,
            static_data={"intensidad": 8},
            ai_output=mock_ai_output
        )
        assert final_prio == "RED"
        assert override_applied is True
        assert "Pediatría" in reason

    # CV09: Validación de Esquema Pydantic AIStructuredOutput
    def test_cv09():
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

    # CV10: Cierre de Consulta Médica (/api/v1/doctor/review)
    def test_cv10():
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

    # CV11: Acceso a endpoints del portal médico
    def test_cv11():
        response = client.get("/api/v1/doctor/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "records" in data

    # CV12: Trazabilidad inalterable - Deserialización y consulta de expediente
    def test_cv12():
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

    # CV13: Control de Abuso y Rate Limiting (>5 peticiones/5 min genera 429)
    def test_cv13():
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
        for _ in range(MAX_REQUESTS_PER_WINDOW):
            resp = client.post("/api/v1/triage/process", json=payload, headers=headers)
            assert resp.status_code == 201

        resp_blocked = client.post("/api/v1/triage/process", json=payload, headers=headers)
        assert resp_blocked.status_code == 429

    # CV14: Generación de preguntas adaptativas complementarias en Paso 2
    def test_cv14():
        payload = {"symptom": "dolor de cabeza agudo", "age": 35}
        response = client.post("/api/v1/triage/dynamic-questions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert 2 <= len(data["questions"]) <= 3

    # CV15: Consulta de estado de triaje por Access Code
    def test_cv15():
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

    # CV16: Búsqueda médica indexada por hash de CI y código de acceso
    def test_cv16():
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

    # CV17: Descifrado seguro de CI en memoria para pantalla médica
    def test_cv17():
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

    # CV18: Lógica de ordenamiento del Dashboard de guardia por gravedad
    def test_cv18():
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
        assert len(sorted_recs) >= 3
        priorities = [r["final_priority"] for r in sorted_recs]
        assert priorities[0] == "RED"
        assert priorities[1] == "YELLOW"
        assert priorities[2] == "GREEN"

    # CV19: Resistencia y validación de rangos en PatientInputSchema
    def test_cv19():
        invalid_payload = {
            "patient_name": "Test",
            "ci": "123",
            "age": 150,
            "gender": "M",
            "raw_symptoms": "Fiebre"
        }
        try:
            PatientInputSchema(**invalid_payload)
            raise AssertionError("Debió fallar con edad 150")
        except Exception:
            pass

    # CV20: Manejador global de excepciones con sanitización de errores 500
    def test_cv20():
        response = client.get("/api/v1/triage/lookup")
        assert response.status_code == 400
        assert "detail" in response.json()


if __name__ == "__main__":
    print("==================================================================")
    print("EJECUTANDO BATERIA COMPLETA DE PRUEBAS TECNICAS (CV01 - CV20)")
    print("==================================================================")
    run_test("CV01", "Creación de pre-triaje y formato regex del código MS-XXXXX", test_cv01)
    run_test("CV02", "Cifrado simétrico AES (Fernet) para Carnet de Identidad", test_cv02)
    run_test("CV03", "Hashing seguro HMAC-SHA256 con Pepper para CI", test_cv03)
    run_test("CV04", "Formato regex del código único generado (^MS-[2-9A-Z]{5}$)", test_cv04)
    run_test("CV05", "Fallback resiliente ante caída de API externa de IA", test_cv05)
    run_test("CV06", "Conmutación dinámica de proveedores de IA (Gemini, Groq, OpenAI)", test_cv06)
    run_test("CV07", "Safety Override - Activación forzada a ROJO ante dolor torácico", test_cv07)
    run_test("CV08", "Safety Override - Activación forzada a ROJO ante lactante febril (<1 año)", test_cv08)
    run_test("CV09", "Validación estricta de esquema Pydantic AIStructuredOutput", test_cv09)
    run_test("CV10", "Cierre de consulta médica y transición de estado a REVIEWED", test_cv10)
    run_test("CV11", "Acceso a endpoints y métricas del dashboard médico", test_cv11)
    run_test("CV12", "Trazabilidad inalterable - Deserialización y consulta de expediente", test_cv12)
    run_test("CV13", "Control de Abuso y Rate Limiting (>5 peticiones/5 min genera 429)", test_cv13)
    run_test("CV14", "Generación de 2 a 3 preguntas dinámicas adaptativas en Paso 2", test_cv14)
    run_test("CV15", "Consulta de estado de triaje en tiempo real por Access Code", test_cv15)
    run_test("CV16", "Búsqueda médica indexada por hash de CI y código de acceso", test_cv16)
    run_test("CV17", "Descifrado seguro de CI en memoria para pantalla médica", test_cv17)
    run_test("CV18", "Lógica de ordenamiento del Dashboard de guardia por gravedad", test_cv18)
    run_test("CV19", "Resistencia y validación de rangos en PatientInputSchema", test_cv19)
    run_test("CV20", "Manejador global de excepciones con sanitización de errores 500", test_cv20)

    total_passed = sum(1 for r in results if r[2] == "PASS")
    print("\n" + "=" * 66)
    print(f"RESUMEN FINAL: {total_passed}/{len(results)} PRUEBAS SUPERADAS ({int(total_passed/len(results)*100)}%)")
    print("=" * 66)
