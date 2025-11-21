-- ============================================================================
-- Migración 005: Agregar columna texto_json a actuaciones
-- ============================================================================
--
-- Esta migración agrega soporte para almacenar texto estructurado extraído
-- de los PDFs de las actuaciones en formato JSON optimizado para IA.
--
-- Estructura del JSON:
-- {
--   "texto_completo": "string",          // Texto completo concatenado
--   "texto_normalizado": "string",       // Texto limpio para búsquedas
--   "texto_por_pagina": [                // Texto separado por página
--     {"pagina": 1, "contenido": "...", "tipo": "texto|imagen|mixto|tabla"}
--   ],
--   "metadata": {
--     "metodo_extraccion": "pypdf2|pdfplumber|ocr",
--     "total_paginas": int,
--     "total_caracteres": int,
--     "tiene_tablas": bool,
--     "tiene_imagenes": bool,
--     "requirio_ocr": bool,
--     "confianza_ocr": float,
--     "fecha_extraccion": "datetime"
--   },
--   "preview": "string"                  // Primeros 500 caracteres
-- }
-- ============================================================================

-- ============================================================================
-- PASO 1: Agregar columna texto_json a tabla actuaciones
-- ============================================================================

ALTER TABLE actuaciones
    ADD COLUMN texto_json JSON DEFAULT NULL
    COMMENT 'Texto estructurado extraído del PDF en formato JSON'
    AFTER hash_contenido;

-- ============================================================================
-- PASO 2: Agregar columna para indicar si tiene texto extraído
-- ============================================================================

ALTER TABLE actuaciones
    ADD COLUMN tiene_texto_extraido TINYINT(1) DEFAULT 0
    COMMENT 'Indica si se ha extraído texto del PDF'
    AFTER texto_json;

-- ============================================================================
-- PASO 3: Agregar columna para método de extracción usado
-- ============================================================================

ALTER TABLE actuaciones
    ADD COLUMN metodo_extraccion VARCHAR(50) DEFAULT NULL
    COMMENT 'Método usado: pypdf2, pdfplumber, ocr, mixto'
    AFTER tiene_texto_extraido;

-- ============================================================================
-- PASO 4: Agregar índices para búsqueda
-- ============================================================================

-- Índice para filtrar actuaciones con texto extraído
CREATE INDEX idx_tiene_texto ON actuaciones (tiene_texto_extraido);

-- Índice para el método de extracción
CREATE INDEX idx_metodo_extraccion ON actuaciones (metodo_extraccion);

-- ============================================================================
-- PASO 5: Crear tabla auxiliar para búsqueda de texto (opcional, para RAG)
-- ============================================================================

CREATE TABLE IF NOT EXISTS actuaciones_texto_fts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    actuacion_id INT NOT NULL,
    expediente_id INT DEFAULT NULL,
    expediente_numero VARCHAR(100) NOT NULL,
    texto_completo LONGTEXT NOT NULL,
    texto_normalizado LONGTEXT NOT NULL,
    fecha_extraccion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE,
    INDEX idx_fts_expediente (expediente_id),
    INDEX idx_fts_expediente_numero (expediente_numero),
    FULLTEXT INDEX ft_texto_completo (texto_completo),
    FULLTEXT INDEX ft_texto_normalizado (texto_normalizado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla auxiliar para búsqueda full-text de textos extraídos';

-- ============================================================================
-- PASO 6: Vista de actuaciones con texto disponible
-- ============================================================================

CREATE OR REPLACE VIEW actuaciones_con_texto AS
SELECT
    a.id,
    a.expediente_id,
    a.expediente_numero,
    a.indice,
    a.tipo,
    a.fecha,
    a.nombre_archivo,
    a.tiene_texto_extraido,
    a.metodo_extraccion,
    JSON_EXTRACT(a.texto_json, '$.metadata.total_caracteres') as total_caracteres,
    JSON_EXTRACT(a.texto_json, '$.metadata.total_paginas') as total_paginas,
    JSON_EXTRACT(a.texto_json, '$.preview') as preview_texto,
    e.caratula,
    e.dependencia
FROM actuaciones a
LEFT JOIN expedientes e ON a.expediente_id = e.id
WHERE a.tiene_texto_extraido = 1;

-- ============================================================================
-- NOTAS DE USO
-- ============================================================================
--
-- Para actualizar el texto extraído de una actuación:
--
-- UPDATE actuaciones SET
--     texto_json = '{"texto_completo": "...", ...}',
--     tiene_texto_extraido = 1,
--     metodo_extraccion = 'pypdf2'
-- WHERE id = ?;
--
-- Para buscar texto en actuaciones (usando tabla FTS):
--
-- SELECT * FROM actuaciones_texto_fts
-- WHERE MATCH(texto_completo) AGAINST('término de búsqueda' IN NATURAL LANGUAGE MODE);
--
-- Para obtener preview de textos:
--
-- SELECT
--     id,
--     expediente_numero,
--     JSON_EXTRACT(texto_json, '$.preview') as preview
-- FROM actuaciones
-- WHERE tiene_texto_extraido = 1;
--
-- ============================================================================
