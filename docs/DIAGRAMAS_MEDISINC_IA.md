# GUÍA OFICIAL DE DIAGRAMAS DE ARQUITECTURA Y DISEÑO DE SOFTWARE - MEDISINC-IA

**Proyecto:** MediSinc-IA (Sistema de Pre-Triaje Clínico e Inteligencia de Salud)  
**Ubicación:** Santa Cruz de la Sierra, Bolivia  
**Estándar:** Diagramación en Sintaxis Mermaid y UML 2.5  
**Fecha:** Agosto de 2026  

---

## 1. Diagrama de Casos de Uso del Sistema (Use Case Diagram)

Este diagrama representa los actores humanos y sistémicos que interactúan con MediSinc-IA y los casos de uso principales que ejecuta cada uno.

```mermaid
graph TD
    %% Actores
    subgraph Actores ["👥 Actores del Ecosistema"]
        P["👤 Paciente / Ciudadano"]
        R["👩‍💼 Personal de Recepción"]
        M["👨‍⚕️ Médico General / Guardia"]
        A["💻 Administrador del Sistema"]
        AI["🤖 Proveedor IA (Gemini/Groq)"]
    end

    %% Casos de Uso
    subgraph Sistema ["🏥 MediSinc-IA System Boundary"]
        UC01("UC01: Ingresar Datos Fijos y Síntoma Base")
        UC02("UC02: Responder Preguntas Dinámicas")
        UC03("UC03: Obtener Código MS-XXXXX y QR")
        UC04("UC04: Generar Resumen Clínico Estructurado")
        UC05("UC05: Ejecutar Safety Overrides (Motor Reglas)")
        UC06("UC06: Escanear QR / Buscar por CI o Código")
        UC07("UC07: Visualizar Dashboard Priorizado (Rojo/Amarillo/Verde)")
        UC08("UC08: Revisar Resumen y Raw Data")
        UC09("UC09: Ajustar Prioridad y Cerrar Atención")
        UC10("UC10: Administrar Usuarios y Auditar Logs")
    end

    %% Relaciones Paciente
    P --> UC01
    P --> UC02
    P --> UC03

    %% Relaciones Sistema / IA
    UC02 --> AI
    UC04 --> AI
    UC04 --> UC05

    %% Relaciones Recepción y Médico
    R --> UC06
    M --> UC06
    M --> UC07
    M --> UC08
    M --> UC09

    %% Relaciones Administrador
    A --> UC10
```

---

## 2. Diagrama de Arquitectura del Sistema C4 / Contenedores (System Architecture Diagram)

Muestra la división en capas desacopladas del sistema: Capa de Presentación (React SPA), Capa de Negocio (FastAPI REST Backend), Capa de IA Agnóstica (Factory Pattern) y Capa de Persistencia y Seguridad (Supabase PostgreSQL + Auth + RLS).

```mermaid
graph TB
    subgraph Cliente ["💻 CAPA DE PRESENTACIÓN (SPA CLIENTE)"]
        ReactApp["React 18 + Vite (Single Page Application)"]
        Components["Componentes UI: StepStaticData, StepDynamicQuestions, StepConfirmationQR, DoctorDashboard"]
        QRScannerModule["Módulo Escáner QR (html5-qrcode)"]
        AxiosClient["Axios HTTP Client + Interceptores JWT"]
    end

    subgraph Backend ["⚙️ CAPA DE NEGOCIO (FASTAPI BACKEND API)"]
        FastAPI["FastAPI Framework (Uvicorn ASGI Engine)"]
        TriageRouter["Router /api/v1/triage"]
        DoctorRouter["Router /api/v1/doctor"]
        AuthRouter["Router /api/v1/auth"]
        
        SecurityModule["Módulo Cifrado AES-256-GCM + HMAC-SHA256 Pepper"]
        RuleEngine["Safety Overrides Engine (Reglas Duras en Python)"]
        AIFactory["AI Provider Factory (Agnostic Adapter)"]
    end

    subgraph ExternalAI ["🤖 CAPA DE IA AGNÓSTICA (SERVICIOS EXTERNOS)"]
        GeminiAPI["Google Gemini 1.5 Flash API"]
        GroqAPI["Groq Llama 3.1 70B API"]
        OpenAIAPI["OpenAI GPT-4o API"]
    end

    subgraph Persistencia ["🗄️ CAPA DE DATOS Y AUTENTICACIÓN (SUPABASE)"]
        SupabaseAuth["Supabase Auth (Tokens JWT)"]
        PostgreSQL["PostgreSQL Engine"]
        RLSPolicies["Políticas RLS (Row Level Security)"]
        
        T_Profiles[("PROFILES")]
        T_Triage[("TRIAGE_RECORD")]
        T_AIResult[("AI_RESULT")]
        T_MedicalReview[("MEDICAL_REVIEW")]
        T_AuditLog[("AUDIT_LOG")]
    end

    %% Conexiones
    ReactApp --> Components
    Components --> AxiosClient
    QRScannerModule --> AxiosClient
    AxiosClient -- "HTTPS / REST JSON" --> FastAPI

    FastAPI --> TriageRouter
    FastAPI --> DoctorRouter
    FastAPI --> AuthRouter

    TriageRouter --> SecurityModule
    TriageRouter --> AIFactory
    TriageRouter --> RuleEngine

    AIFactory -- "API Key" --> GeminiAPI
    AIFactory -- "API Key" --> GroqAPI
    AIFactory -- "API Key" --> OpenAIAPI

    DoctorRouter --> SecurityModule
    AuthRouter --> SupabaseAuth

    TriageRouter --> PostgreSQL
    DoctorRouter --> PostgreSQL

    PostgreSQL --> RLSPolicies
    RLSPolicies --> T_Profiles
    RLSPolicies --> T_Triage
    RLSPolicies --> T_AIResult
    RLSPolicies --> T_MedicalReview
    RLSPolicies --> T_AuditLog
```

---

## 3. Diagrama de Secuencia 1: Flujo de Pre-Triaje del Paciente con IA y Safety Overrides

Ilustra la interacción ordenada paso a paso desde que el paciente llena el formulario público hasta la generación del resumen por IA, evaluación del motor de reglas duras y renderizado del Código QR.

```mermaid
sequenceDiagram
    autonumber
    actor P as Paciente / Ciudadano
    participant FE as Frontend React
    participant API as FastAPI Backend
    participant SEC as Security Module (AES/HMAC)
    participant AI as AI Provider (Gemini/Groq)
    participant OVER as Safety Overrides Engine
    participant DB as Supabase PostgreSQL

    P->>FE: 1. Completa Datos Fijos (Nombre, CI, Edad, Síntoma Base)
    FE->>API: 2. POST /api/v1/triage/dynamic-questions (Síntoma Base)
    API->>AI: 3. Prompt 1: Solicita 2-3 Preguntas Dinámicas
    AI-->>API: 4. Retorna JSON de Preguntas Dinámicas
    API-->>FE: 5. Devuelve Preguntas Dinámicas al Paciente
    P->>FE: 6. Responde Preguntas Dinámicas y Confirma Registro
    
    FE->>API: 7. POST /api/v1/triage/process (Payload Completo)
    API->>SEC: 8. Cifra CI (AES-256-GCM) y Genera Hash (HMAC-SHA256)
    API->>DB: 9. Inserta en TRIAGE_RECORD (Estado: RECEIVED)
    
    API->>AI: 10. Prompt 2: Solicita Resumen Clínico Estructurado Pydantic
    AI-->>API: 11. Retorna JSON Estructurado (Prioridad Sugerida: GREEN/YELLOW/RED)
    
    API->>OVER: 12. evaluate_safety_overrides(JSON_IA, Raw_Symptoms)
    alt Detecta Banderas Rojas (ej. Dolor Pecho, Lactante Febril)
        OVER-->>API: 13. Forzar Prioridad RED (override_applied: true)
    else Sin Banderas Rojas
        OVER-->>API: 14. Mantener Prioridad IA (override_applied: false)
    end

    API->>DB: 15. Guarda resultado en AI_RESULT y actualiza TRIAGE_RECORD (Estado: READY)
    API-->>FE: 16. Retorna access_code (MS-8X92K), Prioridad y Token QR
    FE-->>P: 17. Muestra Código MS-8X92K y Renderiza Código QR Interactivo
```

---

## 4. Diagrama de Secuencia 2: Flujo de Atención Médica, Escaneo QR y Cierre Clínico

Muestra el flujo que realiza el profesional médico para buscar a un paciente, escanear su QR, revisar el informe comparativo y cerrar la consulta.

```mermaid
sequenceDiagram
    autonumber
    actor M as Médico General
    participant FE as Frontend (Dashboard)
    participant API as FastAPI Backend
    participant AUTH as Supabase Auth (JWT)
    participant DB as Supabase PostgreSQL

    M->>FE: 1. Inicia Sesión con Credenciales
    FE->>AUTH: 2. Valida Credenciales y emite Token JWT
    AUTH-->>FE: 3. Token JWT Retornado
    FE->>API: 4. GET /api/v1/doctor/waiting-list (Header Bearer JWT)
    API->>DB: 5. Consulta Registros (Orden: RED -> YELLOW -> GREEN)
    DB-->>API: 6. Retorna Lista de Espera Filtrada por RLS
    API-->>FE: 7. Despliega Tarjetas Priorizadas en Dashboard
    
    alt Opción A: Escaneo de QR
        M->>FE: 8. Abre Cámara y Escanea QR del Paciente
        FE->>FE: 9. Decodifica access_code (MS-8X92K)
    else Opción B: Búsqueda por CI o Código
        M->>FE: 10. Digita CI o Código MS-8X92K en el Buscador
    end

    FE->>API: 11. GET /api/v1/doctor/triage-detail/{access_code}
    API->>DB: 12. Registra Lectura en AUDIT_LOG (user_id, action, timestamp)
    API->>DB: 13. Obtiene Raw Data + Structured AI Result
    DB-->>API: 14. Datos de Ficha Clínica Retornados
    API-->>FE: 15. Devuelve Payload Completo de Detalle
    FE-->>M: 16. Muestra Pantalla Dividida (Raw Data vs. IA + Banderas Rojas)
    
    M->>FE: 17. Escribe Notas Médicas, Ajusta Prioridad (opcional) y hace clic en "Guardar y Confirmar"
    FE->>API: 18. POST /api/v1/doctor/review (triage_id, doctor_notes, priority_adjusted)
    API->>DB: 19. Inserta en MEDICAL_REVIEW y actualiza TRIAGE_RECORD (Status: REVIEWED)
    API-->>FE: 20. Confirmación de Cierre Exitoso (200 OK)
    FE-->>M: 21. Actualiza Dashboard y muestra Confeti de Cierre
```

---

## 5. Diagrama Entidad-Relación de Base de Datos (ERD Diagram)

Muestra las 5 tablas del esquema de base de datos PostgreSQL en Supabase, indicando llaves primarias (`PK`), llaves foráneas (`FK`), tipos de datos, cardinalidades y restricciones RLS.

```mermaid
erDiagram
    PROFILES ||--o{ MEDICAL_REVIEW : "realiza (1:N)"
    PROFILES ||--o{ AUDIT_LOG : "genera (1:N)"
    TRIAGE_RECORD ||--|| AI_RESULT : "posee (1:1)"
    TRIAGE_RECORD ||--o| MEDICAL_REVIEW : "recibe (1:1)"
    TRIAGE_RECORD ||--o{ AUDIT_LOG : "referencia (1:N)"

    PROFILES {
        uuid id PK
        uuid user_id FK
        string full_name
        string role "DOCTOR | ADMIN"
        timestamptz created_at
    }

    TRIAGE_RECORD {
        uuid id PK
        string access_code UK "ej. MS-8X92K"
        string ci_hash INDEX "HMAC-SHA256 Pepper"
        text ci_encrypted "AES-256-GCM"
        string patient_name
        int age
        string gender
        text raw_symptoms
        jsonb static_data
        jsonb dynamic_answers
        string status "RECEIVED | READY | REVIEWED"
        string final_priority "RED | YELLOW | GREEN"
        timestamptz created_at
    }

    AI_RESULT {
        uuid id PK
        uuid triage_id FK, UK
        string provider "gemini | groq | openai"
        string model "gemini-1.5-flash"
        jsonb structured_result "Contrato Pydantic"
        boolean override_applied
        text override_reason
        timestamptz created_at
    }

    MEDICAL_REVIEW {
        uuid id PK
        uuid triage_id FK
        uuid doctor_id FK
        text doctor_notes
        string priority_adjusted
        timestamptz reviewed_at
    }

    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        string action "SEARCH | VIEW | REVIEW | LOGIN"
        uuid resource_id
        string ip_address
        timestamptz timestamp
    }
```

---

## 6. Diagrama de Estados del Registro de Triaje (State Diagram)

Muestra el ciclo de vida de una atención de pre-triaje desde su creación pública hasta su resolución y archivo médico.

```mermaid
stateDiagram-v2
    [*] --> FormularioIniciado: Paciente Escanea QR / Abre Web

    state FormularioIniciado {
        [*] --> Paso1_DatosFijos: Completa Nombre, CI, Edad, Síntoma
        Paso1_DatosFijos --> Paso2_PreguntasDinámicas: Solicitud de Clarificación IA
        Paso2_PreguntasDinámicas --> Paso3_Confirmado: Paciente Responde y Envía
    }

    FormularioIniciado --> RECEIVED: Guardado en BD (Genera MS-XXXXX y QR)

    state RECEIVED {
        [*] --> ProcesandoIA: Envío de Prompt 2 a LLM
        ProcesandoIA --> EvaluandoOverrides: Retorno de JSON Estructurado
        EvaluandoOverrides --> AplicandoReglasDuras: Ejecución evaluate_safety_overrides()
    }

    RECEIVED --> READY: Triaje Procesado y Priorizado (RED/YELLOW/GREEN)

    state READY {
        [*] --> ListaDeEspera: Visible en Dashboard Médico por Urgencia
        ListaDeEspera --> EnRevisionMedica: Médico Abre Ficha por Escaneo QR / CI
    }

    READY --> REVIEWED: Médico Escribe Notas y Confirma Atendido

    state REVIEWED {
        [*] --> AtencionCerrada: Registro Inmutable y Auditado
    }

    REVIEWED --> [*]
```

---

## 7. Diagrama de Despliegue de Infraestructura y Docker (Deployment Diagram)

Representa la topología física y lógica de despliegue containerizado multi-etapa utilizando Docker Compose.

```mermaid
graph TD
    subgraph Host ["💻 SERVIDOR / HOST DE DESPLIEGUE (DOCKER COMPOSE ENVIROMENT)"]
        subgraph FrontendContainer ["📦 Contenedor 1: Frontend Web Server"]
            Nginx["Nginx Alpine Web Server (Puerto 80)"]
            StaticFiles["React Production Build Static Files"]
            Nginx --> StaticFiles
        end

        subgraph BackendContainer ["📦 Contenedor 2: FastAPI Backend Engine"]
            Uvicorn["Uvicorn ASGI Server (Puerto 8000)"]
            FastAPIApp["FastAPI Python Application (Python 3.11)"]
            EnvConfig[".env Configuration (Secrets, Pepper Key, Provider)"]
            Uvicorn --> FastAPIApp
            FastAPIApp --> EnvConfig
        end
    end

    subgraph Internet ["🌐 RED PÚBLICA / INTERNET"]
        UserBrowser["📱/💻 Navegador Web del Paciente / Médico"]
    end

    subgraph ExternalCloud ["☁️ SERVICIOS EN LA NUBE EXTERNOS"]
        SupabaseCloud["⚡ Supabase Cloud (PostgreSQL + Auth Engine)"]
        GeminiCloud["🧠 Google Gemini 1.5 Flash API"]
        GroqCloud["⚡ Groq Llama 3.1 API"]
    end

    %% Flujos de Red
    UserBrowser -- "HTTP (Port 80)" --> Nginx
    UserBrowser -- "HTTP REST (Port 8000)" --> Uvicorn

    FastAPIApp -- "TLS / SQL Port 5432" --> SupabaseCloud
    FastAPIApp -- "HTTPS API Call" --> GeminiCloud
    FastAPIApp -- "HTTPS API Call" --> GroqCloud
```

---

## 8. Diagrama de Flujo del Motor de Reglas Duras (Safety Overrides Flowchart)

Muestra el algoritmo determinista ejecutado en Python por `evaluate_safety_overrides()` para anular o ratificar la sugerencia del modelo de Inteligencia Artificial.

```mermaid
flowchart TD
    Start(["🚀 Inicio: Recibe JSON_IA y Raw_Symptoms"]) --> CheckAge{"¿Edad del paciente < 1 año?"}

    CheckAge -- "Sí" --> CheckFever{"¿Sintoma contiene 'fiebre' o 'temperatura alta'?"}
    CheckFever -- "Sí" --> ForceRed1["🔴 FORZAR PRIORIDAD RED<br/>Motivo: 'Regla de Seguridad: Lactante menor febril'"]

    CheckAge -- "No" --> CheckChest{"¿Sintoma contiene 'dolor de pecho', 'opresión torácica' o 'angina'?"}
    CheckFever -- "No" --> CheckChest

    CheckChest -- "Sí" --> ForceRed2["🔴 FORZAR PRIORIDAD RED<br/>Motivo: 'Regla de Seguridad: Dolor Torácico Opresivo'"]

    CheckChest -- "No" --> CheckDyspnea{"¿Sintoma contiene 'dificultad respiratoria', 'disnea' o 'ahogo'?"}

    CheckDyspnea -- "Sí" --> ForceRed3["🔴 FORZAR PRIORIDAD RED<br/>Motivo: 'Regla de Seguridad: Insuficiencia Respiratoria'"]

    CheckDyspnea -- "No" --> CheckStroke{"¿Sintoma contiene 'parálisis facial', 'pérdida de fuerza' o 'habla traposa'?"}

    CheckStroke -- "Sí" --> ForceRed4["🔴 FORZAR PRIORIDAD RED<br/>Motivo: 'Regla de Seguridad: Sospecha de ACV'"]

    CheckStroke -- "No" --> MaintainPriority["🟢/🟡 MANTENER PRIORIDAD ORIGINAL DE IA<br/>override_applied: false"]

    ForceRed1 --> ApplyOverride["Set override_applied = true & Save in BD"]
    ForceRed2 --> ApplyOverride
    ForceRed3 --> ApplyOverride
    ForceRed4 --> ApplyOverride
    MaintainPriority --> SaveBD(["💾 Retornar Objeto Final a Controller"])
    ApplyOverride --> SaveBD
```
