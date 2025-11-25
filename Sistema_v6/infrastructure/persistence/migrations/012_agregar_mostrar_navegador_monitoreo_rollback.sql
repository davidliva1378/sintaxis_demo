-- ============================================================================
-- Rollback para Migracion 012
-- ============================================================================
--
-- Este script revierte los cambios realizados por la migracion 012.
-- Elimina el campo mostrar_navegador_monitoreo de monitoreo_configuracion.
--
-- ADVERTENCIA: Esta operacion eliminara datos. Asegurar backup antes de ejecutar.
--
-- ============================================================================

ALTER TABLE monitoreo_configuracion
    DROP COLUMN mostrar_navegador_monitoreo;
