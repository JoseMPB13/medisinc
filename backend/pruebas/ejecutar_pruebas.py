"""
Ejecutor de Pruebas de Validación Técnica y Seguridad Médica para MediSinc-IA (CV01 - CV20).
Ejecuta la batería completa de 20 casos de prueba e imprime un reporte detallado.
"""

import sys
import os
import asyncio
import inspect
from pathlib import Path

# Configurar path para importar el paquete app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configurar entorno de pruebas
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = "https://placeholder.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "mock_key"
os.environ["AES_SECRET_KEY"] = "medisinc_secret_aes_key_32_bytes_len!"
os.environ["HMAC_PEPPER_KEY"] = "medisinc_hmac_pepper_secret_key"
os.environ["AI_PROVIDER"] = "gemini"

from app.core.configuracion import settings
from pruebas import prueba_suite_validacion


def ejecutar_bateria_pruebas():
    casos_prueba = [
        ("CV01: Creación de pre-triaje y formato regex del código MS-XXXXX", prueba_suite_validacion.test_cv01_creacion_pretriaje_formato_codigo),
        ("CV02: Cifrado simétrico AES (Fernet) para Carnet de Identidad", prueba_suite_validacion.test_cv02_cifrado_simetrico_ci),
        ("CV03: Hashing seguro HMAC-SHA256 con Pepper para CI", prueba_suite_validacion.test_cv03_hashing_hmac_pepper_ci),
        ("CV04: Formato regex del código único generado (^MS-[2-9A-Z]{5}$)", prueba_suite_validacion.test_cv04_formato_regex_exclusion_ambiguos),
        ("CV05: Fallback resiliente ante caída de API externa de IA", prueba_suite_validacion.test_cv05_fallback_resiliente_ia),
        ("CV06: Conmutación dinámica de proveedores de IA (Gemini, Groq, OpenAI)", prueba_suite_validacion.test_cv06_conmutacion_fabrica_ia),
        ("CV07: Safety Override - Activación forzada a ROJO ante dolor torácico", prueba_suite_validacion.test_cv07_sobreescritura_dolor_toracico),
        ("CV08: Safety Override - Activación forzada a ROJO ante lactante febril (<1 año)", prueba_suite_validacion.test_cv08_sobreescritura_lactante_febril),
        ("CV09: Validación estricta de esquema Pydantic AIStructuredOutput", prueba_suite_validacion.test_cv09_validacion_esquema_salida_ia),
        ("CV10: Cierre de consulta médica y transición de estado a REVIEWED", prueba_suite_validacion.test_cv10_cierre_consulta_revision_medica),
        ("CV11: Acceso a endpoints y métricas del dashboard médico", prueba_suite_validacion.test_cv11_metricas_dashboard_medico),
        ("CV12: Trazabilidad inalterable - Deserialización y consulta de expediente", prueba_suite_validacion.test_cv12_trazabilidad_consulta_expediente),
        ("CV13: Control de Abuso y Rate Limiting (>5 peticiones/5 min genera 429)", prueba_suite_validacion.test_cv13_control_abuso_rate_limiting),
        ("CV14: Generación de 2 a 3 preguntas dinámicas adaptativas en Paso 2", prueba_suite_validacion.test_cv14_preguntas_dinamicas_adaptativas),
        ("CV15: Consulta de estado de triaje en tiempo real por Access Code", prueba_suite_validacion.test_cv15_consulta_estado_tiempo_real),
        ("CV16: Búsqueda médica indexada por hash de CI y código de acceso", prueba_suite_validacion.test_cv16_busqueda_indexada_ci_hash),
        ("CV17: Descifrado seguro de CI en memoria para pantalla médica", prueba_suite_validacion.test_cv17_descifrado_seguro_ci_memoria),
        ("CV18: Lógica de ordenamiento del Dashboard de guardia por gravedad", prueba_suite_validacion.test_cv18_ordenamiento_dashboard_gravedad),
        ("CV19: Resistencia y validación de rangos en PatientInputSchema", prueba_suite_validacion.test_cv19_resistencia_rangos_entrada_paciente),
        ("CV20: Manejador global de excepciones con sanitización de errores 500", prueba_suite_validacion.test_cv20_manejador_global_sanitizacion_errores),
    ]

    print("\n" + "=" * 66)
    print("EJECUTANDO BATERIA COMPLETA DE PRUEBAS TECNICAS EN ESPAÑOL (CV01 - CV20)")
    print("=" * 66)

    pasadas = 0
    falladas = 0

    class MockMonkeypatch:
        def setattr(self, obj, attr, val):
            setattr(obj, attr, val)

    mock_monkeypatch = MockMonkeypatch()

    for descripcion, funcion in casos_prueba:
        try:
            params = inspect.signature(funcion).parameters
            if inspect.iscoroutinefunction(funcion):
                if "monkeypatch" in params:
                    asyncio.run(funcion(mock_monkeypatch))
                else:
                    asyncio.run(funcion())
            else:
                if "monkeypatch" in params:
                    funcion(mock_monkeypatch)
                else:
                    funcion()

            print(f"[PASS] {descripcion}")
            pasadas += 1
        except Exception as e:
            print(f"[FAIL] {descripcion} -> Fallo: {e}")
            falladas += 1

    total = len(casos_prueba)
    porcentaje = (pasadas / total) * 100

    print("\n" + "=" * 66)
    print(f"RESUMEN FINAL: {pasadas}/{total} PRUEBAS SUPERADAS ({porcentaje:.0f}%)")
    print("=" * 66 + "\n")

    return 0 if falladas == 0 else 1


if __name__ == "__main__":
    codigo_salida = ejecutar_bateria_pruebas()
    sys.exit(codigo_salida)
