-- ============================================================================
-- Migracion 003: Crear tablas para modulo Agenda
-- ============================================================================
--
-- Esta migracion crea las tablas para gestionar eventos, tareas y recordatorios
-- del usuario relacionados con expedientes y vencimientos.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla agenda_eventos
-- ============================================================================

CREATE TABLE IF NOT EXISTS agenda_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'FK a tabla users',
    titulo VARCHAR(255) NOT NULL COMMENT 'Titulo del evento',
    descripcion TEXT DEFAULT NULL COMMENT 'Descripcion detallada',
    fecha_inicio DATETIME NOT NULL COMMENT 'Fecha y hora de inicio',
    fecha_fin DATETIME DEFAULT NULL COMMENT 'Fecha y hora de fin',
    todo_el_dia BOOLEAN DEFAULT FALSE COMMENT 'Es evento de todo el dia',
    tipo ENUM('vencimiento', 'audiencia', 'tarea', 'recordatorio', 'otro') NOT NULL DEFAULT 'otro' COMMENT 'Tipo de evento',
    prioridad ENUM('baja', 'media', 'alta', 'urgente') DEFAULT 'media' COMMENT 'Nivel de prioridad',
    estado ENUM('pendiente', 'en_progreso', 'completado', 'cancelado') DEFAULT 'pendiente' COMMENT 'Estado del evento',
    expediente_numero VARCHAR(100) DEFAULT NULL COMMENT 'Expediente relacionado',
    actuacion_indice INT DEFAULT NULL COMMENT 'Actuacion relacionada',
    color VARCHAR(20) DEFAULT NULL COMMENT 'Color para visualizacion',
    recordatorio_minutos INT DEFAULT NULL COMMENT 'Minutos antes para recordatorio',
    notas TEXT DEFAULT NULL COMMENT 'Notas adicionales',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indices para consultas frecuentes
    INDEX idx_user_fecha (user_id, fecha_inicio),
    INDEX idx_user_tipo (user_id, tipo),
    INDEX idx_user_estado (user_id, estado),
    INDEX idx_expediente (expediente_numero),
    INDEX idx_fecha_rango (fecha_inicio, fecha_fin)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Eventos y tareas de agenda del usuario';

-- ============================================================================
-- PASO 2: Crear tabla agenda_etiquetas
-- ============================================================================

CREATE TABLE IF NOT EXISTS agenda_etiquetas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'FK a tabla users',
    nombre VARCHAR(50) NOT NULL COMMENT 'Nombre de la etiqueta',
    color VARCHAR(20) DEFAULT '#3B82F6' COMMENT 'Color de la etiqueta',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_user_nombre (user_id, nombre),
    INDEX idx_user (user_id)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Etiquetas personalizadas para eventos';

-- ============================================================================
-- PASO 3: Crear tabla relacion evento-etiquetas
-- ============================================================================

CREATE TABLE IF NOT EXISTS agenda_evento_etiquetas (
    evento_id INT NOT NULL,
    etiqueta_id INT NOT NULL,

    PRIMARY KEY (evento_id, etiqueta_id),
    FOREIGN KEY (evento_id) REFERENCES agenda_eventos(id) ON DELETE CASCADE,
    FOREIGN KEY (etiqueta_id) REFERENCES agenda_etiquetas(id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relacion muchos a muchos entre eventos y etiquetas';

-- ============================================================================
-- PASO 4: Vista de eventos con informacion completa
-- ============================================================================

CREATE OR REPLACE VIEW agenda_eventos_completos AS
SELECT
    e.id,
    e.user_id,
    e.titulo,
    e.descripcion,
    e.fecha_inicio,
    e.fecha_fin,
    e.todo_el_dia,
    e.tipo,
    e.prioridad,
    e.estado,
    e.expediente_numero,
    e.actuacion_indice,
    e.color,
    e.recordatorio_minutos,
    e.notas,
    e.created_at,
    e.updated_at,
    CASE
        WHEN e.fecha_inicio < NOW() AND e.estado = 'pendiente' THEN 'vencido'
        WHEN e.fecha_inicio <= DATE_ADD(NOW(), INTERVAL 1 DAY) AND e.estado = 'pendiente' THEN 'proximo'
        ELSE 'futuro'
    END as urgencia,
    DATEDIFF(e.fecha_inicio, NOW()) as dias_restantes
FROM agenda_eventos e;

-- ============================================================================
-- PASO 5: Insertar etiquetas predeterminadas (se ejecuta por cada usuario)
-- ============================================================================

-- Nota: Las etiquetas predeterminadas se crean cuando el usuario
-- accede por primera vez al modulo de agenda

