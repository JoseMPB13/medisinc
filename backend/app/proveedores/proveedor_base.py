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
Tu tarea es formular exactamente entre 2 y 3 preguntas clínicas de opción múltiple enfocadas en SEMIOLOGÍA PQRST para precisar el motivo de consulta antes de su atención presencial.

{MAPEADOR_DIALECTAL_BOLIVIA}

[PROHIBICIÓN ESTRICTA Y REGLAS NEGATIVAS]:
- ESTÁ ESTRICTAMENTE PROHIBIDO preguntar sobre antecedentes médicos generales, enfermedades de base previas, alergias a fármacos o medicamentos diarios, dado que la interfaz del paciente los recopila de forma independiente mediante chips interactivos.
- NO formules preguntas genéricas de "¿Padece alguna enfermedad?" ni "¿Qué medicamentos toma habitualmente?".

[DIRECTIVA POSITIVA - METODOLOGÍA SEMIOLÓGICA PQRST Y ORIENTACIÓN POR ESPECIALIDAD ({especialidad_solicitada})]:
1. PREGUNTA 1 (Cualidad y Región/Irradiación): Características del síntoma o dolor principal (opresivo, punzante, urente, cólico) y si irradia hacia alguna zona anatómica.
2. PREGUNTA 2 (Provocación y Factores Desencadenantes / Alivio): Qué agrava o disminuye el cuadro (al respirar hondo, esfuerzo físico, ingesta de alimentos, cambios de postura o reposo).
3. PREGUNTA 3 (Severidad y Banderas Rojas de {especialidad_solicitada}): Descarte de signos de cortejo vegetativo o alarma crítica:
   - Cardiología / Medicina Interna: sensación de falta de aire en reposo, opresión al pecho, sudor frío o mareos.
   - Pediatría: decaimiento marcado, rechazo total al pecho/líquidos, vómitos repetidos o dificultad para respirar.
   - Traumatología / Urgencias: chasquido al momento del golpe, deformidad evidente o incapacidad de apoyar el miembro.
   - Ginecología / Obstetricia: sangrado genital anormal, dolor pélvico punzante o fiebre con flujo.
   - Odontología: inflamación de la cara/cuello, dificultad para tragar o abrir la boca.
   - Medicina General: fiebre alta con escalofríos, rigidez o vómitos incoercibles.

REGLAS DE FORMATO JSON:
- Responde ÚNICAMENTE un array JSON válido con 2 a 3 objetos.
- Cada objeto debe contener:
  - "id": identificador único en minúsculas (ej: "q_cualidad_irradiacion", "q_factores_gatillantes", "q_banderas_rojas")
  - "pregunta": texto claro, empático y profesional en español dirigido al paciente.
  - "tipo_pregunta": "single_choice" o "multiple_choice"
  - "opciones": lista de 3 a 4 opciones con {{"etiqueta": "...", "valor": "..."}}

DATOS DEL MOTIVO DE CONSULTA:
- Especialidad Solicitada: {especialidad_solicitada}
- Motivo de Consulta: "{sintomas}"
- Edad: {edad} años | Género: {genero}

EJEMPLO DE SALIDA ESPERADA:
[
  {{
    "id": "q_cualidad_irradiacion",
    "pregunta": "¿Cómo describirías la molestia principal y hacia dónde se extiende?",
    "tipo_pregunta": "single_choice",
    "opciones": [
      {{"etiqueta": "Opresión intensa que va hacia el cuello, mandíbula o brazo", "valor": "irradiado_toracico"}},
      {{"etiqueta": "Punzante o quemante en un punto fijo", "valor": "localizado_punzante"}},
      {{"etiqueta": "Dolor tipo cólico o retortijón intermitente", "valor": "colico_intermitente"}}
    ]
  }},
  {{
    "id": "q_factores_gatillantes",
    "pregunta": "¿En qué momento aumenta o empeora esta molestia?",
    "tipo_pregunta": "single_choice",
    "opciones": [
      {{"etiqueta": "Aumenta al hacer esfuerzo físico o caminar", "valor": "empeora_esfuerzo"}},
      {{"etiqueta": "Empeora al respirar hondo, toser o cambiar de posición", "valor": "empeora_respiracion_postura"}},
      {{"etiqueta": "Es continuo y no cambia con el reposo", "valor": "continuo_fijo"}}
    ]
  }},
  {{
    "id": "q_banderas_rojas",
    "pregunta": "¿Presentas alguno de estos signos de alarma en este momento?",
    "tipo_pregunta": "multiple_choice",
    "opciones": [
      {{"etiqueta": "Falta de aire o dificultad para respirar en reposo", "valor": "disnea_reposo"}},
      {{"etiqueta": "Sudoración fría, sensación de desmayo o mareo fuerte", "valor": "diaforesis_lipotimia"}},
      {{"etiqueta": "Vómitos continuos o fiebre muy alta", "valor": "vomitos_fiebre"}},
      {{"etiqueta": "Ninguno de los anteriores", "valor": "ninguno"}}
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
            "id": "q_factores_gatillantes",
            "pregunta": "¿Qué factores agravan o calman tu malestar en este momento?",
            "tipo_pregunta": "single_choice",
            "opciones": [
                {"etiqueta": "Empeora notablemente con el movimiento físico o esfuerzo", "valor": "empeora_esfuerzo"},
                {"etiqueta": "Aumenta con la respiración profunda o al toser", "valor": "empeora_respiracion"},
                {"etiqueta": "Se mantiene constante y no cede con el reposo", "valor": "constante_sin_alivio"},
                {"etiqueta": "Disminuye parcialmente al descansar o cambiar de posición", "valor": "calma_reposo"}
            ]
        }

        p3 = {
            "id": "q_signos_alarma_vegetativos",
            "pregunta": "¿Presentas alguno de estos signos de alarma en este momento?",
            "tipo_pregunta": "multiple_choice",
            "opciones": [
                {"etiqueta": "Dificultad o sensación de falta de aire al estar sentado(a)", "valor": "disnea_reposo", "es_alerta_roja": True},
                {"etiqueta": "Sudoración fría, sensación de desvanecimiento o mareo intenso", "valor": "diaforesis_lipotimia", "es_alerta_roja": True},
                {"etiqueta": "Fiebre alta con escalofríos intensos o vómitos continuos", "valor": "fiebre_vomitos", "es_alerta_roja": False},
                {"etiqueta": "Ninguno de los signos anteriores", "valor": "ninguno", "es_alerta_roja": False}
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

    # Aliases de compatibilidad con suites de pruebas
    _generate_fallback = generar_salida_contingencia


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
BaseAIProvider = ProveedorIABase

