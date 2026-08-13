-- =============================================================================
-- ESQUEMA DE BASE DE DATOS MEDISINC-IA (SUPABASE / POSTGRESQL)
-- Versión: 1.0.0
-- Ubicación: Santa Cruz de la Sierra, Bolivia
-- Descripción: Tablas principales, índices, comentarios y políticas de seguridad RLS
-- =============================================================================

-- Habilitar extensión pgcrypto para generación de UUIDs si es necesario
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. TABLA: PROFILES (Perfiles de usuarios autenticados: Médicos y Admins)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS PROFILES (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('DOCTOR', 'ADMIN')),
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE PROFILES IS 'Almacena la información del perfil y rol de médicos y administradores asociados a Supabase Auth';
COMMENT ON COLUMN PROFILES.id IS 'Identificador único del perfil (UUID)';
COMMENT ON COLUMN PROFILES.user_id IS 'Referencia al usuario registrado en auth.users de Supabase';
COMMENT ON COLUMN PROFILES.full_name IS 'Nombre completo del profesional de salud o administrador';
COMMENT ON COLUMN PROFILES.role IS 'Rol dentro del sistema (DOCTOR o ADMIN)';
COMMENT ON COLUMN PROFILES.created_at IS 'Fecha y hora de creación del registro de perfil';

-- -----------------------------------------------------------------------------
-- 2. TABLA: TRIAGE_RECORD (Registros de Pre-Triaje Clínico)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS TRIAGE_RECORD (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_code VARCHAR(20) UNIQUE NOT NULL,
    ci_hash VARCHAR(64) NOT NULL,
    ci_encrypted TEXT NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    age INT NOT NULL CHECK (age >= 0 AND age <= 120),
    gender VARCHAR(20) NOT NULL,
    raw_symptoms TEXT NOT NULL,
    static_data JSONB DEFAULT '{}'::jsonb,
    dynamic_answers JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'RECEIVED' CHECK (status IN ('RECEIVED', 'READY', 'REVIEWED')),
    final_priority VARCHAR(10) CHECK (final_priority IN ('RED', 'YELLOW', 'GREEN')),
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE TRIAGE_RECORD IS 'Almacena los datos de ingreso del paciente, código de acceso, CI encriptado/hash y estado del triaje';
COMMENT ON COLUMN TRIAGE_RECORD.access_code IS 'Código único alfanumérico legible para el paciente (ej. MS-8X92K)';
COMMENT ON COLUMN TRIAGE_RECORD.ci_hash IS 'Hash HMAC-SHA256 con pepper del CI para búsquedas exactas sin exponer el dato real';
COMMENT ON COLUMN TRIAGE_RECORD.ci_encrypted IS 'Carnet de Identidad cifrado con AES-256-GCM para protección de datos personales';
COMMENT ON COLUMN TRIAGE_RECORD.status IS 'Estado del registro: RECEIVED (ingresado), READY (procesado por IA), REVIEWED (atendido por médico)';
COMMENT ON COLUMN TRIAGE_RECORD.final_priority IS 'Prioridad final del paciente: RED (Urgente), YELLOW (Prioritario), GREEN (No Urgente)';

-- Índices de búsqueda para optimizar consultas del portal médico y lista de espera
CREATE INDEX IF NOT EXISTS idx_triage_ci_hash ON TRIAGE_RECORD(ci_hash);
CREATE INDEX IF NOT EXISTS idx_triage_access_code ON TRIAGE_RECORD(access_code);
CREATE INDEX IF NOT EXISTS idx_triage_dashboard ON TRIAGE_RECORD(status, final_priority, created_at DESC);

-- -----------------------------------------------------------------------------
-- 3. TABLA: AI_RESULT (Resultados Estructurados del Modelo de IA)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS AI_RESULT (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    triage_id UUID UNIQUE NOT NULL REFERENCES TRIAGE_RECORD(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    structured_result JSONB NOT NULL,
    override_applied BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE AI_RESULT IS 'Almacena el resumen clínico estructurado por el proveedor de IA y las reglas de seguridad (safety overrides)';
COMMENT ON COLUMN AI_RESULT.triage_id IS 'Referencia 1:1 al registro de triaje evaluado';
COMMENT ON COLUMN AI_RESULT.provider IS 'Proveedor de IA utilizado (gemini, groq, openai)';
COMMENT ON COLUMN AI_RESULT.model IS 'Modelo específico empleado (ej. gemini-1.5-flash, llama-3-70b)';
COMMENT ON COLUMN AI_RESULT.structured_result IS 'JSONB con la respuesta estricta según el esquema Pydantic';
COMMENT ON COLUMN AI_RESULT.override_applied IS 'Indica si el motor de reglas duras anuló la prioridad sugerida por la IA';
COMMENT ON COLUMN AI_RESULT.override_reason IS 'Motivo por el cual se aplicó la regla de seguridad de sobreecritura';

-- -----------------------------------------------------------------------------
-- 4. TABLA: MEDICAL_REVIEW (Evaluación y Confirmación Médica)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS MEDICAL_REVIEW (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    triage_id UUID NOT NULL REFERENCES TRIAGE_RECORD(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES PROFILES(id) ON DELETE CASCADE,
    doctor_notes TEXT,
    priority_adjusted VARCHAR(10) CHECK (priority_adjusted IN ('RED', 'YELLOW', 'GREEN')),
    reviewed_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE MEDICAL_REVIEW IS 'Registra la revisión clínica presencial realizada por el médico y ajustes de prioridad';
COMMENT ON COLUMN MEDICAL_REVIEW.doctor_id IS 'Referencia al perfil del médico que atendió al paciente';
COMMENT ON COLUMN MEDICAL_REVIEW.doctor_notes IS 'Observaciones y notas clínicas registradas por el profesional';
COMMENT ON COLUMN MEDICAL_REVIEW.priority_adjusted IS 'Prioridad ajustada manualmente por el médico si fue necesario';

-- -----------------------------------------------------------------------------
-- 5. TABLA: AUDIT_LOG (Trazabilidad e Historial de Operaciones)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS AUDIT_LOG (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES PROFILES(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_id UUID,
    ip_address VARCHAR(45),
    timestamp TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE AUDIT_LOG IS 'Registro inalterable de auditoría para trazabilidad de lecturas, búsquedas y modificaciones';
COMMENT ON COLUMN AUDIT_LOG.user_id IS 'Usuario médico o admin que ejecutó la acción (NULL para acciones del sistema)';
COMMENT ON COLUMN AUDIT_LOG.action IS 'Descripción corta de la acción realizada (ej. SEARCH_CI, VIEW_RECORD, UPDATE_PRIORITY)';
COMMENT ON COLUMN AUDIT_LOG.resource_id IS 'ID del recurso afectado (ej. id de TRIAGE_RECORD)';
COMMENT ON COLUMN AUDIT_LOG.ip_address IS 'Dirección IP desde la cual se originó la petición';

CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON AUDIT_LOG(user_id, timestamp DESC);

-- =============================================================================
-- HABILITACIÓN DE ROW LEVEL SECURITY (RLS)
-- =============================================================================
ALTER TABLE PROFILES ENABLE ROW LEVEL SECURITY;
ALTER TABLE TRIAGE_RECORD ENABLE ROW LEVEL SECURITY;
ALTER TABLE AI_RESULT ENABLE ROW LEVEL SECURITY;
ALTER TABLE MEDICAL_REVIEW ENABLE ROW LEVEL SECURITY;
ALTER TABLE AUDIT_LOG ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL ANON (Formulario Público de Pacientes)
-- -----------------------------------------------------------------------------
-- El rol público (anon) sólo puede insertar nuevos registros de triaje
CREATE POLICY "Permitir insercion publica a anon en TRIAGE_RECORD"
    ON TRIAGE_RECORD FOR INSERT
    TO anon
    WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL SERVICE_ROLE (Backend FastAPI con Service Key)
-- -----------------------------------------------------------------------------
-- El backend backend (service_role) posee acceso total sobre todas las tablas
CREATE POLICY "Acceso total para service_role en PROFILES"
    ON PROFILES FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en TRIAGE_RECORD"
    ON TRIAGE_RECORD FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en AI_RESULT"
    ON AI_RESULT FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en MEDICAL_REVIEW"
    ON MEDICAL_REVIEW FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en AUDIT_LOG"
    ON AUDIT_LOG FOR ALL TO service_role USING (true) WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL AUTHENTICATED (Médicos y Administradores Autenticados)
-- -----------------------------------------------------------------------------
-- Permisos de lectura para usuarios autenticados
CREATE POLICY "Permitir lectura a usuarios autenticados en PROFILES"
    ON PROFILES FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir lectura a usuarios autenticados en TRIAGE_RECORD"
    ON TRIAGE_RECORD FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir actualizacion de triaje a usuarios autenticados"
    ON TRIAGE_RECORD FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Permitir lectura a usuarios autenticados en AI_RESULT"
    ON AI_RESULT FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir lectura a usuarios autenticados en MEDICAL_REVIEW"
    ON MEDICAL_REVIEW FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir insercion de revision medica a usuarios autenticados"
    ON MEDICAL_REVIEW FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Permitir actualizacion de revision medica a usuarios autenticados"
    ON MEDICAL_REVIEW FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Permitir lectura a usuarios autenticados en AUDIT_LOG"
    ON AUDIT_LOG FOR SELECT TO authenticated USING (true);

CREATE POLICY "Permitir insercion de logs de auditoria a usuarios autenticados"
    ON AUDIT_LOG FOR INSERT TO authenticated WITH CHECK (true);
