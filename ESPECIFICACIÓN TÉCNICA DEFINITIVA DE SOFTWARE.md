📄 ESPECIFICACIÓN TÉCNICA DEFINITIVA DE SOFTWARE
Proyecto: MediSinc-IA (Sistema de Pre-Triaje Clínico e Inteligencia de Salud)
Ubicación: Santa Cruz de la Sierra, Bolivia
Fecha de Consolidación: Agosto de 2026
1. RESUMEN EJECUTIVO Y ARQUITECTURA GENERAL
MediSinc-IA es una aplicación web independiente orientada a la captura, estructuración y priorización de síntomas de pacientes antes de la consulta médica general.
Stack Tecnológico Confirmado
Frontend: React + Vite + Tailwind CSS / UI Components (Single Page Application responsiva para móviles y escritorio).
Backend API: Python + FastAPI (asíncrono, validación con Pydantic).
Base de Datos y Autenticación: Supabase (PostgreSQL + Supabase Auth con tokens JWT + Políticas RLS).
Cola de Tareas y Procesamiento Asíncrono: Upstash Redis + QStash / ARQ (serverless, manejo de retries y rate-limiting sin gestión pesada de infraestructura).
Capa de IA (Agnóstica): Arquitectura con patrón Adapter / Factory que soporta Gemini 1.5 Flash (Google), Groq (Llama 3) y OpenAI. La selección del proveedor se gestiona mediante la variable de entorno AI_PROVIDER.
2. FLUJO DE PACIENTE Y CAPTURA DE DATOS (PORTAL PÚBLICO)
2.1 Formulario Híbrido (Estático + Dinámico)
Paso 1 - Datos Fijos y Síntoma Base:
Datos personales: Nombre completo, Carnet de Identidad (CI), Edad, Sexo.
Síntoma principal en texto libre.
Duración aproximada e Intensidad del dolor/molestia (Escala 1 al 10).
Paso 2 - Preguntas Dinámicas Adaptativas:
Al ingresar el síntoma principal, una petición ligera a la API procesa la respuesta e inserta de 2 a 3 preguntas dinámicas de opción múltiple para precisar el cuadro (ej. ante "dolor abdominal", pregunta ubicación exacta y presencia de náuseas/fiebre).
Paso 3 - Confirmación y Salida:
El sistema genera un Código Único Alfanumérico legible (ej. MS-8X92K).
Se renderiza en pantalla un Código QR dinámico interactivo que empaqueta el código de acceso.
El paciente puede guardar el QR o mostrarlo en la recepción/consultorio.
3. MOTOR DE TRIAJE, IA Y REGLAS DE SEGURIDAD
3.1 Niveles de Priorización de Triaje
🔴 Rojo (Urgente / Emergencia): Requiere atención médica inmediata.
🟡 Amarillo (Prioritario): Síntomas moderados que requieren atención a corto plazo.
🟢 Verde (No Urgente): Sintomatología leve o consulta general.
3.2 Motor de Reglas Duras (Safety Overrides)
La IA no determina la prioridad final de manera aislada. Un Rule Engine interno en FastAPI analiza los síntomas y el JSON generado:
Si la IA sugiere "Verde" o "Amarillo", pero el motor detecta términos críticos (ej. "dolor de pecho opresivo", "dificultad respiratoria", "pérdida de conciencia", "recién nacido con fiebre"), el Backend fuerza automáticamente la prioridad a ROJO.
Se añade una etiqueta de auditoría en la BD: override_applied: true y override_reason: "Regla de Seguridad: Dolor Torácico".
3.3 Esquema Pydantic del Resumen Clínico (IA Output)
La respuesta del proveedor de IA se fuerza en el siguiente contrato estricto de JSON:
informacion_paciente: Datos demográficos y constantes capturados.
sintomas_principales: Lista de síntomas estructurados en terminología médica.
duracion_e_intensidad: Resumen de tiempo de evolución e intensidad.
factores_agravantes_antecedentes: Factores o antecedentes mencionados.
senales_alerta_identificadas: Lista de banderas rojas detectadas.
prioridad_sugerida_ia: Prioridad preliminar (Verde, Amarillo, Rojo).
resumen_clinico_narrativo: Síntesis narrativa de 2 a 3 oraciones redactada para rápida lectura médica.
informacion_faltante_critica: Puntos o preguntas clave no respondidas por el paciente que el médico debe indagar.
4. PORTAL MÉDICO, ADMINISTRACIÓN Y SEGURIDAD
4.1 Métodos de Búsqueda y Dashboard
El profesional médico (autenticado mediante Supabase Auth con JWT) cuenta con cuatro vías de acceso:
Lector de Código QR: Escaneo mediante la cámara de la laptop, tablet o móvil.
Buscador por Código Alfanumérico (MS-8X92K).
Buscador por Carnet de Identidad (CI).
Dashboard de Lista de Espera en Tiempo Real: Panel general ordenado automáticamente por nivel de urgencia (Rojos arriba, luego Amarillos, luego Verdes) y hora de llegada.
4.2 Pantalla de Detalle y Revisión Médica
Visualización Dividida: A la izquierda, la declaración directa del paciente (Raw Data); a la derecha, el resumen estructurado por IA, alertas resaltadas y la información demográfica.
Ajuste Manual de Prioridad: El médico puede corregir manualmente el nivel de prioridad si considera que la clasificación automática no corresponde al examen visual inicial.
Cierre de Atenciones: Al presionar "Guardar y Confirmar", el médico añade sus notas y el estado del registro cambia a REVIEWED.
4.3 Cifrado, Roles y Auditoría
Cifrado de Datos Sensibles: El CI se almacena cifrado en la base de datos mediante AES-256-GCM (ci_encrypted). Para búsquedas exactas, se calcula un hash unidireccional seguro HMAC-SHA256 con Pepper (ci_hash).
Gestión de Usuarios: El registro de cuentas está cerrado al público. Un usuario con rol ADMIN crea y asigna manualmente las credenciales y roles (DOCTOR, ADMIN).
Trazabilidad Inalterable: Cada consulta, búsqueda o actualización realizada por un médico o administrador inserta un registro atómico en la tabla AUDIT_LOG con user_id, patient_id, action, ip y timestamp.
5. MODELO DE DATOS PRINCIPAL (PostgreSQL / Supabase)
      +-------------------+
       |     PROFILES      |
       +-------------------+
       | id (UUID, PK)     |
       | user_id (FK Auth) |
       | full_name         |
       | role (DOCTOR/ADMIN|
       +---------+---------+
                 |
                 | 1:N
                 v
+-----------------------------------+       +-----------------------------------+
|           TRIAGE_RECORD           |       |             AI_RESULT             |
+-----------------------------------+       +-----------------------------------+
| id (UUID, PK)                     | 1:1   | id (UUID, PK)                     |
| access_code (VARCHAR, Unique)     |<----->| triage_id (UUID, FK)              |
| ci_hash (VARCHAR, Indexed)        |       | provider (VARCHAR)                |
| ci_encrypted (TEXT)               |       | model (VARCHAR)                   |
| patient_name (VARCHAR)            |       | structured_result (JSONB)         |
| age (INT)                         |       | override_applied (BOOLEAN)        |
| gender (VARCHAR)                  |       | override_reason (TEXT)            |
| raw_symptoms (TEXT)               |       | created_at (TIMESTAMPTZ)          |
| static_data (JSONB)               |       +-----------------------------------+
| dynamic_answers (JSONB)           |
| status (RECEIVED/READY/REVIEWED)  |       +-----------------------------------+
| final_priority (RED/YELLOW/GREEN) |       |          MEDICAL_REVIEW           |
| created_at (TIMESTAMPTZ)          |       +-----------------------------------+
+-----------------+-----------------+       | id (UUID, PK)                     |
                  |                         | triage_id (UUID, FK)              |
                  | 1:N                     | doctor_id (UUID, FK Profiles)     |
                  v                         | doctor_notes (TEXT)               |
+-----------------------------------+       | priority_adjusted (VARCHAR)       |
|             AUDIT_LOG             |       | reviewed_at (TIMESTAMPTZ)         |
+-----------------------------------+       +-----------------------------------+
| id (UUID, PK)                     |
| user_id (UUID, FK Profiles)       |
| action (VARCHAR)                  |
| resource_id (UUID)                |
| ip_address (VARCHAR)              |
| timestamp (TIMESTAMPTZ)           |
+-----------------------------------+

