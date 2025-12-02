-- ============================================================================
-- Migración 015: Crear tablas para sistema de alertas de vencimientos
-- Fecha: 2025-12-01
-- ============================================================================

-- Tabla de alertas enviadas (historial)
CREATE TABLE IF NOT EXISTS alertas_vencimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vencimiento_id INT NOT NULL,
    tipo_alerta ENUM('3_dias', '1_dia', 'hoy', 'vencido') NOT NULL,
    canal ENUM('email', 'push', 'webhook', 'in_app') NOT NULL DEFAULT 'in_app',
    enviada BOOLEAN DEFAULT FALSE,
    fecha_programada DATETIME NOT NULL,
    fecha_envio DATETIME NULL,
    mensaje TEXT NULL,
    error_envio TEXT NULL,
    intentos INT DEFAULT 0,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_vencimiento_id (vencimiento_id),
    INDEX idx_tipo_alerta (tipo_alerta),
    INDEX idx_enviada (enviada),
    INDEX idx_fecha_programada (fecha_programada),

    CONSTRAINT fk_alerta_vencimiento
        FOREIGN KEY (vencimiento_id)
        REFERENCES vencimientos(id)
        ON DELETE CASCADE
);

-- Tabla de configuración de alertas por usuario
CREATE TABLE IF NOT EXISTS configuracion_alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    alertas_email BOOLEAN DEFAULT TRUE,
    alertas_push BOOLEAN DEFAULT TRUE,
    alertas_in_app BOOLEAN DEFAULT TRUE,
    dias_anticipacion JSON NULL,
    hora_envio TIME DEFAULT '09:00:00',
    expedientes_excluidos JSON NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_usuario (usuario_id),

    CONSTRAINT fk_config_alertas_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

-- Tabla de notificaciones in-app (para mostrar en UI)
CREATE TABLE IF NOT EXISTS notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo ENUM('vencimiento', 'sistema', 'monitoreo', 'extraccion', 'error') NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    datos_extra JSON NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha_lectura DATETIME NULL,
    url_accion VARCHAR(500) NULL,
    prioridad ENUM('baja', 'normal', 'alta', 'urgente') DEFAULT 'normal',
    expira_en DATETIME NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_usuario_leida (usuario_id, leida),
    INDEX idx_tipo (tipo),
    INDEX idx_creado_en (creado_en),
    INDEX idx_prioridad (prioridad),

    CONSTRAINT fk_notificacion_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
);

-- Insertar configuración por defecto para usuario admin (id=1) si existe
INSERT INTO configuracion_alertas (usuario_id, alertas_email, alertas_push, alertas_in_app, dias_anticipacion, expedientes_excluidos)
SELECT 1, TRUE, TRUE, TRUE, JSON_ARRAY(3, 1, 0), JSON_ARRAY()
FROM usuarios WHERE id = 1
ON DUPLICATE KEY UPDATE actualizado_en = CURRENT_TIMESTAMP;

-- Vista para obtener alertas pendientes de envío
CREATE OR REPLACE VIEW v_alertas_pendientes AS
SELECT
    a.id,
    a.vencimiento_id,
    a.tipo_alerta,
    a.canal,
    a.fecha_programada,
    a.intentos,
    v.expediente_numero,
    v.descripcion as vencimiento_descripcion,
    v.fecha_vencimiento,
    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
FROM alertas_vencimientos a
JOIN vencimientos v ON v.id = a.vencimiento_id
WHERE a.enviada = FALSE
  AND a.fecha_programada <= NOW()
  AND a.intentos < 3
  AND v.estado = 'pendiente';

-- Vista para estadísticas de notificaciones
CREATE OR REPLACE VIEW v_estadisticas_notificaciones AS
SELECT
    usuario_id,
    COUNT(*) as total,
    SUM(CASE WHEN leida = FALSE THEN 1 ELSE 0 END) as no_leidas,
    SUM(CASE WHEN tipo = 'vencimiento' THEN 1 ELSE 0 END) as vencimientos,
    SUM(CASE WHEN prioridad IN ('alta', 'urgente') AND leida = FALSE THEN 1 ELSE 0 END) as urgentes_no_leidas
FROM notificaciones
WHERE (expira_en IS NULL OR expira_en > NOW())
GROUP BY usuario_id;
