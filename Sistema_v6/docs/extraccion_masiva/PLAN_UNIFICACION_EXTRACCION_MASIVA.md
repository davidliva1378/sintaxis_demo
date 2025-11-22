# Plan de Implementación: Unificación de Extracción Masiva
## Solución 1: Migración Progresiva con Backend Unificado

**Objetivo**: Crear un único sistema de extracción masiva que combine la arquitectura limpia del Sistema React con las funcionalidades avanzadas del Sistema HTML/JS.

**Rama de trabajo**: `claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG`

---

## 📋 VERIFICACIÓN PREVIA

### ✅ Recursos Existentes Confirmados:

1. **Backend:**
   - ✅ `Sistema_v6/extraccion_masiva/` - Módulo de extracción masiva completo
     - `extractor_masivo.py` - ExtractorMasivo
     - `gestor_batch.py` - GestorBatch para procesamiento por lotes
     - `exportadores.py` - Exportación a JSON, Excel, CSV
   - ✅ `Sistema_v6/application/use_cases/` - Use cases existentes
   - ✅ `Sistema_v6/application/dtos/` - DTOs (commands, queries, responses)
   - ✅ `Sistema_v6/infrastructure/di_container.py` - DI Container
   - ✅ `Sistema_v6/presentation/api/rest/routers/expedientes.py` - Router básico

2. **Frontend:**
   - ✅ `Sistema_v6/frontend/src/stores/expedientesStore.ts` - Zustand store
   - ✅ `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx` - Componente básico

3. **Sistema Legacy:**
   - ✅ `Sistema_v6/interfaz_web/backend/api/extraccion.py` - API completa con WebSocket
   - ✅ `Sistema_v6/interfaz_web/backend/templates/` - Frontend HTML/JS

---

## 🎯 ARQUITECTURA OBJETIVO

```
Sistema_v6/
├── application/
│   ├── use_cases/
│   │   └── extraccion_masiva_use_case.py       # ✨ NUEVO
│   └── dtos/
│       ├── extraccion_masiva_commands.py       # ✨ NUEVO
│       └── extraccion_masiva_responses.py      # ✨ NUEVO
├── infrastructure/
│   ├── di_container.py                         # 🔄 ACTUALIZAR
│   └── services/
│       └── gestor_sesiones_service.py          # ✨ NUEVO
└── presentation/api/rest/
    ├── routers/
    │   ├── expedientes.py                      # 🔄 ACTUALIZAR (deprecar endpoint simple)
    │   └── extraccion_masiva.py                # ✨ NUEVO
    ├── websocket/
    │   ├── __init__.py                         # ✨ NUEVO
    │   └── extraccion_ws.py                    # ✨ NUEVO
    └── main.py                                 # 🔄 ACTUALIZAR (incluir nuevos routers)
```

---

## 📝 PLAN DE IMPLEMENTACIÓN (10 PASOS)

### **PASO 1: Crear DTOs de Extracción Masiva**

**Archivo**: `Sistema_v6/application/dtos/extraccion_masiva_commands.py`

**Contenido**:
```python
"""Comandos para extracción masiva."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class IniciarExtraccionMasivaCommand:
    """Comando para iniciar extracción masiva."""
    usuario: str
    contrasena: str
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    estados: Optional[List[str]] = None
    dependencias: Optional[List[str]] = None
    umbral_errores: int = 10
    headless: bool = True
    exportar_formatos: List[str] = None

    def __post_init__(self):
        if self.exportar_formatos is None:
            self.exportar_formatos = ["json"]


@dataclass
class ControlExtraccionCommand:
    """Comando para controlar extracción (pausar/reanudar/cancelar)."""
    session_id: str
    accion: str  # "pausar", "reanudar", "cancelar"
```

**Archivo**: `Sistema_v6/application/dtos/extraccion_masiva_responses.py`

**Contenido**:
```python
"""Respuestas de extracción masiva."""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class IniciarExtraccionMasivaResponse:
    """Respuesta al iniciar extracción masiva."""
    session_id: str
    mensaje: str
    estado: str


@dataclass
class ProgresoExtraccionResponse:
    """Respuesta con progreso de extracción."""
    session_id: str
    estado: str
    fase: str
    progreso_actual: int
    progreso_total: int
    porcentaje: float
    mensaje: str
    errores: int
    tiempo_transcurrido: float
    tiempo_estimado: Optional[float]
    velocidad: Optional[float]


@dataclass
class ResumenExtraccionResponse:
    """Respuesta con resumen de extracción."""
    session_id: str
    estado: str
    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    velocidad_promedio: float
    archivos_generados: List[str]
```

**Actualizar**: `Sistema_v6/application/dtos/__init__.py`
```python
# Agregar al final:
from .extraccion_masiva_commands import (
    IniciarExtraccionMasivaCommand,
    ControlExtraccionCommand,
)
from .extraccion_masiva_responses import (
    IniciarExtraccionMasivaResponse,
    ProgresoExtraccionResponse,
    ResumenExtraccionResponse,
)

# Agregar a __all__:
__all__ = [
    # ... existentes ...
    "IniciarExtraccionMasivaCommand",
    "ControlExtraccionCommand",
    "IniciarExtraccionMasivaResponse",
    "ProgresoExtraccionResponse",
    "ResumenExtraccionResponse",
]
```

---

### **PASO 2: Crear Servicio de Gestión de Sesiones**

**Archivo**: `Sistema_v6/infrastructure/services/gestor_sesiones_service.py`

**Contenido**: (Copiar de `interfaz_web/backend/api/extraccion.py` la clase `GestorSesiones` y adaptarla)

```python
"""Servicio para gestión de sesiones de extracción masiva."""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GestorSesiones:
    """Gestor de sesiones de extracción activas."""

    def __init__(self):
        self.sesiones: Dict[str, Dict[str, Any]] = {}
        self.websockets: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def crear_sesion(self, session_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Crear una nueva sesión de extracción."""
        async with self.lock:
            sesion = {
                "session_id": session_id,
                "config": config,
                "estado": "iniciando",
                "fase": "configuracion",
                "progreso_actual": 0,
                "progreso_total": 0,
                "porcentaje": 0.0,
                "mensaje": "Iniciando extracción...",
                "errores": 0,
                "tiempo_inicio": datetime.now().isoformat(),
                "tiempo_fin": None,
                "resultados": None,
                "archivos": [],
                "extractor": None,
                "task": None,
            }
            self.sesiones[session_id] = sesion
            self.websockets[session_id] = set()
            return sesion

    async def actualizar_progreso(self, session_id: str, **kwargs):
        """Actualizar el progreso de una sesión."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update(kwargs)

                # Calcular tiempo transcurrido
                inicio = datetime.fromisoformat(self.sesiones[session_id]["tiempo_inicio"])
                transcurrido = (datetime.now() - inicio).total_seconds()
                self.sesiones[session_id]["tiempo_transcurrido"] = transcurrido

                # Enviar actualización por WebSocket
                await self._broadcast(session_id, self.sesiones[session_id])

    async def obtener_sesion(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una sesión."""
        async with self.lock:
            return self.sesiones.get(session_id)

    async def finalizar_sesion(self, session_id: str, resultados: Dict[str, Any]):
        """Finalizar una sesión con resultados."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update({
                    "estado": "completado",
                    "tiempo_fin": datetime.now().isoformat(),
                    "resultados": resultados,
                })
                await self._broadcast(session_id, self.sesiones[session_id])

    async def marcar_error(self, session_id: str, error: str):
        """Marcar una sesión como error."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update({
                    "estado": "error",
                    "mensaje": f"Error: {error}",
                    "tiempo_fin": datetime.now().isoformat(),
                })
                await self._broadcast(session_id, self.sesiones[session_id])

    async def registrar_websocket(self, session_id: str, websocket: WebSocket):
        """Registrar un WebSocket para una sesión."""
        async with self.lock:
            if session_id not in self.websockets:
                self.websockets[session_id] = set()
            self.websockets[session_id].add(websocket)

    async def desregistrar_websocket(self, session_id: str, websocket: WebSocket):
        """Desregistrar un WebSocket."""
        async with self.lock:
            if session_id in self.websockets:
                self.websockets[session_id].discard(websocket)

    async def _broadcast(self, session_id: str, data: Dict[str, Any]):
        """Enviar datos a todos los WebSockets de una sesión."""
        if session_id in self.websockets:
            websockets_copy = self.websockets[session_id].copy()

            for websocket in websockets_copy:
                try:
                    mensaje = {
                        "session_id": data["session_id"],
                        "estado": data["estado"],
                        "fase": data["fase"],
                        "progreso_actual": data["progreso_actual"],
                        "progreso_total": data["progreso_total"],
                        "porcentaje": data["porcentaje"],
                        "mensaje": data["mensaje"],
                        "errores": data["errores"],
                        "tiempo_transcurrido": data.get("tiempo_transcurrido", 0),
                    }
                    await websocket.send_json(mensaje)
                except Exception as e:
                    logger.error(f"Error enviando a WebSocket: {e}")
                    await self.desregistrar_websocket(session_id, websocket)


# Instancia singleton
_gestor: Optional[GestorSesiones] = None


def get_gestor_sesiones() -> GestorSesiones:
    """Obtener instancia singleton del gestor."""
    global _gestor
    if _gestor is None:
        _gestor = GestorSesiones()
    return _gestor
```

---

### **PASO 3: Crear Use Case de Extracción Masiva**

**Archivo**: `Sistema_v6/application/use_cases/extraccion_masiva_use_case.py`

**Contenido**:
```python
"""Use Case de Extracción Masiva de Expedientes."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from application.dtos import (
    IniciarExtraccionMasivaCommand,
    IniciarExtraccionMasivaResponse,
    Result,
)
from application.ports import IStoragePort, IExpedienteRepository
from Sistema_v6.extraccion_masiva import (
    ExtractorMasivo,
    ConfigExtraccionMasiva,
    exportar_json,
    exportar_excel,
)

logger = logging.getLogger(__name__)


class ExtraccionMasivaUseCase:
    """Use case para extracción masiva de expedientes.

    Integra el ExtractorMasivo existente con la arquitectura limpia,
    proporcionando gestión de sesiones, callbacks y exportación.
    """

    def __init__(
        self,
        storage: IStoragePort,
        repository: IExpedienteRepository,
        gestor_sesiones: Any,  # GestorSesiones
    ):
        """Inicializa el use case.

        Args:
            storage: Port de almacenamiento
            repository: Repositorio de expedientes
            gestor_sesiones: Gestor de sesiones de extracción
        """
        self.storage = storage
        self.repository = repository
        self.gestor_sesiones = gestor_sesiones

    async def iniciar_extraccion(
        self,
        command: IniciarExtraccionMasivaCommand,
    ) -> Result[IniciarExtraccionMasivaResponse]:
        """Inicia una extracción masiva.

        Args:
            command: Comando con configuración de extracción

        Returns:
            Result con respuesta de inicio
        """
        try:
            # Generar session_id único
            session_id = f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Crear configuración del extractor
            config_extractor = ConfigExtraccionMasiva(
                fecha_desde=command.fecha_desde,
                fecha_hasta=command.fecha_hasta,
                estados=command.estados,
                dependencias=command.dependencias,
                umbral_errores=command.umbral_errores,
                headless=command.headless,
            )

            # Crear sesión
            await self.gestor_sesiones.crear_sesion(
                session_id,
                config={
                    "usuario": command.usuario,
                    "formatos": command.exportar_formatos,
                    **config_extractor.__dict__,
                },
            )

            # Crear respuesta
            response = IniciarExtraccionMasivaResponse(
                session_id=session_id,
                mensaje="Extracción iniciada correctamente",
                estado="iniciando",
            )

            return Result.success(response)

        except Exception as e:
            logger.exception("Error al iniciar extracción masiva")
            return Result.failure(f"Error al iniciar extracción: {str(e)}")

    def crear_callbacks(self, session_id: str) -> Dict[str, Callable]:
        """Crear callbacks para conectar el extractor con el gestor de sesiones.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con callbacks
        """

        async def on_inicio_listado():
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="en_progreso",
                fase="listado",
                mensaje="Extrayendo listado de expedientes...",
            )

        async def on_progreso_listado(pagina_actual: int, total_paginas: int):
            porcentaje = (pagina_actual / total_paginas * 50) if total_paginas > 0 else 0
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                progreso_actual=pagina_actual,
                progreso_total=total_paginas,
                porcentaje=porcentaje,
                mensaje=f"Extrayendo página {pagina_actual} de {total_paginas}...",
            )

        async def on_fin_listado(expedientes: List[Dict]):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                mensaje=f"Listado completo: {len(expedientes)} expedientes encontrados",
                porcentaje=50.0,
            )

        async def on_inicio_batch(total: int):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                fase="procesamiento",
                progreso_total=total,
                mensaje=f"Iniciando procesamiento de {total} expedientes...",
            )

        async def on_progreso_batch(idx: int, total: int, resultado: Dict):
            porcentaje = 50 + (idx / total * 50) if total > 0 else 50
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                progreso_actual=idx + 1,
                progreso_total=total,
                porcentaje=porcentaje,
                mensaje=f"Procesando {idx + 1}/{total}: {resultado.get('numero', 'N/A')}",
            )

        async def on_fin_batch(resumen: Dict):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                mensaje=f"Procesamiento completo: {resumen.get('exitosos', 0)} exitosos, {resumen.get('errores', 0)} errores",
                porcentaje=100.0,
            )

        async def on_error(error: str):
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)
            if sesion:
                errores = sesion.get("errores", 0) + 1
                await self.gestor_sesiones.actualizar_progreso(
                    session_id,
                    errores=errores,
                    mensaje=f"Error: {error}",
                )

        return {
            "inicio_listado": on_inicio_listado,
            "progreso_listado": on_progreso_listado,
            "fin_listado": on_fin_listado,
            "inicio_batch": on_inicio_batch,
            "progreso_batch": on_progreso_batch,
            "fin_batch": on_fin_batch,
            "error": on_error,
        }

    async def ejecutar_extraccion_background(
        self,
        session_id: str,
        config_extractor: ConfigExtraccionMasiva,
        formatos_exportacion: List[str],
    ):
        """Ejecutar extracción en background.

        Args:
            session_id: ID de la sesión
            config_extractor: Configuración del extractor
            formatos_exportacion: Formatos para exportar
        """
        try:
            # Crear callbacks
            callbacks = self.crear_callbacks(session_id)

            # Crear extractor
            extractor = ExtractorMasivo(config_extractor, callbacks=callbacks)

            # Guardar extractor en la sesión
            await self.gestor_sesiones.actualizar_progreso(session_id, extractor=extractor)

            # Ejecutar extracción
            logger.info(f"Iniciando extracción para sesión {session_id}")
            resultado = await extractor.ejecutar_extraccion_completa()

            # Exportar resultados
            archivos = []
            base_path = extractor.session_dir

            for formato in formatos_exportacion:
                try:
                    if formato == "json":
                        archivo = exportar_json(resultado, base_path / "reporte.json")
                        archivos.append(str(archivo))
                    elif formato == "excel":
                        archivo = exportar_excel(resultado, base_path / "reporte.xlsx")
                        archivos.append(str(archivo))
                except Exception as e:
                    logger.error(f"Error exportando {formato}: {e}")

            # Actualizar sesión con archivos
            await self.gestor_sesiones.actualizar_progreso(session_id, archivos=archivos)

            # Finalizar sesión
            await self.gestor_sesiones.finalizar_sesion(session_id, resultado)

            logger.info(f"Extracción completada para sesión {session_id}")

        except Exception as e:
            logger.error(f"Error en extracción {session_id}: {e}", exc_info=True)
            await self.gestor_sesiones.marcar_error(session_id, str(e))

    async def pausar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Pausar una extracción en progreso."""
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] != "en_progreso":
                return Result.failure("La sesión no está en progreso")

            # Pausar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "gestor_batch"):
                extractor.gestor_batch.pausar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="pausado",
                mensaje="Extracción pausada",
            )

            return Result.success({"mensaje": "Extracción pausada", "session_id": session_id})

        except Exception as e:
            logger.exception(f"Error al pausar extracción {session_id}")
            return Result.failure(str(e))

    async def reanudar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Reanudar una extracción pausada."""
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] != "pausado":
                return Result.failure("La sesión no está pausada")

            # Reanudar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "gestor_batch"):
                extractor.gestor_batch.reanudar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="en_progreso",
                mensaje="Extracción reanudada",
            )

            return Result.success({"mensaje": "Extracción reanudada", "session_id": session_id})

        except Exception as e:
            logger.exception(f"Error al reanudar extracción {session_id}")
            return Result.failure(str(e))

    async def cancelar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Cancelar una extracción."""
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] not in ["en_progreso", "pausado"]:
                return Result.failure("La sesión no se puede cancelar")

            # Cancelar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "cancelar"):
                extractor.cancelar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="cancelado",
                mensaje="Extracción cancelada por el usuario",
                tiempo_fin=datetime.now().isoformat(),
            )

            return Result.success({"mensaje": "Extracción cancelada", "session_id": session_id})

        except Exception as e:
            logger.exception(f"Error al cancelar extracción {session_id}")
            return Result.failure(str(e))
```

**Actualizar**: `Sistema_v6/application/use_cases/__init__.py`
```python
# Agregar:
from .extraccion_masiva_use_case import ExtraccionMasivaUseCase

# Actualizar __all__:
__all__ = [
    # ... existentes ...
    "ExtraccionMasivaUseCase",
]
```

---

### **PASO 4: Actualizar DI Container**

**Archivo**: `Sistema_v6/infrastructure/di_container.py`

**Modificaciones**:
```python
# Agregar imports al inicio:
from application.use_cases import (
    # ... existentes ...
    ExtraccionMasivaUseCase,
)
from .services.gestor_sesiones_service import get_gestor_sesiones

# En la clase DIContainer, agregar método:
def extraccion_masiva_use_case(self) -> ExtraccionMasivaUseCase:
    """Crea el use case de extracción masiva."""
    return ExtraccionMasivaUseCase(
        storage=self.storage,
        repository=self.expediente_repo,
        gestor_sesiones=get_gestor_sesiones(),
    )
```

---

### **PASO 5: Crear WebSocket Handler**

**Archivo**: `Sistema_v6/presentation/api/rest/websocket/__init__.py`
```python
"""WebSocket handlers para la API REST."""
```

**Archivo**: `Sistema_v6/presentation/api/rest/websocket/extraccion_ws.py`

**Contenido**:
```python
"""WebSocket para progreso de extracción masiva en tiempo real."""
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.services.gestor_sesiones_service import get_gestor_sesiones

logger = logging.getLogger(__name__)


async def websocket_progreso(websocket: WebSocket, session_id: str):
    """WebSocket para recibir actualizaciones de progreso en tiempo real.

    Args:
        websocket: Conexión WebSocket
        session_id: ID de la sesión a monitorear
    """
    await websocket.accept()

    gestor = get_gestor_sesiones()

    # Verificar que la sesión existe
    sesion = await gestor.obtener_sesion(session_id)
    if not sesion:
        await websocket.send_json({"error": "Sesión no encontrada"})
        await websocket.close()
        return

    # Registrar WebSocket
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
        })

        # Mantener conexión abierta
        while True:
            # Esperar mensajes del cliente (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo del mensaje recibido (para keep-alive)
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
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para sesión {session_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket {session_id}: {e}")
    finally:
        # Desregistrar WebSocket
        await gestor.desregistrar_websocket(session_id, websocket)
```

---

### **PASO 6: Crear Router de Extracción Masiva**

**Archivo**: `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`

**Contenido**: (Ver archivo completo en descripción detallada a continuación)

---

### **PASO 7: Actualizar main.py de la API**

**Archivo**: `Sistema_v6/presentation/api/rest/main.py`

**Modificaciones**:
```python
# Agregar import:
from .routers import auth, config, expedientes, health, monitoreo, workspaces, extraccion_masiva

# Agregar router (después de la línea 172):
app.include_router(
    extraccion_masiva.router,
    prefix="/api/v1/expedientes/extraer",
    tags=["extraccion_masiva"]
)

# Actualizar docstring al inicio (línea 24-35):
"""
    Extracción Masiva:
    - POST /api/v1/expedientes/extraer/masivo - Inicia extracción masiva
    - GET /api/v1/expedientes/extraer/{session_id}/progreso - Obtiene progreso
    - POST /api/v1/expedientes/extraer/{session_id}/pausar - Pausa extracción
    - POST /api/v1/expedientes/extraer/{session_id}/reanudar - Reanuda extracción
    - POST /api/v1/expedientes/extraer/{session_id}/cancelar - Cancela extracción
    - GET /api/v1/expedientes/extraer/{session_id}/resumen - Obtiene resumen
    - GET /api/v1/expedientes/extraer/{session_id}/descargar/{formato} - Descarga reporte
    - WS /api/v1/expedientes/extraer/{session_id}/ws - WebSocket para progreso
"""
```

---

### **PASO 8: Actualizar Frontend React Store**

**Archivo**: `Sistema_v6/frontend/src/stores/expedientesStore.ts`

**Modificaciones**: Agregar estado y acciones para extracción masiva avanzada.

(Ver código completo en descripción detallada)

---

### **PASO 9: Actualizar Componente React**

**Archivo**: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Modificaciones**: Agregar controles de pausar/reanudar/cancelar, WebSocket, descarga.

(Ver código completo en descripción detallada)

---

### **PASO 10: Testing y Deprecación del Sistema Legacy**

1. **Testing completo**:
   - Probar extracción masiva completa
   - Probar pausar/reanudar/cancelar
   - Probar WebSocket de progreso
   - Probar descarga de reportes

2. **Deprecar sistema legacy**:
   - Agregar banner de deprecación en `interfaz_web/`
   - Redirigir a nueva interfaz React
   - Actualizar documentación

3. **Commit y push**:
   ```bash
   git add .
   git commit -m "feat: Unificar extracción masiva con arquitectura limpia"
   git push -u origin claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG
   ```

---

## 🎯 ENDPOINTS FINALES UNIFICADOS

### API REST v1:
```
POST   /api/v1/expedientes/extraer              # Extracción simple (legacy, mantener)
POST   /api/v1/expedientes/filtrar              # Filtrado
GET    /api/v1/expedientes                      # Listar
GET    /api/v1/expedientes/{numero}             # Obtener uno

POST   /api/v1/expedientes/extraer/masivo       # 🆕 Extracción masiva avanzada
GET    /api/v1/expedientes/extraer/{session_id}/progreso   # 🆕 Progreso
POST   /api/v1/expedientes/extraer/{session_id}/pausar     # 🆕 Pausar
POST   /api/v1/expedientes/extraer/{session_id}/reanudar   # 🆕 Reanudar
POST   /api/v1/expedientes/extraer/{session_id}/cancelar   # 🆕 Cancelar
GET    /api/v1/expedientes/extraer/{session_id}/resumen    # 🆕 Resumen
GET    /api/v1/expedientes/extraer/{session_id}/descargar/{formato}  # 🆕 Descargar
WS     /api/v1/expedientes/extraer/{session_id}/ws         # 🆕 WebSocket
```

---

## ✅ CRITERIOS DE ÉXITO

1. ✅ Un único endpoint de extracción masiva (`/api/v1/expedientes/extraer/masivo`)
2. ✅ Arquitectura limpia mantenida (Use Cases, DTOs, DI)
3. ✅ WebSocket funcional para progreso en tiempo real
4. ✅ Control completo: pausar, reanudar, cancelar
5. ✅ Exportación a múltiples formatos (JSON, Excel, CSV)
6. ✅ Frontend React moderno con todas las funcionalidades
7. ✅ Sistema legacy deprecated con redirección
8. ✅ Tests pasando
9. ✅ Documentación actualizada

---

## 📊 TIEMPO ESTIMADO

- **Paso 1-4** (Backend core): 2-3 horas
- **Paso 5-7** (API y WebSocket): 2 horas
- **Paso 8-9** (Frontend): 2-3 horas
- **Paso 10** (Testing y cleanup): 1-2 horas

**Total**: 7-10 horas (1-2 días de desarrollo)

---

## 🚨 NOTAS IMPORTANTES

1. **No romper compatibilidad**: El endpoint `/api/v1/expedientes/extraer` debe seguir funcionando
2. **Migración gradual**: Los usuarios pueden usar ambos sistemas durante la transición
3. **Testing exhaustivo**: Probar todos los flujos antes de deprecar el sistema legacy
4. **Documentar cambios**: Actualizar README y documentación de la API
5. **Monitoreo**: Agregar logs detallados para debugging

---

## 📚 DEPENDENCIAS Y PREREQUISITOS

### Verificar antes de comenzar:
- ✅ Python 3.10+
- ✅ FastAPI instalado
- ✅ Playwright configurado
- ✅ Node.js 18+ y npm
- ✅ React 18+
- ✅ Zustand instalado

### Archivos críticos que NO deben modificarse sin cuidado:
- `Sistema_v6/extraccion_masiva/extractor_masivo.py` (usado tal cual)
- `Sistema_v6/extraccion_masiva/gestor_batch.py` (usado tal cual)
- Estructura de directorios de workspaces

---

## 🎓 REFERENCIAS

- Arquitectura Hexagonal: https://alistair.cockburn.us/hexagonal-architecture/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- Zustand Store: https://github.com/pmndrs/zustand
- React Hooks: https://react.dev/reference/react

---

**Última actualización**: 2025-11-07
**Rama de trabajo**: `claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG`
**Status**: ✅ LISTO PARA IMPLEMENTACIÓN
