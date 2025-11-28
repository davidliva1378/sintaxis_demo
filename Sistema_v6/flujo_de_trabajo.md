# Flujo de Trabajo del Sistema

Este documento detalla el flujo de datos y procesos del sistema, actualizándose a medida que se analiza y refina.

## 1. Extracción Masiva (Origen de Datos)

El proceso comienza con la extracción masiva de expedientes del PJN.

### 1.1. Proceso de Extracción
1.  **Inicio**: Se inicia una sesión de extracción (`ExtractorMasivo`).
2.  **Scraping**: Se navega por el portal del PJN extrayendo el listado completo de expedientes.
3.  **Resultado Temporal**: Se genera un archivo JSON temporal con el listado "crudo" (ej: `listado_20231128_...json`).

### 1.2. Mantenimiento de Base Permanente (`listado_base.json`)
El sistema mantiene un archivo maestro acumulativo llamado `listado_base.json`.

*   **Ubicación**: `data/extraccion_masiva/listados/listado_base.json`
*   **Lógica de Actualización**:
    *   **Nuevos**: Se agregan los expedientes que no existían.
    *   **Existentes**: Se actualizan sus datos (situación, última actuación, etc.) si han cambiado.
    *   **Eliminados**: NUNCA se eliminan expedientes de la base (es acumulativa).

### 1.3. Estructura de Datos (`ExpedienteListado`)
Cada expediente en `listado_base.json` contiene:

*   `numero`: Número del expediente (ID único).
*   `caratula`: Carátula completa.
*   `dependencia`: Juzgado/Dependencia.
*   `situacion`: Estado procesal (ej: "En letra").
*   `fecha_inicio`: Fecha de inicio.
*   `ultima_actuacion`: Fecha del último movimiento.

## 2. Selección y Procesamiento (Batch)

Una vez extraído el listado, el usuario selecciona qué expedientes procesar en detalle.

1.  **Selección**: El usuario elige expedientes desde la interfaz.
2.  **Procesamiento (`GestorBatch`)**:
    *   **Opciones de Descarga**:
        *   **Solo Metadata**: Descarga actuaciones en JSON.
        *   **Metadata + Archivos**: Descarga JSON y adjuntos (PDFs) si se activa `procesar_con_pdf`.
    *   Se descargan detalles y actuaciones.
    *   Se pueden descargar adjuntos (PDFs).
3.  **Persistencia**:
    *   Los expedientes procesados se guardan en `expedientes_sistema.json` (vía `JsonExpedienteRepository`).
    *   **Nota**: Aquí ocurre una bifurcación. Estos datos van a un JSON local, pero el monitoreo web lee de MySQL.

### 2.1. Estructura de Archivos Generada
Por cada expediente procesado, se genera la siguiente estructura en `data/expedientes/{numero_normalizado}/`:

1.  **`manifest.json`**: Metadatos del expediente y estado de sincronización.
2.  **`json/`**:
    *   `actuaciones-{numero_normalizado}.json`: Contiene metadata completa y listado de actuaciones.
3.  **`actuaciones/`**:
    *   Contiene los archivos **PDF** descargados (solo si se seleccionó "Metadata + Archivos").

### 2.2. Archivo `expedientes_sistema.json`
Es el índice principal de expedientes procesados por el sistema (usado actualmente por el Scheduler).

*   **Creado por**: `GestorBatch` (al finalizar procesamiento).
*   **Actualizado por**: `JsonExpedienteRepository`.
*   **Contenido**: Lista de objetos `ExpedienteResumen` con los campos:
    *   `numero`: Número del expediente (ID único).
    *   `dependencia`: Juzgado o dependencia.
    *   `caratula`: Carátula del expediente.
    *   `situacion`: Situación procesal.
    *   `ultima_actuacion`: Fecha de la última actuación (ISO o DD/MM/YYYY).

## 3. Monitoreo (Estado Actual)

### 3.1. Scheduler
*   **Fuente de Verdad**: Lee de `expedientes_sistema.json`.
*   **Acción**: Verifica cambios en el PJN periódicamente.
*   **Sincronización**: Si detecta cambios, actualiza el JSON y notifica a `MonitoreoService`.

### 3.2. Interfaz Web / Base de Datos
*   **Fuente de Verdad**: Lee de la tabla MySQL `monitoreo_expedientes`.
*   **Problema Identificado**: Existe una desconexión.
    *   Si se agrega un expediente solo al JSON (vía Batch), no aparece en la Web hasta que haya un cambio.
    *   Si se agrega un expediente en la Web, el Scheduler no lo ve (porque lee el JSON).

### 3.3. Mecanismo de Sincronización (Manual)
Existe un endpoint `POST /monitoreo/sincronizar` que:
1.  Lee todos los expedientes de `expedientes_sistema.json`.
2.  Los inserta en MySQL (`monitoreo_expedientes`).
*   **Limitación**: Es un proceso manual. No ocurre automáticamente al terminar el Batch.
*   **Asimetría**: Agregar un expediente manualmente en la Web (`POST /monitoreo/expedientes`) **NO** actualiza `expedientes_sistema.json`, por lo que el Scheduler lo ignora.

### 3.4. Ciclo de Detección y Notificación
Cuando el Scheduler ejecuta una verificación (`MonitorearExpedientesUseCase`):
1.  **Lectura**: Lee la lista de expedientes a monitorear (actualmente desde `expedientes_sistema.json`).
2.  **Extracción**: Usa `ExtractorMasivo` para obtener el estado actual del PJN.
3.  **Comparación**: Detecta cambios (nuevas actuaciones, cambios de situación, etc.).
4.  **Acciones**:
    *   **Actualiza Workspace**: Descarga nuevas actuaciones y actualiza el JSON local del expediente.
    *   **Persistencia**: Actualiza `expedientes_sistema.json` con los nuevos datos.
    *   **Notificación**: Envía notificaciones de escritorio si está configurado.

## 4. Próximos Pasos (Plan de Unificación)

*   [ ] Unificar la fuente de verdad del Scheduler para que lea de MySQL.
*   [ ] Asegurar que el procesamiento Batch inserte en MySQL además del JSON.
