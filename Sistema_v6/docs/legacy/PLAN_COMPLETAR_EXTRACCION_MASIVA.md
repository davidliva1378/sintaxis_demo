# 🎯 PLAN COMPLETO: Finalizar Implementación de Extracción Masiva

**Fecha de creación:** 2025-11-07
**Rama de trabajo:** `sintaxis_parcial2` → `claude/review-sintaxis-parcial2-011CUuHPSBCZ7juywst29TXV`
**Estado actual:** 45% completado (arquitectura y estructura OK, lógica de procesamiento faltante)
**Tiempo estimado total:** 12-16 horas

---

## 📊 DIAGNÓSTICO EJECUTIVO

### ✅ Lo que YA funciona (45%)
- Arquitectura limpia (DTOs, Use Cases, Ports)
- Gestor de sesiones con WebSocket
- Extracción del listado completo de expedientes (Fase 1)
- Estructura de GestorBatch (pause/resume/cancel)
- Frontend React con UI completa
- Callbacks y progreso en tiempo real

### ❌ Lo que FALTA (55%)
- **CRÍTICO:** Lógica real de procesamiento de expedientes (línea 252 de `gestor_batch.py`)
- Router REST deshabilitado (8 endpoints)
- WebSocket handler
- Integración con repository (guardar expedientes)
- Integración con procesador (clasificar actuaciones)
- Integración con gestor de estados
- Tests del flujo completo

### 🔴 PROBLEMA CRÍTICO IDENTIFICADO

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Línea:** 234-275
**Función:** `_procesar_expediente()`

```python
async def _procesar_expediente(...) -> ResultadoProcesamiento:
    try:
        # TODO: Aquí iría la lógica real de procesamiento del expediente  # ⚠️ LÍNEA 252
        # Por ahora, simulamos el procesamiento exitoso
        await asyncio.sleep(0.1)  # ⚠️ SOLO SIMULA - NO HACE NADA REAL

        return ResultadoProcesamiento(
            expediente=expediente,
            estado="success",
            mensaje="Expediente procesado correctamente"
        )
```

**Impacto:** El sistema extrae el listado pero NO procesa, clasifica, ni guarda los expedientes.

---

## 🗺️ ARQUITECTURA OBJETIVO

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTRACCIÓN MASIVA - FLUJO                    │
└─────────────────────────────────────────────────────────────────┘

1. EXTRACCIÓN DE LISTADO (✅ COMPLETO)
   ┌──────────────────────────────────────┐
   │ ExtractorMasivo                      │
   │  └─ extraer_listado_completo()       │ ✅ Funciona
   │      ├─ Navega con Playwright        │
   │      ├─ Extrae todas las páginas     │
   │      ├─ Emite callbacks de progreso  │
   │      └─ Guarda listado.json          │
   └──────────────────────────────────────┘
                    ↓
2. PROCESAMIENTO POR LOTES (❌ FALTA LÓGICA)
   ┌──────────────────────────────────────┐
   │ GestorBatch                          │
   │  └─ procesar_lote()                  │ ⚠️ Estructura OK
   │      └─ _procesar_expediente()       │ ❌ SOLO SIMULA
   │          ├─ Extraer actuaciones      │ ❌ FALTA
   │          ├─ Clasificar actuaciones   │ ❌ FALTA
   │          ├─ Detectar vencimientos    │ ❌ FALTA
   │          ├─ Guardar en repository    │ ❌ FALTA
   │          └─ Actualizar estados       │ ❌ FALTA
   └──────────────────────────────────────┘
                    ↓
3. EXPORTACIÓN (✅ COMPLETO)
   ┌──────────────────────────────────────┐
   │ Exportadores                         │
   │  ├─ exportar_json()                  │ ✅ Funciona
   │  ├─ exportar_excel()                 │ ✅ Funciona
   │  └─ exportar_csv()                   │ ✅ Funciona
   └──────────────────────────────────────┘
                    ↓
4. API REST (❌ DESHABILITADO)
   ┌──────────────────────────────────────┐
   │ Router REST                          │
   │  ├─ POST /masivo                     │ ❌ Comentado
   │  ├─ GET /{id}/progreso               │ ❌ Comentado
   │  ├─ POST /{id}/pausar                │ ❌ Comentado
   │  ├─ POST /{id}/reanudar              │ ❌ Comentado
   │  ├─ POST /{id}/cancelar              │ ❌ Comentado
   │  ├─ GET /{id}/resumen                │ ❌ Comentado
   │  ├─ GET /{id}/descargar/{fmt}        │ ❌ Comentado
   │  └─ WS /{id}/ws                      │ ❌ Comentado
   └──────────────────────────────────────┘
```

---

## 📋 PLAN DE IMPLEMENTACIÓN - 15 TAREAS

---

### **FASE 1: ANÁLISIS Y PREPARACIÓN** (1-2 horas)

---

#### **TAREA 1: Analizar dependencias y módulos existentes**

**Objetivo:** Identificar todos los módulos disponibles para integrar en el procesamiento.

**Archivos a revisar:**
1. `/Sistema_v6/extractor_inicial/procesamiento_expedientes.py`
   - Clase: `ProcesadorExpedientesInicial`
   - Método: `procesar_expedientes_extraidos()`
   - Dependencias: ClasificadorActuaciones, AnalizadorVencimientos, DetectorDuplicados

2. `/Sistema_v6/pjn/scraping/` (buscar módulos de extracción)
   - Identificar función para extraer actuaciones de un expediente
   - Verificar si existe navegación a expediente individual

3. `/Sistema_v6/application/ports/repositories.py`
   - Interface: `IExpedienteRepository`
   - Métodos: `guardar()`, `guardar_varios()`

4. `/Sistema_v6/configuracion/estados.py`
   - Clase: `GestorEstados`
   - Métodos: `actualizar_estado()`, `guardar_estados()`

**Entregable:**
- Documento: `ANALISIS_DEPENDENCIAS_EXTRACCION.md` con:
  - Lista de módulos disponibles
  - Firmas de funciones clave
  - Flujo de integración propuesto
  - Imports necesarios

**Criterios de éxito:**
- ✅ Identificadas todas las funciones necesarias
- ✅ Verificada compatibilidad de firmas
- ✅ Documentado flujo de datos entre módulos

**Comandos útiles:**
```bash
# Buscar funciones de extracción de actuaciones
grep -rn "def extraer_actuaciones\|async def extraer_actuaciones" Sistema_v6/pjn/

# Listar implementaciones de IExpedienteRepository
grep -rn "class.*IExpedienteRepository" Sistema_v6/infrastructure/

# Verificar GestorEstados
grep -rn "def actualizar_estado\|def guardar_estados" Sistema_v6/configuracion/
```

---

### **FASE 2: IMPLEMENTACIÓN DEL CORE** (6-8 horas)

---

#### **TAREA 2: Implementar extracción de actuaciones en _procesar_expediente()**

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Método:** `_procesar_expediente()` (líneas 234-275)

**Objetivo:** Reemplazar la simulación con lógica real de extracción de actuaciones.

**Pseudocódigo:**
```python
async def _procesar_expediente(
    self,
    expediente: Dict,
    descargar_adjuntos: bool,
    headless: bool
) -> ResultadoProcesamiento:
    """Procesar un expediente individual con lógica real."""

    try:
        numero = expediente.get("numero")
        logger.info(f"Procesando expediente {numero}")

        # 1. Crear contexto de navegación
        async with reutilizar_sesion_async() as (page, context, browser):

            # 2. Navegar al expediente específico
            #    - Usar URL del expediente
            #    - Esperar carga completa

            # 3. Extraer actuaciones completas
            #    - Usar función de Sistema_v6.pjn.scraping
            #    - Manejar paginación si existe
            #    - Extraer metadatos de cada actuación

            # 4. Descargar adjuntos (si configurado)
            if descargar_adjuntos:
                #    - Iterar actuaciones con adjuntos
                #    - Descargar PDFs
                #    - Guardar en estructura de carpetas

            # 5. Retornar resultado exitoso
            return ResultadoProcesamiento(
                expediente=expediente,
                estado="success",
                mensaje=f"Expediente {numero} procesado: {len(actuaciones)} actuaciones",
                metadata={
                    "actuaciones_count": len(actuaciones),
                    "adjuntos_descargados": count_adjuntos,
                }
            )

    except TimeoutError:
        return ResultadoProcesamiento(
            expediente=expediente,
            estado="error",
            mensaje="Timeout al procesar expediente",
            error="TimeoutError"
        )
    except Exception as e:
        logger.exception(f"Error procesando {numero}: {e}")
        return ResultadoProcesamiento(
            expediente=expediente,
            estado="error",
            mensaje="Error al procesar expediente",
            error=str(e)
        )
```

**Imports necesarios:**
```python
from Sistema_v6.pjn.auto_login import reutilizar_sesion_async
from Sistema_v6.pjn.scraping.actuaciones import extraer_actuaciones_completas
from Sistema_v6.configuracion.urls import construir_url_expediente
```

**Consideraciones:**
- ⚠️ Cada expediente abre su propia sesión de Playwright
- ⚠️ Manejar timeouts adecuadamente (default: 120s)
- ⚠️ Cerrar navegador correctamente con `async with`
- ⚠️ Loggear errores pero no detener el batch completo

**Criterios de éxito:**
- ✅ Extrae actuaciones reales del expediente
- ✅ Maneja errores sin romper el batch
- ✅ Descarga adjuntos si está configurado
- ✅ Retorna metadata útil para reportes

---

#### **TAREA 3: Integrar clasificación de actuaciones**

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Método:** `_procesar_expediente()` (añadir después de extracción)

**Objetivo:** Clasificar actuaciones extraídas con el procesador existente.

**Pseudocódigo:**
```python
# Dentro de _procesar_expediente(), después de extraer actuaciones:

# 6. Clasificar actuaciones
if self.procesador_expedientes:
    resultado_clasificacion = await self.procesador_expedientes.clasificar_actuaciones(
        expediente=expediente,
        actuaciones=actuaciones
    )

    # Agregar clasificaciones al resultado
    metadata["clasificaciones"] = resultado_clasificacion.get("categorias", {})
    metadata["utilidad_total"] = resultado_clasificacion.get("utilidad_total", "MEDIA")

    # Detectar vencimientos urgentes
    if self.config.get("analizar_vencimientos", True):
        vencimientos = self.procesador_expedientes.detectar_vencimientos_urgentes(
            actuaciones=actuaciones,
            dias_urgencia=self.config.get("dias_urgentes", 7)
        )

        if vencimientos:
            metadata["vencimientos_urgentes"] = vencimientos
            logger.warning(f"⚠️ Expediente {numero} tiene {len(vencimientos)} vencimientos urgentes")
```

**Modificar constructor de GestorBatch:**
```python
def __init__(
    self,
    umbral_errores: int = 5,
    callback_progreso: Optional[Callable] = None,
    timeout_por_expediente: int = 120,
    procesador_expedientes: Optional[ProcesadorExpedientesInicial] = None,  # 🆕 NUEVO
    config: Optional[Dict] = None,  # 🆕 NUEVO
):
    self.umbral_errores = umbral_errores
    self.callback_progreso = callback_progreso
    self.timeout_por_expediente = timeout_por_expediente
    self.procesador_expedientes = procesador_expedientes  # 🆕
    self.config = config or {}  # 🆕

    # ... resto del código
```

**Imports necesarios:**
```python
from Sistema_v6.extractor_inicial.procesamiento_expedientes import ProcesadorExpedientesInicial
```

**Criterios de éxito:**
- ✅ Actuaciones clasificadas por categoría
- ✅ Vencimientos urgentes detectados
- ✅ Metadata enriquecida en el resultado

---

#### **TAREA 4: Integrar guardado en repositorio**

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Método:** `_procesar_expediente()` (añadir después de clasificación)

**Objetivo:** Guardar expediente procesado en el repositorio.

**Pseudocódigo:**
```python
# Dentro de _procesar_expediente(), después de clasificar:

# 7. Convertir a entidad de dominio
from core.domain.entities import ExpedienteResumen, Actuacion

expediente_entidad = ExpedienteResumen(
    numero=expediente.get("numero"),
    caratula=expediente.get("caratula"),
    dependencia=expediente.get("dependencia"),
    situacion=expediente.get("situacion"),
    fecha_inicio=expediente.get("fecha_inicio"),
    ultima_actuacion=expediente.get("ultima_actuacion"),
    # ... otros campos
)

# 8. Guardar en repositorio
if self.repository:
    try:
        await self.repository.guardar(expediente_entidad)
        logger.info(f"✅ Expediente {numero} guardado en repositorio")
        metadata["guardado_en_repository"] = True
    except Exception as e:
        logger.error(f"❌ Error guardando expediente {numero}: {e}")
        metadata["guardado_en_repository"] = False
        metadata["error_guardado"] = str(e)
```

**Modificar constructor de GestorBatch:**
```python
def __init__(
    self,
    # ... parámetros existentes
    repository: Optional[IExpedienteRepository] = None,  # 🆕 NUEVO
):
    # ... código existente
    self.repository = repository  # 🆕
```

**Imports necesarios:**
```python
from application.ports.repositories import IExpedienteRepository
from core.domain.entities import ExpedienteResumen, Actuacion
```

**Criterios de éxito:**
- ✅ Expedientes guardados en el repositorio
- ✅ Errores de guardado no rompen el flujo
- ✅ Metadata indica si se guardó correctamente

---

#### **TAREA 5: Implementar actualización de estados**

**Archivo:** `Sistema_v6/extraccion_masiva/gestor_batch.py`
**Método:** `_procesar_expediente()` (añadir al final)

**Objetivo:** Actualizar el estado del expediente en el gestor de estados.

**Pseudocódigo:**
```python
# Dentro de _procesar_expediente(), al final:

# 9. Actualizar estado del expediente
if self.gestor_estados:
    try:
        # Determinar nuevo estado según resultado
        if resultado.estado == "success":
            nuevo_estado = EstadoExpediente.PROCESADO
        elif resultado.estado == "error":
            nuevo_estado = EstadoExpediente.ERROR_PROCESAMIENTO
        else:
            nuevo_estado = EstadoExpediente.OMITIDO

        self.gestor_estados.actualizar_estado(
            numero=numero,
            nuevo_estado=nuevo_estado
        )

        # Guardar cambios
        await self.gestor_estados.guardar_estados()

        logger.info(f"✅ Estado de {numero} actualizado a {nuevo_estado.value}")
        metadata["estado_actualizado"] = True

    except Exception as e:
        logger.error(f"❌ Error actualizando estado de {numero}: {e}")
        metadata["estado_actualizado"] = False
```

**Modificar constructor de GestorBatch:**
```python
def __init__(
    self,
    # ... parámetros existentes
    gestor_estados: Optional[GestorEstados] = None,  # 🆕 NUEVO
):
    # ... código existente
    self.gestor_estados = gestor_estados  # 🆕
```

**Imports necesarios:**
```python
from Sistema_v6.configuracion.estados import GestorEstados, EstadoExpediente
```

**Criterios de éxito:**
- ✅ Estados actualizados según resultado
- ✅ Estados persistidos en archivo
- ✅ Errores de estado no rompen el flujo

---

### **FASE 3: API REST Y WEBSOCKET** (3-4 horas)

---

#### **TAREA 6: Crear router de extracción masiva**

**Archivo NUEVO:** `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**Objetivo:** Crear los 8 endpoints REST documentados en el plan.

**Estructura:**
```python
"""Router REST para extracción masiva de expedientes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List

from application.dtos import (
    IniciarExtraccionMasivaCommand,
    IniciarExtraccionMasivaResponse,
    ProgresoExtraccionResponse,
    ResumenExtraccionResponse,
)
from application.use_cases import ExtraccionMasivaUseCase
from infrastructure.di_container import get_container

router = APIRouter()


def get_extraccion_use_case() -> ExtraccionMasivaUseCase:
    """Dependency para obtener el use case."""
    container = get_container()
    return container.extraccion_masiva_use_case()


# ========== ENDPOINT 1: Iniciar extracción masiva ==========
@router.post("/masivo", response_model=IniciarExtraccionMasivaResponse)
async def iniciar_extraccion_masiva(
    command: IniciarExtraccionMasivaCommand,
    background_tasks: BackgroundTasks,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """
    Inicia una extracción masiva de expedientes.

    El proceso se ejecuta en background y se puede monitorear vía WebSocket
    o consultando el endpoint de progreso.
    """
    # Iniciar sesión
    result = await use_case.iniciar_extraccion(command)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    response = result.value

    # Ejecutar extracción en background
    # TODO: Crear config_extractor desde command
    # TODO: Llamar use_case.ejecutar_extraccion_background()

    return response


# ========== ENDPOINT 2: Obtener progreso ==========
@router.get("/{session_id}/progreso", response_model=ProgresoExtraccionResponse)
async def obtener_progreso(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """Obtiene el progreso actual de una extracción."""
    # TODO: Implementar
    pass


# ========== ENDPOINT 3: Pausar extracción ==========
@router.post("/{session_id}/pausar")
async def pausar_extraccion(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """Pausa una extracción en progreso."""
    result = await use_case.pausar_extraccion(session_id)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return result.value


# ========== ENDPOINT 4: Reanudar extracción ==========
@router.post("/{session_id}/reanudar")
async def reanudar_extraccion(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """Reanuda una extracción pausada."""
    result = await use_case.reanudar_extraccion(session_id)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return result.value


# ========== ENDPOINT 5: Cancelar extracción ==========
@router.post("/{session_id}/cancelar")
async def cancelar_extraccion(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """Cancela una extracción en progreso o pausada."""
    result = await use_case.cancelar_extraccion(session_id)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return result.value


# ========== ENDPOINT 6: Obtener resumen ==========
@router.get("/{session_id}/resumen", response_model=ResumenExtraccionResponse)
async def obtener_resumen(
    session_id: str,
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """Obtiene el resumen final de una extracción completada."""
    # TODO: Implementar
    pass


# ========== ENDPOINT 7: Descargar reporte ==========
@router.get("/{session_id}/descargar/{formato}")
async def descargar_reporte(
    session_id: str,
    formato: str,  # json, excel, csv, html
    use_case: ExtraccionMasivaUseCase = Depends(get_extraccion_use_case),
):
    """
    Descarga el reporte de extracción en el formato especificado.

    Formatos soportados: json, excel, csv, html
    """
    # TODO: Implementar
    pass


# ========== ENDPOINT 8: WebSocket de progreso ==========
@router.websocket("/{session_id}/ws")
async def websocket_progreso(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket para recibir actualizaciones de progreso en tiempo real.

    El servidor envía mensajes JSON con el estado actual de la extracción.
    El cliente puede enviar 'ping' cada 25s para mantener la conexión.
    """
    # Importar handler
    from presentation.api.rest.websocket.extraccion_ws import websocket_progreso as handler
    await handler(websocket, session_id)
```

**Tareas específicas:**
1. Implementar lógica completa de cada endpoint
2. Agregar validaciones de entrada
3. Manejar errores específicos
4. Agregar documentación OpenAPI completa
5. Implementar tests unitarios

**Criterios de éxito:**
- ✅ 8 endpoints funcionan correctamente
- ✅ Validaciones de entrada implementadas
- ✅ Errores manejados con códigos HTTP correctos
- ✅ Documentación OpenAPI completa

---

#### **TAREA 7: Crear WebSocket handler**

**Archivo NUEVO:** `Sistema_v6/presentation/api/rest/websocket/extraccion_ws.py`

**Objetivo:** Implementar el handler de WebSocket para progreso en tiempo real.

**Código completo:**
```python
"""WebSocket handler para progreso de extracción masiva en tiempo real."""
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.services.gestor_sesiones_service import get_gestor_sesiones

logger = logging.getLogger(__name__)


async def websocket_progreso(websocket: WebSocket, session_id: str):
    """
    WebSocket para recibir actualizaciones de progreso en tiempo real.

    Protocolo:
    - Cliente conecta al WS
    - Servidor envía estado inicial inmediatamente
    - Servidor envía actualizaciones automáticas cuando hay cambios
    - Cliente envía 'ping' cada 25s para keep-alive
    - Servidor responde con 'pong'
    - Conexión se cierra cuando la extracción finaliza

    Args:
        websocket: Conexión WebSocket
        session_id: ID de la sesión a monitorear
    """
    await websocket.accept()
    logger.info(f"WebSocket conectado para sesión {session_id}")

    gestor = get_gestor_sesiones()

    # Verificar que la sesión existe
    sesion = await gestor.obtener_sesion(session_id)
    if not sesion:
        await websocket.send_json({"error": "Sesión no encontrada"})
        await websocket.close()
        return

    # Registrar WebSocket en el gestor
    await gestor.registrar_websocket(session_id, websocket)

    try:
        # Enviar estado actual inmediatamente
        await websocket.send_json({
            "session_id": sesion["session_id"],
            "estado": sesion["estado"],
            "fase": sesion["fase"],
            "progreso_actual": sesion["progreso_actual"],
            "progreso_total": sesion["progreso_total"],
            "porcentaje": sesion["porcentaje"],
            "mensaje": sesion["mensaje"],
            "errores": sesion["errores"],
            "tiempo_transcurrido": sesion.get("tiempo_transcurrido", 0),
        })

        # Mantener conexión abierta
        while True:
            # Esperar mensajes del cliente (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Responder a ping con pong
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Timeout normal, continuar
                pass

            # Verificar si la sesión terminó
            sesion_actual = await gestor.obtener_sesion(session_id)
            if sesion_actual and sesion_actual["estado"] in ["completado", "cancelado", "error"]:
                # Enviar estado final
                await websocket.send_json({
                    "session_id": sesion_actual["session_id"],
                    "estado": sesion_actual["estado"],
                    "mensaje": sesion_actual["mensaje"],
                    "tipo": "fin",
                })
                logger.info(f"Sesión {session_id} finalizada, cerrando WebSocket")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para sesión {session_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket {session_id}: {e}")
    finally:
        # Desregistrar WebSocket
        await gestor.desregistrar_websocket(session_id, websocket)
        logger.info(f"WebSocket limpiado para sesión {session_id}")
```

**Criterios de éxito:**
- ✅ WebSocket acepta conexiones
- ✅ Envía estado inicial inmediatamente
- ✅ Responde a ping con pong
- ✅ Broadcast automático funciona
- ✅ Se cierra correctamente al finalizar

---

#### **TAREA 8: Habilitar router en main.py y __init__.py**

**Archivo 1:** `Sistema_v6/presentation/api/rest/routers/__init__.py`

**Cambio:**
```python
# ANTES:
# extraccion_masiva,  # Temporalmente deshabilitado

# DESPUÉS:
extraccion_masiva,  # ✅ HABILITADO
```

**Archivo 2:** `Sistema_v6/presentation/api/rest/main.py`

**Cambio:**
```python
# ANTES (línea 68):
# extraccion_masiva,  # Temporalmente deshabilitado por problemas de importación

# DESPUÉS:
extraccion_masiva,

# Y ANTES (línea 188-192):
# app.include_router(
#     extraccion_masiva.router,
#     prefix="/api/v1/expedientes/extraer",
#     tags=["extraccion_masiva"],
# )  # Temporalmente deshabilitado

# DESPUÉS:
app.include_router(
    extraccion_masiva.router,
    prefix="/api/v1/expedientes/extraer",
    tags=["extraccion_masiva"],
)  # ✅ HABILITADO
```

**Criterios de éxito:**
- ✅ Imports sin errores
- ✅ Servidor FastAPI inicia correctamente
- ✅ Endpoints visibles en /docs

---

### **FASE 4: INTEGRACIÓN Y CONFIGURACIÓN** (1-2 horas)

---

#### **TAREA 9: Actualizar DI Container**

**Archivo:** `Sistema_v6/infrastructure/di_container.py`

**Objetivo:** Inyectar todas las dependencias necesarias en GestorBatch.

**Cambios:**

```python
# 1. Agregar imports
from Sistema_v6.extractor_inicial.procesamiento_expedientes import ProcesadorExpedientesInicial
from Sistema_v6.configuracion.estados import GestorEstados

# 2. Crear método para ProcesadorExpedientesInicial
def procesador_expedientes(self) -> ProcesadorExpedientesInicial:
    """Crea el procesador de expedientes."""
    config = {
        "clasificar": True,
        "analizar_vencimientos": True,
        "detectar_duplicados": False,
        "dias_urgentes": 7,
        "min_utilidad": "MEDIA",
        "extraer_actuaciones": False,
        "guardar_reportes": True,
    }
    return ProcesadorExpedientesInicial(config)

# 3. Crear método para GestorEstados
def gestor_estados(self) -> GestorEstados:
    """Crea el gestor de estados."""
    gestor = GestorEstados()
    gestor.cargar_estados()
    return gestor

# 4. Modificar extraccion_masiva_use_case para pasar las dependencias
def extraccion_masiva_use_case(self) -> ExtraccionMasivaUseCase:
    """Crea el use case de extracción masiva."""
    return ExtraccionMasivaUseCase(
        storage=self.storage,
        repository=self.expediente_repo,
        gestor_sesiones=get_gestor_sesiones(),
        procesador_expedientes=self.procesador_expedientes(),  # 🆕 NUEVO
        gestor_estados=self.gestor_estados(),  # 🆕 NUEVO
    )
```

**Modificar ExtraccionMasivaUseCase:**

```python
# En application/use_cases/extraccion_masiva_use_case.py

def __init__(
    self,
    storage: IStoragePort,
    repository: IExpedienteRepository,
    gestor_sesiones: Any,
    procesador_expedientes: Optional[ProcesadorExpedientesInicial] = None,  # 🆕
    gestor_estados: Optional[GestorEstados] = None,  # 🆕
):
    self.storage = storage
    self.repository = repository
    self.gestor_sesiones = gestor_sesiones
    self.procesador_expedientes = procesador_expedientes  # 🆕
    self.gestor_estados = gestor_estados  # 🆕

# Y pasar al GestorBatch en ejecutar_extraccion_background():
gestor = GestorBatch(
    umbral_errores=self.config.umbral_errores,
    callback_progreso=lambda data: self._emit("progreso_batch", data),
    repository=self.repository,  # 🆕
    procesador_expedientes=self.procesador_expedientes,  # 🆕
    gestor_estados=self.gestor_estados,  # 🆕
)
```

**Criterios de éxito:**
- ✅ Dependencias inyectadas correctamente
- ✅ Container crea todas las instancias
- ✅ No hay errores de importación

---

### **FASE 5: TESTING** (2-3 horas)

---

#### **TAREA 10: Crear tests unitarios para GestorBatch**

**Archivo NUEVO:** `Sistema_v6/tests/unit/test_gestor_batch.py`

**Objetivo:** Verificar que GestorBatch procesa correctamente con mocks.

**Estructura:**
```python
"""Tests unitarios para GestorBatch."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from Sistema_v6.extraccion_masiva.gestor_batch import GestorBatch, ResultadoProcesamiento


@pytest.fixture
def mock_repository():
    """Mock del repositorio."""
    repo = Mock()
    repo.guardar = AsyncMock()
    return repo


@pytest.fixture
def mock_procesador():
    """Mock del procesador."""
    procesador = Mock()
    procesador.clasificar_actuaciones = AsyncMock(return_value={
        "categorias": {"oficios": 2, "providencias": 3},
        "utilidad_total": "ALTA"
    })
    return procesador


@pytest.fixture
def mock_gestor_estados():
    """Mock del gestor de estados."""
    gestor = Mock()
    gestor.actualizar_estado = Mock()
    gestor.guardar_estados = AsyncMock()
    return gestor


@pytest.mark.asyncio
async def test_procesar_lote_exitoso(mock_repository, mock_procesador, mock_gestor_estados):
    """Test de procesamiento exitoso de un lote."""
    # Arrange
    gestor = GestorBatch(
        umbral_errores=5,
        repository=mock_repository,
        procesador_expedientes=mock_procesador,
        gestor_estados=mock_gestor_estados,
    )

    expedientes = [
        {"numero": "12345/2024", "caratula": "Prueba 1"},
        {"numero": "67890/2024", "caratula": "Prueba 2"},
    ]

    # Act
    with patch('Sistema_v6.pjn.auto_login.reutilizar_sesion_async') as mock_sesion:
        # Mock de sesión Playwright
        mock_page = AsyncMock()
        mock_sesion.return_value.__aenter__.return_value = (mock_page, Mock(), Mock())

        resumen = await gestor.procesar_lote(expedientes)

    # Assert
    assert resumen.total == 2
    assert resumen.exitosos == 2
    assert resumen.errores == 0
    assert mock_repository.guardar.call_count == 2
    assert mock_procesador.clasificar_actuaciones.call_count == 2
    assert mock_gestor_estados.actualizar_estado.call_count == 2


@pytest.mark.asyncio
async def test_procesar_lote_con_errores(mock_repository):
    """Test de manejo de errores en el procesamiento."""
    # Arrange
    gestor = GestorBatch(
        umbral_errores=3,
        repository=mock_repository,
    )

    # Mock para que falle el primer expediente
    mock_repository.guardar.side_effect = [Exception("Error DB"), None]

    expedientes = [
        {"numero": "12345/2024", "caratula": "Fallará"},
        {"numero": "67890/2024", "caratula": "Éxito"},
    ]

    # Act
    resumen = await gestor.procesar_lote(expedientes)

    # Assert
    assert resumen.total == 2
    assert resumen.errores >= 1
    assert resumen.exitosos >= 0


@pytest.mark.asyncio
async def test_pausar_y_reanudar():
    """Test de funcionalidad pause/resume."""
    gestor = GestorBatch()

    assert not gestor.pausado
    gestor.pausar()
    assert gestor.pausado
    gestor.reanudar()
    assert not gestor.pausado


# ... más tests
```

**Criterios de éxito:**
- ✅ Tests pasan correctamente
- ✅ Coverage > 80% en gestor_batch.py
- ✅ Mocks correctamente configurados

---

#### **TAREA 11: Crear tests de integración**

**Archivo NUEVO:** `Sistema_v6/tests/integration/test_extraccion_masiva_completa.py`

**Objetivo:** Probar el flujo completo de extracción masiva end-to-end.

**Estructura:**
```python
"""Tests de integración para extracción masiva completa."""
import pytest
from pathlib import Path

from application.dtos import IniciarExtraccionMasivaCommand
from infrastructure.di_container import get_container


@pytest.mark.integration
@pytest.mark.asyncio
async def test_flujo_completo_extraccion_masiva():
    """Test del flujo completo: listado + procesamiento + guardado."""
    # Arrange
    container = get_container()
    use_case = container.extraccion_masiva_use_case()

    command = IniciarExtraccionMasivaCommand(
        usuario="test",
        contrasena="test",
        headless=True,
        umbral_errores=10,
        exportar_formatos=["json"],
    )

    # Act
    result = await use_case.iniciar_extraccion(command)

    # Assert
    assert result.is_success
    assert result.value.session_id is not None

    # Esperar a que complete (o implementar polling)
    # TODO: Implementar mecanismo de espera

    # Verificar resultados
    sesion = await use_case.gestor_sesiones.obtener_sesion(result.value.session_id)
    assert sesion["estado"] == "completado"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extraccion_con_filtros():
    """Test de extracción con filtros de fecha y estado."""
    # TODO: Implementar
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pausar_y_reanudar_extraccion():
    """Test de pausar y reanudar una extracción en progreso."""
    # TODO: Implementar
    pass
```

**Criterios de éxito:**
- ✅ Flujo completo funciona end-to-end
- ✅ Expedientes guardados en repositorio
- ✅ Estados actualizados correctamente
- ✅ Reportes generados

---

#### **TAREA 12: Probar endpoints REST con curl/Postman**

**Objetivo:** Verificar que todos los endpoints funcionan correctamente.

**Script de prueba:**
```bash
#!/bin/bash
# test_api_extraccion_masiva.sh

API_URL="http://localhost:8000/api/v1/expedientes/extraer"

echo "=== Test 1: Iniciar extracción masiva ==="
SESSION_ID=$(curl -s -X POST "$API_URL/masivo" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario": "test",
    "contrasena": "test",
    "headless": true,
    "umbral_errores": 10,
    "exportar_formatos": ["json"]
  }' | jq -r '.session_id')

echo "Session ID: $SESSION_ID"

echo ""
echo "=== Test 2: Obtener progreso ==="
curl -s "$API_URL/$SESSION_ID/progreso" | jq

sleep 2

echo ""
echo "=== Test 3: Pausar extracción ==="
curl -s -X POST "$API_URL/$SESSION_ID/pausar" | jq

sleep 1

echo ""
echo "=== Test 4: Reanudar extracción ==="
curl -s -X POST "$API_URL/$SESSION_ID/reanudar" | jq

sleep 2

echo ""
echo "=== Test 5: Obtener resumen ==="
curl -s "$API_URL/$SESSION_ID/resumen" | jq

echo ""
echo "=== Test 6: Descargar JSON ==="
curl -s -O "$API_URL/$SESSION_ID/descargar/json"
ls -lh extraccion_*.json

echo ""
echo "=== Test 7: Cancelar extracción ==="
curl -s -X POST "$API_URL/$SESSION_ID/cancelar" | jq
```

**Criterios de éxito:**
- ✅ Todos los endpoints responden
- ✅ Códigos HTTP correctos
- ✅ Respuestas JSON válidas
- ✅ WebSocket conecta y recibe mensajes

---

#### **TAREA 13: Probar WebSocket de progreso**

**Objetivo:** Verificar que el WebSocket funciona correctamente.

**Script de prueba (JavaScript en consola del navegador):**
```javascript
// test_websocket.js

const sessionId = "ext_20251107_120530";  // Reemplazar con session_id real
const ws = new WebSocket(`ws://localhost:8000/api/v1/expedientes/extraer/${sessionId}/ws`);

ws.onopen = () => {
    console.log('✅ WebSocket conectado');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📥 Mensaje recibido:', data);

    // Mostrar progreso
    if (data.porcentaje !== undefined) {
        console.log(`Progreso: ${data.progreso_actual}/${data.progreso_total} (${data.porcentaje.toFixed(1)}%)`);
        console.log(`Estado: ${data.estado} - ${data.mensaje}`);
    }
};

ws.onerror = (error) => {
    console.error('❌ Error WebSocket:', error);
};

ws.onclose = () => {
    console.log('🔌 WebSocket cerrado');
};

// Enviar ping cada 25 segundos
const pingInterval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
        console.log('🏓 Ping enviado');
    } else {
        clearInterval(pingInterval);
    }
}, 25000);
```

**Criterios de éxito:**
- ✅ WebSocket conecta correctamente
- ✅ Recibe estado inicial
- ✅ Recibe actualizaciones automáticas
- ✅ Ping/pong funciona
- ✅ Se cierra correctamente al finalizar

---

#### **TAREA 14: Probar flujo completo desde frontend**

**Objetivo:** Verificar la integración completa con el frontend React.

**Pasos de prueba:**

1. **Iniciar servidores:**
   ```bash
   # Terminal 1: Backend
   cd Sistema_v6
   uvicorn presentation.api.rest.main:app --reload --port 8000

   # Terminal 2: Frontend
   cd Sistema_v6/frontend
   npm run dev
   ```

2. **Flujo de prueba manual:**
   - [ ] Abrir navegador en `http://localhost:5173` (o puerto de Vite)
   - [ ] Navegar a sección de Expedientes
   - [ ] Hacer clic en botón "Extracción Masiva"
   - [ ] Configurar opciones de extracción
   - [ ] Iniciar extracción
   - [ ] Verificar que se muestra progreso en tiempo real
   - [ ] Probar pausar extracción
   - [ ] Probar reanudar extracción
   - [ ] Esperar a que complete
   - [ ] Verificar resumen final
   - [ ] Descargar reporte en JSON
   - [ ] Descargar reporte en Excel
   - [ ] Verificar filtrado de expedientes
   - [ ] Confirmar selección

3. **Verificar en logs del backend:**
   - [ ] Logs de inicio de extracción
   - [ ] Logs de progreso del listado
   - [ ] Logs de procesamiento batch
   - [ ] Logs de clasificación de actuaciones
   - [ ] Logs de guardado en repositorio
   - [ ] Logs de actualización de estados
   - [ ] Logs de finalización

4. **Verificar en base de datos/archivos:**
   - [ ] Expedientes guardados en `data/workspaces/`
   - [ ] Estados actualizados en `data/estados_expedientes.json`
   - [ ] Listado generado en `data/extraccion_masiva/listados/`
   - [ ] Reporte generado en `data/extraccion_masiva/reportes/`

**Criterios de éxito:**
- ✅ Flujo completo funciona sin errores
- ✅ UI actualiza en tiempo real
- ✅ Expedientes guardados correctamente
- ✅ Reportes descargables
- ✅ Sin errores en consola del navegador
- ✅ Sin errores en logs del backend

---

### **FASE 6: DOCUMENTACIÓN** (1 hora)

---

#### **TAREA 15: Actualizar documentación**

**Archivos a actualizar:**

1. **README principal:**
   - Actualizar sección de extracción masiva
   - Agregar ejemplos de uso
   - Actualizar endpoints disponibles

2. **IMPLEMENTACION_EXTRACCION_MASIVA_UNIFICADA.md:**
   - Marcar como ✅ COMPLETADO
   - Agregar sección de "Funcionalidades implementadas"
   - Actualizar diagramas de flujo

3. **PLAN_UNIFICACION_EXTRACCION_MASIVA.md:**
   - Marcar todas las tareas como ✅
   - Agregar fecha de finalización
   - Agregar resumen de implementación

4. **Crear GUIA_USO_EXTRACCION_MASIVA.md:**
   - Guía paso a paso para usuarios finales
   - Ejemplos de configuraciones
   - Troubleshooting común

5. **API Documentation (OpenAPI):**
   - Verificar que Swagger UI muestra todos los endpoints
   - Agregar ejemplos de request/response
   - Agregar descripciones claras

**Criterios de éxito:**
- ✅ Documentación actualizada
- ✅ Ejemplos claros y funcionales
- ✅ Swagger UI completo
- ✅ Guía de troubleshooting

---

## 📊 CHECKLIST DE VERIFICACIÓN FINAL

### Backend
- [ ] GestorBatch._procesar_expediente() implementado con lógica real
- [ ] Extracción de actuaciones funciona
- [ ] Clasificación de actuaciones funciona
- [ ] Detección de vencimientos funciona
- [ ] Guardado en repositorio funciona
- [ ] Actualización de estados funciona
- [ ] Manejo de errores robusto
- [ ] Logs detallados

### API REST
- [ ] Router extraccion_masiva.py creado
- [ ] 8 endpoints implementados
- [ ] WebSocket handler creado y funcional
- [ ] Router habilitado en main.py
- [ ] Servidor inicia sin errores
- [ ] Endpoints visibles en /docs

### Integración
- [ ] DI Container actualizado
- [ ] Dependencias inyectadas correctamente
- [ ] Use case actualizado
- [ ] Frontend conecta correctamente

### Testing
- [ ] Tests unitarios de GestorBatch
- [ ] Tests de integración del flujo completo
- [ ] Tests de endpoints REST
- [ ] Tests de WebSocket
- [ ] Pruebas manuales desde frontend
- [ ] Coverage > 80%

### Documentación
- [ ] README actualizado
- [ ] Documentos de implementación actualizados
- [ ] Guía de uso creada
- [ ] Swagger UI completo
- [ ] Changelog actualizado

---

## 🎯 CRITERIOS DE ÉXITO GLOBAL

El proyecto estará **100% completo** cuando:

1. ✅ **Flujo completo funciona:** Listado → Procesamiento → Clasificación → Guardado → Estados
2. ✅ **API REST funcional:** Los 8 endpoints responden correctamente
3. ✅ **WebSocket funcional:** Progreso en tiempo real sin errores
4. ✅ **Frontend integrado:** UI actualiza correctamente y puede controlar el flujo
5. ✅ **Datos persistidos:** Expedientes guardados en repositorio y estados actualizados
6. ✅ **Tests pasando:** > 80% coverage, tests de integración completos
7. ✅ **Documentación completa:** Guías actualizadas y ejemplos funcionales
8. ✅ **Sin TODOs críticos:** No quedan implementaciones simuladas

---

## 📈 MÉTRICAS DE PROGRESO

| Fase | Tareas | Estimado | Completitud Objetivo |
|------|--------|----------|---------------------|
| 1. Análisis | 1 | 1-2h | 100% |
| 2. Core | 4 | 6-8h | 100% |
| 3. API | 3 | 3-4h | 100% |
| 4. Integración | 1 | 1-2h | 100% |
| 5. Testing | 5 | 2-3h | 100% |
| 6. Docs | 1 | 1h | 100% |
| **TOTAL** | **15** | **14-20h** | **100%** |

**Estado actual:** 45% → **Objetivo:** 100%

---

## 🚨 PRIORIDADES Y DEPENDENCIAS

### Alta Prioridad (CRÍTICO)
1. ⚠️ **TAREA 2:** Implementar lógica de extracción (bloquea todo)
2. ⚠️ **TAREA 3:** Integrar clasificación (necesario para valor)
3. ⚠️ **TAREA 4:** Integrar repositorio (necesario para persistencia)

### Media Prioridad
4. **TAREA 5:** Actualizar estados
5. **TAREA 6-8:** API REST y WebSocket
6. **TAREA 9:** DI Container

### Baja Prioridad
7. **TAREA 10-14:** Testing (pero importante)
8. **TAREA 15:** Documentación

---

## 🔄 FLUJO DE TRABAJO RECOMENDADO

### Semana 1 (8-10 horas)
- **Día 1-2:** Tareas 1-2 (Análisis + Core)
- **Día 3-4:** Tareas 3-5 (Integraciones core)

### Semana 2 (6-8 horas)
- **Día 5-6:** Tareas 6-8 (API REST)
- **Día 7:** Tarea 9 (DI Container)

### Semana 3 (4-6 horas)
- **Día 8-9:** Tareas 10-14 (Testing)
- **Día 10:** Tarea 15 (Documentación)

---

## 📞 COMANDOS ÚTILES DURANTE IMPLEMENTACIÓN

### Verificar imports
```bash
cd Sistema_v6
python -c "from extraccion_masiva.gestor_batch import GestorBatch; print('✅ OK')"
```

### Ejecutar tests
```bash
pytest tests/unit/test_gestor_batch.py -v
pytest tests/integration/test_extraccion_masiva_completa.py -v --cov
```

### Iniciar servidor
```bash
uvicorn presentation.api.rest.main:app --reload --port 8000
```

### Ver logs en tiempo real
```bash
tail -f data/extraccion_masiva/logs/extraccion_*.log
```

### Verificar endpoints
```bash
curl http://localhost:8000/docs
```

---

## 🎓 RECURSOS Y REFERENCIAS

### Arquitectura
- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### FastAPI
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Testing
- [Pytest Async](https://pytest-asyncio.readthedocs.io/)
- [Unittest Mock](https://docs.python.org/3/library/unittest.mock.html)

---

## ✅ FINALIZACIÓN

Una vez completadas las 15 tareas:

1. **Commit final:**
   ```bash
   git add .
   git commit -m "feat: Completar implementación de extracción masiva

   - Implementar lógica real de procesamiento en GestorBatch
   - Integrar clasificación, vencimientos y guardado
   - Habilitar router REST con 8 endpoints
   - Implementar WebSocket para progreso en tiempo real
   - Actualizar DI Container con nuevas dependencias
   - Agregar tests unitarios y de integración
   - Actualizar documentación completa

   Closes #XXX"
   ```

2. **Push a rama de trabajo:**
   ```bash
   git push -u origin claude/review-sintaxis-parcial2-011CUuHPSBCZ7juywst29TXV
   ```

3. **Crear PR:**
   - Título: "feat: Completar implementación de extracción masiva"
   - Descripción: Referenciar este plan y el diagnóstico
   - Asignar reviewers
   - Agregar labels: `enhancement`, `backend`, `frontend`, `api`

4. **Merge a sintaxis_parcial2**

---

**FIN DEL PLAN**

Este plan está listo para ser ejecutado por un agente autónomo o un equipo de desarrollo.
Cada tarea tiene objetivos claros, criterios de éxito y código de referencia.

**Estado:** 📝 LISTO PARA EJECUCIÓN
**Última actualización:** 2025-11-07
**Versión:** 1.0
