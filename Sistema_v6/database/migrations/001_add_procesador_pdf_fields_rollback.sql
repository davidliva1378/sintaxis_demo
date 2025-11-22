-- Rollback: Revertir campos de procesador_pdf
-- Fecha: 2025-11-18
-- Descripción: Revierte los cambios de la migración 001_add_procesador_pdf_fields.sql

-- ============================================
-- 1. Eliminar vistas
-- ============================================

DROP VIEW IF EXISTS actuaciones_alta_utilidad;
DROP VIEW IF EXISTS vencimientos_urgentes;

-- ============================================
-- 2. Eliminar tablas
-- ============================================

DROP TABLE IF EXISTS procesamiento_estadisticas;
DROP TABLE IF EXISTS duplicados_detectados;
DROP TABLE IF EXISTS vencimientos;

-- ============================================
-- 3. Eliminar campos de tabla actuaciones
-- ============================================

ALTER TABLE actuaciones
DROP COLUMN IF EXISTS hash_contenido,
DROP COLUMN IF EXISTS texto_extraido,
DROP COLUMN IF EXISTS fecha_clasificacion,
DROP COLUMN IF EXISTS keywords_detectados,
DROP COLUMN IF EXISTS es_duplicado_probable,
DROP COLUMN IF EXISTS tiene_plazo_probable,
DROP COLUMN IF EXISTS requiere_pdf,
DROP COLUMN IF EXISTS motivo_clasificacion,
DROP COLUMN IF EXISTS score,
DROP COLUMN IF EXISTS utilidad,
DROP INDEX IF EXISTS idx_tiene_plazo,
DROP INDEX IF EXISTS idx_requiere_pdf,
DROP INDEX IF EXISTS idx_score,
DROP INDEX IF EXISTS idx_utilidad;

-- ============================================
-- FIN DE ROLLBACK
-- ============================================
-- Para aplicar: mysql -u usuario -p nombre_db < 001_add_procesador_pdf_fields_rollback.sql
