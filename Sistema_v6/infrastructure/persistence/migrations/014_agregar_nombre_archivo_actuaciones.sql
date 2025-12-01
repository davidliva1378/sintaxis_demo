-- ============================================================================
-- Migración 014: Agregar columna nombre_archivo a actuaciones
-- ============================================================================
--
-- Esta migración agrega la columna nombre_archivo para almacenar directamente
-- el nombre del archivo PDF descargado, independiente de ruta_pdf.
--
-- PROBLEMA QUE RESUELVE:
-- - El JSON de extracción guarda NombreArchivo pero no se persiste en MySQL
-- - ruta_pdf puede ser NULL aunque el archivo exista en disco
-- - El frontend necesita nombre_archivo para mostrar botones de PDF
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Agregar columna nombre_archivo
-- ============================================================================

ALTER TABLE actuaciones
    ADD COLUMN nombre_archivo VARCHAR(255) DEFAULT NULL
    COMMENT 'Nombre del archivo PDF descargado (ej: 2025-11-18_cedula_electronica_tribunal_396aac.pdf)'
    AFTER ruta_pdf;

-- ============================================================================
-- PASO 2: Agregar índice para búsquedas
-- ============================================================================

CREATE INDEX idx_nombre_archivo ON actuaciones (nombre_archivo);

-- ============================================================================
-- PASO 3: Migrar datos existentes desde ruta_pdf (opcional)
-- ============================================================================

-- Si ruta_pdf contiene una ruta completa, extraer solo el nombre del archivo
UPDATE actuaciones
SET nombre_archivo = SUBSTRING_INDEX(ruta_pdf, '/', -1)
WHERE ruta_pdf IS NOT NULL
  AND nombre_archivo IS NULL
  AND ruta_pdf != '';

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================
