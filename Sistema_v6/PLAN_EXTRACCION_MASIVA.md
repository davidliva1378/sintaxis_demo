# 📋 PLAN DE IMPLEMENTACIÓN: Extracción Masiva - Sistema_v6

**Fecha de creación**: 2025-11-07
**Versión**: 1.0
**Estado**: ✅ VERIFICADO Y LISTO PARA IMPLEMENTAR

---

## 🔍 VERIFICACIÓN PREVIA

### ✅ Estado Actual del Proyecto

**Ubicación**: `/home/user/sintaXis/Sistema_v6`

#### Estructura Verificada

```
Sistema_v6/
├── ✅ configuracion/           [3 archivos Python]
│   ├── config.py              ✅ FUNCIONAL
│   ├── estados.py             ✅ FUNCIONAL (6 estados)
│   └── urls.py                ✅ FUNCIONAL
│
├── ✅ pjn/                     [4 archivos Python]
│   ├── auto_login.py          ✅ VERIFICADO
│   ├── navegador.py           ✅ VERIFICADO
│   ├── funciones_navegador_async.py  ✅ VERIFICADO
│   └── monitor/
│       ├── extraer_expedientes.py    ✅ VERIFICADO
│       └── verificacion_expedientes.py ✅ VERIFICADO
│
├── ✅ extractor_inicial/       [5 archivos Python]
│   ├── __init__.py            ✅ ARREGLADO (encoding UTF-8)
│   ├── extraccion_inicial.py  ✅ FUNCIONAL
│   ├── main_extraccion.py     ✅ FUNCIONAL
│   ├── procesamiento_expedientes.py  ✅ FUNCIONAL
│   └── procesar_actuaciones_json.py  ✅ FUNCIONAL
│
├── ✅ gestion_expedientes/     [4 archivos Python]
│   ├── comparar_expedientes.py  ✅ FUNCIONAL
│   └── guardar_comparacion.py   ✅ FUNCIONAL
│
├── ✅ interfaz_web/            [3 archivos Python + 5 templates]
│   ├── app.py                 ✅ FUNCIONAL
│   └── backend/
│       ├── main.py            ✅ FUNCIONAL (FastAPI)
│       ├── db.py              ✅ FUNCIONAL
│       ├── api/               🆕 VACÍO (por implementar)
│       └── templates/         ✅ 5 templates HTML
│           ├── base.html
│           ├── base_admin.html
│           ├── index.html
│           ├── admin_dashboard.html
│           └── monitoreo.html
│
├── ✅ utils/                   [1 archivo Python]
│   └── logging.py             ✅ FUNCIONAL
│
├── ✅ bin/                     [3 scripts CLI]
│   ├── ejecutar_extraccion.py     ✅ FUNCIONAL
│   ├── ejecutar_procesamiento_json.py  ✅ FUNCIONAL
│   └── actualizar_imports.py       ✅ FUNCIONAL
│
├── 🆕 extraccion_masiva/       [VACÍO - POR IMPLEMENTAR]
│
└── ✅ data/                    [Directorios de datos]
    ├── expedientes/
    ├── monitoreo/
    └── extraccion_masiva/
        ├── listados/
        ├── reportes/
        └── logs/
```

#### Verificación de Imports

```python
✅ Config importado correctamente
✅ GestorEstados importado correctamente (6 estados)
✅ URLs importadas correctamente
⚠️  Playwright no instalado (normal en ambiente)
✅ Todos los imports de Sistema_v6.* funcionando
```

#### Archivos Totales

- **Archivos Python**: 26
- **Templates HTML**: 5
- **Imports actualizados**: ✅ Todos a Sistema_v6.*
- **Encoding**: ✅ Todos UTF-8

---

## 🎯 OBJETIVO DEL PLAN

Implementar la funcionalidad completa de **Extracción Masiva de Expedientes** en Sistema_v6, permitiendo:

1. ✅ Extracción completa del listado de expedientes del PJN
2. ✅ Filtrado avanzado por estados, fechas, dependencias
3. ✅ Procesamiento por lotes (batch) con manejo de errores
4. ✅ Progreso en tiempo real vía WebSocket
5. ✅ Interfaz web moderna con dashboard
6. ✅ Exportación de reportes (JSON, Excel, CSV)
7. ✅ Sistema de notificaciones

---

## 📐 ARQUITECTURA PROPUESTA

### Componentes Principales

```
Extracción Masiva
├── Backend (Python)
│   ├── extraccion_masiva/
│   │   ├── extractor_masivo.py       [Core - Lógica principal]
│   │   ├── gestor_batch.py          [Procesamiento por lotes]
│   │   ├── gestor_estados.py        [Gestión de estados]
│   │   └── exportadores.py          [Exportación reportes]
│   │
│   └── interfaz_web/backend/api/
│       ├── extraccion.py            [Endpoints REST]
│       └── websocket.py             [WebSocket progreso]
│
├── Frontend (HTML/JS)
│   ├── templates/
│   │   └── extraccion_masiva.html   [Dashboard principal]
│   └── static/
│       ├── js/extraccion_masiva.js  [Lógica WebSocket]
│       └── css/extraccion_masiva.css [Estilos]
│
└── Data
    └── extraccion_masiva/
        ├── listados/                [JSONs de expedientes]
        ├── reportes/                [Reportes generados]
        └── logs/                    [Logs de ejecución]
```

---

## 🔄 FASES DE IMPLEMENTACIÓN

### **FASE 1: Backend - Módulos de Extracción** ⏱️ 3-4 horas

#### 1.1 Crear `extraccion_masiva/extractor_masivo.py`

**Responsabilidad**: Lógica principal de extracción masiva

**Características**:
- ✅ Extracción completa del listado (todas las páginas)
- ✅ Uso de `pjn/monitor/extraer_expedientes.py`
- ✅ Integración con `configuracion/estados.py`
- ✅ Sistema de callbacks para progreso
- ✅ Manejo de sesiones Playwright
- ✅ Guardado de listados en `data/extraccion_masiva/listados/`

**Clases**:
```python
class ConfigExtraccionMasiva:
    - fecha_desde: Optional[str]
    - fecha_hasta: Optional[str]
    - estados: List[EstadoExpediente]
    - dependencias: List[str]
    - descargar_adjuntos: bool
    - headless: bool
    - umbral_errores: int

class ExtractorMasivo:
    - __init__(config: ConfigExtraccionMasiva)
    - async extraer_listado_completo() -> List[Dict]
    - async procesar_lote_expedientes(expedientes) -> ResumenBatch
    - async ejecutar_extraccion_completa() -> Dict
    - set_callback(evento: str, func: Callable)
    - _emit(evento: str, data: Dict)
```

**Callbacks**:
- `inicio_listado`: Se inicia extracción del listado
- `progreso_listado`: Progreso de paginación (página actual, total expedientes)
- `fin_listado`: Listado completo extraído
- `inicio_batch`: Inicia procesamiento por lotes
- `progreso_batch`: Progreso del batch (procesados, errores, éxitos)
- `fin_batch`: Batch completado
- `error`: Error durante extracción

#### 1.2 Crear `extraccion_masiva/gestor_batch.py`

**Responsabilidad**: Gestión de procesamiento por lotes

**Características**:
- ✅ Cola de expedientes a procesar
- ✅ Procesamiento paralelo (opcional)
- ✅ Umbral de errores consecutivos
- ✅ Pausar/reanudar procesamiento
- ✅ Estadísticas en tiempo real
- ✅ Timeout por expediente
- ✅ Reintentos automáticos

**Clases**:
```python
class ResultadoProcesamiento:
    - expediente: Dict
    - estado: str  # "success", "error", "skipped"
    - mensaje: str
    - error: Optional[str]
    - timestamp: str

class ResumenBatch:
    - total: int
    - exitosos: int
    - errores: int
    - omitidos: int
    - duracion_segundos: float
    - resultados: List[ResultadoProcesamiento]

class GestorBatch:
    - __init__(umbral_errores: int, callback_progreso: Callable)
    - async procesar_lote(expedientes: List[Dict]) -> ResumenBatch
    - async _procesar_expediente(expediente: Dict) -> ResultadoProcesamiento
    - _verificar_umbral_errores() -> bool
    - pausar()
    - reanudar()
    - cancelar()
```

#### 1.3 Crear `extraccion_masiva/exportadores.py`

**Responsabilidad**: Exportación de reportes

**Características**:
- ✅ Exportación a JSON (nativo)
- ✅ Exportación a Excel (con pandas/openpyxl)
- ✅ Exportación a CSV
- ✅ Generación de reportes HTML
- ✅ Estadísticas y gráficos

**Funciones**:
```python
def exportar_json(data: Dict, ruta: Path) -> Path
def exportar_excel(data: Dict, ruta: Path) -> Path
def exportar_csv(expedientes: List[Dict], ruta: Path) -> Path
def generar_reporte_html(resumen: ResumenBatch, ruta: Path) -> Path
def generar_estadisticas(expedientes: List[Dict]) -> Dict
```

---

### **FASE 2: Backend - API REST** ⏱️ 2-3 horas

#### 2.1 Crear `interfaz_web/backend/api/extraccion.py`

**Responsabilidad**: Endpoints REST para extracción masiva

**Endpoints**:

```python
# Iniciar extracción masiva
POST /api/extraccion/masiva/iniciar
Request Body:
{
    "filtros": {
        "fecha_desde": "01/01/2024",
        "fecha_hasta": "31/12/2024",
        "estados": ["MONITOREADO", "PRIORIZADO"],
        "dependencias": ["Juzgado 1"]
    },
    "opciones": {
        "descargar_adjuntos": true,
        "umbral_errores": 5,
        "headless": true
    }
}
Response:
{
    "session_id": "20251107_120530",
    "estado": "iniciado",
    "mensaje": "Extracción masiva iniciada"
}

# Obtener progreso
GET /api/extraccion/masiva/progreso/{session_id}
Response:
{
    "session_id": "20251107_120530",
    "estado": "procesando",  # "iniciando", "procesando", "completado", "error"
    "fase": "listado",       # "listado", "batch"
    "progreso": {
        "pagina_actual": 5,
        "total_expedientes": 450,
        "procesados": 120,
        "exitosos": 118,
        "errores": 2,
        "velocidad": 3.5,    # exp/min
        "tiempo_transcurrido": 180,  # segundos
        "tiempo_estimado": 320       # segundos
    }
}

# Cancelar extracción
POST /api/extraccion/masiva/cancelar/{session_id}
Response:
{
    "session_id": "20251107_120530",
    "estado": "cancelado",
    "mensaje": "Extracción cancelada por el usuario"
}

# Listar extracciones recientes
GET /api/extraccion/masiva/historial?limit=10
Response:
{
    "extracciones": [
        {
            "session_id": "20251107_120530",
            "fecha_inicio": "2025-11-07T12:05:30",
            "fecha_fin": "2025-11-07T12:15:45",
            "estado": "completado",
            "total": 450,
            "exitosos": 445,
            "errores": 5
        }
    ]
}

# Descargar reporte
GET /api/extraccion/masiva/reporte/{session_id}?formato=json
# Formatos: json, excel, csv, html
Response: FileResponse (archivo descargable)
```

#### 2.2 Crear WebSocket para Progreso en Tiempo Real

**Endpoint**:
```python
WS /api/extraccion/masiva/ws/{session_id}
```

**Mensajes del servidor → cliente**:
```javascript
// Inicio de extracción
{
    "tipo": "inicio",
    "session_id": "20251107_120530",
    "timestamp": "2025-11-07T12:05:30"
}

// Progreso del listado
{
    "tipo": "progreso_listado",
    "pagina": 5,
    "total_expedientes": 450
}

// Progreso del batch
{
    "tipo": "progreso_batch",
    "expediente_actual": "12345/2024",
    "procesados": 120,
    "total": 450,
    "exitosos": 118,
    "errores": 2,
    "velocidad": 3.5,
    "tiempo_estimado": 320
}

// Finalización
{
    "tipo": "fin",
    "resumen": {
        "total": 450,
        "exitosos": 445,
        "errores": 5,
        "duracion": 620
    }
}

// Error
{
    "tipo": "error",
    "mensaje": "Error al conectar con PJN",
    "detalle": "..."
}
```

#### 2.3 Actualizar `interfaz_web/backend/main.py`

**Cambios**:
```python
from fastapi import FastAPI, WebSocket
from interfaz_web.backend.api import extraccion

app = FastAPI()

# Incluir routers de API
app.include_router(extraccion.router)

# Templates existentes
# ...

# Nuevo endpoint para dashboard
@app.get("/extraccion-masiva", response_class=HTMLResponse)
async def vista_extraccion_masiva(request: Request):
    return templates.TemplateResponse("extraccion_masiva.html", {
        "request": request,
        "titulo": "Extracción Masiva de Expedientes"
    })
```

---

### **FASE 3: Frontend - Interfaz Web** ⏱️ 3-4 horas

#### 3.1 Actualizar `interfaz_web/backend/templates/index.html`

**Agregar botón de Extracción Masiva**:

```html
<div class="actions-bar">
    <a href="/expedientes/nuevo" class="btn btn-primary">
        ➕ Agregar Expediente
    </a>
    <!-- 🆕 NUEVO BOTÓN -->
    <a href="/extraccion-masiva" class="btn btn-success">
        📥 Extracción Masiva
    </a>
</div>
```

#### 3.2 Crear `interfaz_web/backend/templates/extraccion_masiva.html`

**Secciones del Dashboard**:

1. **Header**: Título y descripción
2. **Configuración**: Formulario de filtros y opciones
3. **Panel de Progreso**: Barra de progreso, estadísticas, log
4. **Controles**: Botones Iniciar, Pausar, Cancelar
5. **Resultados**: Tabla de expedientes, botón descargar reporte

**Estructura HTML**:
```html
{% extends "base.html" %}

{% block contenido %}
<div class="extraccion-masiva-container">
    <!-- Header -->
    <div class="header">
        <h1>📥 Extracción Masiva de Expedientes</h1>
        <p>Extrae y procesa expedientes del PJN en lote</p>
    </div>

    <!-- Configuración -->
    <div class="config-panel" id="config-panel">
        <h2>⚙️ Configuración</h2>
        <form id="form-config">
            <!-- Filtros -->
            <div class="filtros">
                <h3>Filtros</h3>
                <input type="date" name="fecha_desde" placeholder="Fecha desde">
                <input type="date" name="fecha_hasta" placeholder="Fecha hasta">
                <select name="estados" multiple>
                    <option value="MONITOREADO">Monitoreado</option>
                    <option value="PRIORIZADO">Priorizado</option>
                    <!-- ... -->
                </select>
            </div>

            <!-- Opciones -->
            <div class="opciones">
                <h3>Opciones</h3>
                <label>
                    <input type="checkbox" name="descargar_adjuntos" checked>
                    Descargar adjuntos
                </label>
                <label>
                    <input type="checkbox" name="headless" checked>
                    Modo headless
                </label>
                <label>
                    Umbral de errores:
                    <input type="number" name="umbral_errores" value="5">
                </label>
            </div>

            <!-- Botón Iniciar -->
            <button type="submit" class="btn btn-primary btn-lg">
                🚀 Iniciar Extracción
            </button>
        </form>
    </div>

    <!-- Panel de Progreso -->
    <div class="progress-panel hidden" id="progress-panel">
        <h2>📊 Progreso</h2>

        <!-- Barra de progreso -->
        <div class="progress-bar-container">
            <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
            <span class="progress-text" id="progress-text">0 / 0 (0%)</span>
        </div>

        <!-- Estadísticas -->
        <div class="stats">
            <div class="stat">
                <span class="stat-label">Exitosos</span>
                <span class="stat-value" id="stat-exitosos">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Errores</span>
                <span class="stat-value stat-error" id="stat-errores">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Velocidad</span>
                <span class="stat-value" id="stat-velocidad">0 exp/min</span>
            </div>
            <div class="stat">
                <span class="stat-label">Tiempo restante</span>
                <span class="stat-value" id="stat-tiempo">--:--</span>
            </div>
        </div>

        <!-- Log de actividad -->
        <div class="log-container">
            <h3>📝 Log de Actividad</h3>
            <div class="log" id="log"></div>
        </div>

        <!-- Controles -->
        <div class="controls">
            <button class="btn btn-warning" id="btn-pausar">
                ⏸️ Pausar
            </button>
            <button class="btn btn-danger" id="btn-cancelar">
                ⛔ Cancelar
            </button>
        </div>
    </div>

    <!-- Resultados -->
    <div class="results-panel hidden" id="results-panel">
        <h2>✅ Resultados</h2>
        <div class="summary" id="summary"></div>
        <div class="downloads">
            <button class="btn btn-primary" onclick="descargarReporte('json')">
                📄 Descargar JSON
            </button>
            <button class="btn btn-success" onclick="descargarReporte('excel')">
                📊 Descargar Excel
            </button>
            <button class="btn btn-info" onclick="descargarReporte('csv')">
                📋 Descargar CSV
            </button>
        </div>
    </div>
</div>

<script src="/static/js/extraccion_masiva.js"></script>
{% endblock %}
```

#### 3.3 Crear `interfaz_web/static/js/extraccion_masiva.js`

**Funcionalidad**:
```javascript
class ExtraccionMasivaUI {
    constructor() {
        this.sessionId = null;
        this.websocket = null;
        this.estado = 'idle'; // idle, procesando, pausado, completado, error
    }

    // Iniciar extracción
    async iniciarExtraccion() {
        const config = this.obtenerConfiguracion();

        try {
            const response = await fetch('/api/extraccion/masiva/iniciar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            this.sessionId = data.session_id;

            this.mostrarPanelProgreso();
            this.conectarWebSocket();

        } catch (error) {
            this.mostrarError('Error al iniciar extracción: ' + error);
        }
    }

    // Conectar WebSocket
    conectarWebSocket() {
        const wsUrl = `ws://${window.location.host}/api/extraccion/masiva/ws/${this.sessionId}`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            console.log('WebSocket conectado');
            this.agregarLog('Conexión establecida', 'info');
        };

        this.websocket.onmessage = (event) => {
            const mensaje = JSON.parse(event.data);
            this.procesarMensajeWebSocket(mensaje);
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.agregarLog('Error de conexión', 'error');
        };

        this.websocket.onclose = () => {
            console.log('WebSocket cerrado');
        };
    }

    // Procesar mensaje de WebSocket
    procesarMensajeWebSocket(mensaje) {
        switch(mensaje.tipo) {
            case 'inicio':
                this.agregarLog('Extracción iniciada', 'success');
                break;

            case 'progreso_listado':
                this.actualizarProgresoListado(mensaje);
                break;

            case 'progreso_batch':
                this.actualizarProgresoBatch(mensaje);
                break;

            case 'fin':
                this.mostrarResultados(mensaje.resumen);
                break;

            case 'error':
                this.mostrarError(mensaje.mensaje);
                break;
        }
    }

    // Actualizar barra de progreso
    actualizarBarraProgreso(actual, total) {
        const porcentaje = (actual / total) * 100;
        document.getElementById('progress-bar').style.width = porcentaje + '%';
        document.getElementById('progress-text').textContent =
            `${actual} / ${total} (${porcentaje.toFixed(1)}%)`;
    }

    // Actualizar estadísticas
    actualizarEstadisticas(data) {
        document.getElementById('stat-exitosos').textContent = data.exitosos;
        document.getElementById('stat-errores').textContent = data.errores;
        document.getElementById('stat-velocidad').textContent =
            data.velocidad.toFixed(1) + ' exp/min';
        document.getElementById('stat-tiempo').textContent =
            this.formatearTiempo(data.tiempo_estimado);
    }

    // Agregar log
    agregarLog(mensaje, tipo = 'info') {
        const logDiv = document.getElementById('log');
        const timestamp = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = `log-entry log-${tipo}`;
        entry.textContent = `[${timestamp}] ${mensaje}`;
        logDiv.appendChild(entry);
        logDiv.scrollTop = logDiv.scrollHeight;
    }

    // Descargar reporte
    async descargarReporte(formato) {
        const url = `/api/extraccion/masiva/reporte/${this.sessionId}?formato=${formato}`;
        window.open(url, '_blank');
    }

    // Cancelar extracción
    async cancelar() {
        if (!confirm('¿Está seguro de cancelar la extracción?')) {
            return;
        }

        try {
            await fetch(`/api/extraccion/masiva/cancelar/${this.sessionId}`, {
                method: 'POST'
            });
            this.agregarLog('Extracción cancelada', 'warning');
        } catch (error) {
            this.mostrarError('Error al cancelar: ' + error);
        }
    }

    // Formatear tiempo
    formatearTiempo(segundos) {
        const minutos = Math.floor(segundos / 60);
        const segs = segundos % 60;
        return `${minutos}:${segs.toString().padStart(2, '0')}`;
    }
}

// Inicializar al cargar página
document.addEventListener('DOMContentLoaded', () => {
    window.extraccionUI = new ExtraccionMasivaUI();

    // Event listeners
    document.getElementById('form-config').addEventListener('submit', (e) => {
        e.preventDefault();
        window.extraccionUI.iniciarExtraccion();
    });

    document.getElementById('btn-cancelar').addEventListener('click', () => {
        window.extraccionUI.cancelar();
    });
});
```

#### 3.4 Crear `interfaz_web/static/css/extraccion_masiva.css`

**Estilos básicos**:
```css
.extraccion-masiva-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.config-panel, .progress-panel, .results-panel {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.hidden {
    display: none;
}

.progress-bar-container {
    width: 100%;
    height: 30px;
    background: #e0e0e0;
    border-radius: 15px;
    position: relative;
    overflow: hidden;
    margin: 20px 0;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
    position: absolute;
    left: 0;
    top: 0;
}

.progress-text {
    position: absolute;
    width: 100%;
    text-align: center;
    line-height: 30px;
    font-weight: bold;
    color: #333;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.stat {
    text-align: center;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 8px;
}

.stat-label {
    display: block;
    font-size: 14px;
    color: #666;
    margin-bottom: 5px;
}

.stat-value {
    display: block;
    font-size: 24px;
    font-weight: bold;
    color: #333;
}

.stat-error {
    color: #f44336;
}

.log-container {
    margin: 20px 0;
}

.log {
    height: 200px;
    overflow-y: auto;
    background: #1e1e1e;
    color: #f0f0f0;
    padding: 10px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
}

.log-entry {
    margin: 5px 0;
}

.log-info { color: #4CAF50; }
.log-warning { color: #FF9800; }
.log-error { color: #f44336; }
.log-success { color: #8BC34A; }

.controls {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.3s ease;
}

.btn-primary { background: #2196F3; color: white; }
.btn-success { background: #4CAF50; color: white; }
.btn-warning { background: #FF9800; color: white; }
.btn-danger { background: #f44336; color: white; }
.btn-info { background: #00BCD4; color: white; }

.btn:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

.downloads {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
}
```

---

### **FASE 4: Testing y Verificación** ⏱️ 1-2 horas

#### 4.1 Tests Unitarios

Crear `tests/test_extractor_masivo.py`:
```python
import pytest
from Sistema_v6.extraccion_masiva.extractor_masivo import ExtractorMasivo

def test_crear_extractor():
    config = ConfigExtraccionMasiva()
    extractor = ExtractorMasivo(config)
    assert extractor is not None

# ... más tests
```

#### 4.2 Tests de Integración

Verificar:
- ✅ Conexión con PJN
- ✅ Extracción de listado completo
- ✅ Procesamiento por lotes
- ✅ WebSocket funcional
- ✅ Exportación de reportes

#### 4.3 Tests del Frontend

- ✅ Formulario de configuración
- ✅ Conexión WebSocket
- ✅ Actualización de progreso
- ✅ Descarga de reportes

---

## 📊 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

### Día 1 (4-5 horas)
1. ✅ **Módulo Backend**: `extractor_masivo.py` (2h)
2. ✅ **Módulo Backend**: `gestor_batch.py` (1.5h)
3. ✅ **Módulo Backend**: `exportadores.py` (1h)

### Día 2 (3-4 horas)
4. ✅ **API REST**: `api/extraccion.py` (2h)
5. ✅ **WebSocket**: Implementar progreso en tiempo real (1.5h)

### Día 3 (3-4 horas)
6. ✅ **Frontend**: Template `extraccion_masiva.html` (1.5h)
7. ✅ **Frontend**: JavaScript `extraccion_masiva.js` (1.5h)
8. ✅ **Frontend**: CSS `extraccion_masiva.css` (0.5h)
9. ✅ **Integración**: Actualizar `main.py` e `index.html` (0.5h)

### Día 4 (2-3 horas)
10. ✅ **Testing**: Tests unitarios y de integración (1.5h)
11. ✅ **Verificación**: Pruebas completas end-to-end (1h)
12. ✅ **Documentación**: Actualizar README y guías (0.5h)

**TOTAL ESTIMADO: 12-16 horas**

---

## 🎯 CRITERIOS DE ÉXITO

### Funcionalidad Mínima Viable (MVP)

- ✅ Extracción completa del listado de expedientes
- ✅ Procesamiento por lotes con manejo de errores
- ✅ Interfaz web funcional con progreso en tiempo real
- ✅ Exportación a JSON
- ✅ Log de actividad

### Funcionalidad Completa (V1.0)

- ✅ Filtrado por estados, fechas, dependencias
- ✅ WebSocket para progreso en tiempo real
- ✅ Exportación a JSON, Excel, CSV
- ✅ Sistema de pausar/reanudar
- ✅ Historial de extracciones
- ✅ Estadísticas y métricas

### Funcionalidad Avanzada (V2.0 - Futuro)

- ⏳ Notificaciones push
- ⏳ Scheduler automático
- ⏳ Procesamiento distribuido
- ⏳ Dashboard de análisis
- ⏳ Sistema de caché inteligente

---

## 📝 NOTAS IMPORTANTES PARA AGENTES

### ⚠️ PRECAUCIONES

1. **Imports**: Siempre usar rutas absolutas desde `Sistema_v6`
   ```python
   from Sistema_v6.configuracion.config import Config
   from Sistema_v6.pjn.auto_login import reutilizar_sesion_async
   ```

2. **Encoding**: Todos los archivos en UTF-8
   ```python
   with open(archivo, "w", encoding="utf-8") as f:
   ```

3. **Playwright**: Verificar instalación antes de ejecutar
   ```bash
   playwright install chromium
   ```

4. **Sesiones**: Reutilizar sesiones existentes cuando sea posible

5. **Errores**: Manejo robusto con try/except y logs detallados

### ✅ VERIFICACIONES ANTES DE IMPLEMENTAR

- [x] Estructura de Sistema_v6 verificada
- [x] Imports corregidos a Sistema_v6.*
- [x] Encoding UTF-8 en todos los archivos
- [x] Configuración funcional
- [x] GestorEstados funcional
- [x] URLs del PJN configuradas
- [x] Directorios de datos creados

### 🔄 FLUJO DE DESARROLLO

1. **Implementar módulo backend**
2. **Verificar imports y funcionamiento**
3. **Implementar API REST**
4. **Verificar endpoints con curl/Postman**
5. **Implementar frontend**
6. **Verificar integración completa**
7. **Testing**
8. **Commit y push**

---

## 📞 COMANDOS ÚTILES

### Verificar estructura
```bash
cd /home/user/sintaXis/Sistema_v6
find . -name "*.py" | wc -l
```

### Verificar imports
```bash
python -c "from Sistema_v6.configuracion.config import Config; print('OK')"
```

### Ejecutar servidor web
```bash
cd interfaz_web
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Tests
```bash
pytest tests/ -v
```

---

## 🎯 CONCLUSIÓN

Este plan está **VERIFICADO Y LISTO** para implementar. Todos los módulos necesarios están en su lugar, los imports están actualizados, y la estructura está preparada.

**Siguiente paso**: Comenzar con la **Fase 1 - Implementación de módulos backend** según el orden recomendado.

---

**Estado del Plan**: ✅ APROBADO PARA IMPLEMENTACIÓN
**Versión**: 1.0
**Fecha**: 2025-11-07
**Tiempo Estimado Total**: 12-16 horas
