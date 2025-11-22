-- Migración: Agregar campos para procesador_pdf
-- Fecha: 2025-11-18
-- Descripción: Agrega campos de clasificación, utilidad y tabla de vencimientos

-- ============================================
-- 1. Agregar campos a tabla actuaciones
-- ============================================

ALTER TABLE actuaciones
ADD COLUMN utilidad ENUM('nula', 'baja', 'media', 'alta') NULL COMMENT 'Utilidad jurídica clasificada por procesador_pdf',
ADD COLUMN score INT NULL COMMENT 'Score de clasificación (0-100)',
ADD COLUMN motivo_clasificacion TEXT NULL COMMENT 'Motivo de la clasificación',
ADD COLUMN requiere_pdf BOOLEAN DEFAULT FALSE COMMENT 'Indica si requiere revisión del PDF',
ADD COLUMN tiene_plazo_probable BOOLEAN DEFAULT FALSE COMMENT 'Indica si probablemente tiene plazo procesal',
ADD COLUMN es_duplicado_probable BOOLEAN DEFAULT FALSE COMMENT 'Indica si es probable duplicado',
ADD COLUMN keywords_detectados JSON NULL COMMENT 'Keywords jurídicos detectados',
ADD COLUMN fecha_clasificacion DATETIME NULL COMMENT 'Timestamp de cuándo fue clasificada',
ADD COLUMN texto_extraido LONGTEXT NULL COMMENT 'Texto extraído del PDF',
ADD COLUMN hash_contenido VARCHAR(64) NULL COMMENT 'Hash MD5 del contenido del PDF',
ADD INDEX idx_utilidad (utilidad),
ADD INDEX idx_score (score),
ADD INDEX idx_requiere_pdf (requiere_pdf),
ADD INDEX idx_tiene_plazo (tiene_plazo_probable);

-- ============================================
-- 2. Crear tabla de vencimientos
-- ============================================

CREATE TABLE IF NOT EXISTS vencimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_id INT NOT NULL,
    expediente_numero VARCHAR(100) NULL COMMENT 'Número de expediente (desnormalizado para queries)',
    tipo VARCHAR(50) NOT NULL COMMENT 'cedula_electronica, cedula_fisica, traslado, alegato, etc.',
    fecha_notificacion DATE NOT NULL COMMENT 'Fecha en que fue notificado',
    plazo_dias INT NOT NULL COMMENT 'Cantidad de días del plazo',
    fecha_vencimiento DATE NOT NULL COMMENT 'Fecha calculada de vencimiento',
    dias_habiles BOOLEAN DEFAULT TRUE COMMENT 'Si el plazo es en días hábiles',
    descripcion TEXT NULL COMMENT 'Descripción del vencimiento',
    texto_fuente TEXT NULL COMMENT 'Texto de donde se extrajo el vencimiento',
    confianza DECIMAL(3,2) DEFAULT 1.00 COMMENT 'Confianza de la detección (0.00-1.00)',
    estado ENUM('pendiente', 'atendido', 'vencido') DEFAULT 'pendiente' COMMENT 'Estado del vencimiento',
    fecha_atencion DATETIME NULL COMMENT 'Cuándo fue marcado como atendido',
    usuario_atencion VARCHAR(100) NULL COMMENT 'Usuario que lo marcó como atendido',
    notas TEXT NULL COMMENT 'Notas adicionales del usuario',
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE,

    INDEX idx_fecha_vencimiento (fecha_vencimiento),
    INDEX idx_estado (estado),
    INDEX idx_tipo (tipo),
    INDEX idx_expediente_numero (expediente_numero),
    INDEX idx_actuacion_id (actuacion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Vencimientos procesales detectados automáticamente';

-- ============================================
-- 3. Crear tabla de duplicados detectados
-- ============================================

CREATE TABLE IF NOT EXISTS duplicados_detectados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_original_id INT NOT NULL COMMENT 'ID de la actuación a conservar',
    actuacion_duplicada_id INT NOT NULL COMMENT 'ID de la actuación duplicada',
    tipo ENUM('exacto', 'semantico', 'parcial') NOT NULL COMMENT 'Tipo de duplicado',
    similitud DECIMAL(5,4) NOT NULL COMMENT 'Similitud entre 0.0000 y 1.0000',
    hash_normalizado VARCHAR(64) NULL COMMENT 'Hash del contenido normalizado',
    motivo TEXT NULL COMMENT 'Motivo de la detección',
    revisado BOOLEAN DEFAULT FALSE COMMENT 'Si fue revisado por usuario',
    confirmado BOOLEAN NULL COMMENT 'Si el usuario confirmó que es duplicado',
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    revisado_en DATETIME NULL,
    revisado_por VARCHAR(100) NULL,

    FOREIGN KEY (actuacion_original_id) REFERENCES actuaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (actuacion_duplicada_id) REFERENCES actuaciones(id) ON DELETE CASCADE,

    UNIQUE KEY unique_duplicado (actuacion_original_id, actuacion_duplicada_id),
    INDEX idx_tipo (tipo),
    INDEX idx_revisado (revisado),
    INDEX idx_confirmado (confirmado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Duplicados detectados por procesador_pdf';

-- ============================================
-- 4. Crear tabla de estadísticas de procesamiento
-- ============================================

CREATE TABLE IF NOT EXISTS procesamiento_estadisticas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expediente_numero VARCHAR(100) NOT NULL,
    fecha_procesamiento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_actuaciones INT NOT NULL,
    actuaciones_alta INT DEFAULT 0,
    actuaciones_media INT DEFAULT 0,
    actuaciones_baja INT DEFAULT 0,
    actuaciones_nula INT DEFAULT 0,
    reduccion_estimada_pct DECIMAL(5,2) NULL COMMENT 'Porcentaje de reducción de volumen',
    vencimientos_detectados INT DEFAULT 0,
    vencimientos_urgentes INT DEFAULT 0,
    duplicados_detectados INT DEFAULT 0,
    tiempo_procesamiento_seg DECIMAL(10,2) NULL COMMENT 'Tiempo que tardó el procesamiento',
    version_procesador VARCHAR(20) DEFAULT '1.0.0',

    INDEX idx_expediente (expediente_numero),
    INDEX idx_fecha (fecha_procesamiento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Estadísticas de procesamiento por expediente';

-- ============================================
-- 5. Crear vistas útiles
-- ============================================

-- Vista de vencimientos urgentes (próximos 7 días)
CREATE OR REPLACE VIEW vencimientos_urgentes AS
SELECT
    v.*,
    a.tipo AS actuacion_tipo,
    a.detalle AS actuacion_detalle,
    DATEDIFF(v.fecha_vencimiento, CURDATE()) AS dias_restantes,
    CASE
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 0 THEN 'vencido'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 1 THEN 'critico'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 3 THEN 'urgente'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7 THEN 'proximo'
        ELSE 'normal'
    END AS nivel_urgencia
FROM vencimientos v
JOIN actuaciones a ON v.actuacion_id = a.id
WHERE v.estado = 'pendiente'
  AND DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7
ORDER BY v.fecha_vencimiento ASC;

-- Vista de actuaciones de alta utilidad
CREATE OR REPLACE VIEW actuaciones_alta_utilidad AS
SELECT
    a.*,
    v.fecha_vencimiento,
    v.dias_restantes,
    CASE WHEN v.id IS NOT NULL THEN TRUE ELSE FALSE END AS tiene_vencimiento
FROM actuaciones a
LEFT JOIN (
    SELECT actuacion_id, MIN(fecha_vencimiento) AS fecha_vencimiento,
           DATEDIFF(MIN(fecha_vencimiento), CURDATE()) AS dias_restantes
    FROM vencimientos
    WHERE estado = 'pendiente'
    GROUP BY actuacion_id
) v ON a.id = v.actuacion_id
WHERE a.utilidad IN ('alta', 'media')
ORDER BY
    CASE a.utilidad
        WHEN 'alta' THEN 1
        WHEN 'media' THEN 2
    END,
    v.fecha_vencimiento ASC NULLS LAST;

-- ============================================
-- 6. Comentarios y documentación
-- ============================================

-- Comentarios en tablas
ALTER TABLE vencimientos COMMENT = 'Vencimientos procesales detectados automáticamente por procesador_pdf. Incluye cédulas, traslados, alegatos, etc.';
ALTER TABLE duplicados_detectados COMMENT = 'Duplicados detectados por procesador_pdf usando hash MD5 y normalización de contenido';

-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================
-- Para aplicar: mysql -u usuario -p nombre_db < 001_add_procesador_pdf_fields.sql
-- Para revertir: Ver archivo 001_add_procesador_pdf_fields_rollback.sql
