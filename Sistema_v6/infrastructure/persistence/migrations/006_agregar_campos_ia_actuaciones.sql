-- ============================================================================
-- Migración 006: Agregar campos de clasificación IA a actuaciones
-- ============================================================================
--
-- Esta migración agrega campos para almacenar la clasificación generada por
-- el LLM (tipo_ia, confianza_ia, justificacion_ia, metodo_ia)
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Agregar columnas de clasificación IA
-- ============================================================================

ALTER TABLE actuaciones
    ADD COLUMN tipo_ia VARCHAR(100) DEFAULT NULL
    COMMENT 'Tipo de actuación clasificado por IA/LLM';

ALTER TABLE actuaciones
    ADD COLUMN confianza_ia FLOAT DEFAULT NULL
    COMMENT 'Confianza de la clasificación IA (0-1)';

ALTER TABLE actuaciones
    ADD COLUMN justificacion_ia TEXT DEFAULT NULL
    COMMENT 'Justificación de la clasificación IA';

ALTER TABLE actuaciones
    ADD COLUMN metodo_ia VARCHAR(50) DEFAULT NULL
    COMMENT 'Método usado: llm, reglas, hibrido';

ALTER TABLE actuaciones
    ADD COLUMN fecha_clasificacion_ia DATETIME DEFAULT NULL
    COMMENT 'Fecha de la clasificación IA';

ALTER TABLE actuaciones
    ADD COLUMN indexado_rag BOOLEAN DEFAULT FALSE
    COMMENT 'Si la actuación fue indexada en ChromaDB';

-- ============================================================================
-- PASO 2: Crear índice para búsqueda por tipo IA
-- ============================================================================

CREATE INDEX idx_tipo_ia ON actuaciones (tipo_ia);
CREATE INDEX idx_indexado_rag ON actuaciones (indexado_rag);

-- ============================================================================
-- PASO 3: Vista de actuaciones con clasificación IA
-- ============================================================================

CREATE OR REPLACE VIEW actuaciones_con_ia AS
SELECT
    a.id,
    a.expediente_id,
    a.expediente_numero,
    a.tipo,
    a.detalle,
    a.utilidad,
    a.score,
    a.tipo_ia,
    a.confianza_ia,
    a.justificacion_ia,
    a.metodo_ia,
    a.fecha_clasificacion_ia,
    a.indexado_rag,
    a.tiene_texto_extraido,
    CASE
        WHEN a.tipo_ia IS NOT NULL THEN 'clasificado'
        WHEN a.tiene_texto_extraido = TRUE THEN 'pendiente'
        ELSE 'sin_texto'
    END as estado_ia
FROM actuaciones a;
