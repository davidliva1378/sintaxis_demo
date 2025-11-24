-- ============================================================================
-- Migracion 009: Crear tablas para modulo Monitoreo Universal
-- ============================================================================
--
-- Esta migracion crea las tablas para el sistema de monitoreo automatizado
-- de expedientes judiciales con deteccion de cambios.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Crear tabla monitoreo_configuracion
-- ============================================================================

CREATE TABLE IF NOT EXISTS monitoreo_configuracion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL COMMENT 'FK a tabla users',
    activo BOOLEAN DEFAULT TRUE COMMENT 'Si el monitoreo esta activo',
    frecuencia ENUM('5min', '15min', '30min', '1hora', '3horas', '6horas', '12horas', '24horas')
        DEFAULT '1hora' COMMENT 'Frecuencia de verificacion',
    notificar_email BOOLEAN DEFAULT FALSE COMMENT 'Enviar notificaciones por email',
    notificar_sistema BOOLEAN DEFAULT TRUE COMMENT 'Mostrar notificaciones en sistema',
    hora_inicio TIME DEFAULT NULL COMMENT 'Hora inicio ventana de monitoreo (HH:MM:SS)',
    hora_fin TIME DEFAULT NULL COMMENT 'Hora fin ventana de monitoreo (HH:MM:SS)',
    dias_semana JSON DEFAULT NULL COMMENT 'Dias habilitados [0-6] donde 0=domingo',
    ultima_ejecucion DATETIME DEFAULT NULL COMMENT 'Ultima ejecucion del monitoreo',
    proxima_ejecucion DATETIME DEFAULT NULL COMMENT 'Proxima ejecucion programada',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Un usuario solo puede tener una configuracion
    UNIQUE KEY uk_usuario (usuario_id),
    INDEX idx_activo (activo),
    INDEX idx_proxima_ejecucion (proxima_ejecucion)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Configuracion global de monitoreo por usuario';

-- ============================================================================
-- PASO 2: Crear tabla expedientes_monitoreados
-- ============================================================================

CREATE TABLE IF NOT EXISTS expedientes_monitoreados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL COMMENT 'FK a tabla users',
    expediente_numero VARCHAR(100) NOT NULL COMMENT 'Numero del expediente',
    expediente_caratula VARCHAR(500) DEFAULT NULL COMMENT 'Caratula del expediente',
    expediente_dependencia VARCHAR(255) DEFAULT NULL COMMENT 'Dependencia/Juzgado',
    activo BOOLEAN DEFAULT TRUE COMMENT 'Si el monitoreo esta activo para este expediente',
    ultima_verificacion DATETIME DEFAULT NULL COMMENT 'Ultima vez que se verifico',
    ultima_actuacion_fecha DATETIME DEFAULT NULL COMMENT 'Fecha de la ultima actuacion conocida',
    ultima_actuacion_id INT DEFAULT NULL COMMENT 'ID de la ultima actuacion conocida',
    total_cambios_detectados INT DEFAULT 0 COMMENT 'Total de cambios detectados',
    notas TEXT DEFAULT NULL COMMENT 'Notas del usuario sobre el expediente',
    prioridad ENUM('baja', 'media', 'alta') DEFAULT 'media' COMMENT 'Prioridad de monitoreo',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Un usuario no puede monitorear el mismo expediente dos veces
    UNIQUE KEY uk_usuario_expediente (usuario_id, expediente_numero),
    INDEX idx_usuario_activo (usuario_id, activo),
    INDEX idx_ultima_verificacion (ultima_verificacion),
    INDEX idx_expediente (expediente_numero)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Expedientes bajo monitoreo por usuario';

-- ============================================================================
-- PASO 3: Crear tabla cambios_detectados
-- ============================================================================

CREATE TABLE IF NOT EXISTS cambios_detectados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expediente_monitoreado_id INT NOT NULL COMMENT 'FK a expedientes_monitoreados',
    expediente_numero VARCHAR(100) NOT NULL COMMENT 'Numero expediente (desnormalizado)',
    expediente_caratula VARCHAR(500) DEFAULT NULL COMMENT 'Caratula (desnormalizado)',
    tipo_cambio ENUM('nueva_actuacion', 'cambio_estado', 'nuevo_archivo', 'modificacion', 'otro')
        NOT NULL COMMENT 'Tipo de cambio detectado',
    descripcion TEXT NOT NULL COMMENT 'Descripcion del cambio',
    detalles JSON DEFAULT NULL COMMENT 'Detalles adicionales en JSON',
    notificado BOOLEAN DEFAULT FALSE COMMENT 'Si ya se notifico al usuario',
    leido BOOLEAN DEFAULT FALSE COMMENT 'Si el usuario ya lo leyo',
    fecha_deteccion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Cuando se detecto el cambio',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key a expedientes_monitoreados
    CONSTRAINT fk_cambios_expediente
        FOREIGN KEY (expediente_monitoreado_id)
        REFERENCES expedientes_monitoreados(id)
        ON DELETE CASCADE,

    INDEX idx_expediente_monitoreado (expediente_monitoreado_id),
    INDEX idx_fecha_deteccion (fecha_deteccion),
    INDEX idx_leido (leido),
    INDEX idx_notificado (notificado),
    INDEX idx_tipo_cambio (tipo_cambio)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cambios detectados en expedientes monitoreados';

-- ============================================================================
-- PASO 4: Vista de cambios con informacion completa
-- ============================================================================

CREATE OR REPLACE VIEW cambios_detectados_completos AS
SELECT
    c.id,
    c.expediente_monitoreado_id,
    c.expediente_numero,
    c.expediente_caratula,
    c.tipo_cambio,
    c.descripcion,
    c.detalles,
    c.notificado,
    c.leido,
    c.fecha_deteccion,
    c.created_at,
    em.usuario_id,
    em.activo as expediente_activo,
    em.prioridad
FROM cambios_detectados c
INNER JOIN expedientes_monitoreados em ON c.expediente_monitoreado_id = em.id;

-- ============================================================================
-- PASO 5: Vista de estadisticas de monitoreo por usuario
-- ============================================================================

CREATE OR REPLACE VIEW monitoreo_estadisticas AS
SELECT
    em.usuario_id,
    COUNT(em.id) as total_expedientes,
    SUM(CASE WHEN em.activo = TRUE THEN 1 ELSE 0 END) as expedientes_activos,
    SUM(CASE WHEN em.activo = FALSE THEN 1 ELSE 0 END) as expedientes_pausados,
    (SELECT COUNT(*) FROM cambios_detectados cd
     INNER JOIN expedientes_monitoreados em2 ON cd.expediente_monitoreado_id = em2.id
     WHERE em2.usuario_id = em.usuario_id
     AND DATE(cd.fecha_deteccion) = CURDATE()) as cambios_hoy,
    (SELECT COUNT(*) FROM cambios_detectados cd
     INNER JOIN expedientes_monitoreados em2 ON cd.expediente_monitoreado_id = em2.id
     WHERE em2.usuario_id = em.usuario_id
     AND cd.fecha_deteccion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)) as cambios_semana,
    (SELECT COUNT(*) FROM cambios_detectados cd
     INNER JOIN expedientes_monitoreados em2 ON cd.expediente_monitoreado_id = em2.id
     WHERE em2.usuario_id = em.usuario_id
     AND cd.fecha_deteccion >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as cambios_mes,
    (SELECT COUNT(*) FROM cambios_detectados cd
     INNER JOIN expedientes_monitoreados em2 ON cd.expediente_monitoreado_id = em2.id
     WHERE em2.usuario_id = em.usuario_id
     AND cd.leido = FALSE) as cambios_sin_leer,
    mc.ultima_ejecucion,
    mc.proxima_ejecucion
FROM expedientes_monitoreados em
LEFT JOIN monitoreo_configuracion mc ON em.usuario_id = mc.usuario_id
GROUP BY em.usuario_id, mc.ultima_ejecucion, mc.proxima_ejecucion;

-- ============================================================================
-- PASO 6: Indices adicionales para rendimiento
-- ============================================================================

-- Indice para busqueda rapida de cambios no leidos por usuario
CREATE INDEX idx_cambios_usuario_no_leido ON cambios_detectados (
    expediente_monitoreado_id,
    leido,
    fecha_deteccion DESC
);

-- ============================================================================
-- PASO 7: Insertar configuracion predeterminada (se crea con primer uso)
-- ============================================================================

-- Nota: La configuracion predeterminada se crea automaticamente cuando
-- el usuario accede por primera vez al modulo de monitoreo.

