-- ============================================================================
-- Migración 001: Crear tabla expedientes y agregar deduplicación
-- ============================================================================
--
-- Esta migración:
-- 1. Crea la tabla central 'expedientes'
-- 2. Agrega columna expediente_id a tablas existentes
-- 3. Agrega UNIQUE constraints para evitar duplicados
-- 4. Crea índices para mejorar performance
--
-- IMPORTANTE: Ejecutar en orden. Cada sección puede ejecutarse por separado.
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla expedientes
-- ============================================================================

CREATE TABLE IF NOT EXISTS expedientes (
    id INT PRIMARY KEY COMMENT 'ID del expedientes_index.json',
    numero_normalizado VARCHAR(100) NOT NULL UNIQUE COMMENT 'Ej: FPA_012332_2019',
    numero_original VARCHAR(100) NOT NULL COMMENT 'Ej: FPA 012332/2019',
    dependencia VARCHAR(500) DEFAULT NULL COMMENT 'Juzgado/Fiscalía',
    caratula VARCHAR(500) DEFAULT NULL COMMENT 'Carátula del expediente',
    situacion VARCHAR(100) DEFAULT NULL COMMENT 'Estado actual',
    ultima_actuacion DATE DEFAULT NULL COMMENT 'Fecha última actuación',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_extraccion DATETIME DEFAULT NULL,
    fecha_ultimo_procesamiento DATETIME DEFAULT NULL,
    total_actuaciones INT DEFAULT 0,
    total_pdfs_descargados INT DEFAULT 0,
    estado_monitoreo ENUM('activo', 'pausado', 'omitido', 'archivado') DEFAULT 'activo',
    prioridad ENUM('alta', 'normal', 'baja') DEFAULT 'normal',
    INDEX idx_numero_normalizado (numero_normalizado),
    INDEX idx_estado_monitoreo (estado_monitoreo),
    INDEX idx_fecha_ultima_extraccion (fecha_ultima_extraccion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla maestra de expedientes sincronizada con expedientes_index.json';

-- ============================================================================
-- PASO 2: Agregar columna expediente_id a tabla actuaciones
-- ============================================================================

-- Nota: Ejecutar cada ALTER por separado si da error (la columna ya existe)

-- Agregar columna
ALTER TABLE actuaciones
    ADD COLUMN expediente_id INT DEFAULT NULL
    COMMENT 'FK a tabla expedientes' AFTER id;

-- Crear índice para la FK
CREATE INDEX idx_expediente_id ON actuaciones (expediente_id);

-- ============================================================================
-- PASO 3: Agregar columna expediente_id a tabla vencimientos
-- ============================================================================

ALTER TABLE vencimientos
    ADD COLUMN expediente_id INT DEFAULT NULL
    COMMENT 'FK a tabla expedientes' AFTER id;

CREATE INDEX idx_venc_expediente_id ON vencimientos (expediente_id);

-- ============================================================================
-- PASO 4: Agregar columna expediente_id a tabla procesamiento_estadisticas
-- ============================================================================

ALTER TABLE procesamiento_estadisticas
    ADD COLUMN expediente_id INT DEFAULT NULL
    COMMENT 'FK a tabla expedientes' AFTER id;

CREATE INDEX idx_stats_expediente_id ON procesamiento_estadisticas (expediente_id);

-- ============================================================================
-- PASO 5: Agregar UNIQUE constraints para deduplicación
-- ============================================================================

-- Vencimientos: evitar duplicados del mismo vencimiento
-- Un vencimiento se identifica por: expediente + actuación + tipo + fecha
CREATE UNIQUE INDEX uk_vencimiento_unico ON vencimientos
    (expediente_id, actuacion_id, tipo, fecha_vencimiento);

-- Estadísticas: solo un registro por expediente (el más reciente)
-- Esto se manejará con INSERT ON DUPLICATE KEY UPDATE
CREATE UNIQUE INDEX uk_stats_expediente ON procesamiento_estadisticas
    (expediente_id);

-- ============================================================================
-- PASO 6: Vista actualizada de vencimientos urgentes
-- ============================================================================

-- Reemplazar la vista existente para incluir datos del expediente
DROP VIEW IF EXISTS vencimientos_urgentes;

CREATE VIEW vencimientos_urgentes AS
SELECT
    v.id,
    v.expediente_id,
    v.expediente_numero,
    e.caratula,
    e.dependencia,
    v.actuacion_id,
    v.tipo,
    v.fecha_vencimiento,
    v.descripcion,
    v.estado,
    COALESCE(a.tipo, 'N/A') as actuacion_tipo,
    COALESCE(a.detalle, 'Sin detalle') as actuacion_detalle,
    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes,
    CASE
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) < 0 THEN 'vencido'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 3 THEN 'critico'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7 THEN 'urgente'
        ELSE 'normal'
    END as nivel_urgencia
FROM vencimientos v
LEFT JOIN expedientes e ON v.expediente_id = e.id
LEFT JOIN actuaciones a ON v.actuacion_id = a.id
WHERE v.estado = 'pendiente'
ORDER BY v.fecha_vencimiento ASC;

-- ============================================================================
-- PASO 7: Vista de resumen por expediente
-- ============================================================================

CREATE OR REPLACE VIEW resumen_expedientes AS
SELECT
    e.id,
    e.numero_normalizado,
    e.numero_original,
    e.dependencia,
    e.caratula,
    e.situacion,
    e.estado_monitoreo,
    e.prioridad,
    e.fecha_ultima_extraccion,
    e.total_actuaciones,
    (SELECT COUNT(*) FROM actuaciones a WHERE a.expediente_id = e.id AND a.utilidad = 'alta') as actuaciones_alta,
    (SELECT COUNT(*) FROM vencimientos v WHERE v.expediente_id = e.id AND v.estado = 'pendiente') as vencimientos_pendientes,
    (SELECT COUNT(*) FROM vencimientos v WHERE v.expediente_id = e.id
        AND v.estado = 'pendiente'
        AND DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7) as vencimientos_urgentes
FROM expedientes e;

-- ============================================================================
-- SCRIPT DE MIGRACIÓN DE DATOS (ejecutar después de crear expedientes)
-- ============================================================================

-- Después de sincronizar expedientes_index.json con la tabla expedientes,
-- ejecutar esto para actualizar las columnas expediente_id en las tablas existentes:

-- UPDATE actuaciones a
-- INNER JOIN expedientes e ON a.expediente_numero = e.numero_original
-- SET a.expediente_id = e.id
-- WHERE a.expediente_id IS NULL;

-- UPDATE vencimientos v
-- INNER JOIN expedientes e ON v.expediente_numero = e.numero_original
-- SET v.expediente_id = e.id
-- WHERE v.expediente_id IS NULL;

-- UPDATE procesamiento_estadisticas ps
-- INNER JOIN expedientes e ON ps.expediente_numero = e.numero_original
-- SET ps.expediente_id = e.id
-- WHERE ps.expediente_id IS NULL;
