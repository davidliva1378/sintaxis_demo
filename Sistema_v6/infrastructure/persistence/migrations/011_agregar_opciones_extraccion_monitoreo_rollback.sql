-- ============================================================================
-- Rollback para Migracion 011
-- ============================================================================
--
-- Este script revierte los cambios realizados por la migracion 011.
-- Elimina las columnas de opciones de extraccion de monitoreo_configuracion.
--
-- ADVERTENCIA: Esta operacion eliminara datos. Asegurar backup antes de ejecutar.
--
-- ============================================================================

ALTER TABLE monitoreo_configuracion
    DROP COLUMN fecha_corte_dias,
    DROP COLUMN max_paginas_monitoreo,
    DROP COLUMN tiempo_maximo_extraccion,
    DROP COLUMN detener_en_duplicado,
    DROP COLUMN orden_extraccion;
