-- ============================================================================
-- Migracion 011: Agregar opciones de extraccion a monitoreo_configuracion
-- ============================================================================
--
-- Esta migracion separa las opciones de extraccion del monitoreo automatico
-- de las opciones de extraccion masiva, permitiendo que cada modulo opere
-- de forma independiente.
--
-- Los valores en .env (MONITOREO_*) seguiran siendo los defaults del sistema,
-- pero cada usuario podra personalizar sus propias opciones de extraccion
-- para el monitoreo.
--
-- ============================================================================

-- ============================================================================
-- PASO 1: Agregar columnas de opciones de extraccion
-- ============================================================================

ALTER TABLE monitoreo_configuracion
    ADD COLUMN fecha_corte_dias INT NULL DEFAULT 30
        COMMENT 'Dias hacia atras para buscar actuaciones (NULL = sin limite)',
    ADD COLUMN max_paginas_monitoreo INT NULL DEFAULT 50
        COMMENT 'Maximo numero de paginas a procesar (NULL = sin limite)',
    ADD COLUMN tiempo_maximo_extraccion INT NULL DEFAULT 600
        COMMENT 'Tiempo maximo en segundos para extraccion (NULL = sin limite)',
    ADD COLUMN detener_en_duplicado BOOLEAN DEFAULT TRUE
        COMMENT 'Detener extraccion al encontrar actuacion ya procesada',
    ADD COLUMN orden_extraccion VARCHAR(20) DEFAULT 'fecha'
        COMMENT 'Orden de extraccion: "fecha" o "caratula"';

-- ============================================================================
-- PASO 2: Indices adicionales para mejorar rendimiento
-- ============================================================================

-- No se requieren indices adicionales para estas columnas ya que solo
-- se acceden mediante la clave primaria (id) o clave unica (usuario_id)

-- ============================================================================
-- PASO 3: Actualizar registros existentes con valores default de .env
-- ============================================================================

-- Nota: Los registros existentes ya tendran los valores DEFAULT de las columnas.
-- Si se desea sincronizar con .env actual, ejecutar:
--
-- UPDATE monitoreo_configuracion SET
--     fecha_corte_dias = 30,
--     max_paginas_monitoreo = 50,
--     tiempo_maximo_extraccion = 600,
--     detener_en_duplicado = TRUE,
--     orden_extraccion = 'fecha'
-- WHERE fecha_corte_dias IS NULL;

-- ============================================================================
-- ROLLBACK SCRIPT (Guardar en 011_agregar_opciones_extraccion_monitoreo_rollback.sql)
-- ============================================================================
--
-- Para revertir esta migracion, ejecutar:
--
-- ALTER TABLE monitoreo_configuracion
--     DROP COLUMN fecha_corte_dias,
--     DROP COLUMN max_paginas_monitoreo,
--     DROP COLUMN tiempo_maximo_extraccion,
--     DROP COLUMN detener_en_duplicado,
--     DROP COLUMN orden_extraccion;
--
-- ============================================================================
