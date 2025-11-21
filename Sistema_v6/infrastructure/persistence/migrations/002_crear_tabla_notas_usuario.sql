-- ============================================================================
-- Migracion 002: Crear tabla notas de usuario para analisis de actuaciones
-- ============================================================================
--
-- Esta migracion crea la tabla para almacenar notas y etiquetas personales
-- del usuario sobre las actuaciones de expedientes.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla usuario_actuaciones_notas
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuario_actuaciones_notas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'FK a tabla users',
    expediente_numero VARCHAR(100) NOT NULL COMMENT 'Numero del expediente',
    actuacion_indice INT NOT NULL COMMENT 'Indice de la actuacion',
    nota TEXT DEFAULT NULL COMMENT 'Nota personal del usuario',
    tags JSON DEFAULT NULL COMMENT 'Array de etiquetas personalizadas',
    destacado BOOLEAN DEFAULT FALSE COMMENT 'Actuacion destacada/anclada',
    oculto BOOLEAN DEFAULT FALSE COMMENT 'Actuacion ocultada por el usuario',
    color VARCHAR(20) DEFAULT NULL COMMENT 'Color de resaltado',
    orden_personalizado INT DEFAULT NULL COMMENT 'Orden personalizado',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraint: una nota por usuario/expediente/actuacion
    UNIQUE KEY uk_user_exp_act (user_id, expediente_numero, actuacion_indice),

    -- Indices para consultas frecuentes
    INDEX idx_user_expediente (user_id, expediente_numero),
    INDEX idx_destacado (user_id, destacado),
    INDEX idx_expediente_numero (expediente_numero)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Notas y analisis personales del usuario sobre actuaciones';

-- ============================================================================
-- PASO 2: Vista de actuaciones con notas del usuario
-- ============================================================================

CREATE OR REPLACE VIEW actuaciones_con_notas AS
SELECT
    a.id as actuacion_id,
    a.expediente_numero,
    a.tipo,
    a.detalle,
    a.fecha,
    a.utilidad,
    n.id as nota_id,
    n.user_id,
    n.nota,
    n.tags,
    n.destacado,
    n.oculto,
    n.color,
    n.orden_personalizado,
    n.updated_at as nota_updated_at
FROM actuaciones a
LEFT JOIN usuario_actuaciones_notas n ON
    a.expediente_numero = n.expediente_numero
    AND a.id = n.actuacion_indice;

-- ============================================================================
-- PASO 3: Trigger para validar datos JSON
-- ============================================================================

DELIMITER //

CREATE TRIGGER before_insert_notas
BEFORE INSERT ON usuario_actuaciones_notas
FOR EACH ROW
BEGIN
    -- Asegurar que tags sea un array JSON valido
    IF NEW.tags IS NOT NULL AND NOT JSON_VALID(NEW.tags) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'tags debe ser un JSON valido';
    END IF;
END//

CREATE TRIGGER before_update_notas
BEFORE UPDATE ON usuario_actuaciones_notas
FOR EACH ROW
BEGIN
    IF NEW.tags IS NOT NULL AND NOT JSON_VALID(NEW.tags) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'tags debe ser un JSON valido';
    END IF;
END//

DELIMITER ;
