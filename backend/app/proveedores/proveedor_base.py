"""
Clase Base Abstracta para los Proveedores de Inteligencia Artificial en MediSinc-IA.
Define la interfaz uniforme (patrón Adapter) y el motor de prompts con metodología
semiológica PQRST, triaje Manchester, contextualización por especialidad médica
y mapeador sociolingüístico boliviano/cruceño.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA, AIStructuredOutput

# Mapeador Dialectal y Semántico de Expresiones Populares de Santa Cruz de la Sierra y Bolivia
MAPEADOR_DIALECTAL_BOLIVIA = """
GUÍA DE INTERPRETACIÓN SOCIOLINGÜÍSTICA (ESPAÑOL BOLIVIANO / CRUCEÑO):
- "Chuy" / "Chucho de frío" -> Escalofríos intensos o síndrome febril en evolución (riesgo de bacteriemia/dengue).
- "Basca" / "Asco" -> Náuseas, arcadas o emesis/vómitos persistentes.
- "Estómago aventado" / "Empacho" -> Distensión abdominal aguda o meteorismo/íleo severo.
- "Quebrantamiento de cuerpo" / "Cuerpo cortado" -> Astenia, adinamia y mialgias generalizadas intensas.
- "Dolor de tutuma" / "Retumbo en la cabeza" -> Cefalea holocraneana pulsátil o hipertensiva.
"""


class ProveedorIABase(ABC):
    """
    Interfaz abstracta del proveedor de Inteligencia Artificial para el sistema de pre-triaje.
    """

    @abstractmethod
    async def estructurar_triaje(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        datos_estaticos: Optional[Dict[str, Any]] = None,
        respuestas_dinamicas: Optional[Dict[str, Any]] = None,
        especialidad_solicitada: Optional[str] = "Medicina General",
        alergias_medicamentosas: Optional[str] = "Ninguna conocida",
        medicacion_actual: Optional[str] = "Ninguna",
        enfermedades_base: Optional[List[str]] = None
    ) -> EsquemaSalidaEstructuradaIA:
        """
        Analiza los síntomas brutos y genera el informe clínico estructurado en formato Pydantic.
        """
        pass

    async def process_triage(self, patient_data: Dict[str, Any]) -> EsquemaSalidaEstructuradaIA:
        """
        Método de conveniencia para invocar el triaje mediante un diccionario de paciente.
        """
        sintomas = patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "")
        edad = patient_data.get("age") if patient_data.get("age") is not None else patient_data.get("edad", 0)
        genero = patient_data.get("gender") or patient_data.get("genero", "No especificado")
        datos_estaticos = patient_data.get("static_data") or patient_data.get("datos_estaticos", {})
        respuestas_dinamicas = patient_data.get("dynamic_answers") or patient_data.get("respuestas_dinamicas", {})
        especialidad = patient_data.get("requested_specialty") or patient_data.get("especialidad_solicitada", "Medicina General")
        alergias = patient_data.get("drug_allergies") or patient_data.get("alergias_medicamentosas", "Ninguna conocida")
        medicacion = patient_data.get("current_medication") or patient_data.get("medicacion_actual", "Ninguna")
        enfermedades = patient_data.get("base_diseases") or patient_data.get("enfermedades_base", [])

        return await self.estructurar_triaje(
            sintomas=sintomas,
            edad=edad,
            genero=genero,
            datos_estaticos=datos_estaticos,
            respuestas_dinamicas=respuestas_dinamicas,
            especialidad_solicitada=especialidad,
            alergias_medicamentosas=alergias,
            medicacion_actual=medicacion,
            enfermedades_base=enfermedades
        )

    def construir_prompt_triaje(self, patient_data: Dict[str, Any]) -> str:
        """
        Construye el prompt clínico para extracción estructurada inyectando las directivas
        de la escala Manchester, método semiológico PQRST, especialidad médica y antecedentes.
        """
        sintomas = patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "")
        edad = patient_data.get("age") if patient_data.get("age") is not None else patient_data.get("edad", 0)
        genero = patient_data.get("gender") or patient_data.get("genero", "No especificado")
        datos_estaticos = patient_data.get("static_data") or patient_data.get("datos_estaticos", {})
        respuestas_dinamicas = patient_data.get("dynamic_answers") or patient_data.get("respuestas_dinamicas", {})
        nombre = patient_data.get("patient_name") or patient_data.get("nombre_paciente", "Paciente")
        especialidad = patient_data.get("requested_specialty") or patient_data.get("especialidad_solicitada", "Medicina General")
        alergias = patient_data.get("drug_allergies") or patient_data.get("alergias_medicamentosas", "Ninguna conocida")
        medicacion = patient_data.get("current_medication") or patient_data.get("medicacion_actual", "Ninguna")
        enfermedades = patient_data.get("base_diseases") or patient_data.get("enfermedades_base", [])

        return f"""
[SYSTEM PROMPT]
Eres un médico especialista en medicina de emergencias y triaje clínico asistiendo al sistema MediSinc-IA en Santa Cruz de la Sierra, Bolivia.
El paciente ha solicitado atención en el área de: {especialidad}.
Tu función es analizar la declaración del paciente y generar un informe clínico estructurado en formato JSON estricto para el médico tratante.

{MAPEADOR_DIALECTAL_BOLIVIA}

REGLAS DE EVALUACIÓN CLÍNICA (ESCALA MANCHESTER / RAC ADAPTADO):
1. FORCING DE ESQUEMA JSON: Responde ÚNICAMENTE un objeto JSON válido sin bloques markdown adicionales.
2. NIVELES DE PRIORIDAD ESTRICTOS:
   - "ROJO": Emergencia Vital Inmediata (dolor precordial irradiado, disnea aguda en reposo, síncope/desmayo, convulsiones, hemorragia activa severa, lactantes <1 año febriles).
   - "AMARILLO": Urgencia Mayor / Riesgo Potencial (dolor agudo severo 7-10/10, sospecha de abdomen agudo en fosa ilíaca, vómitos incoercibles con deshidratación, fiebre alta persistente).
   - "VERDE": Cuadro Leve / Consulta General (dolor leve/moderado 1-6/10 sin compromiso hemodinámico ni signos de alarma).
3. INTEGRACIÓN DE ANTECEDENTES Y ALERGIAS: Considera especialmente las alergias reportadas ({alergias}), fármacos actuales ({medicacion}) y comorbilidades ({enfermedades}).
4. TRADUCCIÓN SOCIOLINGÜÍSTICA: Interpreta modismos cruceños y bolivianos traduciéndolos a terminología médica formal.
5. RESUMEN NARRATIVO: Redacta una síntesis clínica concisa de 2 a 3 oraciones usando lenguaje profesional médico estructurado orientado a la especialidad ({especialidad}).

DATOS DEL PACIENTE:
- Nombre: {nombre}
- Edad: {edad} años | Género: {genero}
- Especialidad Solicitada: {especialidad}
- Motivo de Consulta: "{sintomas}"
- Alergias a Medicamentos: {alergias}
- Medicación Actual: {medicacion}
- Enfermedades de Base: {enfermedades}
- Datos Adicionales e Intensidad: {datos_estaticos}
- Respuestas a Preguntas Dinámicas (PQRST): {respuestas_dinamicas}

FORMATO JSON REQUERIDO:
{{
  "sintomas_principales": ["lista de síntomas traducidos a terminología médica formal"],
  "duracion_e_intensidad": "resumen de evolución e intensidad (ej. 'Evolución de 3 horas con intensidad 8/10')",
  "factores_agravantes_antecedentes": ["comorbilidades, alergias, medicación o factores agravantes reportados"],
  "senales_alerta_identificadas": ["banderas rojas o signos de alarma detectados"],
  "prioridad_sugerida_ia": "ROJO" | "AMARILLO" | "VERDE",
  "resumen_clinico_narrativo": "síntesis concisa de 2 a 3 oraciones para el médico de guardia",
  "informacion_faltante_critica": ["aspectos o datos no especificados que el médico debe interrogar"]
}}
"""

    def construir_prompt_preguntas_dinamicas(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        especialidad_solicitada: str = "Medicina General",
        alergias_medicamentosas: str = "Ninguna conocida",
        medicacion_actual: str = "Ninguna",
        enfermedades_base: Optional[List[str]] = None
    ) -> str:
        """
        Construye el prompt para que el LLM formule de 2 a 3 preguntas adaptativas de opción múltiple
        aplicando semiología PQRST y contextualización según la especialidad médica elegida.
        """
        comorb_str = ", ".join(enfermedades_base) if enfermedades_base else "Ninguna reportada"

        return f"""
[SYSTEM PROMPT]
Eres un médico especialista en triaje de emergencias de MediSinc-IA.
El paciente solicita atención en la especialidad: {especialidad_solicitada}.
Tu tarea es generar exactamente entre 2 y 3 preguntas clínicas de opción múltiple para interrogar al paciente antes de su evaluación presencial.

{MAPEADOR_DIALECTAL_BOLIVIA}

METODOLOGÍA SEMIOLÓGICA PQRST Y ORIENTACIÓN POR ESPECIALIDAD ({especialidad_solicitada}):
1. PREGUNTA 1 (Semiología Específica / Banderas Rojas): Interroga la irradiación, tipo de dolor (opresivo vs punzante), velocidad de inicio o signos de peligro enfocados en {especialidad_solicitada}.
   - Pediatría: tolerancia oral, llanto inconsolable o decaimiento.
   - Cardiología / Medicina Interna: irradiación precordial, disnea paroxística, palpitaciones.
   - Traumatología / Cirugía: mecanismo del trauma, impotencia funcional, deformidad articular.
   - Ginecología / Obstetricia: fecha de última menstruación, sangrado o dolor cólico pélvico.
   - Medicina General: tiempo de instauración, fiebre cuantificada o síntomas sistémicos.
2. PREGUNTA 2 (Profundización de Antecedentes y Comorbilidades): Profundiza en las enfermedades de base reportadas ({comorb_str}) o descarta condiciones afines.
3. PREGUNTA 3 (Tratamiento Fármaco / Alergias): Interroga sobre respuesta a medicamentos ({medicacion_actual}), analgésicos tomados o descarte de reacciones a fármacos ({alergias_medicamentosas}).

REGLAS DE FORMATO JSON:
- Responde ÚNICAMENTE un array JSON con 2 a 3 objetos.
- Cada objeto debe contener:
  - "id": identificador único en minúsculas (ej: "q_caracteristica_dolor", "q_enfermedades_previas", "q_medicacion")
  - "pregunta": texto claro y empático en español dirigido al paciente.
  - "tipo_pregunta": "single_choice" o "multiple_choice"
  - "opciones": lista de 3 a 4 opciones con {{"etiqueta": "...", "valor": "..."}}

DATOS DEL PACIENTE:
- Especialidad Solicitada: {especialidad_solicitada}
- Motivo de Consulta: "{sintomas}"
- Edad: {edad} años | Género: {genero}
- Alergias Reportadas: {alergias_medicamentosas}
- Medicación Actual: {medicacion_actual}
- Comorbilidades: {comorb_str}

EJEMPLO DE SALIDA ESPERADA:
[
  {{
    "id": "q_caracteristica",
    "pregunta": "¿Cómo describirías la molestia principal y hacia dónde se extiende?",
    "tipo_pregunta": "single_choice",
    "opciones": [
      {{"etiqueta": "Opresión intensa que irradia a mandíbula o brazo", "valor": "irradiado"}},
      {{"etiqueta": "Punzante o quemante localizado", "valor": "localizado"}},
      {{"etiqueta": "Sensación de pesadez difusa", "valor": "difuso"}}
    ]
  }},
  {{
    "id": "q_enfermedades",
    "pregunta": "¿Padece alguna enfermedad o condición médica diagnosticada?",
    "tipo_pregunta": "multiple_choice",
    "opciones": [
      {{"etiqueta": "Hipertensión arterial (presión alta)", "valor": "hipertension"}},
      {{"etiqueta": "Diabetes mellitus (azúcar alta)", "valor": "diabetes"}},
      {{"etiqueta": "Problemas cardíacos o respiratorios crónicos", "valor": "cardio_resp"}},
      {{"etiqueta": "Ninguna enfermedad diagnosticada", "valor": "ninguna"}}
    ]
  }},
  {{
    "id": "q_medicamentos",
    "pregunta": "¿Toma medicamentos habitualmente o ha tomado algo hoy para este malestar?",
    "tipo_pregunta": "multiple_choice",
    "opciones": [
      {{"etiqueta": "Medicamentos para la presión o anticoagulantes", "valor": "cardiovasculares"}},
      {{"etiqueta": "Medicación para la diabetes", "valor": "antidiabeticos"}},
      {{"etiqueta": "Tomé analgésicos o antiinflamatorios recientemente", "valor": "analgesicos"}},
      {{"etiqueta": "No tomo ningún medicamento", "valor": "ninguno"}}
    ]
  }}
]
"""

    def generar_salida_contingencia(self, patient_data: Dict[str, Any]) -> EsquemaSalidaEstructuradaIA:
        """
        Genera una evaluación médica preliminar determinista y estructurada en caso de indisponibilidad del LLM.
        """
        sintomas = str(patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "")).lower()
        datos_est = patient_data.get("static_data") or patient_data.get("datos_estaticos", {})
        especialidad = patient_data.get("requested_specialty") or patient_data.get("especialidad_solicitada", "Medicina General")
        alergias = patient_data.get("drug_allergies") or patient_data.get("alergias_medicamentosas", "Ninguna conocida")
        medicacion = patient_data.get("current_medication") or patient_data.get("medicacion_actual", "Ninguna")
        enfermedades = patient_data.get("base_diseases") or patient_data.get("enfermedades_base", [])
        
        intensidad = 5
        try:
            intensidad = int(datos_est.get("intensidad", 5))
        except (ValueError, TypeError):
            intensidad = 5

        # Banderas rojas deterministas para fallback
        es_rojo = any(termino in sintomas for termino in [
            "pecho", "torac", "respirar", "aire", "desmayo", "convulsion", "sangrado",
            "conciencia", "chuy", "asfixia", "paralisis", "mandibula"
        ])

        if es_rojo:
            prioridad = "RED"
        elif intensidad >= 7:
            prioridad = "YELLOW"
        else:
            prioridad = "GREEN"

        duracion_txt = str(datos_est.get("duracion", "Evolución reciente"))
        edad = patient_data.get("age") if patient_data.get("age") is not None else patient_data.get("edad", "No especificada")
        nombre = patient_data.get("patient_name") or patient_data.get("nombre_paciente", "Paciente")
        sintoma_reportado = patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "Sintomatología general")

        antecedentes_reportados = []
        if alergias and alergias != "Ninguna conocida":
            antecedentes_reportados.append(f"Alergias: {alergias}")
        if medicacion and medicacion != "Ninguna":
            antecedentes_reportados.append(f"Medicación: {medicacion}")
        if enfermedades:
            antecedentes_reportados.append(f"Comorbilidades: {', '.join(enfermedades)}")
        if not antecedentes_reportados:
            antecedentes_reportados.append("Sin antecedentes críticos documentados en pre-triaje")

        return EsquemaSalidaEstructuradaIA(
            sintomas_principales=[sintoma_reportado],
            duracion_e_intensidad=f"Tiempo de evolución: {duracion_txt} | Intensidad: {intensidad}/10",
            factores_agravantes_antecedentes=antecedentes_reportados,
            senales_alerta_identificadas=["Evaluación emitida mediante protocolo de contingencia clínica rápida"],
            prioridad_sugerida_ia=prioridad,
            resumen_clinico_narrativo=(
                f"{nombre} ({edad} años) consulta para {especialidad} por '{sintoma_reportado}'. "
                f"Cuadro de intensidad {intensidad}/10 con {duracion_txt}. "
                f"Alergias: {alergias}. Evaluación preliminar generada por el motor de contingencia clínica."
            ),
            informacion_faltante_critica=[
                "Control de signos vitales (presión arterial, SpO2, frecuencia cardíaca)",
                f"Interrogatorio dirigido a la especialidad de {especialidad}"
            ]
        )

    def generar_preguntas_dinamicas_fallback(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        especialidad_solicitada: str = "Medicina General",
        alergias_medicamentosas: str = "Ninguna conocida",
        medicacion_actual: str = "Ninguna",
        enfermedades_base: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna preguntas estructuradas adaptadas por árbol de decisión semiológico si el LLM no responde.
        """
        sintoma_norm = (sintomas or "").lower()

        if any(t in sintoma_norm for t in ["cabeza", "cefalea", "tutuma"]):
            p1 = {
                "id": "q_headache_pqrst",
                "pregunta": "¿El dolor de cabeza inició súbitamente de golpe o con alteración visual/cuello rígido?",
                "tipo_pregunta": "single_choice",
                "opciones": [
                    {"etiqueta": "Inicio súbito en segundos con dolor insoportable", "valor": "subito_trueno", "es_alerta_roja": True},
                    {"etiqueta": "Acompañado de rigidez de cuello o fiebre alta", "valor": "rigidez_nuca", "es_alerta_roja": True},
                    {"etiqueta": "Dolor progresivo o pulsátil habitual", "valor": "progresivo", "es_alerta_roja": False}
                ]
            }
        elif any(t in sintoma_norm for t in ["pecho", "torac", "card", "palpit"]):
            p1 = {
                "id": "q_chest_pqrst",
                "pregunta": "¿Cómo describirías la molestia en el pecho y hacia dónde se extiende?",
                "tipo_pregunta": "single_choice",
                "opciones": [
                    {"etiqueta": "Opresión fuerte que va hacia brazo izquierdo, cuello o mandíbula", "valor": "irradiado_brazo", "es_alerta_roja": True},
                    {"etiqueta": "Punzante al respirar hondo o toser", "valor": "pleuritico", "es_alerta_roja": False},
                    {"etiqueta": "Sensación de ardor o acidez digestiva", "valor": "reflujo", "es_alerta_roja": False}
                ]
            }
        elif any(t in sintoma_norm for t in ["estomago", "abdom", "barriga", "aventado", "basca"]):
            p1 = {
                "id": "q_abdo_pqrst",
                "pregunta": "¿En qué zona del abdomen se ubica y presenta vómitos continuos?",
                "tipo_pregunta": "single_choice",
                "opciones": [
                    {"etiqueta": "En la parte inferior derecha con dolor agudo al tacto", "valor": "fosa_iliaca_derecha", "es_alerta_roja": False},
                    {"etiqueta": "En la boca del estómago con náuseas y ardor", "valor": "epigastrio", "es_alerta_roja": False},
                    {"etiqueta": "Vómitos continuos e imposibilidad de retener líquidos", "valor": "vomitos_incoercibles", "es_alerta_roja": True}
                ]
            }
        else:
            p1 = {
                "id": "q_gen_pqrst",
                "pregunta": "¿Con qué rapidez aparecieron los síntomas y qué tanto limitan su actividad?",
                "tipo_pregunta": "single_choice",
                "opciones": [
                    {"etiqueta": "Aparición súbita e incapacidad total de mantenerse de pie", "valor": "agudo_severo", "es_alerta_roja": True},
                    {"etiqueta": "Comenzó gradualmente en las últimas 24 a 48 horas", "valor": "subagudo", "es_alerta_roja": False},
                    {"etiqueta": "Molestia persistente de más de una semana", "valor": "cronico", "es_alerta_roja": False}
                ]
            }

        p2 = {
            "id": "q_enfermedades_comorbilidades",
            "pregunta": f"Para su consulta en {especialidad_solicitada}, ¿padece alguna de estas condiciones?",
            "tipo_pregunta": "multiple_choice",
            "opciones": [
                {"etiqueta": "Hipertensión arterial (presión alta)", "valor": "hipertension"},
                {"etiqueta": "Diabetes mellitus (azúcar en sangre)", "valor": "diabetes"},
                {"etiqueta": "Problemas cardíacos o infarto previo", "valor": "cardiopatia"},
                {"etiqueta": "Asma, bronquitis crónica o EPOC", "valor": "asma_epoc"},
                {"etiqueta": "Ninguna enfermedad diagnosticada", "valor": "ninguna"}
            ]
        }

        p3 = {
            "id": "q_medicamentos_tratamientos",
            "pregunta": "¿Toma medicamentos habitualmente o ha tomado fármacos para este malestar?",
            "tipo_pregunta": "multiple_choice",
            "opciones": [
                {"etiqueta": "Medicamentos para la presión arterial o el corazón", "valor": "antihipertensivos"},
                {"etiqueta": "Anticoagulantes o aspirina diariamente", "valor": "anticoagulantes"},
                {"etiqueta": "Insulina o pastillas para la diabetes", "valor": "antidiabeticos"},
                {"etiqueta": "Tomé analgésicos o antibióticos en las últimas horas", "valor": "analgesicos"},
                {"etiqueta": "No tomo ningún medicamento de forma regular", "valor": "ninguno"}
            ]
        }

        return [p1, p2, p3]

    async def generar_preguntas_dinamicas(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        especialidad_solicitada: str = "Medicina General",
        alergias_medicamentosas: str = "Ninguna conocida",
        medicacion_actual: str = "Ninguna",
        enfermedades_base: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Método por defecto que invoca el árbol de contingencia si no se sobreescribe en la subclase.
        """
        return self.generar_preguntas_dinamicas_fallback(
            sintomas=sintomas,
            edad=edad,
            genero=genero,
            especialidad_solicitada=especialidad_solicitada,
            alergias_medicamentosas=alergias_medicamentosas,
            medicacion_actual=medicacion_actual,
            enfermedades_base=enfermedades_base
        )


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
BaseAIProvider = ProveedorIABase
