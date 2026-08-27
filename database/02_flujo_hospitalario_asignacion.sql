-- =============================================================================
-- MIGRACIÓN DE BASE DE DATOS: Flujo Hospitalario de Asignación Concurrente
-- Versión: 2.1.0 (Evolución Hospitalaria MediSinc-IA)
-- Ubicación: Santa Cruz de la Sierra, Bolivia
-- Descripción:
-- 1. Ampliación del ciclo de vida del triaje con estado 'EN_CONSULTA'.
-- 2. Columnas para asignación médica facultativa (medico_asignado_id, asignado_en).
-- 3. Índices compuestos para alto rendimiento en cola de guardia y 'Mis Pacientes'.
-- 4. Políticas RLS con control de concurrencia y asignación segura.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. MODIFICACIÓN DE RESTRICCIÓN CHECK DE ESTADOS EN registros_triaje
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    -- Eliminar restricción previa de estados si existe
    ALTER TABLE IF EXISTS registros_triaje 
    DROP CONSTRAINT IF EXISTS registros_triaje_estado_check;

    -- Agregar restricción actualizada con soporte para EN_CONSULTA
    ALTER TABLE IF EXISTS registros_triaje 
    ADD CONSTRAINT registros_triaje_estado_check 
    CHECK (estado IN ('RECIBIDO', 'LISTO', 'EN_CONSULTA', 'REVISADO', 'RECEIVED', 'READY', 'IN_CONSULTATION', 'REVIEWED'));
END $$;

-- -----------------------------------------------------------------------------
-- 2. AGREGAR COLUMNAS DE ASIGNACIÓN MÉDICA A registros_triaje
-- -----------------------------------------------------------------------------
ALTER TABLE IF EXISTS registros_triaje
ADD COLUMN IF NOT EXISTS medico_asignado_id UUID REFERENCES perfiles(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS asignado_en TIMESTAMPTZ;

-- Comentarios explicativos en español
COMMENT ON COLUMN registros_triaje.medico_asignado_id IS 'Identificador del profesional médico que tiene asignada la atención activa del paciente';
COMMENT ON COLUMN registros_triaje.asignado_en IS 'Estampa de tiempo ISO 8601 en la que el médico tomó el caso';

-- -----------------------------------------------------------------------------
-- 3. ÍNDICES COMPUESTOS PARA ALTA CONCURRENCIA
-- -----------------------------------------------------------------------------
-- Índice para filtrado veloz en pestaña "Mis Pacientes"
CREATE INDEX IF NOT EXISTS idx_triaje_medico_asignado 
ON registros_triaje (medico_asignado_id, estado);

-- Índice para filtrado de pacientes disponibles en espera de guardia
CREATE INDEX IF NOT EXISTS idx_triaje_cola_disponible 
ON registros_triaje (estado, prioridad_final, creado_en) 
WHERE medico_asignado_id IS NULL;

-- -----------------------------------------------------------------------------
-- 4. POLÍTICAS ROW LEVEL SECURITY (RLS) ACTUALIZADAS PARA ASIGNACIÓN
-- -----------------------------------------------------------------------------
-- Habilitar RLS en registros_triaje
ALTER TABLE registros_triaje ENABLE ROW LEVEL SECURITY;

-- Política 1: Lectura para personal médico y administradores
-- Permite ver pacientes sin asignar en espera o pacientes asignados a su propia cuenta
DROP POLICY IF EXISTS "Medicos y Admins pueden ver cola y sus asignados" ON registros_triaje;
CREATE POLICY "Medicos y Admins pueden ver cola y sus asignados"
ON registros_triaje
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM perfiles
        WHERE perfiles.usuario_id = auth.uid()
        AND perfiles.esta_activo = TRUE
        AND (
            perfiles.rol IN ('ADMIN')
            OR (
                perfiles.rol IN ('MEDICO', 'DOCTOR')
                AND (
                    registros_triaje.medico_asignado_id IS NULL 
                    OR registros_triaje.medico_asignado_id = perfiles.id
                    OR registros_triaje.estado IN ('RECIBIDO', 'LISTO', 'RECEIVED', 'READY')
                )
            )
        )
    )
);

-- Política 2: Actualización/Reclamo de pacientes por médico
-- Un médico puede reclamar un paciente si no está asignado o si es el médico asignado actual
DROP POLICY IF EXISTS "Medicos pueden reclamar y atender pacientes" ON registros_triaje;
CREATE POLICY "Medicos pueden reclamar y atender pacientes"
ON registros_triaje
FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM perfiles
        WHERE perfiles.usuario_id = auth.uid()
        AND perfiles.esta_activo = TRUE
        AND (
            perfiles.rol = 'ADMIN'
            OR (
                perfiles.rol IN ('MEDICO', 'DOCTOR')
                AND (
                    registros_triaje.medico_asignado_id IS NULL
                    OR registros_triaje.medico_asignado_id = perfiles.id
                )
            )
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM perfiles
        WHERE perfiles.usuario_id = auth.uid()
        AND perfiles.esta_activo = TRUE
        AND perfiles.rol IN ('MEDICO', 'ADMIN', 'DOCTOR')
    )
);
