-- Migración: Crear tablas para sistema de escritos
-- Fecha: 2025-11-21
-- Descripción: Gestión de escritos judiciales con plantillas, borradores y seguimiento

-- Tabla de plantillas de escritos
CREATE TABLE IF NOT EXISTS plantillas_escritos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    contenido TEXT NOT NULL,
    variables JSON COMMENT 'Variables disponibles en la plantilla',
    categoria VARCHAR(100) DEFAULT 'general',
    es_publica BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plantillas_user (user_id),
    INDEX idx_plantillas_categoria (categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de escritos
CREATE TABLE IF NOT EXISTS escritos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    expediente_numero VARCHAR(100),
    plantilla_id INT,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    estado ENUM('borrador', 'revision', 'presentado', 'confirmado') DEFAULT 'borrador',
    fecha_presentacion DATETIME,
    numero_escrito VARCHAR(100) COMMENT 'Número asignado por el juzgado',
    notas TEXT,
    metadata JSON COMMENT 'Metadatos adicionales',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_escritos_user (user_id),
    INDEX idx_escritos_expediente (expediente_numero),
    INDEX idx_escritos_estado (estado),
    INDEX idx_escritos_fecha (fecha_presentacion),
    FOREIGN KEY (plantilla_id) REFERENCES plantillas_escritos(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de adjuntos de escritos
CREATE TABLE IF NOT EXISTS escritos_adjuntos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    escrito_id INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    tipo_archivo VARCHAR(100),
    tamanio INT,
    ruta_archivo VARCHAR(500) NOT NULL,
    descripcion VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_adjuntos_escrito (escrito_id),
    FOREIGN KEY (escrito_id) REFERENCES escritos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de versiones de escritos (historial)
CREATE TABLE IF NOT EXISTS escritos_versiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    escrito_id INT NOT NULL,
    version INT NOT NULL,
    contenido TEXT NOT NULL,
    comentario VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_versiones_escrito (escrito_id),
    FOREIGN KEY (escrito_id) REFERENCES escritos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar algunas plantillas de ejemplo
INSERT INTO plantillas_escritos (user_id, nombre, descripcion, contenido, variables, categoria, es_publica) VALUES
(1, 'Contesta Demanda', 'Plantilla básica para contestar demanda',
'CONTESTA DEMANDA\n\nExcmo. Sr. Juez:\n\n{{nombre_letrado}}, abogado, inscripto al Tº {{tomo}} Fº {{folio}} del CPACF, constituyendo domicilio procesal en {{domicilio_procesal}} y domicilio electrónico en {{domicilio_electronico}}, en mi carácter de apoderado/patrocinante de {{nombre_cliente}}, en los autos caratulados "{{caratula}}" (Expte. Nº {{expediente}}), a V.S. me presento y respetuosamente digo:\n\nI. OBJETO\nQue vengo a contestar la demanda incoada en mi contra.\n\nII. NEGATIVA\nNiego todos y cada uno de los hechos expuestos en el escrito de demanda...\n\nIII. HECHOS\n{{hechos}}\n\nIV. DERECHO\n{{derecho}}\n\nV. PETITORIO\nPor todo lo expuesto a V.S. solicito:\n1. Se tenga por contestada la demanda en tiempo y forma.\n2. Se rechace la demanda con costas.\n\nProveer de conformidad,\nSERÁ JUSTICIA',
'["nombre_letrado", "tomo", "folio", "domicilio_procesal", "domicilio_electronico", "nombre_cliente", "caratula", "expediente", "hechos", "derecho"]',
'contestaciones', TRUE),

(1, 'Apela Resolución', 'Plantilla para interponer recurso de apelación',
'INTERPONE RECURSO DE APELACIÓN\n\nExcmo. Sr. Juez:\n\n{{nombre_letrado}}, en mi carácter de apoderado/patrocinante de {{nombre_cliente}}, en los autos caratulados "{{caratula}}" (Expte. Nº {{expediente}}), a V.S. me presento y digo:\n\nQue vengo a interponer recurso de apelación contra la resolución de fecha {{fecha_resolucion}}, por considerar que la misma causa gravamen irreparable a los intereses de mi mandante.\n\nFundo el recurso en los siguientes\n\nAGRAVIOS:\n\n{{agravios}}\n\nPor lo expuesto, a V.S. solicito:\n1. Se tenga por interpuesto el recurso de apelación.\n2. Se eleven los autos al Superior.\n\nProveer de conformidad,\nSERÁ JUSTICIA',
'["nombre_letrado", "nombre_cliente", "caratula", "expediente", "fecha_resolucion", "agravios"]',
'recursos', TRUE),

(1, 'Solicita Pronto Despacho', 'Plantilla para solicitar pronto despacho',
'SOLICITA PRONTO DESPACHO\n\nExcmo. Sr. Juez:\n\n{{nombre_letrado}}, en mi carácter de apoderado/patrocinante de la parte {{parte}}, en los autos caratulados "{{caratula}}" (Expte. Nº {{expediente}}), a V.S. me presento y respetuosamente digo:\n\nQue habiendo transcurrido el plazo legal sin que se haya dictado resolución respecto de {{peticion_pendiente}}, vengo a solicitar a V.S. se sirva proveer lo peticionado oportunamente.\n\nProveer de conformidad,\nSERÁ JUSTICIA',
'["nombre_letrado", "parte", "caratula", "expediente", "peticion_pendiente"]',
'general', TRUE);

-- Vista para estadísticas de escritos
CREATE OR REPLACE VIEW escritos_estadisticas AS
SELECT
    user_id,
    COUNT(*) as total_escritos,
    SUM(CASE WHEN estado = 'borrador' THEN 1 ELSE 0 END) as borradores,
    SUM(CASE WHEN estado = 'revision' THEN 1 ELSE 0 END) as en_revision,
    SUM(CASE WHEN estado = 'presentado' THEN 1 ELSE 0 END) as presentados,
    SUM(CASE WHEN estado = 'confirmado' THEN 1 ELSE 0 END) as confirmados,
    COUNT(DISTINCT expediente_numero) as expedientes_con_escritos
FROM escritos
GROUP BY user_id;
