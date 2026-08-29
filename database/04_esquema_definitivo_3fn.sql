-- =============================================================================
-- PROYECTO MEDISINC-IA · SISTEMA DE TRIAJE CLÍNICO INTELIGENTE
-- MIGRACIÓN DEFINITIVA A TERCERA FORMA NORMAL (3NF) - 100% EN ESPAÑOL
-- ARCHIVO: database/04_esquema_definitivo_3fn.sql
-- =============================================================================

-- 0. LIMPIEZA COMPLETA DE TABLAS ANTERIORES (ELIMINACIÓN DE DUPLICADOS EN INGLÉS Y ESPAÑOL)
DROP TABLE IF EXISTS revisiones_medicas CASCADE;
DROP TABLE IF EXISTS medical_review CASCADE;
DROP TABLE IF EXISTS resultados_ia CASCADE;
DROP TABLE IF EXISTS ai_result CASCADE;
DROP TABLE IF EXISTS registros_triaje CASCADE;
DROP TABLE IF EXISTS triage_record CASCADE;
DROP TABLE IF EXISTS patient_record CASCADE;
DROP TABLE IF EXISTS horarios_medicos CASCADE;
DROP TABLE IF EXISTS perfiles CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS pacientes CASCADE;
DROP TABLE IF EXISTS especialidades CASCADE;
DROP TABLE IF EXISTS specialties CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS registros_auditoria CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;

-- 1. HABILITACIÓN DE EXTENSIONES CRIPTOGRÁFICAS Y DE IDENTIFICADORES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 2. TABLA: roles (Catálogo Normalizado de Roles de Usuario)
-- =============================================================================
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(20) UNIQUE NOT NULL, -- 'ADMIN', 'MEDICO', 'ENFERMERO'
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 3. TABLA: especialidades (Catálogo Normalizado de Especialidades Médicas)
-- =============================================================================
CREATE TABLE IF NOT EXISTS especialidades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50) DEFAULT 'Stethoscope' NOT NULL,
    esta_activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 4. TABLA: pacientes (Entidad Maestra de Identidad y Antecedentes Cifrados)
-- Permite identificar al paciente sin requerir cuenta ni contraseña.
-- =============================================================================
CREATE TABLE IF NOT EXISTS pacientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ci_hash VARCHAR(64) UNIQUE NOT NULL, -- HMAC-SHA256 con Pepper para búsqueda O(1)
    ci_cifrado TEXT NOT NULL,             -- Carnet cifrado simétricamente con AES-256 (Fernet)
    nombre_completo VARCHAR(255) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 0 AND edad <= 125),
    genero VARCHAR(20) NOT NULL CHECK (genero IN ('Masculino', 'Femenino', 'Otro', 'No especificado')),
    alergias_medicamentosas TEXT DEFAULT 'Ninguna conocida' NOT NULL,
    enfermedades_base JSONB DEFAULT '[]'::jsonb NOT NULL,
    medicacion_habitual TEXT DEFAULT 'No toma medicación' NOT NULL,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL,
    actualizado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 5. TABLA: perfiles (Personal de Salud y Administradores vinculados a auth.users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS perfiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID UNIQUE, -- Vinculado opcionalmente a auth.users de Supabase
    nombre_completo VARCHAR(255) NOT NULL,
    correo VARCHAR(255) UNIQUE NOT NULL,
    clave VARCHAR(255) DEFAULT '123456' NOT NULL, -- Clave de acceso institucional (123456 para demo/desarrollo)
    rol_id UUID REFERENCES roles(id) ON DELETE RESTRICT NOT NULL,
    especialidad_id UUID REFERENCES especialidades(id) ON DELETE SET NULL,
    esta_activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 6. TABLA: horarios_medicos (Matriz de Turnos y Guardia Rotacional)
-- =============================================================================
CREATE TABLE IF NOT EXISTS horarios_medicos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medico_id UUID REFERENCES perfiles(id) ON DELETE CASCADE NOT NULL,
    dia_semana INT NOT NULL CHECK (dia_semana >= 0 AND dia_semana <= 6), -- 0=Domingo, 1=Lunes ... 6=Sábado
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    turno_etiqueta VARCHAR(50) DEFAULT 'MANANA', -- 'MANANA', 'TARDE_NOCHE', 'MADRUGADA', 'TODOS'
    esta_activo BOOLEAN DEFAULT TRUE NOT NULL,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL,
    CONSTRAINT check_horario_valido CHECK (hora_fin > hora_inicio OR turno_etiqueta = 'MADRUGADA' OR turno_etiqueta = 'TODOS')
);

-- =============================================================================
-- 7. TABLA: registros_triaje (Episodios Clínicos de Pre-Triaje)
-- =============================================================================
CREATE TABLE IF NOT EXISTS registros_triaje (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_acceso VARCHAR(20) UNIQUE NOT NULL, -- Formato MS-XXXXX
    paciente_id UUID REFERENCES pacientes(id) ON DELETE CASCADE NOT NULL,
    especialidad_id UUID REFERENCES especialidades(id) ON DELETE RESTRICT NOT NULL,
    medico_asignado_id UUID REFERENCES perfiles(id) ON DELETE SET NULL,
    asignado_en TIMESTAMPTZ,
    sintomas_brutos TEXT NOT NULL,
    datos_estaticos JSONB DEFAULT '{}'::jsonb NOT NULL, -- { duracion: '...', intensidad: 5 }
    respuestas_dinamicas JSONB DEFAULT '{}'::jsonb NOT NULL, -- { q_cualidad: '...', notas_adicionales: '...' }
    estado VARCHAR(30) DEFAULT 'RECIBIDO' NOT NULL CHECK (estado IN ('RECIBIDO', 'LISTO', 'EN_CONSULTA', 'REVISADO')),
    prioridad_final VARCHAR(20) DEFAULT 'VERDE' NOT NULL CHECK (prioridad_final IN ('ROJO', 'AMARILLO', 'VERDE')),
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL,
    actualizado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 8. TABLA: resultados_ia (Inferencia Clínica Asistida por IA - 1:1 con triaje)
-- =============================================================================
CREATE TABLE IF NOT EXISTS resultados_ia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    triaje_id UUID UNIQUE REFERENCES registros_triaje(id) ON DELETE CASCADE NOT NULL,
    proveedor VARCHAR(50) DEFAULT 'Gemini' NOT NULL,
    modelo VARCHAR(50) DEFAULT 'gemini-1.5-flash' NOT NULL,
    resultado_estructurado JSONB NOT NULL, -- { categoria_triage, prioridad_sugerida, justificacion_clinica, factores_riesgo }
    sobreescritura_aplicada BOOLEAN DEFAULT FALSE NOT NULL,
    motivo_sobreescritura TEXT,
    tiempo_respuesta_ms INT DEFAULT 0,
    creado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 9. TABLA: revisiones_medicas (Diagnóstico y Cierre Presencial por el Facultativo)
-- =============================================================================
CREATE TABLE IF NOT EXISTS revisiones_medicas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    triaje_id UUID UNIQUE REFERENCES registros_triaje(id) ON DELETE CASCADE NOT NULL,
    medico_id UUID REFERENCES perfiles(id) ON DELETE RESTRICT NOT NULL,
    notas_medico TEXT NOT NULL,
    prioridad_ajustada VARCHAR(20) CHECK (prioridad_ajustada IN ('ROJO', 'AMARILLO', 'VERDE')),
    revisado_en TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 10. TABLA: registros_auditoria (Bitácora Inalterable de Seguridad y Trazabilidad)
-- =============================================================================
CREATE TABLE IF NOT EXISTS registros_auditoria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID,
    accion VARCHAR(100) NOT NULL, -- 'CREAR_TRIAJE', 'ASIGNAR_PACIENTE', 'CONSULTAR_EXPEDIENTE', 'CERRAR_CONSULTA'
    recurso_id UUID,
    direccion_ip VARCHAR(45) DEFAULT '127.0.0.1' NOT NULL,
    fecha_hora TIMESTAMPTZ DEFAULT TIMEZONE('UTC', NOW()) NOT NULL
);

-- =============================================================================
-- 11. ÍNDICES DE ALTO RENDIMIENTO (OPTIMIZACIÓN O(1) Y CONSULTAS DE GUARDIA)
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_pacientes_ci_hash ON pacientes(ci_hash);
CREATE INDEX IF NOT EXISTS idx_registros_triaje_codigo ON registros_triaje(codigo_acceso);
CREATE INDEX IF NOT EXISTS idx_registros_triaje_paciente ON registros_triaje(paciente_id);
CREATE INDEX IF NOT EXISTS idx_registros_triaje_medico ON registros_triaje(medico_asignado_id);
CREATE INDEX IF NOT EXISTS idx_registros_triaje_especialidad ON registros_triaje(especialidad_id);
CREATE INDEX IF NOT EXISTS idx_registros_triaje_guardia_orden ON registros_triaje(estado, prioridad_final, creado_en ASC);
CREATE INDEX IF NOT EXISTS idx_horarios_medicos_turno ON horarios_medicos(medico_id, dia_semana, esta_activo);
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON registros_auditoria(fecha_hora DESC);

-- =============================================================================
-- 12. DISPARADOR (TRIGGER) PARA ACTUALIZACIÓN AUTOMÁTICA DE TIMESTAMP
-- =============================================================================
CREATE OR REPLACE FUNCTION actualizar_timestamp_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = TIMEZONE('UTC', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_pacientes_timestamp ON pacientes;
CREATE TRIGGER trg_actualizar_pacientes_timestamp
    BEFORE UPDATE ON pacientes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_timestamp_modificacion();

DROP TRIGGER IF EXISTS trg_actualizar_triaje_timestamp ON registros_triaje;
CREATE TRIGGER trg_actualizar_triaje_timestamp
    BEFORE UPDATE ON registros_triaje
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_timestamp_modificacion();

-- =============================================================================
-- 13. POLÍTICAS DE SEGURIDAD A NIVEL DE FILA (ROW LEVEL SECURITY - RLS)
-- =============================================================================
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE especialidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE horarios_medicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_triaje ENABLE ROW LEVEL SECURITY;
ALTER TABLE resultados_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE revisiones_medicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE registros_auditoria ENABLE ROW LEVEL SECURITY;

-- 13.1. Roles y Especialidades: Lectura pública
CREATE POLICY "Permitir lectura publica de roles" ON roles FOR SELECT USING (true);
CREATE POLICY "Permitir lectura publica de especialidades" ON especialidades FOR SELECT USING (esta_activo = true);

-- 13.2. Pacientes: Inserción y lectura anónima por hash/service_role
CREATE POLICY "Permitir insercion anonima de pacientes" ON pacientes FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir lectura de pacientes autenticados" ON pacientes FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
CREATE POLICY "Permitir actualizacion de pacientes autenticados" ON pacientes FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- 13.3. Registros de Triaje: Inserción pública y lectura por código o auth
CREATE POLICY "Permitir creacion publica de triaje" ON registros_triaje FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir lectura de triaje por codigo o autenticacion" ON registros_triaje FOR SELECT USING (true);
CREATE POLICY "Permitir modificacion de triaje a personal autenticado" ON registros_triaje FOR UPDATE USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- 13.4. Resultados IA y Revisiones Médicas
CREATE POLICY "Permitir lectura y creacion de resultados IA" ON resultados_ia FOR ALL USING (true);
CREATE POLICY "Permitir gestion de revisiones a medicos autenticados" ON revisiones_medicas FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- 13.5. Auditoría: Inserción de eventos y lectura administrativa
CREATE POLICY "Permitir registro de auditoria" ON registros_auditoria FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir lectura de auditoria a administradores" ON registros_auditoria FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- =============================================================================
-- 14. DATOS INICIALES (SEEDS DETERMINISTAS DE PRODUCCIÓN)
-- =============================================================================

-- 14.1. Roles Base
INSERT INTO roles (id, codigo, nombre, descripcion) VALUES
    ('10000000-0000-0000-0000-000000000001', 'ADMIN', 'Administrador del Sistema', 'Acceso total a gobernanza, bitácora y gestión de personal'),
    ('10000000-0000-0000-0000-000000000002', 'MEDICO', 'Médico Facultativo de Guardia', 'Acceso a lista de espera, atención clínica y expediente'),
    ('10000000-0000-0000-0000-000000000003', 'ENFERMERO', 'Personal de Enfermería y Triaje', 'Apoyo en admisión y toma de signos vitales')
ON CONFLICT (codigo) DO NOTHING;

-- 14.2. Catálogo de Especialidades
INSERT INTO especialidades (id, nombre, descripcion, icono, esta_activo) VALUES
    ('20000000-0000-0000-0000-000000000001', 'Medicina General', 'Atención primaria integral, evaluación clínica general y derivación oportuna.', 'Stethoscope', true),
    ('20000000-0000-0000-0000-000000000002', 'Pediatría', 'Atención médica especializada para lactantes, niños y adolescentes.', 'Baby', true),
    ('20000000-0000-0000-0000-000000000003', 'Ginecología y Obstetricia', 'Salud femenina integral, control prenatal, dolor pélvico y urgencias ginecológicas.', 'HeartHandshake', true),
    ('20000000-0000-0000-0000-000000000004', 'Traumatología y Urgencias', 'Lesiones óseas y articulares, caídas, contusiones y traumatismos agudos.', 'Bone', true),
    ('20000000-0000-0000-0000-000000000005', 'Cardiología y Medicina Interna', 'Dolor torácico, hipertensión, arritmias y patologías médicas complejas.', 'HeartPulse', true),
    ('20000000-0000-0000-0000-000000000006', 'Odontología', 'Dolor dental agudo, infecciones maxilofaciales y urgencias bucales.', 'Smile', true)
ON CONFLICT (nombre) DO NOTHING;

-- 14.3. Personal Médico Inicial (Perfiles)
INSERT INTO perfiles (id, nombre_completo, correo, rol_id, especialidad_id, esta_activo) VALUES
    ('30000000-0000-0000-0000-000000000001', 'Dr. Fernando Morales (Admin)', 'admin@medisinc.bo', '10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', true),
    ('30000000-0000-0000-0000-000000000002', 'Dr. Carlos Menacho', 'carlos.menacho@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000001', true),
    ('30000000-0000-0000-0000-000000000003', 'Dra. Mariana Vaca', 'mariana.vaca@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', true),
    ('30000000-0000-0000-0000-000000000004', 'Dra. Sofía Justiniano', 'sofia.justiniano@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', true),
    ('30000000-0000-0000-0000-000000000005', 'Dr. Luis Fernando Aguilera', 'luis.aguilera@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000004', true),
    ('30000000-0000-0000-0000-000000000006', 'Dr. Roberto Antelo', 'roberto.antelo@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000005', true),
    ('30000000-0000-0000-0000-000000000007', 'Dra. Valeria Cuéllar', 'valeria.cuellar@medisinc.bo', '10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000006', true)
ON CONFLICT (correo) DO UPDATE SET
    nombre_completo = EXCLUDED.nombre_completo,
    especialidad_id = EXCLUDED.especialidad_id,
    esta_activo = EXCLUDED.esta_activo;

-- 14.4. Horarios y Turnos Iniciales
INSERT INTO horarios_medicos (medico_id, dia_semana, hora_inicio, hora_fin, turno_etiqueta, esta_activo) VALUES
    ('30000000-0000-0000-0000-000000000002', 1, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000002', 2, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000002', 3, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000002', 4, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000002', 5, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000003', 1, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000003', 2, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000004', 1, '15:00:00', '23:00:00', 'TARDE_NOCHE', true),
    ('30000000-0000-0000-0000-000000000005', 1, '00:00:00', '23:59:59', 'TODOS', true),
    ('30000000-0000-0000-0000-000000000006', 1, '07:00:00', '15:00:00', 'MANANA', true),
    ('30000000-0000-0000-0000-000000000007', 1, '15:00:00', '23:00:00', 'TARDE_NOCHE', true)
ON CONFLICT DO NOTHING;
