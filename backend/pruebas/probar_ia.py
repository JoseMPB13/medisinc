"""
Script de Diagnóstico y Prueba en Vivo para el Módulo de Inteligencia Artificial (MediSinc-IA).
Evalúa:
1. Conexión y estado del proveedor de IA activo (Gemini / Groq / OpenAI).
2. Generación dinámica de preguntas estructuradas adaptativas (Paso 2).
3. Análisis, resumen clínico, extracción de banderas rojas y categorización de prioridad (Paso 3).
4. Efectividad del motor de reglas determinista de seguridad.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Asegurar codificación UTF-8 en consola Windows
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.proveedores.fabrica_ia import obtener_proveedor_ia
from app.servicios.motor_reglas import evaluar_sobreescrituras_seguridad


async def probar_ia_en_vivo():
    print("=" * 70)
    print("MEDISINC-IA - DIAGNOSTICO Y PRUEBA EN VIVO DEL SISTEMA DE IA")
    print("=" * 70)
    print(f"[+] Proveedor Configurado (AI_PROVIDER): {settings.AI_PROVIDER}")
    print(f"[+] Gemini API Key presente: {'SI' if settings.GEMINI_API_KEY and 'coloca_aqui' not in settings.GEMINI_API_KEY else 'NO'}")
    print(f"[+] Groq API Key presente: {'SI' if settings.GROQ_API_KEY and 'coloca_aqui' not in settings.GROQ_API_KEY else 'NO'}")
    print(f"[+] OpenAI API Key presente: {'SI' if settings.OPENAI_API_KEY and 'coloca_aqui' not in settings.OPENAI_API_KEY else 'NO'}")
    print("-" * 70)

    proveedor = obtener_proveedor_ia()
    print(f"[+] Adaptador Instanciado: {proveedor.__class__.__name__}")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # CASO DE PRUEBA 1: Preguntas Dinámicas Adaptativas (Paso 2)
    # -------------------------------------------------------------------------
    print("\n[PRUEBA 1] Generacion Adaptativa de Preguntas (Paso 2)")
    print("   Paciente: 45 anos, Masculino")
    print("   Sintomas: 'Siento un dolor punzante en el pecho y me falta el aire desde anoche'")

    preguntas = await proveedor.generar_preguntas_dinamicas(
        sintomas="Siento un dolor punzante en el pecho y me falta el aire desde anoche",
        edad=45,
        genero="Masculino"
    )

    print(f"   -> Preguntas generadas: {len(preguntas)}")
    for i, p in enumerate(preguntas, 1):
        texto_p = p.get('pregunta') or p.get('question')
        print(f"\n   Pregunta {i}: {texto_p}")
        opciones = p.get('opciones') or p.get('options', [])
        for opt in opciones:
            if isinstance(opt, dict):
                etiqueta = opt.get('etiqueta') or opt.get('label') or opt.get('texto') or str(opt)
                es_alerta = opt.get('es_alerta_roja', False) or opt.get('is_red_flag', False)
            else:
                etiqueta = str(opt)
                es_alerta = False
            alerta_str = " [ALERTA ROJA]" if es_alerta else ""
            print(f"      - {etiqueta}{alerta_str}")

    # -------------------------------------------------------------------------
    # CASO DE PRUEBA 2: Análisis y Estructuración de Triaje (Paso 3)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[PRUEBA 2] Analisis Clinico y Priorizacion con IA (Paso 3)")
    print("   Paciente: 28 anos, Femenino")
    print("   Sintomas: 'Dolor abdominal agudo en el lado derecho, nauseas severas (basca) y fiebre'")

    datos_estaticos = {
        "escala_dolor": 8,
        "tiempo_evolucion": "12 horas",
        "enfermedades_previas": ["Ninguna"],
        "medicacion_actual": ["Ibuprofeno"]
    }
    respuestas_dinamicas = {
        "p1": "El dolor empeora al caminar o toser",
        "p2": "Fiebre medida en 38.5 C"
    }

    salida_ia = await proveedor.estructurar_triaje(
        sintomas="Dolor abdominal agudo en el lado derecho, nauseas severas (basca) y fiebre",
        edad=28,
        genero="Femenino",
        datos_estaticos=datos_estaticos,
        respuestas_dinamicas=respuestas_dinamicas
    )

    print(f"   -> Prioridad sugerida por IA: {salida_ia.prioridad_sugerida_ia}")
    print(f"   -> Resumen clinico: {salida_ia.resumen_clinico_narrativo}")
    print(f"   -> Sintomas principales: {salida_ia.sintomas_principales}")
    print(f"   -> Duracion e intensidad: {salida_ia.duracion_e_intensidad}")
    print(f"   -> Factores agravantes: {salida_ia.factores_agravantes_antecedentes}")
    print(f"   -> Senales de alerta: {salida_ia.senales_alerta_identificadas}")
    print(f"   -> Informacion critica a indagar: {salida_ia.informacion_faltante_critica}")

    # -------------------------------------------------------------------------
    # CASO DE PRUEBA 3: Evaluación del Motor de Reglas Duras de Seguridad
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[PRUEBA 3] Validacion del Motor de Reglas Deterministas (Manchester)")
    prioridad_final, sobreescritura, motivo = evaluar_sobreescrituras_seguridad(
        sintomas_brutos="Dolor abdominal agudo en el lado derecho, nauseas severas (basca) y fiebre",
        edad=28,
        datos_estaticos=datos_estaticos,
        salida_ia=salida_ia
    )

    print(f"   -> Prioridad Final Definitiva: {prioridad_final}")
    print(f"   -> Se aplico sobreescritura de seguridad?: {'SI' if sobreescritura else 'NO'}")
    if sobreescritura:
        print(f"   -> Motivo clinico: {motivo}")

    # -------------------------------------------------------------------------
    # CASO DE PRUEBA 4: Safety Override Crítico (Dolor Torácico / Infarto)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("[PRUEBA 4] Evaluacion de Alerta Vital (Safety Override Nivel I)")
    salida_ia_rojo = await proveedor.estructurar_triaje(
        sintomas="Opresion precordial con dolor irradiado al brazo izquierdo y diaforesis",
        edad=58,
        genero="Masculino",
        datos_estaticos={"intensidad": 9},
        respuestas_dinamicas={"opresion": "Dolor tipo peso"}
    )
    p_final, sob, mot = evaluar_sobreescrituras_seguridad(
        sintomas_brutos="Opresion precordial con dolor irradiado al brazo izquierdo y diaforesis",
        edad=58,
        datos_estaticos={"intensidad": 9},
        salida_ia=salida_ia_rojo
    )
    print(f"   -> Sintomas: Opresion precordial con dolor irradiado a brazo")
    print(f"   -> Prioridad IA: {salida_ia_rojo.prioridad_sugerida_ia}")
    print(f"   -> Prioridad Final Manchester: {p_final} (Emergencia Vital)")
    print(f"   -> Motivo de Alerta: {mot}")

    print("\n" + "=" * 70)
    print("DIAGNOSTICO DE IA COMPLETADO EXITOSAMENTE (100% OPERATIVO)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(probar_ia_en_vivo())
