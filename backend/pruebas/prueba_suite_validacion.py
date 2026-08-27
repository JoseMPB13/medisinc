"""
Banco de Pruebas Automatizadas de Validación Técnica, Seguridad Médica y Reglas Clínicas (CV01 - CV20).
Proyecto: MediSinc-IA (FastAPI + Supabase + IA Agnóstica en Español).
"""

import re
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.core.configuracion import configuracion, settings
from app.core.seguridad import cifrar_ci, descifrar_ci, hashear_ci, generar_codigo_acceso
from app.core.limite_peticiones import _LOCAL_RATE_LIMIT_DB, VENTANA_SEGUNDOS, LIMITE_PETICIONES_VENTANA
from app.servicios.motor_reglas import evaluar_sobreescrituras_seguridad
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA, EsquemaEntradaPaciente
from app.proveedores.fabrica_ia import obtener_proveedor_ia
from app.proveedores.proveedor_gemini import ProveedorGemini
from app.proveedores.proveedor_groq import ProveedorGroq
from app.proveedores.proveedor_openai import ProveedorOpenAI
from app.servicios.servicio_supabase import _BD_LOCAL_TRIAJES, _BD_LOCAL_RESULTADOS_IA, servicio_supabase

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# CV01: Creación de pre-triaje y formato regex del código alfanumérico (^MS-[2-9A-Z]{5}$)
# =============================================================================
def test_cv01_creacion_pretriaje_formato_codigo():
    payload = {
        "nombre_paciente": "Carlos Mamani",
        "ci": "8765432 SC",
        "edad": 42,
        "genero": "Masculino",
        "sintomas_brutos": "Dolor abdominal moderado y náuseas",
        "datos_estaticos": {"intensidad": 6, "duracion": "4 horas"},
        "respuestas_dinamicas": {"ubicacion": "epigastrio"}
    }
    respuesta = client.post("/api/v1/triaje/procesar", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert "triaje_id" in datos or "triage_id" in datos
    assert "codigo_acceso" in datos or "access_code" in datos
    codigo = datos.get("codigo_acceso") or datos.get("access_code")
    assert re.match(r"^MS-[2-9A-Z]{5}$", codigo)


# =============================================================================
# CV02: Cifrado simétrico AES-256 (Fernet) para Carnet de Identidad
# =============================================================================
def test_cv02_cifrado_simetrico_ci():
    ci_original = "7891234 LP"
    cifrado = cifrar_ci(ci_original)
    assert cifrado != ci_original
    assert len(cifrado) > 20
    descifrado = descifrar_ci(cifrado)
    assert descifrado == ci_original


# =============================================================================
# CV03: Hashing seguro ciego HMAC-SHA256 con Pepper para CI
# =============================================================================
def test_cv03_hashing_hmac_pepper_ci():
    ci_1 = "1234567-SC"
    ci_2 = " 1234567-sc "
    hash_1 = hashear_ci(ci_1)
    hash_2 = hashear_ci(ci_2)
    assert hash_1 == hash_2
    assert len(hash_1) == 64  # SHA-256 hexdigest
    assert hash_1 != ci_1


# =============================================================================
# CV04: Formato regex y exclusión de caracteres ambiguos (0, O, 1, I)
# =============================================================================
def test_cv04_formato_regex_exclusion_ambiguos():
    patron_regex = r"^MS-[2-9A-Z]{5}$"
    for _ in range(50):
        codigo = generar_codigo_acceso()
        assert re.match(patron_regex, codigo)
        assert "0" not in codigo and "O" not in codigo
        assert "1" not in codigo and "I" not in codigo


# =============================================================================
# CV05: Fallback clínico resiliente ante caída de API externa de IA
# =============================================================================
@pytest.mark.asyncio
async def test_cv05_fallback_resiliente_ia():
    proveedor = ProveedorGemini()
    datos_paciente = {
        "nombre_paciente": "Paciente Prueba",
        "edad": 30,
        "genero": "Femenino",
        "sintomas_brutos": "Dolor de cabeza leve",
        "datos_estaticos": {"duracion": "1 hora"}
    }
    salida_contingencia = proveedor.generar_salida_contingencia(datos_paciente)
    assert isinstance(salida_contingencia, EsquemaSalidaEstructuradaIA)
    assert salida_contingencia.prioridad_sugerida_ia in ["VERDE", "AMARILLO", "ROJO", "GREEN", "YELLOW", "RED"]
    assert len(salida_contingencia.sintomas_principales) > 0
    assert len(salida_contingencia.resumen_clinico_narrativo) > 10


# =============================================================================
# CV06: Conmutación dinámica de proveedores de IA (Gemini, Groq, OpenAI)
# =============================================================================
def test_cv06_conmutacion_fabrica_ia(monkeypatch=None):
    from app.core.config import settings as s1
    from app.core.configuracion import settings as s2

    s1.AI_PROVIDER = "gemini"
    s2.AI_PROVIDER = "gemini"
    p1 = obtener_proveedor_ia()
    assert isinstance(p1, ProveedorGemini) or "gemini" in type(p1).__name__.lower()

    s1.AI_PROVIDER = "groq"
    s2.AI_PROVIDER = "groq"
    p2 = obtener_proveedor_ia()
    assert isinstance(p2, ProveedorGroq) or "groq" in type(p2).__name__.lower()

    s1.AI_PROVIDER = "openai"
    s2.AI_PROVIDER = "openai"
    p3 = obtener_proveedor_ia()
    assert isinstance(p3, ProveedorOpenAI) or "openai" in type(p3).__name__.lower()


# =============================================================================
# CV07: Safety Override - Activación forzada a ROJO ante dolor torácico
# =============================================================================
def test_cv07_sobreescritura_dolor_toracico():
    salida_mock_ia = EsquemaSalidaEstructuradaIA(
        sintomas_principales=["Molestia en pecho"],
        duracion_e_intensidad="1 hora",
        factores_agravantes_antecedentes=[],
        senales_alerta_identificadas=[],
        prioridad_sugerida_ia="VERDE",
        resumen_clinico_narrativo="Paciente refiere molestia en el pecho.",
        informacion_faltante_critica=[]
    )

    prioridad_final, sobreescritura_aplicada, motivo = evaluar_sobreescrituras_seguridad(
        sintomas_brutos="Siento una fuerte opresión en el pecho y dolor precordial",
        edad=50,
        datos_estaticos={"intensidad": 7},
        salida_ia=salida_mock_ia
    )

    assert prioridad_final in ["ROJO", "RED"]
    assert sobreescritura_aplicada is True
    assert "Regla de Seguridad" in motivo or "Seguridad" in motivo


# =============================================================================
# CV08: Safety Override - Activación forzada a ROJO ante lactante febril (<1 año)
# =============================================================================
def test_cv08_sobreescritura_lactante_febril():
    salida_mock_ia = EsquemaSalidaEstructuradaIA(
        sintomas_principales=["Fiebre moderada"],
        duracion_e_intensidad="3 horas",
        factores_agravantes_antecedentes=[],
        senales_alerta_identificadas=[],
        prioridad_sugerida_ia="AMARILLO",
        resumen_clinico_narrativo="Lactante con fiebre.",
        informacion_faltante_critica=[]
    )

    prioridad_final, sobreescritura_aplicada, motivo = evaluar_sobreescrituras_seguridad(
        sintomas_brutos="El bebé tiene chucho de frío y fiebre alta constante",
        edad=0,
        datos_estaticos={"intensidad": 8},
        salida_ia=salida_mock_ia
    )

    assert prioridad_final in ["ROJO", "RED"]
    assert sobreescritura_aplicada is True


# =============================================================================
# CV09: Validación estricta de esquema Pydantic EsquemaSalidaEstructuradaIA
# =============================================================================
def test_cv09_validacion_esquema_salida_ia():
    datos_validos = {
        "sintomas_principales": ["Cefalea pulsátil"],
        "duracion_e_intensidad": "2 días, 7/10",
        "factores_agravantes_antecedentes": ["Estrés laboral"],
        "senales_alerta_identificadas": ["Fotofobia"],
        "prioridad_sugerida_ia": "AMARILLO",
        "resumen_clinico_narrativo": "Paciente con cefalea pulsátil de intensidad 7/10.",
        "informacion_faltante_critica": ["Toma de presión arterial"]
    }
    esquema = EsquemaSalidaEstructuradaIA(**datos_validos)
    assert esquema.prioridad_sugerida_ia == "AMARILLO"

    with pytest.raises(ValidationError):
        datos_invalidos = datos_validos.copy()
        datos_invalidos["prioridad_sugerida_ia"] = "PRIORIDAD_INVALIDA"
        EsquemaSalidaEstructuradaIA(**datos_invalidos)


# =============================================================================
# CV10: Cierre de consulta médica y transición de estado a REVISADO
# =============================================================================
def test_cv10_cierre_consulta_revision_medica():
    triaje_id = "test-triage-cv10"
    _BD_LOCAL_TRIAJES[triaje_id] = {
        "id": triaje_id,
        "codigo_acceso": "MS-REV10",
        "nombre_paciente": "Paciente Cierre",
        "estado": "LISTO",
        "status": "READY",
        "creado_en": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "triaje_id": triaje_id,
        "medico_id": "doc-uuid-12345",
        "notas_medico": "Paciente evaluado presencialmente. Se descarta abdomen agudo.",
        "prioridad_ajustada": "VERDE"
    }

    resp = client.post("/api/v1/medico/revisar", json=payload)
    assert resp.status_code == 200
    assert resp.json()["estado"] in ["exito", "success"] or resp.json()["status"] in ["exito", "success"]
    assert _BD_LOCAL_TRIAJES[triaje_id]["estado"] in ["REVISADO", "REVIEWED"]


# =============================================================================
# CV11: Acceso a endpoints y métricas del dashboard médico
# =============================================================================
def test_cv11_metricas_dashboard_medico():
    resp = client.get("/api/v1/medico/panel")
    assert resp.status_code == 200
    datos = resp.json()
    assert "metricas" in datos or "metrics" in datos
    assert "registros" in datos or "records" in datos


# =============================================================================
# CV12: Trazabilidad inalterable - Deserialización y consulta de expediente
# =============================================================================
def test_cv12_trazabilidad_consulta_expediente():
    codigo = "MS-AUD12"
    _BD_LOCAL_TRIAJES[codigo] = {
        "id": codigo,
        "codigo_acceso": codigo,
        "ci_cifrado": cifrar_ci("9876543 SC"),
        "nombre_paciente": "Paciente Auditoria",
        "edad": 29,
        "genero": "Femenino",
        "sintomas_brutos": "Dolor lumbar",
        "datos_estaticos": {},
        "respuestas_dinamicas": {},
        "estado": "RECIBIDO",
        "creado_en": datetime.now(timezone.utc).isoformat()
    }

    resp = client.get(f"/api/v1/medico/paciente/{codigo}")
    assert resp.status_code == 200
    datos = resp.json()
    assert datos.get("ci_descifrado") == "9876543 SC" or datos.get("decrypted_ci") == "9876543 SC"


# =============================================================================
# CV13: Control de Abuso y Rate Limiting (>5 peticiones/5 min genera 429)
# =============================================================================
def test_cv13_control_abuso_rate_limiting():
    _LOCAL_RATE_LIMIT_DB.clear()
    ip_prueba = "192.168.1.100"
    headers = {"X-Forwarded-For": ip_prueba}
    payload = {
        "nombre_paciente": "Test Rate Limit",
        "ci": "112233 SC",
        "edad": 25,
        "genero": "Masculino",
        "sintomas_brutos": "Consulta general"
    }

    for _ in range(LIMITE_PETICIONES_VENTANA):
        resp = client.post("/api/v1/triaje/procesar", json=payload, headers=headers)
        assert resp.status_code == 201

    resp_bloqueado = client.post("/api/v1/triaje/procesar", json=payload, headers=headers)
    assert resp_bloqueado.status_code == 429


# =============================================================================
# CV14: Generación de 2 a 3 preguntas dinámicas adaptativas en Paso 2
# =============================================================================
def test_cv14_preguntas_dinamicas_adaptativas():
    payload = {"sintomas_brutos": "dolor de cabeza agudo", "edad": 35}
    respuesta = client.post("/api/v1/triaje/preguntas-dinamicas", json=payload)
    assert respuesta.status_code == 200
    datos = respuesta.json()
    preguntas = datos.get("preguntas") or datos.get("questions")
    assert 2 <= len(preguntas) <= 3


# =============================================================================
# CV15: Consulta de estado de triaje en tiempo real por Access Code
# =============================================================================
def test_cv15_consulta_estado_tiempo_real():
    codigo = "MS-STA15"
    _BD_LOCAL_TRIAJES[codigo] = {
        "id": codigo,
        "codigo_acceso": codigo,
        "nombre_paciente": "Paciente Estado",
        "estado": "RECIBIDO",
        "creado_en": datetime.now(timezone.utc).isoformat()
    }
    resp = client.get(f"/api/v1/triaje/estado/{codigo}")
    assert resp.status_code == 200
    assert resp.json().get("codigo_acceso") == codigo or resp.json().get("access_code") == codigo


# =============================================================================
# CV16: Búsqueda médica indexada por hash de CI y código de acceso
# =============================================================================
def test_cv16_busqueda_indexada_ci_hash():
    codigo = "MS-SRC16"
    ci_paciente = "6543210 SC"
    ci_hash = hashear_ci(ci_paciente)

    item = {
        "id": "tr-src-16",
        "codigo_acceso": codigo,
        "access_code": codigo,
        "ci_hash": ci_hash,
        "nombre_paciente": "Paciente Busqueda",
        "patient_name": "Paciente Busqueda",
        "estado": "RECIBIDO",
        "status": "RECEIVED",
        "creado_en": datetime.now(timezone.utc).isoformat()
    }
    _BD_LOCAL_TRIAJES[codigo] = item
    _BD_LOCAL_TRIAJES["tr-src-16"] = item

    # Búsqueda por código
    resp_cod = client.get("/api/v1/triaje/buscar", params={"codigo_acceso": codigo})
    assert resp_cod.status_code == 200
    assert resp_cod.json().get("codigo_acceso") == codigo or resp_cod.json().get("access_code") == codigo

    # Búsqueda por CI
    resp_ci = client.get("/api/v1/triaje/buscar", params={"ci": ci_paciente})
    assert resp_ci.status_code == 200


# =============================================================================
# CV17: Descifrado seguro de CI en memoria únicamente en revisión
# =============================================================================
def test_cv17_descifrado_seguro_ci_memoria():
    codigo = "MS-DEC17"
    ci_secreto = "5544332 SC"
    _BD_LOCAL_TRIAJES[codigo] = {
        "id": codigo,
        "codigo_acceso": codigo,
        "ci_cifrado": cifrar_ci(ci_secreto),
        "nombre_paciente": "Paciente Descifrado",
        "edad": 45,
        "genero": "Masculino",
        "sintomas_brutos": "Evaluación de rutina",
        "datos_estaticos": {},
        "respuestas_dinamicas": {},
        "estado": "RECIBIDO",
        "creado_en": datetime.now(timezone.utc).isoformat()
    }

    resp = client.get(f"/api/v1/medico/paciente/{codigo}")
    assert resp.status_code == 200
    assert resp.json().get("ci_descifrado") == ci_secreto or resp.json().get("decrypted_ci") == ci_secreto


# =============================================================================
# CV18: Lógica de ordenamiento del Dashboard de guardia por gravedad
# =============================================================================
def test_cv18_ordenamiento_dashboard_gravedad(monkeypatch):
    monkeypatch.setattr(servicio_supabase, "obtener_cliente", lambda: None)
    _BD_LOCAL_TRIAJES.clear()

    _BD_LOCAL_TRIAJES["t1"] = {
        "id": "t1", "codigo_acceso": "MS-0001", "nombre_paciente": "P1 Verde",
        "prioridad_final": "VERDE", "estado": "RECIBIDO", "creado_en": "2026-08-20T10:00:00Z"
    }
    _BD_LOCAL_TRIAJES["t2"] = {
        "id": "t2", "codigo_acceso": "MS-0002", "nombre_paciente": "P2 Rojo",
        "prioridad_final": "ROJO", "estado": "RECIBIDO", "creado_en": "2026-08-20T10:05:00Z"
    }
    _BD_LOCAL_TRIAJES["t3"] = {
        "id": "t3", "codigo_acceso": "MS-0003", "nombre_paciente": "P3 Amarillo",
        "prioridad_final": "AMARILLO", "estado": "RECIBIDO", "creado_en": "2026-08-20T10:02:00Z"
    }

    cola = servicio_supabase.obtener_cola_guardia()
    assert len(cola) == 3
    assert cola[0]["prioridad_final"] == "ROJO"
    assert cola[1]["prioridad_final"] == "AMARILLO"
    assert cola[2]["prioridad_final"] == "VERDE"


# =============================================================================
# CV19: Resistencia y validación de rangos en EsquemaEntradaPaciente
# =============================================================================
def test_cv19_resistencia_rangos_entrada_paciente():
    payload_valido = {
        "nombre_paciente": "Ana Gómez",
        "ci": "998877 SC",
        "edad": 25,
        "genero": "Femenino",
        "sintomas_brutos": "Dolor de garganta"
    }
    paciente = EsquemaEntradaPaciente(**payload_valido)
    assert paciente.edad == 25

    with pytest.raises(ValidationError):
        payload_edad_invalida = payload_valido.copy()
        payload_edad_invalida["edad"] = 150
        EsquemaEntradaPaciente(**payload_edad_invalida)


# =============================================================================
# CV20: Manejador global de excepciones con sanitización de errores 500
# =============================================================================
def test_cv20_manejador_global_sanitizacion_errores():
    @app.get("/test-error-500-endpoint", include_in_schema=False)
    async def ruta_con_error():
        raise RuntimeError("DATABASE_PASSWORD=SuperSecretKey123! Table corruption error")

    resp = client.get("/test-error-500-endpoint")
    assert resp.status_code == 500
    datos = resp.json()
    assert "SuperSecretKey123" not in str(datos)
    assert "Ha ocurrido un error interno en el servidor" in (datos.get("detalle") or datos.get("detail", ""))
