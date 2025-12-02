-- ============================================================================
-- Migracion 014: Crear tabla para gestión dinámica de feriados
-- ============================================================================
--
-- Esta migracion crea la tabla para almacenar feriados de forma dinámica,
-- permitiendo actualizar el calendario sin modificar código.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla feriados
-- ============================================================================

CREATE TABLE IF NOT EXISTS feriados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL COMMENT 'Fecha del feriado',
    nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del feriado',
    tipo ENUM('nacional', 'judicial', 'provincial', 'feria_judicial') NOT NULL DEFAULT 'nacional' COMMENT 'Tipo de feriado',
    es_trasladable BOOLEAN DEFAULT FALSE COMMENT 'Si el feriado es trasladable',
    año INT GENERATED ALWAYS AS (YEAR(fecha)) STORED COMMENT 'Año del feriado (calculado)',
    activo BOOLEAN DEFAULT TRUE COMMENT 'Si el feriado está activo',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Índices
    UNIQUE KEY uk_fecha (fecha),
    INDEX idx_año (año),
    INDEX idx_tipo (tipo),
    INDEX idx_fecha_activo (fecha, activo)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Feriados nacionales, judiciales y provinciales';

-- ============================================================================
-- PASO 2: Crear tabla feria_judicial (períodos de feria)
-- ============================================================================

CREATE TABLE IF NOT EXISTS feria_judicial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    año INT NOT NULL COMMENT 'Año de la feria',
    fecha_inicio DATE NOT NULL COMMENT 'Fecha de inicio de feria',
    fecha_fin DATE NOT NULL COMMENT 'Fecha de fin de feria',
    nombre VARCHAR(100) DEFAULT 'Feria Judicial de Verano' COMMENT 'Nombre del período',
    activo BOOLEAN DEFAULT TRUE COMMENT 'Si está activo',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_año (año),
    INDEX idx_fechas (fecha_inicio, fecha_fin)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Períodos de feria judicial';

-- ============================================================================
-- PASO 3: Insertar feriados 2024
-- ============================================================================

INSERT IGNORE INTO feriados (fecha, nombre, tipo, es_trasladable) VALUES
('2024-01-01', 'Año Nuevo', 'nacional', FALSE),
('2024-02-12', 'Carnaval', 'nacional', FALSE),
('2024-02-13', 'Carnaval', 'nacional', FALSE),
('2024-03-24', 'Día Nacional de la Memoria', 'nacional', FALSE),
('2024-03-29', 'Viernes Santo', 'nacional', FALSE),
('2024-04-02', 'Día del Veterano y Caídos de Malvinas', 'nacional', FALSE),
('2024-05-01', 'Día del Trabajador', 'nacional', FALSE),
('2024-05-25', 'Día de la Revolución de Mayo', 'nacional', FALSE),
('2024-06-17', 'Paso a la Inmortalidad de Güemes', 'nacional', TRUE),
('2024-06-20', 'Día de la Bandera', 'nacional', FALSE),
('2024-07-09', 'Día de la Independencia', 'nacional', FALSE),
('2024-08-17', 'Paso a la Inmortalidad de San Martín', 'nacional', TRUE),
('2024-10-12', 'Día del Respeto a la Diversidad Cultural', 'nacional', TRUE),
('2024-11-18', 'Día de la Soberanía Nacional', 'nacional', TRUE),
('2024-12-08', 'Día de la Inmaculada Concepción', 'nacional', FALSE),
('2024-12-25', 'Navidad', 'nacional', FALSE);

-- ============================================================================
-- PASO 4: Insertar feriados 2025
-- ============================================================================

INSERT IGNORE INTO feriados (fecha, nombre, tipo, es_trasladable) VALUES
('2025-01-01', 'Año Nuevo', 'nacional', FALSE),
('2025-03-03', 'Carnaval', 'nacional', FALSE),
('2025-03-04', 'Carnaval', 'nacional', FALSE),
('2025-03-24', 'Día Nacional de la Memoria', 'nacional', FALSE),
('2025-04-02', 'Día del Veterano y Caídos de Malvinas', 'nacional', FALSE),
('2025-04-18', 'Viernes Santo', 'nacional', FALSE),
('2025-05-01', 'Día del Trabajador', 'nacional', FALSE),
('2025-05-25', 'Día de la Revolución de Mayo', 'nacional', FALSE),
('2025-06-16', 'Paso a la Inmortalidad de Güemes', 'nacional', TRUE),
('2025-06-20', 'Día de la Bandera', 'nacional', FALSE),
('2025-07-09', 'Día de la Independencia', 'nacional', FALSE),
('2025-08-17', 'Paso a la Inmortalidad de San Martín', 'nacional', FALSE),
('2025-10-12', 'Día del Respeto a la Diversidad Cultural', 'nacional', TRUE),
('2025-11-24', 'Día de la Soberanía Nacional', 'nacional', TRUE),
('2025-12-08', 'Día de la Inmaculada Concepción', 'nacional', FALSE),
('2025-12-25', 'Navidad', 'nacional', FALSE);

-- ============================================================================
-- PASO 5: Insertar feriados 2026 (estimados, ajustar según calendario oficial)
-- ============================================================================

INSERT IGNORE INTO feriados (fecha, nombre, tipo, es_trasladable) VALUES
('2026-01-01', 'Año Nuevo', 'nacional', FALSE),
('2026-02-16', 'Carnaval', 'nacional', FALSE),
('2026-02-17', 'Carnaval', 'nacional', FALSE),
('2026-03-24', 'Día Nacional de la Memoria', 'nacional', FALSE),
('2026-04-02', 'Día del Veterano y Caídos de Malvinas', 'nacional', FALSE),
('2026-04-03', 'Viernes Santo', 'nacional', FALSE),
('2026-05-01', 'Día del Trabajador', 'nacional', FALSE),
('2026-05-25', 'Día de la Revolución de Mayo', 'nacional', FALSE),
('2026-06-15', 'Paso a la Inmortalidad de Güemes', 'nacional', TRUE),
('2026-06-20', 'Día de la Bandera', 'nacional', FALSE),
('2026-07-09', 'Día de la Independencia', 'nacional', FALSE),
('2026-08-17', 'Paso a la Inmortalidad de San Martín', 'nacional', FALSE),
('2026-10-12', 'Día del Respeto a la Diversidad Cultural', 'nacional', TRUE),
('2026-11-23', 'Día de la Soberanía Nacional', 'nacional', TRUE),
('2026-12-08', 'Día de la Inmaculada Concepción', 'nacional', FALSE),
('2026-12-25', 'Navidad', 'nacional', FALSE);

-- ============================================================================
-- PASO 6: Insertar períodos de feria judicial
-- ============================================================================

INSERT IGNORE INTO feria_judicial (año, fecha_inicio, fecha_fin, nombre) VALUES
(2024, '2024-01-01', '2024-02-29', 'Feria Judicial de Verano 2024'),
(2025, '2025-01-01', '2025-02-28', 'Feria Judicial de Verano 2025'),
(2026, '2026-01-01', '2026-02-28', 'Feria Judicial de Verano 2026');

-- ============================================================================
-- PASO 7: Vista de feriados con información adicional
-- ============================================================================

CREATE OR REPLACE VIEW feriados_calendario AS
SELECT
    f.id,
    f.fecha,
    f.nombre,
    f.tipo,
    f.es_trasladable,
    f.año,
    DAYNAME(f.fecha) as dia_semana,
    CASE
        WHEN DAYOFWEEK(f.fecha) IN (1, 7) THEN 'fin_semana'
        ELSE 'laboral'
    END as tipo_dia,
    f.activo
FROM feriados f
WHERE f.activo = TRUE
ORDER BY f.fecha;
