"""
Clase Base Abstracta para los Proveedores de Inteligencia Artificial en MediSinc-IA.
Define la interfaz uniforme (patrón Adapter) y el motor de prompts con mapeador dialectal
cruceño/boliviano que deben implementar Gemini, Groq y OpenAI.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA, AIStructuredOutput

# Mapeador Dialectal y Semántico de Expresiones Populares de Santa Cruz de la Sierra y Bolivia
MAPEADOR_DIALECTAL_BOLIVIA = """
GUÍA DE INTERPRETACIÓN SOCIOLINGÜÍSTICA (ESPAÑOL BOLIVIANO / CRUCEÑO):
- "Chuy" / "Chucho de frío" -> Escalofríos intensos o síndrome febril en evolución.
- "Basca" / "Asco" -> Náuseas o emesis (vómitos).
- "Estómago aventado" / "Empacho" -> Distensión abdominal o meteorismo severo.
- "Quebrantamiento de cuerpo" / "Cuerpo cortado" -> Astenia, adinamia, mialgias generalizadas.
- "Dolor de tutuma" / "Retumbo en la cabeza" -> Cefalea holocraneana o pulsátil.
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
        respuestas_dinamicas: Optional[Dict[str, Any]] = None
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

        return await self.estructurar_triaje(
            sintomas=sintomas,
            edad=edad,
            genero=genero,
            datos_estaticos=datos_estaticos,
            respuestas_dinamicas=respuestas_dinamicas
        )

    def construir_prompt_triaje(self, patient_data: Dict[str, Any]) -> str:
        """
        Construye el prompt clínico para extracción estructurada inyectando las directivas
        de triaje de emergencias y el mapeador dialectal de Bolivia.
        """
        sintomas = patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "")
        edad = patient_data.get("age") if patient_data.get("age") is not None else patient_data.get("edad", 0)
        genero = patient_data.get("gender") or patient_data.get("genero", "No especificado")
        datos_estaticos = patient_data.get("static_data") or patient_data.get("datos_estaticos", {})
        respuestas_dinamicas = patient_data.get("dynamic_answers") or patient_data.get("respuestas_dinamicas", {})
        nombre = patient_data.get("patient_name") or patient_data.get("nombre_paciente", "Paciente")

        return f"""
[SYSTEM PROMPT]
Eres un médico especialista en medicina de emergencias y triaje clínico asistiendo al sistema MediSinc-IA en Santa Cruz de la Sierra, Bolivia.
Tu función es analizar la declaración del paciente y generar un informe clínico estructurado en formato JSON estricto para el médico tratante.

{MAPEADOR_DIALECTAL_BOLIVIA}

REGLAS DE EVALUACIÓN Y CLINICAL REASONING:
1. FORCING DE ESQUEMA JSON: Responde ÚNICAMENTE un objeto JSON válido sin texto introductorio ni explicaciones adicionales.
2. NIVELES DE PRIORIDAD: Asigna preliminarmente strictly:
   - "ROJO": Emergencia vital (dolor torácico opresivo, disnea aguda, síncope, convulsiones, hemorragias, parálisis o asimetría facial, lactantes <1 año febriles).
   - "AMARILLO": Cuadro prioritario / dolor moderado a severo (6-8/10), deshidratación o fiebre persistente sin colapso.
   - "VERDE": Cuadro leve (1-5/10), síntomas catarrales no complicados o consultas generales.
3. TRADUCCIÓN SOCIOLINGÜÍSTICA: Interpreta modismos cruceños y bolivianos traduciéndolos a terminología médica formal.
4. RESUMEN NARRATIVO: Redacta una síntesis clínica concisa de 2 a 3 oraciones usando lenguaje profesional médico.

DATOS DEL PACIENTE:
- Nombre: {nombre}
- Edad: {edad} años | Género: {genero}
- Motivo de Consulta (Declaración directa del paciente): "{sintomas}"
- Datos Adicionales / Intensidad: {datos_estaticos}
- Respuestas a Preguntas Dinámicas: {respuestas_dinamicas}

FORMATO JSON REQUERIDO:
{{
  "sintomas_principales": ["lista de síntomas traducidos a terminología médica formal"],
  "duracion_e_intensidad": "resumen de evolución e intensidad (ej. 'Evolución de 2 horas con intensidad 8/10')",
  "factores_agravantes_antecedentes": ["factores agravantes o comorbilidades mencionadas"],
  "senales_alerta_identificadas": ["banderas rojas o signos de alarma detectados"],
  "prioridad_sugerida_ia": "ROJO" | "AMARILLO" | "VERDE" | "RED" | "YELLOW" | "GREEN",
  "resumen_clinico_narrativo": "síntesis concisa de 2 a 3 oraciones para el médico de guardia",
  "informacion_faltante_critica": ["aspectos o datos no especificados que el médico debe interrogar"]
}}
"""

    def _build_prompt(self, patient_data: Dict[str, Any]) -> str:
        """Alias para compatibilidad con código existente."""
        return self.construir_prompt_triaje(patient_data)

    def generar_salida_contingencia(self, patient_data: Dict[str, Any]) -> EsquemaSalidaEstructuradaIA:
        """
        Genera una evaluación médica preliminar determinista y estructurada en caso de indisponibilidad del LLM.
        """
        sintomas = str(patient_data.get("raw_symptoms") or patient_data.get("sintomas_brutos", "")).lower()
        datos_est = patient_data.get("static_data") or patient_data.get("datos_estaticos", {})
        
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

        return EsquemaSalidaEstructuradaIA(
            sintomas_principales=[sintoma_reportado],
            duracion_e_intensidad=f"Tiempo de evolución: {duracion_txt} | Intensidad: {intensidad}/10",
            factores_agravantes_antecedentes=["Sin antecedentes críticos documentados en pre-triaje"],
            senales_alerta_identificadas=["Evaluación emitida mediante protocolo de contingencia clínica rápida"],
            prioridad_sugerida_ia=prioridad,
            resumen_clinico_narrativo=(
                f"{nombre} ({edad} años) consulta por '{sintoma_reportado}'. "
                f"Cuadro de intensidad {intensidad}/10 con {duracion_txt}. "
                f"Evaluación preliminar generada por el motor de contingencia clínica."
            ),
            informacion_faltante_critica=[
                "Control de signos vitales (presión arterial, SpO2, frecuencia cardíaca)",
                "Alergias medicamentosas y antecedentes patológicos familiares"
            ]
        )

    def _generate_fallback(self, patient_data: Dict[str, Any]) -> EsquemaSalidaEstructuradaIA:
        """Alias para compatibilidad con código existente."""
        return self.generar_salida_contingencia(patient_data)


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
BaseAIProvider = ProveedorIABase
