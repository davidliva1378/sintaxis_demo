# 🤖 DOCUMENTO DE SEGUIMIENTO PARA AGENTES - Extracción Masiva

**Sistema**: Sistema_v6 - Extracción Masiva de Expedientes
**Fecha**: 2025-11-07
**Versión**: 1.0

---

## 📋 RESUMEN EJECUTIVO

Este documento proporciona instrucciones detalladas para agentes de IA que implementarán la funcionalidad de **Extracción Masiva** en Sistema_v6.

**Estado actual**:
- ✅ Estructura de Sistema_v6 verificada y funcional
- ✅ 26 archivos Python migrados
- ✅ Imports actualizados a Sistema_v6.*
- ✅ Configuración centralizada funcionando
- ✅ Sistema de estados implementado
- ⏳ Módulo extraccion_masiva/ vacío (pendiente implementar)

---

## 🎯 OBJETIVO PRINCIPAL

Implementar un sistema completo de **Extracción Masiva de Expedientes** que permita:

1. Extraer listados completos del portal PJN (todas las páginas)
2. Procesar expedientes por lotes con manejo robusto de errores
3. Mostrar progreso en tiempo real vía WebSocket
4. Proporcionar interfaz web moderna y responsiva
5. Exportar reportes en múltiples formatos (JSON, Excel, CSV)

---

## 📐 CONTEXTO TÉCNICO

### Ubicación del Proyecto
```
/home/user/sintaXis/Sistema_v6
```

### Estructura Actual (Verificada)

```
Sistema_v6/
├── configuracion/           ✅ FUNCIONAL
│   ├── config.py           # Configuración central
│   ├── estados.py          # 6 estados de expedientes
│   └── urls.py             # URLs del PJN
│
├── pjn/                    ✅ FUNCIONAL
│   ├── auto_login.py       # Autenticación Playwright
│   ├── navegador.py        # Control de navegador
│   └── monitor/
│       └── extraer_expedientes.py  # Extracción paginada
│
├── extractor_inicial/      ✅ FUNCIONAL
│   └── extraccion_inicial.py  # Extracción incremental
│
├── gestion_expedientes/    ✅ FUNCIONAL
│   └── comparar_expedientes.py
│
├── interfaz_web/           ✅ FUNCIONAL
│   ├── app.py
│   └── backend/
│       ├── main.py         # FastAPI server
│       ├── api/            ⚠️ VACÍO (por implementar)
│       └── templates/      ✅ 5 templates HTML
│
├── extraccion_masiva/      ❌ VACÍO (TODO)
│
└── data/                   ✅ CREADO
    └── extraccion_masiva/
        ├── listados/
        ├── reportes/
        └── logs/
```

### Módulos Reutilizables

Estos módulos YA EXISTEN y deben ser utilizados:

1. **`pjn/monitor/extraer_expedientes.py`**
   - Función: `async def extraer_expedientes(page, ...)`
   - Extrae expedientes página por página
   - Maneja paginación automática
   - Detecta duplicados

2. **`pjn/auto_login.py`**
   - Función: `async def reutilizar_sesion_async()`
   - Context manager para sesiones Playwright
   - Reutiliza sesiones existentes

3. **`configuracion/estados.py`**
   - Clase: `GestorEstados`
   - Enum: `EstadoExpediente` (6 estados)
   - Métodos: filtrar_por_estado(), actualizar_estado()

4. **`configuracion/config.py`**
   - Clase: `Config`
   - Configuración centralizada
   - Paths de directorios

---

## 🔧 INSTRUCCIONES DE IMPLEMENTACIÓN

### PASO 1: Crear `extraccion_masiva/extractor_masivo.py`

**Tiempo estimado**: 2 horas

#### Objetivo
Implementar la clase principal que orquesta la extracción masiva completa.

#### Pseudocódigo de Alto Nivel

```python
"""
extraccion_masiva/extractor_masivo.py

Módulo principal de extracción masiva de expedientes del PJN.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import json
import asyncio

from Sistema_v6.configuracion.config import Config
from Sistema_v6.configuracion.estados import GestorEstados, EstadoExpediente
from Sistema_v6.configuracion.urls import URL_CONSULTAS
from Sistema_v6.pjn.auto_login import reutilizar_sesion_async
from Sistema_v6.pjn.monitor.extraer_expedientes import extraer_expedientes


class ConfigExtraccionMasiva:
    """Configuración para extracción masiva."""

    def __init__(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        estados: List[EstadoExpediente] = None,
        dependencias: List[str] = None,
        descargar_adjuntos: bool = True,
        headless: bool = True,
        umbral_errores: int = 5,
    ):
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.estados = estados or [EstadoExpediente.MONITOREADO, EstadoExpediente.PRIORIZADO]
        self.dependencias = dependencias or []
        self.descargar_adjuntos = descargar_adjuntos
        self.headless = headless
        self.umbral_errores = umbral_errores


class ExtractorMasivo:
    """Extractor masivo de expedientes del PJN."""

    def __init__(self, config: ConfigExtraccionMasiva):
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.callbacks: Dict[str, Callable] = {}
        self.cancelado = False

        # Paths de guardado
        self.listados_dir = Config.DATA_DIR / "extraccion_masiva" / "listados"
        self.reportes_dir = Config.DATA_DIR / "extraccion_masiva" / "reportes"
        self.logs_dir = Config.DATA_DIR / "extraccion_masiva" / "logs"

    def set_callback(self, evento: str, func: Callable):
        """Registrar callback para evento."""
        self.callbacks[evento] = func

    def _emit(self, evento: str, data: Dict):
        """Emitir evento a través de callback."""
        if evento in self.callbacks:
            try:
                self.callbacks[evento](data)
            except Exception as e:
                print(f"Error en callback {evento}: {e}")

    async def extraer_listado_completo(self) -> List[Dict]:
        """
        FASE 1: Extraer listado completo de expedientes del PJN.

        Returns:
            Lista de diccionarios con datos de expedientes
        """
        self._emit("inicio_listado", {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })

        expedientes = []
        pagina_actual = 1

        async with reutilizar_sesion_async() as (page, context, browser):
            await page.goto(URL_CONSULTAS)
            await page.wait_for_load_state("domcontentloaded")

            while not self.cancelado:
                self._emit("progreso_listado", {
                    "pagina": pagina_actual,
                    "total": len(expedientes)
                })

                # Usar función existente de extracción
                nuevos, _, motivo = await extraer_expedientes(
                    page=page,
                    guardar_json=False,
                    detener_en_duplicado=False,  # Queremos TODOS
                    fecha_corte=self.config.fecha_desde,
                )

                expedientes.extend(nuevos)

                if motivo == "fin_tabla":
                    break

                # Siguiente página
                try:
                    siguiente = await page.query_selector("a.ui-paginator-next")
                    if siguiente and not await siguiente.is_disabled():
                        await siguiente.click()
                        await page.wait_for_load_state("domcontentloaded")
                        pagina_actual += 1
                    else:
                        break
                except Exception:
                    break

        # Guardar listado completo
        listado_path = self.listados_dir / f"listado_{self.session_id}.json"
        listado_path.parent.mkdir(parents=True, exist_ok=True)

        with open(listado_path, "w", encoding="utf-8") as f:
            json.dump(expedientes, f, indent=2, ensure_ascii=False)

        self._emit("fin_listado", {
            "total": len(expedientes),
            "archivo": str(listado_path)
        })

        return expedientes

    async def procesar_lote_expedientes(
        self,
        expedientes: List[Dict]
    ) -> Dict:
        """
        FASE 2: Procesar lote de expedientes.

        Args:
            expedientes: Lista de expedientes a procesar

        Returns:
            Diccionario con resumen del procesamiento
        """
        from Sistema_v6.extraccion_masiva.gestor_batch import GestorBatch

        self._emit("inicio_batch", {
            "total": len(expedientes),
            "timestamp": datetime.now().isoformat()
        })

        # Crear gestor de batch
        gestor = GestorBatch(
            umbral_errores=self.config.umbral_errores,
            callback_progreso=lambda data: self._emit("progreso_batch", data)
        )

        # Procesar
        resumen = await gestor.procesar_lote(
            expedientes,
            descargar_adjuntos=self.config.descargar_adjuntos,
            headless=self.config.headless
        )

        self._emit("fin_batch", resumen.to_dict())

        return resumen.to_dict()

    async def ejecutar_extraccion_completa(self) -> Dict:
        """
        Ejecutar extracción masiva completa (listado + procesamiento).

        Returns:
            Diccionario con resultado completo
        """
        try:
            # Fase 1: Extraer listado
            expedientes = await self.extraer_listado_completo()

            if self.cancelado:
                return {
                    "estado": "cancelado",
                    "mensaje": "Extracción cancelada por el usuario"
                }

            # Filtrar por estados si es necesario
            if self.config.estados:
                gestor_estados = GestorEstados()
                gestor_estados.cargar_estados()
                expedientes = gestor_estados.filtrar_por_estado(
                    expedientes,
                    self.config.estados
                )

            # Fase 2: Procesar lote
            resumen = await self.procesar_lote_expedientes(expedientes)

            # Guardar reporte final
            reporte_path = self.reportes_dir / f"reporte_{self.session_id}.json"
            with open(reporte_path, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self.session_id,
                    "fecha": datetime.now().isoformat(),
                    "config": {
                        "estados": [e.value for e in self.config.estados],
                        "fecha_desde": self.config.fecha_desde,
                        "fecha_hasta": self.config.fecha_hasta,
                    },
                    "resultado": resumen
                }, f, indent=2, ensure_ascii=False)

            return {
                "estado": "completado",
                "session_id": self.session_id,
                "resultado": resumen,
                "reporte": str(reporte_path)
            }

        except Exception as e:
            self._emit("error", {
                "mensaje": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return {
                "estado": "error",
                "mensaje": str(e)
            }

    def cancelar(self):
        """Cancelar extracción en curso."""
        self.cancelado = True
```

#### Verificación

```python
# Test rápido
import asyncio
from Sistema_v6.extraccion_masiva.extractor_masivo import ExtractorMasivo, ConfigExtraccionMasiva

config = ConfigExtraccionMasiva(headless=True)
extractor = ExtractorMasivo(config)

# Verificar que se crea correctamente
assert extractor.session_id is not None
print("✅ ExtractorMasivo creado correctamente")
```

---

### PASO 2: Crear `extraccion_masiva/gestor_batch.py`

**Tiempo estimado**: 1.5 horas

#### Objetivo
Gestionar procesamiento por lotes con manejo robusto de errores.

#### Pseudocódigo

```python
"""
extraccion_masiva/gestor_batch.py

Gestor de procesamiento por lotes de expedientes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Callable, Optional
import asyncio
import time


@dataclass
class ResultadoProcesamiento:
    """Resultado del procesamiento de un expediente."""
    expediente: Dict
    estado: str  # "success", "error", "skipped"
    mensaje: str
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ResumenBatch:
    """Resumen del procesamiento batch."""
    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    resultados: List[ResultadoProcesamiento]
    tiempo_inicio: str = None
    tiempo_fin: str = None

    def to_dict(self) -> Dict:
        return {
            "total": self.total,
            "exitosos": self.exitosos,
            "errores": self.errores,
            "omitidos": self.omitidos,
            "duracion_segundos": self.duracion_segundos,
            "tiempo_inicio": self.tiempo_inicio,
            "tiempo_fin": self.tiempo_fin,
            "resultados": [
                {
                    "numero": r.expediente.get("numero"),
                    "estado": r.estado,
                    "mensaje": r.mensaje,
                    "error": r.error,
                    "timestamp": r.timestamp
                }
                for r in self.resultados
            ]
        }


class GestorBatch:
    """Gestor de procesamiento por lotes."""

    def __init__(
        self,
        umbral_errores: int = 5,
        callback_progreso: Optional[Callable] = None
    ):
        self.umbral_errores = umbral_errores
        self.callback_progreso = callback_progreso

        self.resultados: List[ResultadoProcesamiento] = []
        self.errores_consecutivos = 0
        self.pausado = False
        self.cancelado = False

    async def procesar_lote(
        self,
        expedientes: List[Dict],
        descargar_adjuntos: bool = True,
        headless: bool = True
    ) -> ResumenBatch:
        """
        Procesar lote de expedientes.

        Args:
            expedientes: Lista de expedientes a procesar
            descargar_adjuntos: Si descargar adjuntos
            headless: Modo headless de Playwright

        Returns:
            ResumenBatch con resultados
        """
        tiempo_inicio = time.time()
        tiempo_inicio_str = datetime.now().isoformat()

        total = len(expedientes)
        exitosos = 0
        errores = 0
        omitidos = 0

        for i, expediente in enumerate(expedientes):
            if self.cancelado:
                break

            # Pausar si es necesario
            while self.pausado and not self.cancelado:
                await asyncio.sleep(0.5)

            try:
                # Emitir progreso
                if self.callback_progreso:
                    self.callback_progreso({
                        "expediente_actual": expediente.get("numero"),
                        "procesados": i + 1,
                        "total": total,
                        "exitosos": exitosos,
                        "errores": errores,
                        "velocidad": self._calcular_velocidad(i + 1, tiempo_inicio),
                        "tiempo_estimado": self._estimar_tiempo_restante(i + 1, total, tiempo_inicio)
                    })

                # Procesar expediente
                resultado = await self._procesar_expediente(expediente)
                self.resultados.append(resultado)

                if resultado.estado == "success":
                    exitosos += 1
                    self.errores_consecutivos = 0
                elif resultado.estado == "error":
                    errores += 1
                    self.errores_consecutivos += 1

                    # Verificar umbral de errores
                    if self.errores_consecutivos >= self.umbral_errores:
                        # Aquí se podría pausar o preguntar al usuario
                        print(f"⚠️ Umbral de errores alcanzado: {self.errores_consecutivos}")
                        # Por ahora, continuamos
                        self.errores_consecutivos = 0
                else:
                    omitidos += 1

            except Exception as e:
                print(f"Error inesperado procesando {expediente.get('numero')}: {e}")
                errores += 1

            # Pequeño delay entre expedientes
            await asyncio.sleep(0.5)

        tiempo_fin = time.time()
        duracion = tiempo_fin - tiempo_inicio

        return ResumenBatch(
            total=total,
            exitosos=exitosos,
            errores=errores,
            omitidos=omitidos,
            duracion_segundos=duracion,
            resultados=self.resultados,
            tiempo_inicio=tiempo_inicio_str,
            tiempo_fin=datetime.now().isoformat()
        )

    async def _procesar_expediente(self, expediente: Dict) -> ResultadoProcesamiento:
        """
        Procesar un expediente individual.

        Args:
            expediente: Datos del expediente

        Returns:
            ResultadoProcesamiento
        """
        try:
            # TODO: Aquí iría la lógica real de procesamiento
            # Por ahora, simulamos el procesamiento
            await asyncio.sleep(0.1)  # Simular tiempo de procesamiento

            return ResultadoProcesamiento(
                expediente=expediente,
                estado="success",
                mensaje="Expediente procesado correctamente"
            )

        except Exception as e:
            return ResultadoProcesamiento(
                expediente=expediente,
                estado="error",
                mensaje="Error al procesar expediente",
                error=str(e)
            )

    def _calcular_velocidad(self, procesados: int, tiempo_inicio: float) -> float:
        """Calcular velocidad de procesamiento (exp/min)."""
        tiempo_transcurrido = time.time() - tiempo_inicio
        if tiempo_transcurrido > 0:
            return (procesados / tiempo_transcurrido) * 60
        return 0.0

    def _estimar_tiempo_restante(self, procesados: int, total: int, tiempo_inicio: float) -> int:
        """Estimar tiempo restante en segundos."""
        if procesados == 0:
            return 0

        tiempo_transcurrido = time.time() - tiempo_inicio
        tiempo_por_expediente = tiempo_transcurrido / procesados
        restantes = total - procesados

        return int(restantes * tiempo_por_expediente)

    def pausar(self):
        """Pausar procesamiento."""
        self.pausado = True

    def reanudar(self):
        """Reanudar procesamiento."""
        self.pausado = False

    def cancelar(self):
        """Cancelar procesamiento."""
        self.cancelado = True
```

---

### PASO 3: Crear `extraccion_masiva/exportadores.py`

**Tiempo estimado**: 1 hora

```python
"""
extraccion_masiva/exportadores.py

Módulo de exportación de reportes en múltiples formatos.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def exportar_json(data: Dict, ruta: Path) -> Path:
    """
    Exportar datos a JSON.

    Args:
        data: Datos a exportar
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return ruta


def exportar_excel(data: Dict, ruta: Path) -> Path:
    """
    Exportar datos a Excel.

    Args:
        data: Datos a exportar (debe contener 'resultados')
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas no está instalado. Ejecute: pip install pandas openpyxl")

    # Convertir resultados a DataFrame
    resultados = data.get("resultados", [])

    df = pd.DataFrame([
        {
            "Número": r.get("numero"),
            "Estado": r.get("estado"),
            "Mensaje": r.get("mensaje"),
            "Error": r.get("error", ""),
            "Timestamp": r.get("timestamp")
        }
        for r in resultados
    ])

    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(ruta, index=False, engine="openpyxl")

    return ruta


def exportar_csv(expedientes: List[Dict], ruta: Path) -> Path:
    """
    Exportar expedientes a CSV.

    Args:
        expedientes: Lista de expedientes
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado
    """
    import csv

    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, "w", encoding="utf-8", newline="") as f:
        if not expedientes:
            return ruta

        fieldnames = expedientes[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(expedientes)

    return ruta


def generar_estadisticas(expedientes: List[Dict]) -> Dict:
    """
    Generar estadísticas de expedientes.

    Args:
        expedientes: Lista de expedientes

    Returns:
        Diccionario con estadísticas
    """
    total = len(expedientes)

    # Agrupar por dependencia
    por_dependencia = {}
    for exp in expedientes:
        dep = exp.get("dependencia", "Sin dependencia")
        por_dependencia[dep] = por_dependencia.get(dep, 0) + 1

    # Agrupar por situación
    por_situacion = {}
    for exp in expedientes:
        sit = exp.get("situacion", "Sin situación")
        por_situacion[sit] = por_situacion.get(sit, 0) + 1

    return {
        "total": total,
        "por_dependencia": por_dependencia,
        "por_situacion": por_situacion,
        "fecha_generacion": datetime.now().isoformat()
    }
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

Antes de continuar a la siguiente fase, verificar:

### Backend (Fase 1)

- [ ] `extractor_masivo.py` creado y funcional
  - [ ] Clase ConfigExtraccionMasiva
  - [ ] Clase ExtractorMasivo
  - [ ] Método extraer_listado_completo()
  - [ ] Método procesar_lote_expedientes()
  - [ ] Sistema de callbacks funcionando
  - [ ] Guardado de listados en data/

- [ ] `gestor_batch.py` creado y funcional
  - [ ] Clase ResultadoProcesamiento
  - [ ] Clase ResumenBatch
  - [ ] Clase GestorBatch
  - [ ] Método procesar_lote()
  - [ ] Manejo de errores consecutivos
  - [ ] Cálculo de velocidad y tiempo estimado

- [ ] `exportadores.py` creado y funcional
  - [ ] Función exportar_json()
  - [ ] Función exportar_excel()
  - [ ] Función exportar_csv()
  - [ ] Función generar_estadisticas()

### API REST (Fase 2)

- [ ] `interfaz_web/backend/api/extraccion.py` creado
  - [ ] POST /api/extraccion/masiva/iniciar
  - [ ] GET /api/extraccion/masiva/progreso/{id}
  - [ ] POST /api/extraccion/masiva/cancelar/{id}
  - [ ] GET /api/extraccion/masiva/historial
  - [ ] GET /api/extraccion/masiva/reporte/{id}

- [ ] WebSocket implementado
  - [ ] WS /api/extraccion/masiva/ws/{id}
  - [ ] Mensajes de progreso
  - [ ] Manejo de desconexiones

- [ ] `main.py` actualizado
  - [ ] Router de API incluido
  - [ ] Endpoint /extraccion-masiva agregado

### Frontend (Fase 3)

- [ ] `templates/extraccion_masiva.html` creado
  - [ ] Formulario de configuración
  - [ ] Panel de progreso
  - [ ] Log de actividad
  - [ ] Botones de control
  - [ ] Panel de resultados

- [ ] `static/js/extraccion_masiva.js` creado
  - [ ] Clase ExtraccionMasivaUI
  - [ ] Conexión WebSocket
  - [ ] Actualización de progreso
  - [ ] Manejo de eventos

- [ ] `static/css/extraccion_masiva.css` creado
  - [ ] Estilos responsive
  - [ ] Animaciones de progreso
  - [ ] Tema consistente

- [ ] `templates/index.html` actualizado
  - [ ] Botón de Extracción Masiva agregado

### Testing (Fase 4)

- [ ] Tests unitarios creados
- [ ] Tests de integración ejecutados
- [ ] Verificación end-to-end completada
- [ ] Documentación actualizada

---

## 🚨 PUNTOS CRÍTICOS DE ATENCIÓN

### 1. **Imports Absolutos**
```python
# ✅ CORRECTO
from Sistema_v6.configuracion.config import Config

# ❌ INCORRECTO
from configuracion.config import Config
```

### 2. **Encoding UTF-8**
```python
# Siempre especificar encoding
with open(archivo, "w", encoding="utf-8") as f:
    f.write(contenido)
```

### 3. **Manejo de Errores**
```python
# Siempre usar try/except en operaciones críticas
try:
    resultado = await operacion_critica()
except Exception as e:
    logger.error(f"Error: {e}")
    # Emitir evento de error
    self._emit("error", {"mensaje": str(e)})
```

### 4. **Sesiones Playwright**
```python
# Usar context manager
async with reutilizar_sesion_async() as (page, context, browser):
    # Tu código aquí
    pass
```

### 5. **Cancelación**
```python
# Verificar cancelación en loops largos
while not self.cancelado:
    # Procesar
    if self.cancelado:
        break
```

---

## 📞 COMANDOS DE VERIFICACIÓN

```bash
# Verificar estructura
find Sistema_v6/extraccion_masiva -name "*.py"

# Verificar imports
cd /home/user/sintaXis/Sistema_v6
python -c "from extraccion_masiva.extractor_masivo import ExtractorMasivo; print('OK')"

# Ejecutar tests
pytest tests/test_extractor_masivo.py -v

# Iniciar servidor
cd interfaz_web
uvicorn backend.main:app --reload
```

---

## 🎯 CRITERIO DE COMPLETITUD

La implementación está completa cuando:

1. ✅ Todos los módulos backend están creados y funcionan
2. ✅ API REST responde correctamente a todas las peticiones
3. ✅ WebSocket envía y recibe mensajes en tiempo real
4. ✅ Frontend muestra progreso correctamente
5. ✅ Se pueden descargar reportes en JSON, Excel, CSV
6. ✅ Todos los tests pasan
7. ✅ La documentación está actualizada

---

**Estado**: ✅ LISTO PARA IMPLEMENTAR
**Próximo paso**: Comenzar con PASO 1 - `extractor_masivo.py`
