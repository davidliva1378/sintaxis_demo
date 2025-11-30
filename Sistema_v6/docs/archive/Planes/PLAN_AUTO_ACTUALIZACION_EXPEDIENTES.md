# Plan: Auto-Actualización de Expedientes con Cambios

**Fecha de creación:** 2025-11-24
**Estado:** Pendiente
**Prioridad:** Media-Alta
**Estimación:** 7-8 horas

---

## Resumen Ejecutivo

Implementar una funcionalidad que permita actualizar automáticamente los expedientes (descargar nuevas actuaciones y archivos) cuando el sistema de monitoreo detecte cambios.

**Componentes principales**:
- ✅ Checkbox en UI: "Auto-actualizar expedientes con cambios" (junto a "Monitoreo activo")
- ✅ Backend: Use case nuevo que usa `GestorBatch` para actualizar UN expediente
- ✅ Scheduler: Lanza actualizaciones en background sin bloquear verificaciones
- ✅ Base de datos: Campo `auto_actualizar` + tabla de log de actualizaciones

---

## Tabla de Contenidos

1. [Análisis del Sistema Actual](#1-análisis-del-sistema-actual)
2. [Arquitectura Propuesta](#2-arquitectura-propuesta)
3. [Cambios en Base de Datos](#3-cambios-en-base-de-datos)
4. [Cambios en Backend](#4-cambios-en-backend)
5. [Cambios en Frontend](#5-cambios-en-frontend)
6. [Flujo de Ejecución](#6-flujo-de-ejecución)
7. [Plan de Implementación](#7-plan-de-implementación)
8. [Testing y Validación](#8-testing-y-validación)
9. [Riesgos y Mitigaciones](#9-riesgos-y-mitigaciones)
10. [Mejoras Futuras](#10-mejoras-futuras)

---

## 1. Análisis del Sistema Actual

### 1.1 Flujo de Detección de Cambios

**Componentes involucrados**:

1. **DetectorCambios** (`application/services/detector_cambios.py`)
   - Método: `detectar_cambios_expedientes()` (líneas 106-211)
   - Detecta cambios en 4 campos: `ultima_actuacion`, `situacion`, `dependencia`, `caratula`
   - Retorna: `list[CambioExpediente]`

2. **MonitorearExpedientesUseCase** (`application/use_cases/monitorear_expedientes_use_case.py`)
   - Método: `execute()` (líneas 115-432)
   - Extrae datos actualizados del PJN con `ExtractorMasivo`
   - Usa `DetectorCambios` para comparar estados
   - Actualiza workspaces

3. **MonitorSchedulerService** (`application/services/monitor_scheduler_service.py`)
   - Método: `_ejecutar_verificacion_expedientes()` (líneas 169-276)
   - Ejecuta verificaciones periódicas
   - Registra cambios en BD: tabla `cambios_detectados`
   - **AQUÍ se agregará la lógica de auto-actualización**

**Tipos de cambio detectados**:
- `nueva_actuacion` - Solo cambió fecha de última actuación
- `cambio_situacion` - Solo cambió situación del expediente
- `cambio_dependencia` - Solo cambió dependencia asignada
- `cambio_caratula` - Solo cambió carátula
- `multiples_cambios` - 2 o más campos cambiaron simultáneamente

### 1.2 Opciones de Actualización de Expedientes

**Análisis de opciones**:

#### Opción A: `CrearWorkspacesUseCase` ❌ NO RECOMENDADO
- **Archivo**: `application/use_cases/crear_workspaces_use_case.py`
- **Limitación**: NO descarga archivos adjuntos (TODO en línea 140)
- **Uso**: Solo crea estructura de workspace

#### Opción B: `GestorBatch.procesar_seleccionados()` ✅ RECOMENDADO
- **Archivo**: `extraccion_masiva/gestor_batch.py`
- **Método**: `procesar_seleccionados(numeros_expedientes, username, password)` (líneas 72-198)
- **Funcionalidades**:
  - ✅ Procesa lista específica de expedientes
  - ✅ Navega PJN y extrae actuaciones
  - ✅ Descarga archivos adjuntos (si `config.procesar_con_pdf=True`)
  - ✅ Clasifica actuaciones (opcional)
  - ✅ Guarda en repositorio
  - ✅ Maneja errores y timeouts
- **Parámetros necesarios**:
  ```python
  numeros_expedientes: List[str]
  username: str  # Credenciales PJN del usuario
  password: str
  config: ConfigExtraccionMasiva  # headless, procesar_con_pdf, etc
  ```

**DECISIÓN**: Usar `GestorBatch` por ser más completo y robusto.

### 1.3 Estado de Tablas en BD

**Tabla `monitoreo_configuracion`** (migration 009, líneas 14-36):
```sql
CREATE TABLE IF NOT EXISTS monitoreo_configuracion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    frecuencia ENUM(...) DEFAULT '1hora',
    notificar_email BOOLEAN DEFAULT FALSE,
    notificar_sistema BOOLEAN DEFAULT TRUE,
    hora_inicio TIME DEFAULT NULL,
    hora_fin TIME DEFAULT NULL,
    dias_semana JSON DEFAULT NULL,
    -- FALTA: auto_actualizar BOOLEAN
    ...
)
```

**Tabla `cambios_detectados`** (migration 009, líneas 71-98):
```sql
CREATE TABLE IF NOT EXISTS cambios_detectados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expediente_monitoreado_id INT NOT NULL,
    tipo_cambio VARCHAR(50) NOT NULL,
    descripcion TEXT,
    detalles JSON,
    fecha_deteccion DATETIME NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    notificado BOOLEAN DEFAULT FALSE,
    ...
)
```

**NECESIDAD**: Tabla nueva para log de auto-actualizaciones.

---

## 2. Arquitectura Propuesta

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  ConfiguracionMonitoreo.tsx                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ Monitoreo activo                                  │   │
│  │ ☑ Auto-actualizar expedientes con cambios  ← NUEVO │   │
│  │   Al detectar cambios, descarga automáticamente    │   │
│  │   nuevas actuaciones y archivos                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ PUT /api/v1/monitoreo/configuracion
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND API                          │
│  monitoreo.py (router)                                       │
│  ├─ GET  /configuracion  → response.auto_actualizar         │
│  └─ PUT  /configuracion  ← request.auto_actualizar          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     MONITOREO SERVICE                        │
│  MonitoreoService                                            │
│  ├─ obtener_configuracion(usuario_id)                       │
│  └─ actualizar_configuracion(usuario_id, auto_actualizar)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        REPOSITORY                            │
│  MonitoreoRepository                                         │
│  ├─ obtener_configuracion() → {auto_actualizar: bool}       │
│  ├─ actualizar_configuracion(auto_actualizar)               │
│  ├─ registrar_auto_actualizacion_inicio()     ← NUEVO       │
│  └─ registrar_auto_actualizacion_fin()        ← NUEVO       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      BASE DE DATOS                           │
│  monitoreo_configuracion                                     │
│  ├─ auto_actualizar BOOLEAN                  ← NUEVO        │
│                                                               │
│  auto_actualizaciones_log                    ← NUEVA TABLA  │
│  ├─ expediente_numero                                        │
│  ├─ cambio_id (FK → cambios_detectados)                     │
│  ├─ estado (pendiente|procesando|completado|error)          │
│  ├─ total_actuaciones, archivos_descargados                 │
│  └─ error_mensaje, tiempo_procesamiento_seg                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   SCHEDULER (Background)                     │
│  MonitorSchedulerService                                     │
│  ├─ _ejecutar_verificacion_expedientes()                    │
│  │   ├─ MonitorearExpedientesUseCase.execute()              │
│  │   │   └─ DetectorCambios → cambios: list[...]            │
│  │   │                                                       │
│  │   └─ Por cada cambio:                                    │
│  │       ├─ Registra en cambios_detectados                  │
│  │       └─ Si auto_actualizar=TRUE:                        │
│  │           └─ _ejecutar_auto_actualizacion() ← NUEVO     │
│  │                                                           │
│  └─ _ejecutar_auto_actualizacion(cambio)     ← NUEVO       │
│      └─ asyncio.create_task(                                │
│            ActualizarExpedienteUseCase.execute()            │
│         )                                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ asyncio.create_task (no bloquea)
┌─────────────────────────────────────────────────────────────┐
│              ACTUALIZAR EXPEDIENTE USE CASE  ← NUEVO         │
│  ActualizarExpedienteUseCase                                 │
│  └─ execute(command: ActualizarExpedienteCommand)           │
│      ├─ 1. Registra inicio en auto_actualizaciones_log      │
│      ├─ 2. Obtiene credenciales usuario (desencriptadas)    │
│      ├─ 3. Configura GestorBatch                            │
│      ├─ 4. Ejecuta procesar_seleccionados([expediente])     │
│      │      └─ GestorBatch.procesar_seleccionados()         │
│      │          ├─ Login PJN con credenciales usuario       │
│      │          ├─ Busca expediente                         │
│      │          ├─ Extrae actuaciones                       │
│      │          ├─ Descarga archivos adjuntos               │
│      │          └─ Actualiza workspace                      │
│      └─ 5. Registra fin (completado/error) en log           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Flujo de Datos

```
Usuario marca checkbox → Frontend envía PUT {auto_actualizar: true}
                               ↓
                     Backend guarda en BD
                               ↓
           Scheduler ejecuta verificación periódica
                               ↓
                  DetectorCambios detecta cambio
                               ↓
              Scheduler lee config.auto_actualizar
                               ↓
                  Si TRUE y tipo actualizarle:
                               ↓
         Lanza ActualizarExpedienteUseCase (background)
                               ↓
                  Use case obtiene credenciales
                               ↓
                   GestorBatch actualiza expediente
                               ↓
                  Registra resultado en log
                               ↓
              Scheduler continúa con otros expedientes
```

---

## 3. Cambios en Base de Datos

### 3.1 Migration 010: Agregar Campo y Tabla

**Archivo**: `Sistema_v6/infrastructure/persistence/migrations/010_add_auto_actualizar.sql` (NUEVO)

```sql
-- =====================================================
-- Migration 010: Auto-actualización de expedientes
-- Fecha: 2025-11-24
-- Descripción: Agrega funcionalidad para actualizar
--              expedientes automáticamente al detectar
--              cambios en el monitoreo.
-- =====================================================

-- 1. Agregar columna auto_actualizar a configuración
ALTER TABLE monitoreo_configuracion
ADD COLUMN auto_actualizar BOOLEAN DEFAULT FALSE
COMMENT 'Auto-actualizar expedientes al detectar cambios';

-- 2. Crear tabla de log de auto-actualizaciones
CREATE TABLE IF NOT EXISTS auto_actualizaciones_log (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Información del expediente
    expediente_monitoreado_id INT NOT NULL
        COMMENT 'FK a expedientes_monitoreados',
    expediente_numero VARCHAR(100) NOT NULL
        COMMENT 'Número de expediente (normalizado)',

    -- Información del cambio que disparó la actualización
    cambio_id INT NOT NULL
        COMMENT 'FK a cambios_detectados',
    tipo_cambio VARCHAR(50) NOT NULL
        COMMENT 'Tipo de cambio detectado (nueva_actuacion, cambio_situacion, etc)',

    -- Estado de la actualización
    estado ENUM('pendiente', 'procesando', 'completado', 'error') NOT NULL
        COMMENT 'Estado actual de la actualización',

    -- Resultados de la actualización
    total_actuaciones INT DEFAULT 0
        COMMENT 'Total de actuaciones procesadas',
    archivos_descargados INT DEFAULT 0
        COMMENT 'Total de archivos descargados',
    error_mensaje TEXT DEFAULT NULL
        COMMENT 'Mensaje de error si estado=error',
    tiempo_procesamiento_seg FLOAT DEFAULT NULL
        COMMENT 'Tiempo total de procesamiento en segundos',

    -- Fechas
    fecha_inicio DATETIME NOT NULL
        COMMENT 'Momento en que inició la actualización',
    fecha_fin DATETIME DEFAULT NULL
        COMMENT 'Momento en que finalizó la actualización',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Índices para consultas eficientes
    INDEX idx_expediente (expediente_numero),
    INDEX idx_estado (estado),
    INDEX idx_fecha_inicio (fecha_inicio),
    INDEX idx_fecha_fin (fecha_fin),

    -- Foreign key al cambio que disparó la actualización
    CONSTRAINT fk_auto_actualizacion_cambio
        FOREIGN KEY (cambio_id)
        REFERENCES cambios_detectados(id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Log de auto-actualizaciones ejecutadas por el sistema de monitoreo';

-- 3. Insertar registros iniciales (opcional)
-- Actualizar configuración existente para que auto_actualizar=FALSE por defecto
-- (Ya establecido por DEFAULT FALSE en ALTER TABLE)
```

### 3.2 Estructura de Tabla `auto_actualizaciones_log`

| Campo | Tipo | Descripción | Uso |
|-------|------|-------------|-----|
| `id` | INT PK | Identificador único | Clave primaria |
| `expediente_monitoreado_id` | INT | FK a expedientes_monitoreados | Relacionar con expediente |
| `expediente_numero` | VARCHAR(100) | Número expediente normalizado | Búsqueda rápida |
| `cambio_id` | INT | FK a cambios_detectados | Rastrear qué cambio disparó |
| `tipo_cambio` | VARCHAR(50) | Tipo de cambio | Filtrar por tipo |
| `estado` | ENUM | pendiente/procesando/completado/error | Estado actual |
| `total_actuaciones` | INT | Actuaciones procesadas | Métrica |
| `archivos_descargados` | INT | Archivos descargados | Métrica |
| `error_mensaje` | TEXT | Mensaje de error | Debugging |
| `tiempo_procesamiento_seg` | FLOAT | Tiempo en segundos | Performance |
| `fecha_inicio` | DATETIME | Inicio actualización | Trazabilidad |
| `fecha_fin` | DATETIME | Fin actualización | Trazabilidad |

**Queries útiles**:
```sql
-- Ver últimas auto-actualizaciones
SELECT * FROM auto_actualizaciones_log
ORDER BY fecha_inicio DESC LIMIT 10;

-- Ver actualizaciones en progreso
SELECT * FROM auto_actualizaciones_log
WHERE estado IN ('pendiente', 'procesando');

-- Ver actualizaciones con error
SELECT * FROM auto_actualizaciones_log
WHERE estado = 'error'
ORDER BY fecha_inicio DESC;

-- Ver estadísticas por expediente
SELECT
    expediente_numero,
    COUNT(*) as total_actualizaciones,
    SUM(CASE WHEN estado='completado' THEN 1 ELSE 0 END) as exitosas,
    SUM(CASE WHEN estado='error' THEN 1 ELSE 0 END) as fallidas,
    AVG(tiempo_procesamiento_seg) as tiempo_promedio_seg
FROM auto_actualizaciones_log
GROUP BY expediente_numero;
```

### 3.3 Ejecución de Migration

**Comando**:
```bash
mysql -u root -pSulaco01 sintaxis < Sistema_v6/infrastructure/persistence/migrations/010_add_auto_actualizar.sql
```

**Verificación**:
```sql
-- Verificar columna agregada
DESCRIBE monitoreo_configuracion;

-- Verificar tabla creada
SHOW CREATE TABLE auto_actualizaciones_log;

-- Verificar datos iniciales
SELECT auto_actualizar FROM monitoreo_configuracion;
```

---

## 4. Cambios en Backend

### 4.1 Schemas Pydantic

**Archivo**: `Sistema_v6/presentation/api/rest/schemas/monitoreo_schemas.py`

#### Cambio 1: `ConfiguracionMonitoreoResponse` (líneas 105-121)

**ANTES**:
```python
class ConfiguracionMonitoreoResponse(BaseModel):
    id: int
    usuario_id: int
    activo: bool
    frecuencia: str
    notificar_email: bool
    notificar_sistema: bool
    hora_inicio: str | None = None
    hora_fin: str | None = None
    dias_semana: list[int] | None = None
    ultima_ejecucion: str | None = None
    proxima_ejecucion: str | None = None
    created_at: str
    updated_at: str
```

**DESPUÉS**:
```python
class ConfiguracionMonitoreoResponse(BaseModel):
    id: int
    usuario_id: int
    activo: bool
    frecuencia: str
    notificar_email: bool
    notificar_sistema: bool
    auto_actualizar: bool  # ← NUEVO
    hora_inicio: str | None = None
    hora_fin: str | None = None
    dias_semana: list[int] | None = None
    ultima_ejecucion: str | None = None
    proxima_ejecucion: str | None = None
    created_at: str
    updated_at: str
```

#### Cambio 2: `ActualizarConfiguracionRequest` (líneas 123-133)

**ANTES**:
```python
class ActualizarConfiguracionRequest(BaseModel):
    activo: bool | None = None
    frecuencia: str | None = Field(None, description="5min, 15min, 30min, 1hora, etc.")
    notificar_email: bool | None = None
    notificar_sistema: bool | None = None
    hora_inicio: str | None = Field(None, description="HH:MM formato")
    hora_fin: str | None = Field(None, description="HH:MM formato")
    dias_semana: list[int] | None = Field(None, description="Lista de días 0-6")
```

**DESPUÉS**:
```python
class ActualizarConfiguracionRequest(BaseModel):
    activo: bool | None = None
    frecuencia: str | None = Field(None, description="5min, 15min, 30min, 1hora, etc.")
    notificar_email: bool | None = None
    notificar_sistema: bool | None = None
    auto_actualizar: bool | None = None  # ← NUEVO
    hora_inicio: str | None = Field(None, description="HH:MM formato")
    hora_fin: str | None = Field(None, description="HH:MM formato")
    dias_semana: list[int] | None = Field(None, description="Lista de días 0-6")
```

### 4.2 Repository

**Archivo**: `Sistema_v6/infrastructure/persistence/monitoreo_repository.py`

#### Cambio 1: `crear_configuracion()` (líneas 78-137)

**Modificar firma**:
```python
def crear_configuracion(
    self,
    usuario_id: int,
    activo: bool = True,
    frecuencia: str = '30min',  # Alineado con frontend
    notificar_email: bool = False,
    notificar_sistema: bool = True,
    hora_inicio: Optional[str] = '08:00',  # Valor por defecto
    hora_fin: Optional[str] = '18:00',     # Valor por defecto
    dias_semana: Optional[List[int]] = None,
    auto_actualizar: bool = False  # ← NUEVO
) -> int:
```

**Modificar query INSERT** (aproximadamente línea 110):
```python
query = """
    INSERT INTO monitoreo_configuracion (
        usuario_id, activo, frecuencia,
        notificar_email, notificar_sistema,
        hora_inicio, hora_fin, dias_semana,
        auto_actualizar
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
```

**Modificar params** (aproximadamente línea 120):
```python
cursor.execute(query, (
    usuario_id,
    activo,
    frecuencia,
    notificar_email,
    notificar_sistema,
    hora_inicio,
    hora_fin,
    dias_json,
    auto_actualizar  # ← NUEVO
))
```

#### Cambio 2: `actualizar_configuracion()` (líneas 139-196)

**Agregar lógica para auto_actualizar**:

Buscar donde se construye la lista `updates` (aproximadamente línea 158-180) y agregar:

```python
if auto_actualizar is not None:
    updates.append("auto_actualizar = %s")
    params.append(auto_actualizar)
```

#### Cambio 3: Agregar nuevos métodos (al final del archivo)

```python
def registrar_auto_actualizacion_inicio(
    self,
    expediente_monitoreado_id: int,
    expediente_numero: str,
    cambio_id: int,
    tipo_cambio: str
) -> int:
    """Registra inicio de auto-actualización en log.

    Args:
        expediente_monitoreado_id: ID del expediente monitoreado
        expediente_numero: Número de expediente normalizado
        cambio_id: ID del cambio que disparó la actualización
        tipo_cambio: Tipo de cambio detectado

    Returns:
        ID del registro creado en auto_actualizaciones_log

    Raises:
        Exception: Si hay error en BD
    """
    conn = None
    try:
        conn = get_pooled_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO auto_actualizaciones_log (
                expediente_monitoreado_id,
                expediente_numero,
                cambio_id,
                tipo_cambio,
                estado,
                fecha_inicio
            ) VALUES (%s, %s, %s, %s, 'procesando', NOW())
        """

        cursor.execute(query, (
            expediente_monitoreado_id,
            expediente_numero,
            cambio_id,
            tipo_cambio
        ))

        conn.commit()
        log_id = cursor.lastrowid
        cursor.close()

        logger.info(
            f"Registrado inicio auto-actualización: "
            f"log_id={log_id}, expediente={expediente_numero}"
        )

        return log_id

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error registrando inicio auto-actualización: {e}")
        raise
    finally:
        if conn:
            conn.close()

def registrar_auto_actualizacion_fin(
    self,
    log_id: int,
    estado: str,
    total_actuaciones: int = 0,
    archivos_descargados: int = 0,
    tiempo_seg: float = 0,
    error_mensaje: Optional[str] = None
) -> bool:
    """Registra finalización de auto-actualización en log.

    Args:
        log_id: ID del registro en auto_actualizaciones_log
        estado: Estado final ('completado' o 'error')
        total_actuaciones: Total de actuaciones procesadas
        archivos_descargados: Total de archivos descargados
        tiempo_seg: Tiempo de procesamiento en segundos
        error_mensaje: Mensaje de error si estado='error'

    Returns:
        True si se actualizó correctamente

    Raises:
        Exception: Si hay error en BD
    """
    conn = None
    try:
        conn = get_pooled_connection()
        cursor = conn.cursor()

        query = """
            UPDATE auto_actualizaciones_log
            SET estado = %s,
                total_actuaciones = %s,
                archivos_descargados = %s,
                tiempo_procesamiento_seg = %s,
                error_mensaje = %s,
                fecha_fin = NOW()
            WHERE id = %s
        """

        cursor.execute(query, (
            estado,
            total_actuaciones,
            archivos_descargados,
            tiempo_seg,
            error_mensaje,
            log_id
        ))

        conn.commit()
        cursor.close()

        logger.info(
            f"Registrado fin auto-actualización: "
            f"log_id={log_id}, estado={estado}"
        )

        return True

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error registrando fin auto-actualización: {e}")
        raise
    finally:
        if conn:
            conn.close()
```

### 4.3 Service

**Archivo**: `Sistema_v6/application/services/monitoreo_service.py`

#### Cambio: `actualizar_configuracion()` (líneas 57-101)

**Modificar firma**:
```python
def actualizar_configuracion(
    self,
    usuario_id: int,
    activo: Optional[bool] = None,
    frecuencia: Optional[str] = None,
    notificar_email: Optional[bool] = None,
    notificar_sistema: Optional[bool] = None,
    hora_inicio: Optional[str] = None,
    hora_fin: Optional[str] = None,
    dias_semana: Optional[List[int]] = None,
    auto_actualizar: Optional[bool] = None  # ← NUEVO
) -> Dict[str, Any]:
```

**Agregar en kwargs** (aproximadamente línea 80):
```python
if auto_actualizar is not None:
    kwargs['auto_actualizar'] = auto_actualizar
```

### 4.4 Nuevo Use Case: `ActualizarExpedienteUseCase`

**Archivo**: `Sistema_v6/application/use_cases/actualizar_expediente_use_case.py` (NUEVO)

```python
"""Use Case: Actualizar Expediente Individual.

Actualiza UN expediente cuando el monitor detecta cambios:
- Descarga actuaciones nuevas desde PJN
- Descarga archivos adjuntos
- Actualiza workspace local
- Registra resultado en auto_actualizaciones_log
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from application.dtos import Result
    from infrastructure.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class ActualizarExpedienteCommand:
    """Comando para actualizar expediente individual.

    Attributes:
        expediente_numero: Número del expediente a actualizar
        usuario_id: ID del usuario que tiene el expediente monitoreado
        cambio_id: ID del cambio en cambios_detectados que disparó esta actualización
        tipo_cambio: Tipo de cambio detectado (nueva_actuacion, cambio_situacion, etc)
        headless: Si True, ejecuta navegador en modo headless
        descargar_archivos: Si True, descarga archivos adjuntos de actuaciones
    """
    expediente_numero: str
    usuario_id: int
    cambio_id: int
    tipo_cambio: str
    headless: bool = True
    descargar_archivos: bool = True


@dataclass
class ActualizarExpedienteResponse:
    """Respuesta de actualización de expediente.

    Attributes:
        success: True si la actualización fue exitosa
        expediente_numero: Número del expediente actualizado
        total_actuaciones: Total de actuaciones procesadas
        archivos_descargados: Total de archivos descargados
        tiempo_segundos: Tiempo total de procesamiento
        error: Mensaje de error si success=False
    """
    success: bool
    expediente_numero: str
    total_actuaciones: int = 0
    archivos_descargados: int = 0
    tiempo_segundos: float = 0
    error: str | None = None


class ActualizarExpedienteUseCase:
    """Use case para actualizar expediente individual al detectar cambio.

    Este use case se ejecuta en background cuando el scheduler detecta
    un cambio en un expediente monitoreado y la configuración tiene
    auto_actualizar=True.

    Utiliza GestorBatch para:
    - Extraer actuaciones actualizadas desde PJN
    - Descargar archivos adjuntos
    - Actualizar workspace local
    - Guardar en repositorio MySQL

    Registra el resultado en auto_actualizaciones_log para trazabilidad.
    """

    def __init__(
        self,
        monitoreo_repository: "MonitoreoRepository",
        settings: "Settings"
    ):
        """Inicializa el use case.

        Args:
            monitoreo_repository: Repository para acceder a datos de monitoreo
            settings: Configuración global del sistema
        """
        self._repo = monitoreo_repository
        self._settings = settings

    async def execute(
        self,
        command: ActualizarExpedienteCommand
    ) -> "Result[ActualizarExpedienteResponse]":
        """Ejecuta actualización de expediente individual.

        Args:
            command: Comando con datos del expediente a actualizar

        Returns:
            Result con respuesta (éxito) o error
        """
        from application.dtos import Result
        from extraccion_masiva.gestor_batch import GestorBatch
        from extraccion_masiva.models import ConfigExtraccionMasiva

        inicio = datetime.now()
        log_id = None

        try:
            logger.info(
                f"[AUTO-ACT] Iniciando actualización: {command.expediente_numero} "
                f"(tipo_cambio: {command.tipo_cambio})"
            )

            # 1. Obtener expediente monitoreado
            expediente = self._repo.obtener_expediente(
                command.usuario_id,
                command.expediente_numero
            )
            if not expediente:
                return Result.fail(
                    f"Expediente {command.expediente_numero} no encontrado en monitoreo",
                    error_code="EXPEDIENTE_NO_ENCONTRADO"
                )

            # 2. Registrar inicio en log
            log_id = self._repo.registrar_auto_actualizacion_inicio(
                expediente_monitoreado_id=expediente['id'],
                expediente_numero=command.expediente_numero,
                cambio_id=command.cambio_id,
                tipo_cambio=command.tipo_cambio
            )

            # 3. Obtener credenciales PJN del usuario
            credenciales = await self._obtener_credenciales_usuario(command.usuario_id)
            if not credenciales:
                error_msg = "No se encontraron credenciales PJN para el usuario"

                if log_id:
                    duracion = (datetime.now() - inicio).total_seconds()
                    self._repo.registrar_auto_actualizacion_fin(
                        log_id=log_id,
                        estado='error',
                        tiempo_seg=duracion,
                        error_mensaje=error_msg
                    )

                logger.error(f"[AUTO-ACT] {error_msg}: usuario_id={command.usuario_id}")
                return Result.fail(error_msg, error_code="CREDENCIALES_NO_ENCONTRADAS")

            username, password = credenciales

            # 4. Configurar GestorBatch para actualización
            config = ConfigExtraccionMasiva(
                headless=command.headless,
                procesar_con_pdf=command.descargar_archivos,
                directorio_base=Path(self._settings.paths.workspaces_dir),
                max_paginas=50,
                tiempo_maximo_segundos=600,
                umbral_errores=1  # Fallar rápido si hay error
            )

            gestor = GestorBatch(
                config=config,
                caratulas={
                    command.expediente_numero: expediente.get('expediente_caratula', '')
                }
            )

            # 5. Procesar expediente (ejecutar actualización)
            logger.info(f"[AUTO-ACT] Ejecutando GestorBatch: {command.expediente_numero}")

            resumen = await gestor.procesar_seleccionados(
                numeros_expedientes=[command.expediente_numero],
                username=username,
                password=password
            )

            # 6. Calcular tiempo total
            duracion = (datetime.now() - inicio).total_seconds()

            # 7. Verificar éxito y registrar resultado
            if resumen.exitosos == 1:
                # Actualización exitosa
                self._repo.registrar_auto_actualizacion_fin(
                    log_id=log_id,
                    estado='completado',
                    total_actuaciones=resumen.total if hasattr(resumen, 'total') else 0,
                    archivos_descargados=resumen.archivos_descargados,
                    tiempo_seg=duracion
                )

                logger.info(
                    f"[AUTO-ACT] ✓ Actualización exitosa: {command.expediente_numero} "
                    f"({resumen.archivos_descargados} archivos, {duracion:.2f}s)"
                )

                return Result.ok(ActualizarExpedienteResponse(
                    success=True,
                    expediente_numero=command.expediente_numero,
                    total_actuaciones=resumen.total if hasattr(resumen, 'total') else 0,
                    archivos_descargados=resumen.archivos_descargados,
                    tiempo_segundos=duracion
                ))

            else:
                # Error en procesamiento
                error_msg = (
                    resumen.errores_detalles[0]['error']
                    if resumen.errores_detalles
                    else "Error desconocido en GestorBatch"
                )

                if log_id:
                    self._repo.registrar_auto_actualizacion_fin(
                        log_id=log_id,
                        estado='error',
                        tiempo_seg=duracion,
                        error_mensaje=error_msg
                    )

                logger.error(
                    f"[AUTO-ACT] ✗ Error en actualización {command.expediente_numero}: "
                    f"{error_msg}"
                )

                return Result.fail(error_msg, error_code="ACTUALIZACION_ERROR")

        except Exception as e:
            # Excepción no controlada
            duracion = (datetime.now() - inicio).total_seconds()
            error_msg = str(e)

            if log_id:
                self._repo.registrar_auto_actualizacion_fin(
                    log_id=log_id,
                    estado='error',
                    tiempo_seg=duracion,
                    error_mensaje=error_msg
                )

            logger.error(
                f"[AUTO-ACT] ✗ Excepción en actualización {command.expediente_numero}: {e}",
                exc_info=True
            )

            return Result.fail(error_msg, error_code="ACTUALIZACION_EXCEPCION")

    async def _obtener_credenciales_usuario(
        self,
        usuario_id: int
    ) -> tuple[str, str] | None:
        """Obtiene credenciales PJN del usuario desde BD.

        Las credenciales están almacenadas encriptadas en la tabla users.
        Este método las desencripta para poder usarlas en GestorBatch.

        Args:
            usuario_id: ID del usuario

        Returns:
            Tupla (username, password) o None si no existen credenciales
        """
        try:
            from infrastructure.persistence.database import get_db, Usuario
            from infrastructure.security import decrypt_credentials

            db = next(get_db())
            try:
                usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
                if not usuario:
                    logger.warning(f"Usuario {usuario_id} no encontrado en BD")
                    return None

                if not (usuario.pjn_usuario_encrypted and usuario.pjn_password_encrypted):
                    logger.warning(f"Usuario {usuario_id} sin credenciales PJN configuradas")
                    return None

                # Desencriptar credenciales
                username = decrypt_credentials(usuario.pjn_usuario_encrypted)
                password = decrypt_credentials(usuario.pjn_password_encrypted)

                if username and password:
                    logger.info(f"Credenciales PJN obtenidas para usuario {usuario_id}")
                    return (username, password)

                logger.warning(f"Error desencriptando credenciales usuario {usuario_id}")
                return None

            finally:
                db.close()

        except Exception as e:
            logger.error(
                f"Error obteniendo credenciales usuario {usuario_id}: {e}",
                exc_info=True
            )
            return None
```

### 4.5 Modificar Scheduler

**Archivo**: `Sistema_v6/application/services/monitor_scheduler_service.py`

#### Cambio 1: Agregar constante (después de imports, antes de clase)

```python
# Tipos de cambio que disparan auto-actualización
TIPOS_AUTO_ACTUALIZABLES = [
    'nueva_actuacion',      # Nueva actuación detectada
    'cambio_situacion',     # Cambió situación del expediente
    'multiples_cambios'     # Múltiples campos cambiaron
]
# NO incluye: cambio_dependencia, cambio_caratula (no requieren actualización completa)
```

#### Cambio 2: Constructor (líneas 52-74)

**Modificar firma**:
```python
def __init__(
    self,
    monitorear_use_case: MonitorearExpedientesUseCase,
    config: MonitoreoSettings,
    json_sistema_path: Path,
    workspaces_dir: Path,
    monitoreo_service: "MonitoreoService | None" = None,
    settings: "Settings | None" = None  # ← NUEVO
):
    """Inicializa el scheduler de monitoreo.

    Args:
        monitorear_use_case: Use case para monitorear expedientes
        config: Configuración de monitoreo
        json_sistema_path: Ruta al JSON del sistema
        workspaces_dir: Directorio de workspaces
        monitoreo_service: Servicio de monitoreo (opcional)
        settings: Configuración global del sistema (opcional)  ← NUEVO
    """
    self._monitorear_use_case = monitorear_use_case
    self._config = config
    self._json_sistema_path = json_sistema_path
    self._workspaces_dir = workspaces_dir
    self._scheduler = None
    self._monitoreo_service = monitoreo_service
    self._settings = settings  # ← NUEVO
    self._job_id = "monitorear_expedientes"
```

#### Cambio 3: Modificar `_ejecutar_verificacion_expedientes()` (después línea 216)

**Localizar bloque** (aproximadamente líneas 216-258):
```python
# Registrar cambios en la base de datos si hay servicio disponible
if self._monitoreo_service and response.cambios_detectados:
    logger.info(f"Registrando {len(response.cambios_detectados)} cambios en la base de datos")

    for cambio in response.cambios_detectados:
        try:
            # ... código existente de registro de cambio ...
```

**Reemplazar con**:
```python
# Registrar cambios en la base de datos si hay servicio disponible
if self._monitoreo_service and response.cambios_detectados:
    logger.info(
        f"Registrando {len(response.cambios_detectados)} cambios "
        f"en la base de datos"
    )

    # NUEVO: Obtener configuración de auto-actualización
    config_monitoreo = self._monitoreo_service.obtener_configuracion(1)  # usuario_id=1
    auto_actualizar = config_monitoreo.get('auto_actualizar', False)

    if auto_actualizar:
        logger.info("✓ Auto-actualización HABILITADA - procesando cambios")
    else:
        logger.debug("○ Auto-actualización deshabilitada")

    for cambio in response.cambios_detectados:
        try:
            detalles = (
                cambio.datos_adicionales
                if hasattr(cambio, 'datos_adicionales')
                else {}
            )

            # ... código existente de registro de cambio ...
            # (mantener todo el bloque try/except existente)

            # NUEVO: Auto-actualizar si está habilitado
            if auto_actualizar and cambio.tipo in TIPOS_AUTO_ACTUALIZABLES:
                logger.info(
                    f"[AUTO-ACT] Lanzando actualización en background: "
                    f"{cambio.numero_expediente} (tipo: {cambio.tipo})"
                )

                await self._ejecutar_auto_actualizacion(
                    cambio=cambio,
                    usuario_id=1  # TODO: Obtener usuario_id real (FIX-MON-03)
                )
            elif auto_actualizar and cambio.tipo not in TIPOS_AUTO_ACTUALIZABLES:
                logger.debug(
                    f"[AUTO-ACT] Cambio tipo '{cambio.tipo}' no requiere "
                    f"actualización completa"
                )

        except Exception as e:
            logger.error(
                f"Error al procesar cambio {cambio.numero_expediente}: {e}",
                exc_info=True
            )
```

#### Cambio 4: Agregar nuevo método (después línea 276)

```python
async def _ejecutar_auto_actualizacion(
    self,
    cambio: "CambioDetectado",
    usuario_id: int
) -> None:
    """Ejecuta auto-actualización de expediente en background.

    Lanza ActualizarExpedienteUseCase como task asyncio sin esperar
    su finalización, permitiendo que el scheduler continúe verificando
    otros expedientes.

    Args:
        cambio: Cambio detectado que disparó la actualización
        usuario_id: ID del usuario dueño del expediente monitoreado

    Raises:
        No lanza excepciones, las captura y registra en log
    """
    from application.use_cases.actualizar_expediente_use_case import (
        ActualizarExpedienteUseCase,
        ActualizarExpedienteCommand
    )
    from infrastructure.persistence.monitoreo_repository import MonitoreoRepository

    try:
        logger.info(
            f"[AUTO-ACT] Preparando actualización para {cambio.numero_expediente} "
            f"(tipo: {cambio.tipo})"
        )

        # Crear use case
        repo = MonitoreoRepository()
        use_case = ActualizarExpedienteUseCase(
            monitoreo_repository=repo,
            settings=self._settings
        )

        # Crear comando
        command = ActualizarExpedienteCommand(
            expediente_numero=cambio.numero_expediente,
            usuario_id=usuario_id,
            cambio_id=getattr(cambio, 'id', 0),  # Si CambioDetectado tiene ID
            tipo_cambio=cambio.tipo,
            headless=True,
            descargar_archivos=True
        )

        # Lanzar en background (NO await)
        # Esto permite que el scheduler continúe sin esperar
        asyncio.create_task(use_case.execute(command))

        logger.info(
            f"[AUTO-ACT] ✓ Actualización lanzada en background: "
            f"{cambio.numero_expediente}"
        )

    except Exception as e:
        logger.error(
            f"[AUTO-ACT] ✗ Error al lanzar auto-actualización "
            f"{cambio.numero_expediente}: {e}",
            exc_info=True
        )
```

### 4.6 Dependency Injection Container

**Archivo**: `Sistema_v6/infrastructure/di_container.py`

#### Cambio 1: Agregar atributo (en sección de atributos de use cases)

```python
# Use Cases
self._crear_workspaces_use_case = None
self._monitorear_expedientes_use_case = None
self._actualizar_expediente_use_case = None  # ← NUEVO
```

#### Cambio 2: Agregar método getter (en sección de getters de use cases)

```python
def actualizar_expediente_use_case(self) -> "ActualizarExpedienteUseCase":
    """Obtiene el use case de actualización de expediente individual.

    Returns:
        Instancia de ActualizarExpedienteUseCase
    """
    if self._actualizar_expediente_use_case is None:
        from application.use_cases.actualizar_expediente_use_case import (
            ActualizarExpedienteUseCase
        )
        from infrastructure.persistence.monitoreo_repository import (
            MonitoreoRepository
        )

        self._actualizar_expediente_use_case = ActualizarExpedienteUseCase(
            monitoreo_repository=MonitoreoRepository(),
            settings=self.settings()
        )

    return self._actualizar_expediente_use_case
```

#### Cambio 3: Modificar `monitor_scheduler_service()` (localizar método existente)

**ANTES**:
```python
def monitor_scheduler_service(self) -> MonitorSchedulerService:
    if self._monitor_scheduler_service is None:
        self._monitor_scheduler_service = MonitorSchedulerService(
            monitorear_use_case=self.monitorear_expedientes_use_case(),
            config=self.settings().monitoreo,
            json_sistema_path=self.json_sistema_path(),
            workspaces_dir=self.workspaces_dir(),
            monitoreo_service=self.monitoreo_service()
        )
    return self._monitor_scheduler_service
```

**DESPUÉS**:
```python
def monitor_scheduler_service(self) -> MonitorSchedulerService:
    if self._monitor_scheduler_service is None:
        self._monitor_scheduler_service = MonitorSchedulerService(
            monitorear_use_case=self.monitorear_expedientes_use_case(),
            config=self.settings().monitoreo,
            json_sistema_path=self.json_sistema_path(),
            workspaces_dir=self.workspaces_dir(),
            monitoreo_service=self.monitoreo_service(),
            settings=self.settings()  # ← NUEVO
        )
    return self._monitor_scheduler_service
```

---

## 5. Cambios en Frontend

### 5.1 Types TypeScript

**Archivo**: `Sistema_v6/frontend/src/types/monitoreo.ts`

#### Cambio 1: Interface `ConfiguracionMonitoreo` (líneas 39-52)

**ANTES**:
```typescript
export interface ConfiguracionMonitoreo {
  id: number
  usuario_id: number
  activo: boolean
  frecuencia: FrecuenciaMonitoreo
  notificar_email: boolean
  notificar_sistema: boolean
  hora_inicio?: string
  hora_fin?: string
  dias_semana?: number[]
  created_at: string
  updated_at: string
}
```

**DESPUÉS**:
```typescript
export interface ConfiguracionMonitoreo {
  id: number
  usuario_id: number
  activo: boolean
  frecuencia: FrecuenciaMonitoreo
  notificar_email: boolean
  notificar_sistema: boolean
  auto_actualizar: boolean  // ← NUEVO
  hora_inicio?: string
  hora_fin?: string
  dias_semana?: number[]
  created_at: string
  updated_at: string
}
```

#### Cambio 2: Interface `ActualizarMonitoreo` (líneas 118-126)

**ANTES**:
```typescript
export interface ActualizarMonitoreo {
  activo?: boolean
  frecuencia?: FrecuenciaMonitoreo
  notificar_email?: boolean
  notificar_sistema?: boolean
  hora_inicio?: string
  hora_fin?: string
  dias_semana?: number[]
}
```

**DESPUÉS**:
```typescript
export interface ActualizarMonitoreo {
  activo?: boolean
  frecuencia?: FrecuenciaMonitoreo
  notificar_email?: boolean
  notificar_sistema?: boolean
  auto_actualizar?: boolean  // ← NUEVO
  hora_inicio?: string
  hora_fin?: string
  dias_semana?: number[]
}
```

### 5.2 Component UI

**Archivo**: `Sistema_v6/frontend/src/components/settings/ConfiguracionMonitoreo.tsx`

#### Cambio 1: Agregar import (línea 12)

**ANTES**:
```typescript
import { Activity, Save, Clock, Calendar, Settings, AlertCircle } from 'lucide-react'
```

**DESPUÉS**:
```typescript
import { Activity, Save, Clock, Calendar, Settings, AlertCircle, RefreshCw } from 'lucide-react'
```

#### Cambio 2: Actualizar schema Zod (líneas 19-27)

**ANTES**:
```typescript
const monitoreoSchema = z.object({
  activo: z.boolean(),
  frecuencia: z.enum(['5min', '15min', '30min', '1hora', '3horas', '6horas', '12horas', '24horas']),
  notificar_email: z.boolean(),
  notificar_sistema: z.boolean(),
  hora_inicio: z.string().min(5).max(5),
  hora_fin: z.string().min(5).max(5),
  dias_semana: z.array(z.number()).min(1),
})
```

**DESPUÉS**:
```typescript
const monitoreoSchema = z.object({
  activo: z.boolean(),
  frecuencia: z.enum(['5min', '15min', '30min', '1hora', '3horas', '6horas', '12horas', '24horas']),
  notificar_email: z.boolean(),
  notificar_sistema: z.boolean(),
  auto_actualizar: z.boolean(),  // ← NUEVO
  hora_inicio: z.string().min(5).max(5),
  hora_fin: z.string().min(5).max(5),
  dias_semana: z.array(z.number()).min(1),
})
```

#### Cambio 3: Actualizar defaultValues (líneas 69-78)

**ANTES**:
```typescript
defaultValues: {
  activo: true,
  frecuencia: '30min',
  notificar_email: false,
  notificar_sistema: true,
  hora_inicio: '08:00',
  hora_fin: '18:00',
  dias_semana: [1, 2, 3, 4, 5],
},
```

**DESPUÉS**:
```typescript
defaultValues: {
  activo: true,
  frecuencia: '30min',
  notificar_email: false,
  notificar_sistema: true,
  auto_actualizar: false,  // ← NUEVO
  hora_inicio: '08:00',
  hora_fin: '18:00',
  dias_semana: [1, 2, 3, 4, 5],
},
```

#### Cambio 4: Actualizar reset en useEffect (líneas 88-96)

**ANTES**:
```typescript
reset({
  activo: configMonitoreo.activo,
  frecuencia: configMonitoreo.frecuencia as MonitoreoForm['frecuencia'],
  notificar_email: configMonitoreo.notificar_email,
  notificar_sistema: configMonitoreo.notificar_sistema,
  hora_inicio: configMonitoreo.hora_inicio || '08:00',
  hora_fin: configMonitoreo.hora_fin || '18:00',
  dias_semana: configMonitoreo.dias_semana || [1, 2, 3, 4, 5],
}, { keepDefaultValues: false })
```

**DESPUÉS**:
```typescript
reset({
  activo: configMonitoreo.activo,
  frecuencia: configMonitoreo.frecuencia as MonitoreoForm['frecuencia'],
  notificar_email: configMonitoreo.notificar_email,
  notificar_sistema: configMonitoreo.notificar_sistema,
  auto_actualizar: configMonitoreo.auto_actualizar ?? false,  // ← NUEVO
  hora_inicio: configMonitoreo.hora_inicio || '08:00',
  hora_fin: configMonitoreo.hora_fin || '18:00',
  dias_semana: configMonitoreo.dias_semana || [1, 2, 3, 4, 5],
}, { keepDefaultValues: false })
```

#### Cambio 5: Actualizar onSubmit (líneas 146-154)

**ANTES**:
```typescript
await monitoreoApi.actualizarConfiguracion({
  activo: monitoreoData.activo,
  frecuencia: monitoreoData.frecuencia,
  notificar_email: monitoreoData.notificar_email,
  notificar_sistema: monitoreoData.notificar_sistema,
  hora_inicio: monitoreoData.hora_inicio,
  hora_fin: monitoreoData.hora_fin,
  dias_semana: monitoreoData.dias_semana,
})
```

**DESPUÉS**:
```typescript
await monitoreoApi.actualizarConfiguracion({
  activo: monitoreoData.activo,
  frecuencia: monitoreoData.frecuencia,
  notificar_email: monitoreoData.notificar_email,
  notificar_sistema: monitoreoData.notificar_sistema,
  auto_actualizar: monitoreoData.auto_actualizar,  // ← NUEVO
  hora_inicio: monitoreoData.hora_inicio,
  hora_fin: monitoreoData.hora_fin,
  dias_semana: monitoreoData.dias_semana,
})
```

#### Cambio 6: Agregar checkbox UI (DESPUÉS línea 278)

**Localizar** el checkbox de "Monitoreo activo" (aproximadamente línea 263-278):
```tsx
{/* Monitoreo activo */}
<label className="flex items-center justify-between p-4 rounded-lg border border-green-200 dark:border-green-800 cursor-pointer hover:bg-green-50 dark:hover:bg-green-900/20">
  <div>
    <div className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
      <Activity className="h-4 w-4 text-green-600 dark:text-green-400" />
      Monitoreo activo
    </div>
    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
      Habilita o deshabilita la verificación automática de expedientes
    </div>
  </div>
  <input
    {...register('activo')}
    type="checkbox"
    className="w-5 h-5 text-green-600 rounded focus:ring-green-500"
  />
</label>
```

**Agregar DESPUÉS** de ese checkbox:

```tsx
{/* Auto-actualizar expedientes con cambios */}
<label className="flex items-center justify-between p-4 rounded-lg border border-blue-200 dark:border-blue-800 cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20">
  <div>
    <div className="text-sm font-medium text-gray-900 dark:text-white flex items-center gap-2">
      <RefreshCw className="h-4 w-4 text-blue-600 dark:text-blue-400" />
      Auto-actualizar expedientes con cambios
    </div>
    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
      Al detectar cambios, descarga automáticamente nuevas actuaciones y archivos.
      La actualización se ejecuta en segundo plano sin bloquear el monitoreo.
    </div>
  </div>
  <input
    {...register('auto_actualizar')}
    type="checkbox"
    className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
  />
</label>
```

---

## 6. Flujo de Ejecución

### 6.1 Diagrama de Secuencia Completo

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌─────────┐   ┌──────────┐
│ Usuario │   │ Frontend │   │  Router  │   │  Service  │   │  Repo   │   │   BD     │
└────┬────┘   └─────┬────┘   └─────┬────┘   └─────┬─────┘   └────┬────┘   └─────┬────┘
     │              │                │               │              │              │
     │ 1. Habilita  │                │               │              │              │
     │   checkbox   │                │               │              │              │
     ├─────────────>│                │               │              │              │
     │              │                │               │              │              │
     │              │ 2. PUT /config │               │              │              │
     │              │   {auto_act:T} │               │              │              │
     │              ├───────────────>│               │              │              │
     │              │                │               │              │              │
     │              │                │ 3. actualizar │              │              │
     │              │                │   (..., T)    │              │              │
     │              │                ├──────────────>│              │              │
     │              │                │               │              │              │
     │              │                │               │ 4. UPDATE    │              │
     │              │                │               │   auto_act=T │              │
     │              │                │               ├─────────────>│              │
     │              │                │               │              │              │
     │              │                │               │              │ 5. UPDATE    │
     │              │                │               │              │   monit_conf │
     │              │                │               │              ├─────────────>│
     │              │                │               │              │              │
     │              │ 6. 200 OK      │               │              │              │
     │              │<───────────────┴───────────────┴──────────────┘              │
     │              │                                                               │
     │ 7. Toast     │                                                               │
     │  "Guardado"  │                                                               │
     │<─────────────┤                                                               │
     │              │                                                               │

    ... Tiempo pasa, scheduler ejecuta verificación ...

┌──────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌─────────┐
│Scheduler │   │ Detector │   │  Service  │   │UseCase   │   │ Gestor  │
└────┬─────┘   └─────┬────┘   └─────┬─────┘   └────┬─────┘   └────┬────┘
     │               │               │              │              │
     │ 8. verificar  │               │              │              │
     ├──────────────>│               │              │              │
     │               │               │              │              │
     │  9. cambios   │               │              │              │
     │<──────────────┤               │              │              │
     │               │               │              │              │
     │ 10. lee config│               │              │              │
     │   auto_act=T  │               │              │              │
     ├───────────────┴──────────────>│              │              │
     │                               │              │              │
     │ 11. registra cambio en BD     │              │              │
     ├───────────────────────────────┘              │              │
     │                                               │              │
     │ 12. lanza actualización (asyncio.create_task) │              │
     ├──────────────────────────────────────────────>│              │
     │ (NO espera)                                   │              │
     │                                               │              │
     │ 13. continúa verificando                      │              │
     │     otros expedientes...                      │              │
     │                                               │              │
     │                              ... Background ...              │
     │                                               │              │
     │                                               │ 14. obtiene  │
     │                                               │   credenciales│
     │                                               ├──────┐       │
     │                                               │<─────┘       │
     │                                               │              │
     │                                               │ 15. procesar │
     │                                               │   [expediente]│
     │                                               ├─────────────>│
     │                                               │              │
     │                                               │              │ 16. login PJN
     │                                               │              │ 17. extrae
     │                                               │              │ 18. descarga
     │                                               │              │
     │                                               │ 19. resumen  │
     │                                               │<─────────────┤
     │                                               │              │
     │                                               │ 20. registra │
     │                                               │     fin en BD│
     │                                               ├──────┐       │
     │                                               │<─────┘       │
     │                                               │              │
```

### 6.2 Escenarios de Uso

#### Escenario 1: Actualización Exitosa

```
09:00:00 - Usuario habilita "Auto-actualizar" en UI
09:00:01 - Backend guarda auto_actualizar=TRUE en BD
09:15:00 - Scheduler ejecuta verificación periódica (frecuencia: 15min)
09:15:05 - DetectorCambios detecta cambio en FRE-010171-2019: nueva_actuacion
09:15:06 - Scheduler registra cambio en tabla cambios_detectados
09:15:07 - Scheduler lee config: auto_actualizar=TRUE
09:15:08 - Scheduler verifica tipo: 'nueva_actuacion' ∈ TIPOS_AUTO_ACTUALIZABLES ✓
09:15:09 - Scheduler lanza ActualizarExpedienteUseCase en background
09:15:10 - Scheduler continúa verificando otros expedientes (NO espera)

          ... Background task ...

09:15:11 - UseCase registra inicio en auto_actualizaciones_log (estado='procesando')
09:15:12 - UseCase obtiene credenciales usuario desde BD (desencriptadas)
09:15:13 - UseCase configura GestorBatch (headless=True, procesar_con_pdf=True)
09:15:14 - GestorBatch inicia: login PJN con credenciales
09:15:20 - GestorBatch busca expediente FRE-010171-2019
09:15:25 - GestorBatch extrae actuaciones (15 nuevas)
09:15:30 - GestorBatch descarga archivos adjuntos (3 PDFs)
09:17:15 - GestorBatch finaliza: 15 actuaciones, 3 archivos, workspace actualizado
09:17:16 - UseCase registra fin: estado='completado', tiempo=125.5s
09:17:17 - Log: "[AUTO-ACT] ✓ Actualización exitosa: FRE-010171-2019 (3 archivos, 125.50s)"
```

#### Escenario 2: Auto-Actualización Deshabilitada

```
09:00:00 - Usuario NO marca checkbox "Auto-actualizar" (o lo desmarca)
09:00:01 - Backend guarda auto_actualizar=FALSE en BD
09:15:00 - Scheduler ejecuta verificación periódica
09:15:05 - DetectorCambios detecta cambio en FRE-010171-2019: nueva_actuacion
09:15:06 - Scheduler registra cambio en tabla cambios_detectados
09:15:07 - Scheduler lee config: auto_actualizar=FALSE
09:15:08 - Scheduler NO lanza actualización
09:15:09 - Log: "○ Auto-actualización deshabilitada"
09:15:10 - Scheduler continúa verificando otros expedientes
```

#### Escenario 3: Error - Credenciales No Encontradas

```
09:00:00 - Usuario habilita "Auto-actualizar"
09:15:05 - Scheduler detecta cambio en FRE-010171-2019
09:15:09 - Scheduler lanza ActualizarExpedienteUseCase en background

          ... Background task ...

09:15:11 - UseCase registra inicio en auto_actualizaciones_log (estado='procesando')
09:15:12 - UseCase intenta obtener credenciales usuario
09:15:13 - ERROR: Usuario no tiene credenciales PJN configuradas
09:15:14 - UseCase registra fin: estado='error', error_mensaje="No se encontraron credenciales PJN"
09:15:15 - Log: "[AUTO-ACT] ✗ Error: No se encontraron credenciales PJN: usuario_id=1"
```

#### Escenario 4: Cambio No Actualizable

```
09:15:05 - Scheduler detecta cambio en FRE-010171-2019: cambio_dependencia
09:15:07 - Scheduler lee config: auto_actualizar=TRUE
09:15:08 - Scheduler verifica tipo: 'cambio_dependencia' ∉ TIPOS_AUTO_ACTUALIZABLES ✗
09:15:09 - Scheduler NO lanza actualización
09:15:10 - Log: "[AUTO-ACT] Cambio tipo 'cambio_dependencia' no requiere actualización completa"
09:15:11 - Scheduler continúa verificando otros expedientes
```

---

## 7. Plan de Implementación

### 7.1 Orden de Ejecución (Fases)

| Fase | Descripción | Archivos | Tiempo | Depende de |
|------|-------------|----------|--------|------------|
| **1** | **Base de Datos** | Migration SQL | 30 min | - |
| **2** | **Backend - Schemas y Repository** | 2 archivos | 1 hora | Fase 1 |
| **3** | **Backend - Service** | 1 archivo | 20 min | Fase 2 |
| **4** | **Backend - Use Case** | 1 archivo nuevo | 2 horas | Fase 2 |
| **5** | **Backend - Scheduler** | 1 archivo | 1.5 horas | Fase 4 |
| **6** | **Backend - DI Container** | 1 archivo | 20 min | Fase 5 |
| **7** | **Frontend - Types** | 1 archivo | 15 min | - |
| **8** | **Frontend - UI** | 1 archivo | 45 min | Fase 7 |
| **9** | **Testing** | Manual | 1.5 horas | Todas |

### 7.2 Detalle por Fase

#### Fase 1: Base de Datos (30 min)

**Objetivo**: Crear campo `auto_actualizar` y tabla `auto_actualizaciones_log`

**Pasos**:
1. Crear archivo `010_add_auto_actualizar.sql`
2. Ejecutar migration con mysql CLI
3. Verificar columna creada: `DESCRIBE monitoreo_configuracion`
4. Verificar tabla creada: `SHOW CREATE TABLE auto_actualizaciones_log`

**Criterio de éxito**:
- [ ] Columna `auto_actualizar` existe en `monitoreo_configuracion`
- [ ] Tabla `auto_actualizaciones_log` creada con todas las columnas
- [ ] Foreign key a `cambios_detectados` funciona
- [ ] Índices creados

---

#### Fase 2: Backend - Schemas y Repository (1 hora)

**Objetivo**: Agregar campo `auto_actualizar` en schemas y métodos de repository

**Pasos**:
1. Modificar `monitoreo_schemas.py`:
   - Agregar campo en `ConfiguracionMonitoreoResponse`
   - Agregar campo en `ActualizarConfiguracionRequest`
2. Modificar `monitoreo_repository.py`:
   - Actualizar `crear_configuracion()` con parámetro `auto_actualizar`
   - Actualizar query INSERT
   - Actualizar `actualizar_configuracion()` con lógica para `auto_actualizar`
   - Agregar métodos `registrar_auto_actualizacion_inicio()` y `registrar_auto_actualizacion_fin()`

**Criterio de éxito**:
- [ ] Schemas tienen campo `auto_actualizar`
- [ ] `crear_configuracion()` acepta parámetro `auto_actualizar`
- [ ] `actualizar_configuracion()` actualiza campo `auto_actualizar`
- [ ] Métodos de log funcionan correctamente

**Test rápido**:
```python
# En shell Python
from infrastructure.persistence.monitoreo_repository import MonitoreoRepository
repo = MonitoreoRepository()

# Test crear con auto_actualizar
config_id = repo.crear_configuracion(usuario_id=999, auto_actualizar=True)
config = repo.obtener_configuracion(999)
assert config['auto_actualizar'] == True

# Test actualizar
repo.actualizar_configuracion(999, auto_actualizar=False)
config = repo.obtener_configuracion(999)
assert config['auto_actualizar'] == False
```

---

#### Fase 3: Backend - Service (20 min)

**Objetivo**: Agregar parámetro `auto_actualizar` en service

**Pasos**:
1. Modificar `monitoreo_service.py`:
   - Agregar parámetro `auto_actualizar` en `actualizar_configuracion()`
   - Agregar lógica para incluir en kwargs

**Criterio de éxito**:
- [ ] Service acepta parámetro `auto_actualizar`
- [ ] Parámetro se pasa correctamente al repository

**Test rápido**:
```python
from application.services.monitoreo_service import MonitoreoService
service = MonitoreoService()

# Test actualizar
service.actualizar_configuracion(usuario_id=999, auto_actualizar=True)
config = service.obtener_configuracion(999)
assert config['auto_actualizar'] == True
```

---

#### Fase 4: Backend - Use Case (2 horas)

**Objetivo**: Crear `ActualizarExpedienteUseCase` completo

**Pasos**:
1. Crear archivo `actualizar_expediente_use_case.py`
2. Implementar dataclasses: `ActualizarExpedienteCommand`, `ActualizarExpedienteResponse`
3. Implementar clase `ActualizarExpedienteUseCase`:
   - Método `execute()` con toda la lógica
   - Método `_obtener_credenciales_usuario()`
4. Agregar logging detallado con prefijo `[AUTO-ACT]`
5. Agregar manejo de errores robusto

**Criterio de éxito**:
- [ ] Archivo creado con imports correctos
- [ ] Use case acepta `ActualizarExpedienteCommand`
- [ ] Registra inicio/fin en `auto_actualizaciones_log`
- [ ] Obtiene credenciales correctamente
- [ ] Ejecuta `GestorBatch.procesar_seleccionados()`
- [ ] Maneja errores y los registra en log

**Test manual**:
```python
# Test en shell Python (requiere credenciales PJN)
from application.use_cases.actualizar_expediente_use_case import (
    ActualizarExpedienteUseCase,
    ActualizarExpedienteCommand
)
from infrastructure.persistence.monitoreo_repository import MonitoreoRepository
from infrastructure.config import settings

import asyncio

repo = MonitoreoRepository()
use_case = ActualizarExpedienteUseCase(
    monitoreo_repository=repo,
    settings=settings
)

command = ActualizarExpedienteCommand(
    expediente_numero="FRE-010171-2019",
    usuario_id=1,
    cambio_id=1,
    tipo_cambio="nueva_actuacion",
    headless=True,
    descargar_archivos=True
)

# Ejecutar
result = asyncio.run(use_case.execute(command))
print(result)
```

---

#### Fase 5: Backend - Scheduler (1.5 horas)

**Objetivo**: Integrar auto-actualización en scheduler

**Pasos**:
1. Modificar `monitor_scheduler_service.py`:
   - Agregar constante `TIPOS_AUTO_ACTUALIZABLES`
   - Actualizar constructor con parámetro `settings`
   - Modificar `_ejecutar_verificacion_expedientes()` para leer config y lanzar actualizaciones
   - Agregar método `_ejecutar_auto_actualizacion()`
2. Probar que no rompe scheduler existente

**Criterio de éxito**:
- [ ] Scheduler lee `auto_actualizar` de configuración
- [ ] Scheduler verifica tipo de cambio contra `TIPOS_AUTO_ACTUALIZABLES`
- [ ] Scheduler lanza `asyncio.create_task()` sin esperar
- [ ] Scheduler continúa verificando otros expedientes
- [ ] Logs muestran `[AUTO-ACT]` cuando lanza actualización

**Test manual**:
1. Iniciar scheduler
2. Forzar cambio editando JSON sistema
3. Esperar que scheduler detecte cambio
4. Verificar logs: debe mostrar "[AUTO-ACT] Lanzando actualización"
5. Verificar tabla `auto_actualizaciones_log`: debe tener registro

---

#### Fase 6: Backend - DI Container (20 min)

**Objetivo**: Registrar use case en container y pasar settings a scheduler

**Pasos**:
1. Modificar `di_container.py`:
   - Agregar atributo `_actualizar_expediente_use_case`
   - Agregar método `actualizar_expediente_use_case()`
   - Modificar `monitor_scheduler_service()` para pasar `settings`

**Criterio de éxito**:
- [ ] Container puede crear `ActualizarExpedienteUseCase`
- [ ] Scheduler recibe `settings` en constructor
- [ ] No hay errores de import

---

#### Fase 7: Frontend - Types (15 min)

**Objetivo**: Agregar campo `auto_actualizar` en types TypeScript

**Pasos**:
1. Modificar `types/monitoreo.ts`:
   - Agregar campo en `ConfiguracionMonitoreo`
   - Agregar campo en `ActualizarMonitoreo`

**Criterio de éxito**:
- [ ] TypeScript compila sin errores
- [ ] Tipos actualizados correctamente

---

#### Fase 8: Frontend - UI (45 min)

**Objetivo**: Agregar checkbox en UI de configuración

**Pasos**:
1. Modificar `ConfiguracionMonitoreo.tsx`:
   - Agregar import de `RefreshCw`
   - Actualizar schema Zod
   - Actualizar defaultValues
   - Actualizar reset en useEffect
   - Actualizar onSubmit
   - Agregar checkbox UI después de "Monitoreo activo"
2. Verificar que frontend compila
3. Verificar que UI se ve correcta

**Criterio de éxito**:
- [ ] Checkbox aparece en UI
- [ ] Checkbox está después de "Monitoreo activo"
- [ ] Texto descriptivo es claro
- [ ] Checkbox funciona (se puede marcar/desmarcar)
- [ ] Al guardar, valor se persiste
- [ ] Al recargar página, valor se mantiene

---

#### Fase 9: Testing (1.5 horas)

**Objetivo**: Validar funcionalidad end-to-end

**Pasos**:
1. **Test básico UI**:
   - [ ] Acceder a Configuración > Monitoreo
   - [ ] Verificar checkbox visible
   - [ ] Marcar checkbox
   - [ ] Guardar
   - [ ] Recargar página
   - [ ] Verificar checkbox sigue marcado

2. **Test funcional completo**:
   - [ ] Habilitar auto-actualización
   - [ ] Identificar expediente monitoreado
   - [ ] Editar JSON sistema: cambiar `ultima_actuacion` del expediente
   - [ ] Esperar que scheduler ejecute (según frecuencia configurada)
   - [ ] Verificar logs backend: debe mostrar "[AUTO-ACT] Lanzando actualización"
   - [ ] Verificar tabla `cambios_detectados`: debe tener registro nuevo
   - [ ] Verificar tabla `auto_actualizaciones_log`: debe tener registro con estado='completado'
   - [ ] Verificar workspace: debe tener actuaciones actualizadas

3. **Test error - sin credenciales**:
   - [ ] Eliminar credenciales PJN del usuario en BD
   - [ ] Forzar cambio en expediente
   - [ ] Verificar logs: debe mostrar error de credenciales
   - [ ] Verificar tabla log: estado='error', error_mensaje="No se encontraron credenciales"

4. **Test deshabilitado**:
   - [ ] Deshabilitar checkbox auto-actualizar
   - [ ] Guardar
   - [ ] Forzar cambio en expediente
   - [ ] Verificar logs: debe mostrar "Auto-actualización deshabilitada"
   - [ ] Verificar que NO se lanza actualización

**Queries de validación**:
```sql
-- Ver configuración actual
SELECT auto_actualizar FROM monitoreo_configuracion WHERE usuario_id = 1;

-- Ver últimas auto-actualizaciones
SELECT * FROM auto_actualizaciones_log ORDER BY fecha_inicio DESC LIMIT 5;

-- Ver cambios detectados con auto-actualización
SELECT
    cd.expediente_numero,
    cd.tipo_cambio,
    cd.descripcion,
    cd.fecha_deteccion,
    aal.estado as auto_act_estado,
    aal.total_actuaciones,
    aal.archivos_descargados,
    aal.tiempo_procesamiento_seg,
    aal.error_mensaje
FROM cambios_detectados cd
LEFT JOIN auto_actualizaciones_log aal ON cd.id = aal.cambio_id
ORDER BY cd.fecha_deteccion DESC
LIMIT 10;

-- Estadísticas de auto-actualizaciones
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN estado='completado' THEN 1 ELSE 0 END) as exitosas,
    SUM(CASE WHEN estado='error' THEN 1 ELSE 0 END) as fallidas,
    AVG(tiempo_procesamiento_seg) as tiempo_promedio_seg,
    AVG(archivos_descargados) as archivos_promedio
FROM auto_actualizaciones_log;
```

---

### 7.3 Checklist Completo

```
FASE 1: BASE DE DATOS
[ ] Crear 010_add_auto_actualizar.sql
[ ] Ejecutar migration
[ ] Verificar columna auto_actualizar
[ ] Verificar tabla auto_actualizaciones_log

FASE 2: BACKEND - SCHEMAS Y REPOSITORY
[ ] Modificar ConfiguracionMonitoreoResponse
[ ] Modificar ActualizarConfiguracionRequest
[ ] Modificar crear_configuracion()
[ ] Modificar actualizar_configuracion()
[ ] Agregar registrar_auto_actualizacion_inicio()
[ ] Agregar registrar_auto_actualizacion_fin()

FASE 3: BACKEND - SERVICE
[ ] Modificar actualizar_configuracion() en service
[ ] Test manual service

FASE 4: BACKEND - USE CASE
[ ] Crear actualizar_expediente_use_case.py
[ ] Implementar ActualizarExpedienteCommand
[ ] Implementar ActualizarExpedienteResponse
[ ] Implementar ActualizarExpedienteUseCase
[ ] Implementar execute()
[ ] Implementar _obtener_credenciales_usuario()
[ ] Agregar logging detallado
[ ] Test manual use case

FASE 5: BACKEND - SCHEDULER
[ ] Agregar constante TIPOS_AUTO_ACTUALIZABLES
[ ] Modificar constructor
[ ] Modificar _ejecutar_verificacion_expedientes()
[ ] Agregar _ejecutar_auto_actualizacion()
[ ] Test scheduler no roto

FASE 6: BACKEND - DI CONTAINER
[ ] Agregar atributo _actualizar_expediente_use_case
[ ] Agregar método actualizar_expediente_use_case()
[ ] Modificar monitor_scheduler_service()

FASE 7: FRONTEND - TYPES
[ ] Modificar ConfiguracionMonitoreo interface
[ ] Modificar ActualizarMonitoreo interface

FASE 8: FRONTEND - UI
[ ] Agregar import RefreshCw
[ ] Modificar schema Zod
[ ] Modificar defaultValues
[ ] Modificar reset
[ ] Modificar onSubmit
[ ] Agregar checkbox UI
[ ] Verificar compilación

FASE 9: TESTING
[ ] Test básico UI
[ ] Test funcional completo
[ ] Test error sin credenciales
[ ] Test deshabilitado
[ ] Queries de validación
[ ] Documentar resultados
```

---

## 8. Testing y Validación

### 8.1 Tests Unitarios (Recomendado, No en Scope Actual)

**Archivo**: `tests/unit/application/use_cases/test_actualizar_expediente_use_case.py`

```python
import pytest
from unittest.mock import Mock, patch
from application.use_cases.actualizar_expediente_use_case import (
    ActualizarExpedienteUseCase,
    ActualizarExpedienteCommand,
    ActualizarExpedienteResponse
)

@pytest.fixture
def mock_repo():
    return Mock()

@pytest.fixture
def mock_settings():
    settings = Mock()
    settings.paths.workspaces_dir = "/tmp/workspaces"
    return settings

@pytest.fixture
def use_case(mock_repo, mock_settings):
    return ActualizarExpedienteUseCase(
        monitoreo_repository=mock_repo,
        settings=mock_settings
    )

@pytest.mark.asyncio
async def test_execute_success(use_case, mock_repo):
    """Test actualización exitosa."""
    # Arrange
    command = ActualizarExpedienteCommand(
        expediente_numero="FRE-010171-2019",
        usuario_id=1,
        cambio_id=1,
        tipo_cambio="nueva_actuacion"
    )

    mock_repo.obtener_expediente.return_value = {'id': 1, 'expediente_caratula': 'Test'}
    mock_repo.registrar_auto_actualizacion_inicio.return_value = 1

    with patch.object(use_case, '_obtener_credenciales_usuario') as mock_creds:
        mock_creds.return_value = ('user', 'pass')

        with patch('extraccion_masiva.gestor_batch.GestorBatch') as mock_gestor:
            mock_resumen = Mock()
            mock_resumen.exitosos = 1
            mock_resumen.archivos_descargados = 3
            mock_gestor.return_value.procesar_seleccionados.return_value = mock_resumen

            # Act
            result = await use_case.execute(command)

            # Assert
            assert result.is_success
            assert result.value.success
            assert result.value.archivos_descargados == 3
            mock_repo.registrar_auto_actualizacion_fin.assert_called_once()

@pytest.mark.asyncio
async def test_execute_no_credentials(use_case, mock_repo):
    """Test falla cuando no hay credenciales."""
    # Arrange
    command = ActualizarExpedienteCommand(
        expediente_numero="FRE-010171-2019",
        usuario_id=1,
        cambio_id=1,
        tipo_cambio="nueva_actuacion"
    )

    mock_repo.obtener_expediente.return_value = {'id': 1}
    mock_repo.registrar_auto_actualizacion_inicio.return_value = 1

    with patch.object(use_case, '_obtener_credenciales_usuario') as mock_creds:
        mock_creds.return_value = None

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.is_failure
        assert "credenciales" in result.error.lower()
```

### 8.2 Tests de Integración (Manual)

#### Test 1: Flujo Completo Exitoso

**Precondiciones**:
- MySQL corriendo
- Backend corriendo
- Frontend corriendo
- Usuario con credenciales PJN configuradas
- Al menos 1 expediente monitoreado

**Pasos**:
1. Acceder a http://localhost:3000/configuracion
2. Navegar a tab "Monitoreo"
3. Marcar checkbox "Auto-actualizar expedientes con cambios"
4. Click "Guardar configuración"
5. Verificar toast "Configuración guardada"

6. Abrir MySQL Workbench:
   ```sql
   SELECT auto_actualizar FROM monitoreo_configuracion WHERE usuario_id = 1;
   ```
   **Esperado**: `auto_actualizar = 1`

7. Identificar expediente monitoreado:
   ```sql
   SELECT expediente_numero FROM expedientes_monitoreados WHERE usuario_id = 1 LIMIT 1;
   ```
   **Ejemplo**: `FRE-010171-2019`

8. Editar JSON sistema para forzar cambio:
   ```bash
   # Abrir archivo
   nano /Users/.../sintaXis/Sistema_v6/data/Sistema_json/sistema.json

   # Buscar expediente FRE-010171-2019
   # Cambiar "ultima_actuacion" a fecha futura: "2025-11-25"
   # Guardar
   ```

9. Esperar que scheduler ejecute verificación (según frecuencia configurada, ej: 15min)
   - O forzar ejecución manualmente si se tiene acceso

10. Monitorear logs backend:
    ```bash
    tail -f logs/sistema.log | grep AUTO-ACT
    ```

    **Esperado**:
    ```
    [AUTO-ACT] Lanzando actualización en background: FRE-010171-2019 (tipo: nueva_actuacion)
    [AUTO-ACT] ✓ Actualización lanzada en background: FRE-010171-2019
    [AUTO-ACT] Iniciando actualización: FRE-010171-2019 (tipo_cambio: nueva_actuacion)
    [AUTO-ACT] Ejecutando GestorBatch: FRE-010171-2019
    [AUTO-ACT] ✓ Actualización exitosa: FRE-010171-2019 (3 archivos, 125.50s)
    ```

11. Verificar tabla `auto_actualizaciones_log`:
    ```sql
    SELECT * FROM auto_actualizaciones_log
    WHERE expediente_numero = 'FRE-010171-2019'
    ORDER BY fecha_inicio DESC LIMIT 1;
    ```

    **Esperado**:
    - `estado = 'completado'`
    - `total_actuaciones > 0`
    - `archivos_descargados >= 0`
    - `error_mensaje IS NULL`
    - `tiempo_procesamiento_seg > 0`

12. Verificar workspace actualizado:
    ```bash
    ls -la /Users/.../sintaXis/Sistema_v6/data/workspaces/FRE-010171-2019/
    ```

    **Esperado**: Archivos recién modificados

**Resultado esperado**: ✅ PASS

---

#### Test 2: Auto-Actualización Deshabilitada

**Precondiciones**: Mismo que Test 1

**Pasos**:
1. Acceder a Configuración > Monitoreo
2. **Desmarcar** checkbox "Auto-actualizar expedientes con cambios"
3. Guardar
4. Verificar en BD: `auto_actualizar = 0`
5. Forzar cambio en expediente (editar JSON sistema)
6. Esperar scheduler
7. Verificar logs: debe mostrar "Auto-actualización deshabilitada"
8. Verificar tabla `auto_actualizaciones_log`: NO debe tener registro nuevo

**Resultado esperado**: ✅ PASS (sin actualización)

---

#### Test 3: Error - Credenciales No Encontradas

**Precondiciones**: Mismo que Test 1

**Pasos**:
1. Habilitar auto-actualización
2. Eliminar credenciales del usuario:
   ```sql
   UPDATE users
   SET pjn_usuario_encrypted = NULL, pjn_password_encrypted = NULL
   WHERE id = 1;
   ```
3. Forzar cambio en expediente
4. Esperar scheduler
5. Verificar logs: debe mostrar error de credenciales
6. Verificar tabla log:
   ```sql
   SELECT estado, error_mensaje FROM auto_actualizaciones_log
   ORDER BY fecha_inicio DESC LIMIT 1;
   ```
   **Esperado**:
   - `estado = 'error'`
   - `error_mensaje = 'No se encontraron credenciales PJN para el usuario'`

**Resultado esperado**: ✅ PASS (error manejado correctamente)

---

#### Test 4: Tipo de Cambio No Actualizable

**Precondiciones**: Mismo que Test 1

**Pasos**:
1. Habilitar auto-actualización
2. Editar JSON sistema: cambiar solo `dependencia` del expediente (no `ultima_actuacion`)
3. Esperar scheduler
4. Verificar logs: debe mostrar "Cambio tipo 'cambio_dependencia' no requiere actualización completa"
5. Verificar tabla log: NO debe tener registro nuevo para este cambio

**Resultado esperado**: ✅ PASS (cambio detectado pero no actualizado)

---

### 8.3 Queries de Validación SQL

```sql
-- =====================================================
-- Queries de Validación - Auto-Actualización
-- =====================================================

-- 1. Verificar configuración actual
SELECT
    usuario_id,
    activo,
    frecuencia,
    auto_actualizar,
    created_at,
    updated_at
FROM monitoreo_configuracion
WHERE usuario_id = 1;

-- 2. Ver últimas auto-actualizaciones (todas)
SELECT
    id,
    expediente_numero,
    tipo_cambio,
    estado,
    total_actuaciones,
    archivos_descargados,
    ROUND(tiempo_procesamiento_seg, 2) as tiempo_seg,
    error_mensaje,
    DATE_FORMAT(fecha_inicio, '%Y-%m-%d %H:%i:%s') as inicio,
    DATE_FORMAT(fecha_fin, '%Y-%m-%d %H:%i:%s') as fin
FROM auto_actualizaciones_log
ORDER BY fecha_inicio DESC
LIMIT 10;

-- 3. Ver auto-actualizaciones exitosas
SELECT
    expediente_numero,
    tipo_cambio,
    total_actuaciones,
    archivos_descargados,
    ROUND(tiempo_procesamiento_seg, 2) as tiempo_seg,
    DATE_FORMAT(fecha_inicio, '%Y-%m-%d %H:%i:%s') as fecha
FROM auto_actualizaciones_log
WHERE estado = 'completado'
ORDER BY fecha_inicio DESC
LIMIT 10;

-- 4. Ver auto-actualizaciones con error
SELECT
    expediente_numero,
    tipo_cambio,
    error_mensaje,
    DATE_FORMAT(fecha_inicio, '%Y-%m-%d %H:%i:%s') as fecha
FROM auto_actualizaciones_log
WHERE estado = 'error'
ORDER BY fecha_inicio DESC
LIMIT 10;

-- 5. Ver auto-actualizaciones en progreso
SELECT
    expediente_numero,
    tipo_cambio,
    estado,
    DATE_FORMAT(fecha_inicio, '%Y-%m-%d %H:%i:%s') as inicio,
    TIMESTAMPDIFF(SECOND, fecha_inicio, NOW()) as segundos_transcurridos
FROM auto_actualizaciones_log
WHERE estado IN ('pendiente', 'procesando')
ORDER BY fecha_inicio DESC;

-- 6. Ver cambios detectados con auto-actualización asociada
SELECT
    cd.id as cambio_id,
    cd.expediente_numero,
    cd.tipo_cambio,
    cd.descripcion,
    DATE_FORMAT(cd.fecha_deteccion, '%Y-%m-%d %H:%i:%s') as fecha_cambio,
    cd.leido,
    aal.id as auto_act_id,
    aal.estado as auto_act_estado,
    aal.total_actuaciones,
    aal.archivos_descargados,
    ROUND(aal.tiempo_procesamiento_seg, 2) as tiempo_seg,
    aal.error_mensaje
FROM cambios_detectados cd
LEFT JOIN auto_actualizaciones_log aal ON cd.id = aal.cambio_id
ORDER BY cd.fecha_deteccion DESC
LIMIT 20;

-- 7. Estadísticas generales de auto-actualizaciones
SELECT
    COUNT(*) as total_actualizaciones,
    SUM(CASE WHEN estado='completado' THEN 1 ELSE 0 END) as exitosas,
    SUM(CASE WHEN estado='error' THEN 1 ELSE 0 END) as fallidas,
    SUM(CASE WHEN estado IN ('pendiente', 'procesando') THEN 1 ELSE 0 END) as en_progreso,
    ROUND(AVG(CASE WHEN estado='completado' THEN tiempo_procesamiento_seg END), 2) as tiempo_promedio_seg,
    ROUND(AVG(CASE WHEN estado='completado' THEN total_actuaciones END), 1) as actuaciones_promedio,
    ROUND(AVG(CASE WHEN estado='completado' THEN archivos_descargados END), 1) as archivos_promedio
FROM auto_actualizaciones_log;

-- 8. Estadísticas por expediente
SELECT
    expediente_numero,
    COUNT(*) as total_actualizaciones,
    SUM(CASE WHEN estado='completado' THEN 1 ELSE 0 END) as exitosas,
    SUM(CASE WHEN estado='error' THEN 1 ELSE 0 END) as fallidas,
    ROUND(AVG(CASE WHEN estado='completado' THEN tiempo_procesamiento_seg END), 2) as tiempo_promedio_seg,
    MAX(fecha_inicio) as ultima_actualizacion
FROM auto_actualizaciones_log
GROUP BY expediente_numero
ORDER BY COUNT(*) DESC
LIMIT 10;

-- 9. Errores más comunes
SELECT
    error_mensaje,
    COUNT(*) as ocurrencias,
    GROUP_CONCAT(DISTINCT expediente_numero SEPARATOR ', ') as expedientes_afectados
FROM auto_actualizaciones_log
WHERE estado = 'error'
GROUP BY error_mensaje
ORDER BY COUNT(*) DESC;

-- 10. Performance: Actualizaciones más lentas
SELECT
    expediente_numero,
    tipo_cambio,
    total_actuaciones,
    archivos_descargados,
    ROUND(tiempo_procesamiento_seg, 2) as tiempo_seg,
    DATE_FORMAT(fecha_inicio, '%Y-%m-%d %H:%i:%s') as fecha
FROM auto_actualizaciones_log
WHERE estado = 'completado'
ORDER BY tiempo_procesamiento_seg DESC
LIMIT 10;

-- 11. Cambios detectados sin auto-actualización
-- (útil para verificar que tipos no actualizables funcionan)
SELECT
    cd.expediente_numero,
    cd.tipo_cambio,
    cd.descripcion,
    DATE_FORMAT(cd.fecha_deteccion, '%Y-%m-%d %H:%i:%s') as fecha
FROM cambios_detectados cd
LEFT JOIN auto_actualizaciones_log aal ON cd.id = aal.cambio_id
WHERE aal.id IS NULL
ORDER BY cd.fecha_deteccion DESC
LIMIT 10;

-- 12. Limpiar registros de prueba (CUIDADO: solo en desarrollo)
-- DELETE FROM auto_actualizaciones_log WHERE expediente_numero = 'TEST-000000-0000';
```

---

## 9. Riesgos y Mitigaciones

### 9.1 Riesgos Técnicos

#### Riesgo 1: Concurrencia - Múltiples Actualizaciones Simultáneas

**Descripción**: Si muchos expedientes cambian simultáneamente, se lanzarán muchas tareas `asyncio.create_task()` en paralelo, sobrecargando PJN y el servidor.

**Probabilidad**: Media
**Impacto**: Alto (rate limiting PJN, bloqueo IP)

**Mitigación**:
- **Actual**: `asyncio.create_task()` maneja concurrencia automáticamente
- **Mejora futura**: Implementar semáforo para limitar actualizaciones concurrentes:
  ```python
  # En MonitorSchedulerService
  self._semaforo_actualizaciones = asyncio.Semaphore(3)  # Máximo 3 simultáneas

  async def _ejecutar_auto_actualizacion(self, ...):
      async with self._semaforo_actualizaciones:
          # ... código actual ...
  ```

---

#### Riesgo 2: Credenciales Inválidas/Expiradas

**Descripción**: Usuario tiene credenciales configuradas pero inválidas (contraseña cambiada en PJN).

**Probabilidad**: Media
**Impacto**: Medio (actualizaciones fallan)

**Mitigación**:
- **Implementado**: Error se registra en `auto_actualizaciones_log` con `estado='error'`
- **Implementado**: Logging detallado con `[AUTO-ACT]`
- **Mejora futura**: Notificar al usuario por email/sistema

---

#### Riesgo 3: Timeouts en PJN

**Descripción**: PJN está lento o caído, `GestorBatch` tarda más de 600s.

**Probabilidad**: Baja
**Impacto**: Medio (actualización falla)

**Mitigación**:
- **Implementado**: `ConfigExtraccionMasiva` tiene `tiempo_maximo_segundos=600`
- **Implementado**: `GestorBatch` maneja timeouts y registra error
- **Implementado**: Error se registra en log con estado='error'
- **No implementado**: Reintentos automáticos (mejora futura)

---

#### Riesgo 4: Workspace Corruption

**Descripción**: Actualización parcial corrompe workspace (proceso interrumpido).

**Probabilidad**: Muy Baja
**Impacto**: Alto (pérdida de datos)

**Mitigación**:
- **Implementado**: `GestorBatch` ya maneja transaccionalidad
- **Implementado**: Si falla, workspace mantiene estado anterior
- **Mejora futura**: Backup automático antes de actualizar

---

#### Riesgo 5: Loops Infinitos de Actualización

**Descripción**: Actualización modifica expediente → Scheduler detecta cambio → Nueva actualización → Loop infinito.

**Probabilidad**: Muy Baja
**Impacto**: Alto (sobrecarga sistema)

**Mitigación**:
- **Implementado**: `DetectorCambios` compara estados ANTES y DESPUÉS
- **Implementado**: Si estado DESPUÉS = estado ANTERIOR, NO detecta cambio
- **Lógica**: Actualización no modifica campos monitoreados (`ultima_actuacion`, `situacion`, `dependencia`, `caratula`), solo descarga actuaciones/archivos

---

### 9.2 Riesgos de Performance

#### Riesgo 1: Carga en Base de Datos

**Descripción**: Cada cambio escribe 2 registros (cambios_detectados + auto_actualizaciones_log).

**Probabilidad**: Baja
**Impacto**: Bajo

**Mitigación**:
- **Implementado**: Índices en tablas (`idx_expediente`, `idx_estado`, `idx_fecha_inicio`)
- **Implementado**: Foreign key con `ON DELETE CASCADE` mantiene integridad
- **Mejora futura**: Limpieza periódica de registros antiguos (>90 días)

---

#### Riesgo 2: Carga en Scheduler

**Descripción**: `asyncio.create_task()` lanza tareas en background, pero scheduler puede acumular muchas tareas.

**Probabilidad**: Baja
**Impacto**: Medio

**Mitigación**:
- **Implementado**: `asyncio.create_task()` NO bloquea scheduler
- **Implementado**: Scheduler continúa verificando otros expedientes
- **Mejora futura**: Monitorear número de tareas activas con `asyncio.all_tasks()`

---

#### Riesgo 3: Carga en PJN

**Descripción**: Cada actualización = 1 login + 1 búsqueda + N descargas. Muchas actualizaciones → sobrecarga PJN.

**Probabilidad**: Media (si muchos cambios)
**Impacto**: Alto (rate limiting, bloqueo IP)

**Mitigación**:
- **Implementado**: Solo tipos específicos disparan actualización (`TIPOS_AUTO_ACTUALIZABLES`)
- **Implementado**: Headless mode reduce carga
- **Mejora futura**: Delay aleatorio entre actualizaciones (5-15s)
- **Mejora futura**: Semáforo para limitar concurrencia (ver Riesgo 1)

---

### 9.3 Riesgos de UX

#### Riesgo 1: Falta de Feedback Visual

**Descripción**: Usuario no ve cuando inicia/termina actualización.

**Probabilidad**: Alta
**Impacto**: Bajo (confusión usuario)

**Mitigación**:
- **Actual**: Logs backend tienen prefijo `[AUTO-ACT]` para debugging
- **Actual**: Tabla `auto_actualizaciones_log` registra todo
- **Mejora futura**: Endpoint GET `/api/v1/monitoreo/auto-actualizaciones/recientes`
- **Mejora futura**: UI en `MonitoreoPage` mostrando estado de actualizaciones

---

#### Riesgo 2: Configuración No Granular

**Descripción**: Usuario no puede configurar auto-actualización por expediente individual.

**Probabilidad**: Media
**Impacto**: Bajo

**Mitigación**:
- **Decisión**: Usar checkbox global por simplicidad en v1
- **Mejora futura**: Agregar checkbox por expediente en tabla de monitoreados

---

#### Riesgo 3: Sin Notificaciones de Completado

**Descripción**: Usuario no recibe notificación cuando completa actualización.

**Probabilidad**: Alta
**Impacto**: Bajo

**Mitigación**:
- **Actual**: Usuario debe revisar logs o tabla BD
- **Mejora futura**: Notificación sistema (toast) cuando completa
- **Mejora futura**: Notificación email con resumen

---

### 9.4 Riesgos de Seguridad

#### Riesgo 1: Credenciales en Memoria

**Descripción**: Credenciales desencriptadas en memoria durante actualización.

**Probabilidad**: Baja
**Impacto**: Alto (si hay vulnerabilidad)

**Mitigación**:
- **Implementado**: Credenciales se obtienen justo antes de usar
- **Implementado**: Credenciales en scope local del método
- **Implementado**: Python garbage collector limpia automáticamente
- **Mejora futura**: Limpiar explícitamente con `del username, del password`

---

#### Riesgo 2: Rate Limiting PJN

**Descripción**: PJN puede bloquear IP si detecta muchas requests rápidas.

**Probabilidad**: Media (si muchas actualizaciones)
**Impacto**: Alto (bloqueo temporal/permanente)

**Mitigación**:
- **Actual**: Solo tipos específicos disparan actualización
- **Mejora futura**: Delay aleatorio entre actualizaciones
- **Mejora futura**: Semáforo para limitar concurrencia
- **Mejora futura**: Backoff exponencial si detecta rate limiting

---

### 9.5 Matriz de Riesgos

| ID | Riesgo | Probabilidad | Impacto | Severidad | Mitigación |
|----|--------|--------------|---------|-----------|------------|
| T-1 | Concurrencia alta | Media | Alto | **ALTA** | Semáforo (futuro) |
| T-2 | Credenciales inválidas | Media | Medio | MEDIA | Logging + error handling ✅ |
| T-3 | Timeouts PJN | Baja | Medio | BAJA | Timeout config ✅ |
| T-4 | Workspace corruption | Muy Baja | Alto | BAJA | Transaccionalidad ✅ |
| T-5 | Loops infinitos | Muy Baja | Alto | BAJA | DetectorCambios lógica ✅ |
| P-1 | Carga BD | Baja | Bajo | BAJA | Índices ✅ |
| P-2 | Carga scheduler | Baja | Medio | BAJA | asyncio.create_task ✅ |
| P-3 | Carga PJN | Media | Alto | **MEDIA** | Tipos específicos ✅ + delay (futuro) |
| UX-1 | Sin feedback visual | Alta | Bajo | BAJA | Logging ✅ + UI (futuro) |
| UX-2 | No granular | Media | Bajo | BAJA | Global v1 ✅ + granular (futuro) |
| UX-3 | Sin notificaciones | Alta | Bajo | BAJA | Logs ✅ + notif (futuro) |
| S-1 | Credenciales memoria | Baja | Alto | MEDIA | Scope local ✅ + del (futuro) |
| S-2 | Rate limiting PJN | Media | Alto | **MEDIA** | Tipos específicos ✅ + delay (futuro) |

**Leyenda Severidad**:
- **ALTA**: Requiere mitigación antes de deploy
- **MEDIA**: Monitorear en producción
- **BAJA**: Aceptable, mejora futura

---

## 10. Mejoras Futuras

### 10.1 Corto Plazo (1-2 Semanas)

#### Mejora 1: UI para Ver Historial de Auto-Actualizaciones

**Descripción**: Agregar pestaña/página en Monitoreo para ver historial de `auto_actualizaciones_log`.

**Componentes**:
- Endpoint GET `/api/v1/monitoreo/auto-actualizaciones?limit=20&offset=0`
- Componente `AutoActualizacionesList.tsx`
- Filtros por estado, expediente, fecha

**Estimación**: 4-6 horas

---

#### Mejora 2: Notificación Toast al Completar

**Descripción**: Mostrar toast en frontend cuando completa actualización.

**Componentes**:
- WebSocket o SSE para push notification
- Toast con link a expediente actualizado

**Estimación**: 3-4 horas (si ya existe WebSocket)

---

#### Mejora 3: Configuración Granular por Expediente

**Descripción**: Checkbox individual en cada `MonitoreoCard` para habilitar/deshabilitar auto-actualización.

**Componentes**:
- Campo `auto_actualizar` en tabla `expedientes_monitoreados`
- Checkbox en `MonitoreoCard.tsx`
- Endpoint PUT `/api/v1/monitoreo/expedientes/{id}`

**Estimación**: 3-4 horas

---

### 10.2 Medio Plazo (3-4 Semanas)

#### Mejora 4: Reintentos Automáticos con Backoff

**Descripción**: Si falla actualización, reintentar automáticamente con backoff exponencial.

**Componentes**:
- Lógica de reintentos en `ActualizarExpedienteUseCase`
- Campo `intentos` en `auto_actualizaciones_log`
- Backoff: 5min → 15min → 30min → 1h

**Estimación**: 6-8 horas

---

#### Mejora 5: Rate Limiting y Semáforo

**Descripción**: Limitar número de actualizaciones concurrentes y agregar delay aleatorio.

**Componentes**:
- `asyncio.Semaphore(3)` en scheduler
- Delay aleatorio 5-15s entre actualizaciones
- Configuración en `monitoreo_configuracion.max_actualizaciones_concurrentes`

**Estimación**: 4-6 horas

---

#### Mejora 6: Métricas y Dashboard

**Descripción**: Panel con gráficos de actualizaciones exitosas/fallidas, tiempo promedio, etc.

**Componentes**:
- Endpoint GET `/api/v1/monitoreo/metricas`
- Componente `MetricasMonitoreo.tsx` con Recharts
- Gráficos: línea temporal, pie chart estados, bar chart por expediente

**Estimación**: 8-12 horas

---

### 10.3 Largo Plazo (1-2 Meses)

#### Mejora 7: Filtros Avanzados de Tipos Actualizables

**Descripción**: Permitir al usuario configurar qué tipos de cambio disparan auto-actualización.

**Componentes**:
- Campo JSON `tipos_actualizables` en `monitoreo_configuracion`
- UI con checkboxes para cada tipo
- Lógica en scheduler para leer configuración

**Estimación**: 6-8 horas

---

#### Mejora 8: Prioridad de Expedientes

**Descripción**: Actualizar expedientes de alta prioridad primero.

**Componentes**:
- Campo `prioridad` en `expedientes_monitoreados`
- Cola de prioridad en scheduler
- UI para configurar prioridad

**Estimación**: 10-15 horas

---

#### Mejora 9: Limpieza Automática de Logs Antiguos

**Descripción**: Job programado para eliminar registros de `auto_actualizaciones_log` >90 días.

**Componentes**:
- Job APScheduler diario
- Configuración `dias_retencion_historial` en `monitoreo_configuracion`
- Query DELETE con fecha

**Estimación**: 3-4 horas

---

#### Mejora 10: Notificaciones Email con Resumen

**Descripción**: Enviar email diario/semanal con resumen de actualizaciones.

**Componentes**:
- Job APScheduler diario
- Template email HTML
- Servicio de email (SMTP)

**Estimación**: 12-16 horas

---

## Apéndices

### A. Archivos del Proyecto

**Resumen de archivos afectados**:

| Categoría | Archivos | Acción |
|-----------|----------|--------|
| Base de Datos | 1 | Crear |
| Backend - Schemas | 1 | Modificar |
| Backend - Repository | 1 | Modificar |
| Backend - Service | 1 | Modificar |
| Backend - Use Case | 1 | Crear |
| Backend - Scheduler | 1 | Modificar |
| Backend - DI Container | 1 | Modificar |
| Frontend - Types | 1 | Modificar |
| Frontend - UI | 1 | Modificar |
| **TOTAL** | **9** | **7 mod + 2 crear** |

---

### B. Glosario

| Término | Definición |
|---------|------------|
| **Auto-actualización** | Proceso automático de descargar actuaciones y archivos de un expediente cuando el monitor detecta cambios |
| **Cambio actualizable** | Tipo de cambio que dispara auto-actualización (nueva_actuacion, cambio_situacion, multiples_cambios) |
| **Cambio no actualizable** | Tipo de cambio que NO dispara auto-actualización (cambio_dependencia, cambio_caratula) |
| **DetectorCambios** | Servicio que compara estados de expedientes y detecta cambios |
| **GestorBatch** | Clase que maneja extracción masiva y procesamiento de expedientes desde PJN |
| **Headless** | Modo de navegador sin interfaz gráfica (más rápido) |
| **Scheduler** | Servicio que ejecuta verificaciones periódicas en background (APScheduler) |
| **Workspace** | Directorio local con datos de un expediente (actuaciones, archivos, etc) |

---

### C. Referencias

**Documentos relacionados**:
- `PLAN_MEJORAS_SISTEMA_V6.md` - Plan maestro de mejoras
- `PLAN_IMPLEMENTACION_FUNCIONALIDADES.md` - Fases 1-8 de funcionalidades
- `migration 009_crear_tablas_monitoreo.sql` - Schema de monitoreo existente

**Archivos clave del código**:
- `application/services/detector_cambios.py` - Detección de cambios
- `extraccion_masiva/gestor_batch.py` - Procesamiento de expedientes
- `application/services/monitor_scheduler_service.py` - Scheduler periódico
- `infrastructure/persistence/monitoreo_repository.py` - Acceso a BD

---

### D. Contacto y Soporte

**Para consultas sobre este plan**:
- Crear issue en repositorio
- Etiquetar con `feature: auto-actualizacion`
- Mencionar a agente IA responsable

---

## Historial de Cambios del Plan

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-11-24 | 1.0 | Creación inicial del plan completo |

---

*Plan generado para seguimiento por agente IA - Sistema PJN v6*
*Fecha: 2025-11-24*
*Estimación total: 7-8 horas*
*Prioridad: Media-Alta*