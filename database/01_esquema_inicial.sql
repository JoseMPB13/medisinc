-- =============================================================================
-- ESQUEMA DE BASE DE DATOS MEDISINC-IA (SUPABASE / POSTGRESQL) - ESTANDARIZADO
-- Versión: 2.0.0 (Estandarización al Español)
-- Ubicación: Santa Cruz de la Sierra, Bolivia
-- Descripción: Tablas relacionales en español, restricciones, índices y RLS
-- =============================================================================

-- Habilitar extensión pgcrypto para generación de UUIDs y funciones criptográficas
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. TABLA: perfiles (Perfiles de usuarios autenticados: Médicos y Administradores)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perfiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    nombre_completo VARCHAR(255) NOT NULL,
    correo VARCHAR(255),
    especialidad VARCHAR(150) DEFAULT 'Medicina General',
    rol VARCHAR(50) NOT NULL CHECK (rol IN ('MEDICO', 'ADMIN', 'DOCTOR')),
    esta_activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE perfiles IS 'Almacena la información de perfil, especialidad y rol de médicos y administradores asociados a Supabase Auth';
COMMENT ON COLUMN perfiles.id IS 'Identificador único del perfil (UUID)';
COMMENT ON COLUMN perfiles.usuario_id IS 'Referencia al usuario registrado en auth.users de Supabase';
COMMENT ON COLUMN perfiles.nombre_completo IS 'Nombre y apellidos del profesional de salud o administrador';
COMMENT ON COLUMN perfiles.correo IS 'Correo electrónico institucional o de contacto';
COMMENT ON COLUMN perfiles.especialidad IS 'Especialidad médica (ej. Triaje, Medicina General, Emergenciología)';
COMMENT ON COLUMN perfiles.rol IS 'Rol dentro del sistema (MEDICO, ADMIN)';
COMMENT ON COLUMN perfiles.esta_activo IS 'Estado de habilitación del usuario en la plataforma';
COMMENT ON COLUMN perfiles.creado_en IS 'Fecha y hora de creación del registro de perfil';

-- -----------------------------------------------------------------------------
-- 2. TABLA: registros_triaje (Registros de Pre-Triaje Clínico de Pacientes)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registros_triaje (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_acceso VARCHAR(20) UNIQUE NOT NULL,
    ci_hash VARCHAR(64) NOT NULL,
    ci_cifrado TEXT NOT NULL,
    nombre_paciente VARCHAR(255) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 0 AND edad <= 120),
    genero VARCHAR(20) NOT NULL,
    sintomas_brutos TEXT NOT NULL,
    datos_estaticos JSONB DEFAULT '{}'::jsonb,
    respuestas_dinamicas JSONB DEFAULT '{}'::jsonb,
    estado VARCHAR(20) DEFAULT 'RECIBIDO' CHECK (estado IN ('RECIBIDO', 'LISTO', 'REVISADO', 'RECEIVED', 'READY', 'REVIEWED')),
    prioridad_final VARCHAR(10) CHECK (prioridad_final IN ('ROJO', 'AMARILLO', 'VERDE', 'RED', 'YELLOW', 'GREEN')),
    creado_en TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE registros_triaje IS 'Almacena los datos de ingreso del paciente, código alfanumérico, CI cifrado/hash y estado de triaje';
COMMENT ON COLUMN registros_triaje.codigo_acceso IS 'Código único alfanumérico legible para el paciente (ej. MS-8X92K)';
COMMENT ON COLUMN registros_triaje.ci_hash IS 'Hash ciego HMAC-SHA256 con Pepper del CI para búsquedas exactas sin exponer datos personales';
COMMENT ON COLUMN registros_triaje.ci_cifrado IS 'Carnet de Identidad cifrado simétricamente con AES-256 (Fernet)';
COMMENT ON COLUMN registros_triaje.estado IS 'Estado del triaje: RECIBIDO (ingresado), LISTO (procesado por IA), REVISADO (atendido por médico)';
COMMENT ON COLUMN registros_triaje.prioridad_final IS 'Nivel de urgencia clínica: ROJO (Urgente), AMARILLO (Prioritario), VERDE (No Urgente)';

-- Índices optimizados para consultas del portal médico y búsqueda por código/hash
CREATE INDEX IF NOT EXISTS idx_triaje_ci_hash ON registros_triaje(ci_hash);
CREATE INDEX IF NOT EXISTS idx_triaje_codigo_acceso ON registros_triaje(codigo_acceso);
CREATE INDEX IF NOT EXISTS idx_triaje_panel_orden ON registros_triaje(estado, prioridad_final, creado_en DESC);

-- -----------------------------------------------------------------------------
-- 3. TABLA: resultados_ia (Resultados Estructurados y Safety Overrides)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resultados_ia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    triaje_id UUID UNIQUE NOT NULL REFERENCES registros_triaje(id) ON DELETE CASCADE,
    proveedor VARCHAR(50) NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    resultado_estructurado JSONB NOT NULL,
    sobreescritura_aplicada BOOLEAN DEFAULT FALSE,
    motivo_sobreescritura TEXT,
    creado_en TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE resultados_ia IS 'Almacena el resumen clínico estructurado emitido por el LLM y la aplicación de reglas de seguridad';
COMMENT ON COLUMN resultados_ia.triaje_id IS 'Referencia 1:1 al registro de pre-triaje evaluado';
COMMENT ON COLUMN resultados_ia.proveedor IS 'Proveedor de IA utilizado (gemini, groq, openai)';
COMMENT ON COLUMN resultados_ia.modelo IS 'Identificador del modelo empleado (ej. gemini-1.5-flash, llama-3-70b)';
COMMENT ON COLUMN resultados_ia.resultado_estructurado IS 'JSONB con la respuesta estricta según el esquema Pydantic';
COMMENT ON COLUMN resultados_ia.sobreescritura_aplicada IS 'Indica si el motor de reglas deterministas forzó la prioridad';
COMMENT ON COLUMN resultados_ia.motivo_sobreescritura IS 'Justificación médica de la sobreescritura de seguridad';

-- -----------------------------------------------------------------------------
-- 4. TABLA: revisiones_medicas (Evaluación y Cierre de Consulta Facultativa)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS revisiones_medicas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    triaje_id UUID NOT NULL REFERENCES registros_triaje(id) ON DELETE CASCADE,
    medico_id UUID NOT NULL REFERENCES perfiles(id) ON DELETE CASCADE,
    notas_medico TEXT NOT NULL,
    prioridad_ajustada VARCHAR(10) CHECK (prioridad_ajustada IN ('ROJO', 'AMARILLO', 'VERDE', 'RED', 'YELLOW', 'GREEN')),
    revisado_en TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE revisiones_medicas IS 'Registra la atención presencial, observaciones clínicas y ajustes de prioridad del médico tratante';
COMMENT ON COLUMN revisiones_medicas.medico_id IS 'Referencia al perfil del médico que realizó la atención';
COMMENT ON COLUMN revisiones_medicas.notas_medico IS 'Diagnóstico inicial y notas clínicas registradas en consulta';
COMMENT ON COLUMN revisiones_medicas.prioridad_ajustada IS 'Prioridad reclasificada manualmente por el facultativo';

-- -----------------------------------------------------------------------------
-- 5. TABLA: registros_auditoria (Trazabilidad e Historial Inalterable)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registros_auditoria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES perfiles(id) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    recurso_id UUID,
    direccion_ip VARCHAR(45),
    fecha_hora TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE registros_auditoria IS 'Bitácora inalterable de auditoría para trazabilidad de lecturas, descifrados y modificaciones';
COMMENT ON COLUMN registros_auditoria.usuario_id IS 'Usuario médico o administrador que ejecutó la acción (NULL para eventos de sistema)';
COMMENT ON COLUMN registros_auditoria.accion IS 'Identificador de la acción ejecutada (ej. CONSULTAR_EXPEDIENTE, DESCIFRAR_CI, CREAR_MEDICO)';
COMMENT ON COLUMN registros_auditoria.recurso_id IS 'ID del recurso afectado (ej. id de registros_triaje)';
COMMENT ON COLUMN registros_auditoria.direccion_ip IS 'Dirección IP desde la cual se originó la solicitud';

CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_fecha ON registros_auditoria(usuario_id, fecha_hora DESC);

-- =============================================================================
-- HABILITACIÓN DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- =============================================================================
ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_triaje ENABLE ROW LEVEL SECURITY;
ALTER TABLE resultados_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE revisiones_medicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_auditoria ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL ANON (Formulario Público de Pacientes)
-- -----------------------------------------------------------------------------
-- Los pacientes anónimos sólo tienen permiso para registrar su propio pre-triaje
CREATE POLICY "Permitir insercion publica a anon en registros_triaje"
    ON registros_triaje FOR INSERT
    TO anon
    WITH CHECK (true);

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL AUTHENTICATED (Médicos y Administradores Autenticados)
-- -----------------------------------------------------------------------------
CREATE POLICY "Lectura de perfiles para usuarios autenticados"
    ON perfiles FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Lectura de triajes para medicos autenticados"
    ON registros_triaje FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Actualizacion de triajes para medicos autenticados"
    ON registros_triaje FOR UPDATE
    TO authenticated
    USING (true);

CREATE POLICY "Lectura de resultados IA para medicos autenticados"
    ON resultados_ia FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Insercion de revisiones medicas para medicos autenticados"
    ON revisiones_medicas FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Lectura de revisiones medicas para personal autenticado"
    ON revisiones_medicas FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Insercion de eventos en bitacora de auditoria"
    ON registros_auditoria FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Lectura de bitacora para administradores"
    ON registros_auditoria FOR SELECT
    TO authenticated
    USING (true);

-- -----------------------------------------------------------------------------
-- POLÍTICAS RLS: ROL SERVICE_ROLE (Backend FastAPI con Clave de Servicio)
-- -----------------------------------------------------------------------------
CREATE POLICY "Acceso total para service_role en perfiles"
    ON perfiles FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en registros_triaje"
    ON registros_triaje FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en resultados_ia"
    ON resultados_ia FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en revisiones_medicas"
    ON revisiones_medicas FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Acceso total para service_role en registros_auditoria"
    ON registros_auditoria FOR ALL TO service_role USING (true) WITH CHECK (true);
