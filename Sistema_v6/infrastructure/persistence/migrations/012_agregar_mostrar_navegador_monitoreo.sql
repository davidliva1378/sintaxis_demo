-- ============================================================================
-- Migracion 012: Agregar campo mostrar_navegador_monitoreo
-- ============================================================================
--
-- Este script agrega el campo mostrar_navegador_monitoreo a la tabla
-- monitoreo_configuracion para permitir que el monitoreo tenga su propia
-- configuración de visualización del navegador, independiente del extractor
-- masivo que usa BROWSER_HEADLESS del .env.
--
-- Autor: Sistema
-- Fecha: 2025-11-24
--
-- ============================================================================

ALTER TABLE monitoreo_configuracion
    ADD COLUMN mostrar_navegador_monitoreo BOOLEAN DEFAULT FALSE
    COMMENT 'Mostrar navegador durante monitoreo (independiente del extractor masivo)';
