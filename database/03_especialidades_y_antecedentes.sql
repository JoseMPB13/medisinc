-- =============================================================================
-- MIGRACIÓN 03: ESPECIALIDADES MÉDICAS Y ANTECEDENTES CLÍNICOS AMPLIADOS
-- =============================================================================
-- Fecha: 2026-08-28
-- Descripción:
-- 1. Agrega columnas de especialidad solicitada y antecedentes (alergias, medicación,
--    enfermedades de base) a registros_triaje y triage_record.
-- 2. Crea índices optimizados para filtrado de guardia por especialidad médica.
-- =============================================================================

-- 1. Agregar columnas a registros_triaje (Esquema en Español)
ALTER TABLE registros_triaje 
  ADD COLUMN IF NOT EXISTS especialidad_solicitada VARCHAR(80) DEFAULT 'Medicina General',
  ADD COLUMN IF NOT EXISTS alergias_medicamentosas TEXT DEFAULT 'Ninguna conocida',
  ADD COLUMN IF NOT EXISTS medicacion_actual TEXT DEFAULT 'Ninguna',
  ADD COLUMN IF NOT EXISTS enfermedades_base JSONB DEFAULT '[]'::jsonb;

-- 2. Soporte defensivo para tabla legacy triage_record (Esquema en Inglés)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'triage_record') THEN
    ALTER TABLE triage_record 
      ADD COLUMN IF NOT EXISTS requested_specialty VARCHAR(80) DEFAULT 'Medicina General',
      ADD COLUMN IF NOT EXISTS drug_allergies TEXT DEFAULT 'Ninguna conocida',
      ADD COLUMN IF NOT EXISTS current_medication TEXT DEFAULT 'Ninguna',
      ADD COLUMN IF NOT EXISTS base_diseases JSONB DEFAULT '[]'::jsonb;
  END IF;
END $$;

-- 3. Índices de rendimiento para el filtrado de guardia
CREATE INDEX IF NOT EXISTS idx_triaje_especialidad 
  ON registros_triaje (especialidad_solicitada);

CREATE INDEX IF NOT EXISTS idx_triaje_especialidad_estado 
  ON registros_triaje (especialidad_solicitada, estado);

COMMENT ON COLUMN registros_triaje.especialidad_solicitada IS 'Especialidad médica seleccionada por el paciente en el Paso 0';
COMMENT ON COLUMN registros_triaje.alergias_medicamentosas IS 'Alergias a medicamentos declaradas explícitamente';
COMMENT ON COLUMN registros_triaje.medicacion_actual IS 'Fármacos o tratamientos que el paciente consume habitualmente';
COMMENT ON COLUMN registros_triaje.enfermedades_base IS 'Comorbilidades o enfermedades crónicas de base en formato JSON';
