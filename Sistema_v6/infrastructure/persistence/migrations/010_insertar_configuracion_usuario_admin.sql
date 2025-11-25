-- =====================================================
-- Migration 010: Insertar configuración por defecto
-- Fecha: 2025-11-24
-- Descripción: Asegura que usuario admin tiene
--              configuración de monitoreo por defecto
-- =====================================================

-- NOTA: La tabla users está en SQLite, no en MySQL
-- Asumimos que usuario_id=1 (admin) ya existe

-- Insertar configuración por defecto para usuario admin
-- IMPORTANTE: INSERT IGNORE no falla si ya existe (basado en UNIQUE KEY uk_usuario)
INSERT IGNORE INTO monitoreo_configuracion (
    usuario_id,
    activo,
    frecuencia,
    notificar_email,
    notificar_sistema,
    hora_inicio,
    hora_fin,
    dias_semana,
    created_at,
    updated_at
) VALUES (
    1,                              -- usuario_id
    TRUE,                           -- activo
    '30min',                        -- frecuencia (alineado con frontend)
    FALSE,                          -- notificar_email
    TRUE,                           -- notificar_sistema
    '08:00:00',                     -- hora_inicio (formato TIME)
    '18:00:00',                     -- hora_fin (formato TIME)
    '[1,2,3,4,5]',                  -- dias_semana (JSON, lunes a viernes)
    NOW(),                          -- created_at
    NOW()                           -- updated_at
);

-- Verificar que se creó correctamente
SELECT
    id,
    usuario_id,
    activo,
    frecuencia,
    hora_inicio,
    hora_fin,
    dias_semana
FROM monitoreo_configuracion
WHERE usuario_id = 1;
