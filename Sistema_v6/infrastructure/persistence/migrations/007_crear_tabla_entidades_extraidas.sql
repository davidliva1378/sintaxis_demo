-- ============================================================================
-- Migración 007: Crear tabla para entidades extraídas (NER)
-- ============================================================================
--
-- Esta migración crea la tabla para almacenar entidades extraídas por IA
-- (GLiNER) o agregadas manualmente por el usuario.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla entidades_extraidas
-- ============================================================================

CREATE TABLE IF NOT EXISTS entidades_extraidas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expediente_numero VARCHAR(50) NOT NULL,
    actuacion_id INT DEFAULT NULL,
    entity_type VARCHAR(50) NOT NULL
        COMMENT 'Tipo de entidad: PERSONA, MONTO, FECHA, NORMA, DECRETO, CONCEPTO, etc.',
    entity_value TEXT NOT NULL
        COMMENT 'Valor de la entidad extraída',
    score DECIMAL(5,4) DEFAULT NULL
        COMMENT 'Confianza de la extracción IA (0-1), NULL para manuales',
    start_pos INT DEFAULT NULL
        COMMENT 'Posición inicio en texto (para IA)',
    end_pos INT DEFAULT NULL
        COMMENT 'Posición fin en texto (para IA)',
    origen ENUM('ia', 'manual') DEFAULT 'ia'
        COMMENT 'Origen de la entidad: IA automático o manual',
    usuario_id INT DEFAULT NULL
        COMMENT 'ID usuario que agregó/modificó (NULL para IA)',
    notas TEXT DEFAULT NULL
        COMMENT 'Notas adicionales del usuario',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Índices
    INDEX idx_expediente_numero (expediente_numero),
    INDEX idx_actuacion_id (actuacion_id),
    INDEX idx_entity_type (entity_type),
    INDEX idx_origen (origen),
    INDEX idx_fecha_creacion (fecha_creacion),

    -- Foreign keys
    CONSTRAINT fk_entidades_expediente
        FOREIGN KEY (expediente_numero)
        REFERENCES expedientes(numero_normalizado)
        ON DELETE CASCADE,
    CONSTRAINT fk_entidades_actuacion
        FOREIGN KEY (actuacion_id)
        REFERENCES actuaciones(id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- PASO 2: Crear vista para estadísticas de entidades
-- ============================================================================

CREATE OR REPLACE VIEW estadisticas_entidades AS
SELECT
    expediente_numero,
    entity_type,
    COUNT(*) as total,
    SUM(CASE WHEN origen = 'ia' THEN 1 ELSE 0 END) as por_ia,
    SUM(CASE WHEN origen = 'manual' THEN 1 ELSE 0 END) as manuales,
    AVG(CASE WHEN origen = 'ia' THEN score ELSE NULL END) as avg_score_ia
FROM entidades_extraidas
GROUP BY expediente_numero, entity_type;

-- ============================================================================
-- PASO 3: Crear índice full-text para búsqueda en valores
-- ============================================================================

ALTER TABLE entidades_extraidas
    ADD FULLTEXT INDEX idx_entity_value_fulltext (entity_value);
