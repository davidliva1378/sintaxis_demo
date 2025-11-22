-- ============================================================================
-- Migracion 008: Crear tabla para tipos de entidad personalizados
-- ============================================================================
--
-- Esta migracion crea la tabla para almacenar tipos de entidad custom
-- que el usuario puede agregar ademas de los predefinidos.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla tipos_entidad_custom
-- ============================================================================

CREATE TABLE IF NOT EXISTS tipos_entidad_custom (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
        COMMENT 'Nombre del tipo en mayusculas (ej: ACTOR, DEMANDADO)',
    descripcion VARCHAR(200) DEFAULT NULL
        COMMENT 'Descripcion del tipo de entidad',
    color VARCHAR(20) DEFAULT 'gray'
        COMMENT 'Color para mostrar en UI (ej: blue, red, green)',
    es_predefinido BOOLEAN DEFAULT FALSE
        COMMENT 'TRUE si es un tipo predefinido del sistema',
    activo BOOLEAN DEFAULT TRUE
        COMMENT 'Si el tipo esta activo para uso',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indices
    INDEX idx_nombre (nombre),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- PASO 2: Insertar tipos predefinidos
-- ============================================================================

INSERT INTO tipos_entidad_custom (nombre, descripcion, color, es_predefinido) VALUES
    ('PERSONA', 'Nombres de personas en general', 'blue', TRUE),
    ('ORGANIZACION', 'Empresas, instituciones, organizaciones', 'purple', TRUE),
    ('TRIBUNAL', 'Juzgados, camaras, tribunales', 'indigo', TRUE),
    ('JUEZ', 'Nombre del juez o magistrado', 'cyan', TRUE),
    ('ABOGADO', 'Letrados, apoderados', 'teal', TRUE),
    ('FECHA', 'Fechas relevantes', 'orange', TRUE),
    ('MONTO', 'Cantidades de dinero', 'green', TRUE),
    ('NORMA', 'Leyes, articulos, codigos', 'red', TRUE),
    ('PLAZO', 'Periodos de tiempo', 'yellow', TRUE),
    ('EXPEDIENTE', 'Referencias a otros expedientes', 'gray', TRUE),
    ('DOMICILIO', 'Direcciones, domicilios', 'pink', TRUE),
    ('DECRETO', 'Decretos, resoluciones', 'amber', TRUE),
    ('CONCEPTO', 'Conceptos juridicos', 'lime', TRUE),
    ('ACTOR', 'Parte demandante/actora', 'blue', TRUE),
    ('DEMANDADO', 'Parte demandada', 'red', TRUE),
    ('TERCERO', 'Terceros citados en el proceso', 'violet', TRUE),
    ('PERITO', 'Peritos designados', 'emerald', TRUE),
    ('TESTIGO', 'Testigos del proceso', 'sky', TRUE)
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);
