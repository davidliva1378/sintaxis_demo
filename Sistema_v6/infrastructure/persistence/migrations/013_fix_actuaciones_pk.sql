-- ============================================================================
-- Migración 013: Corregir PK de actuaciones y agregar índice relativo
-- ============================================================================

-- 1. Agregar columna indice
ALTER TABLE actuaciones
ADD COLUMN indice INT DEFAULT NULL COMMENT 'Indice relativo dentro del expediente' AFTER expediente_id;

-- 2. Agregar índice único compuesto (expediente_id, indice)
-- Esto permitirá usar ON DUPLICATE KEY UPDATE correctamente sin depender del ID global
CREATE UNIQUE INDEX uk_expediente_indice ON actuaciones (expediente_id, indice);

-- 3. Asegurar que ID sea AUTO_INCREMENT (si no lo era)
-- Nota: Esto puede fallar si hay IDs duplicados (que no debería por ser PK)
-- o si ya es auto_increment. Lo dejamos comentado por seguridad, 
-- asumiendo que ya es PK Auto Increment o que el cambio de lógica bastará.
-- ALTER TABLE actuaciones MODIFY id INT AUTO_INCREMENT;
