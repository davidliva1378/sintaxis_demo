# Monitor PJN v5 - Documentacion

Sistema de monitoreo automatico del Portal Judicial de la Nacion (PJN) que detecta y notifica nuevas entradas/notificaciones y cambios en expedientes.

## Tabla de Contenidos

- [Caracteristicas](#caracteristicas)
- [Requisitos](#requisitos)
- [Instalacion](#instalacion)
- [Configuracion](#configuracion)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Troubleshooting](#troubleshooting)

---

## Caracteristicas

### Funcionalidades principales

- **Monitoreo de Entradas/Notificaciones**
  - Deteccion automatica de nuevas notificaciones y despachos
  - Filtrado por tipo de evento (N=Notificacion, D=Despacho)
  - Filtrado por rango de fechas (fecha_desde/fecha_hasta)
  - Corte temprano inteligente para evitar scroll innecesario
  - Deduplicacion automatica de entradas

- **Monitoreo de Expedientes** (opcional)
  - Deteccion de cambios en ultima_actuacion
  - Soporte para fecha de corte
  - Extraccion paginada con limite configurable

- **Notificaciones Desktop**
  - Notificaciones mediante plyer (Windows, macOS, Linux)
  - Configurable por tipo de evento
  - Notificaciones de errores opcionales

- **Scheduler Inteligente**
  - Modo automatico: alterna intervalos segun horario laboral
  - Modo laboral: siempre usa intervalos laborales
  - Modo no_laboral: siempre usa intervalos no laborales
  - Deteccion automatica de dias/horarios laborales

- **Persistencia y Estado**
  - Almacenamiento JSON de entradas y expedientes conocidos
  - Seguimiento de errores consecutivos
  - Historial de ultima verificacion

### Caracteristicas tecnicas

- Navegacion automatica con Playwright
- Autenticacion reutilizable (sesion persistente)
- Logging detallado con niveles configurables
- Manejo de errores con reintentos automaticos
- Modo headless para ejecucion en segundo plano
- CLI completo con multiples opciones

---

## Requisitos

### Software

- Python 3.10+
- Playwright (instalado automaticamente)
- Navegadores Chromium (instalado automaticamente por Playwright)

### Dependencias Python

Ver `requirements.txt` para la lista completa. Principales:

```
playwright>=1.40.0
plyer>=2.1.0
apscheduler>=3.10.0
```

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd Sistema_v5
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Instalar navegadores Playwright

```bash
playwright install chromium
```

### 6. Configurar credenciales

Crear archivo `.env` en la raiz con tus credenciales PJN:

```env
PJN_USER=tu_usuario
PJN_PASS=tu_password
```

**IMPORTANTE:** Nunca comitear el archivo `.env` al repositorio.

---

## Configuracion

### Archivo de configuracion

El monitor se configura mediante `config/monitor.json`:

```json
{
  "modo": "automatico",
  "headless": true,
  "directorio_datos": "data/monitor",

  "intervalos_laboral_expedientes": 15,
  "intervalos_laboral_entradas": 10,
  "intervalos_no_laboral_expedientes": 60,
  "intervalos_no_laboral_entradas": 30,

  "dias_laborales": ["lunes", "martes", "miercoles", "jueves", "viernes"],
  "hora_inicio": "08:00",
  "hora_fin": "18:00",

  "max_reintentos_expedientes": 3,
  "espera_reintentos_expedientes": 30,
  "max_reintentos_entradas": 3,
  "espera_reintentos_entradas": 30,

  "notificar_nuevas_entradas": true,
  "notificar_cambios_expedientes": true,
  "notificar_errores": true,

  "verificar_entradas": true,
  "verificar_expedientes": false,

  "comparacion_automatica": false,
  "fecha_corte_expedientes": null,
  "fecha_desde_entradas": "15/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

### Parametros principales

#### Modo de operacion

- **`modo`**: `"automatico"` | `"laboral"` | `"no_laboral"`
  - `automatico`: Alterna intervalos segun horario laboral
  - `laboral`: Siempre usa intervalos laborales (para testing)
  - `no_laboral`: Siempre usa intervalos no laborales

#### Visualizacion

- **`headless`**: `true` | `false`
  - `true`: Ejecuta browser sin interfaz grafica (recomendado para produccion)
  - `false`: Muestra ventana del browser (util para debugging)

#### Intervalos (en minutos)

- **`intervalos_laboral_entradas`**: Intervalo para verificar entradas en horario laboral
- **`intervalos_laboral_expedientes`**: Intervalo para verificar expedientes en horario laboral
- **`intervalos_no_laboral_entradas`**: Intervalo para verificar entradas fuera de horario laboral
- **`intervalos_no_laboral_expedientes`**: Intervalo para verificar expedientes fuera de horario laboral

#### Horario laboral

- **`dias_laborales`**: Array de dias considerados laborales
  - Valores validos: `"lunes"`, `"martes"`, `"miercoles"`, `"jueves"`, `"viernes"`, `"sabado"`, `"domingo"`
- **`hora_inicio`**: Hora de inicio del horario laboral (formato "HH:MM")
- **`hora_fin`**: Hora de fin del horario laboral (formato "HH:MM")

#### Notificaciones

- **`notificar_nuevas_entradas`**: Notificar cuando hay nuevas entradas
- **`notificar_cambios_expedientes`**: Notificar cambios en expedientes
- **`notificar_errores`**: Notificar cuando ocurren errores

#### Verificaciones

- **`verificar_entradas`**: `true` | `false`
  - Habilita/deshabilita verificacion de entradas
- **`verificar_expedientes`**: `true` | `false`
  - Habilita/deshabilita verificacion de expedientes

#### Filtros de fecha

- **`fecha_desde_entradas`**: Fecha minima para filtrar entradas (formato "DD/MM/YYYY" o "YYYY-MM-DD")
  - Solo se extraeran entradas con fecha >= fecha_desde
  - `null`: Sin filtro de fecha minima

- **`fecha_hasta_entradas`**: Fecha maxima para filtrar entradas (formato "DD/MM/YYYY" o "YYYY-MM-DD")
  - Solo se extraeran entradas con fecha <= fecha_hasta
  - `null`: Sin filtro de fecha maxima

- **`fecha_corte_expedientes`**: Fecha de corte para expedientes (formato "YYYY-MM-DD")
  - El extractor dejara de paginar cuando encuentre expedientes anteriores a esta fecha
  - `null`: Sin fecha de corte

#### Reintentos

- **`max_reintentos_entradas`**: Numero maximo de reintentos al fallar verificacion de entradas
- **`espera_reintentos_entradas`**: Segundos de espera entre reintentos de entradas
- **`max_reintentos_expedientes`**: Numero maximo de reintentos al fallar verificacion de expedientes
- **`espera_reintentos_expedientes`**: Segundos de espera entre reintentos de expedientes

---

## Uso

### Modo CLI

#### Verificacion inmediata

Ejecuta una verificacion unica y sale:

```bash
# Con configuracion por defecto
python scripts/monitor_cli.py --verificar-ahora

# Con logs detallados
python scripts/monitor_cli.py --verificar-ahora --verbose

# Con ventana visible (para debugging)
python scripts/monitor_cli.py --verificar-ahora --no-headless

# Combinando opciones
python scripts/monitor_cli.py --verificar-ahora --verbose --no-headless
```

#### Modo continuo (Scheduler)

Ejecuta el monitor de forma continua con verificaciones periodicas:

```bash
# Con configuracion por defecto
python scripts/monitor_cli.py

# Forzando modo laboral
python scripts/monitor_cli.py --modo laboral

# Con configuracion personalizada
python scripts/monitor_cli.py --config mi_config.json
```

#### Opciones del CLI

```
--config PATH         Ruta al archivo de configuracion (default: config/monitor.json)
--verificar-ahora     Ejecuta una verificacion inmediata y sale
--modo MODE           Sobrescribe el modo (automatico/laboral/no_laboral)
--headless            Ejecuta browser en modo headless (default)
--no-headless         Ejecuta browser con interfaz visible
--verbose             Log detallado (DEBUG level)
--quiet               Solo errores (ERROR level)
```

### Modo Programatico

#### Ejemplo basico

```python
import asyncio
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

async def main():
    # Cargar configuracion
    config = MonitorConfig.from_file("config/monitor.json")

    # Crear monitor
    monitor = MonitorPJN(config)

    # Verificar entradas
    nuevas_entradas = await monitor.verificar_entradas()
    print(f"Detectadas {len(nuevas_entradas)} nuevas entradas")

    # Verificar expedientes
    cambios = await monitor.verificar_expedientes()
    print(f"Detectados {len(cambios)} expedientes con cambios")

if __name__ == "__main__":
    asyncio.run(main())
```

#### Ejemplo con scheduler

```python
import asyncio
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor

async def main():
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)
    scheduler = SchedulerMonitor(monitor, config)

    # Iniciar scheduler
    scheduler.iniciar()
    print("Monitor iniciado. Presiona Ctrl+C para detener.")

    # Mantener ejecutando
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.detener()
        print("Monitor detenido.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Arquitectura

### Estructura de modulos

```
pjn/
├── monitor/
│   ├── __init__.py
│   ├── config.py          # Configuracion del monitor
│   ├── core.py            # Motor principal (MonitorPJN)
│   ├── detector.py        # Deteccion de cambios
│   ├── notifier.py        # Sistema de notificaciones
│   ├── scheduler.py       # Scheduler inteligente
│   └── storage.py         # Persistencia y estado
├── scraping/
│   ├── entradas.py        # Extractor de entradas
│   └── expedientes.py     # Extractor de expedientes
├── models.py              # Modelos de datos (Entrada, ExpedienteResumen)
└── utils/
    └── logging.py         # Configuracion de logging
```

### Componentes principales

#### MonitorPJN (core.py)

Motor principal que coordina las verificaciones:

- `verificar_entradas()`: Verifica nuevas entradas/notificaciones
- `verificar_expedientes()`: Verifica cambios en expedientes
- `detener()`: Detiene el monitor

#### DetectorCambios (detector.py)

Compara estados y detecta cambios:

- `detectar_nuevas_entradas()`: Identifica entradas no vistas anteriormente
- `detectar_cambios_expedientes()`: Identifica expedientes con cambios en ultima_actuacion

#### StorageManager (storage.py)

Gestiona persistencia en disco:

- `guardar_entradas()` / `cargar_entradas_conocidas()`
- `guardar_expedientes()` / `cargar_expedientes_conocidos()`
- `guardar_estado()` / `cargar_estado()`

#### SchedulerMonitor (scheduler.py)

Scheduler inteligente con APScheduler:

- Deteccion automatica de horario laboral
- Ajuste dinamico de intervalos
- Manejo de errores con reintentos

#### NotificadorPlyer (notifier.py)

Sistema de notificaciones desktop:

- Notificaciones mediante plyer
- Soporte multiplataforma
- Configuracion granular

### Flujo de verificacion

```
1. MonitorPJN.verificar_entradas()
   ├─> Autentica sesion (reutiliza si existe)
   ├─> Extrae entradas actuales del portal
   ├─> Carga entradas conocidas desde disco
   ├─> DetectorCambios.detectar_nuevas_entradas()
   ├─> Guarda entradas actualizadas
   ├─> Envia notificacion si hay nuevas
   └─> Actualiza estado

2. MonitorPJN.verificar_expedientes()
   ├─> Autentica sesion
   ├─> Extrae expedientes actuales del portal
   ├─> Carga expedientes conocidos desde disco
   ├─> DetectorCambios.detectar_cambios_expedientes()
   ├─> Guarda expedientes actualizados
   ├─> Envia notificacion si hay cambios
   └─> Actualiza estado
```

### Persistencia

#### Estructura de directorios

```
data/monitor/
├── entradas_conocidas.json    # Historial de entradas
├── expedientes_conocidos.json # Historial de expedientes
└── estado.json                # Estado del monitor
```

#### Formato de estado.json

```json
{
  "ultima_verificacion_entradas": "2025-10-16T05:09:37.123456",
  "ultima_verificacion_expedientes": null,
  "errores_consecutivos_entradas": 0,
  "errores_consecutivos_expedientes": 1
}
```

---

## Troubleshooting

### Problema: Error de autenticacion

**Sintoma:** `ExtraccionError: Contenedor o filas no visibles`

**Solucion:**
1. Verificar credenciales en `.env`
2. Eliminar sesion guardada: `rm pjn/scraping/pjn_storage_state.json`
3. Ejecutar con `--no-headless` para ver que esta pasando

### Problema: Error 404 en expedientes

**Sintoma:** `Locator.wait_for: Timeout 25000ms exceeded`

**Solucion:**
1. Deshabilitar verificacion de expedientes temporalmente:
   ```json
   "verificar_expedientes": false
   ```
2. Verificar que la URL de consultas este correcta
3. Revisar si el portal cambio su estructura

### Problema: No detecta nuevas entradas

**Sintoma:** Siempre muestra "Sin nuevas entradas"

**Solucion:**
1. Verificar filtros de fecha en configuracion
2. Eliminar historial: `rm data/monitor/entradas_conocidas.json`
3. Ejecutar con `--verbose` para ver entradas capturadas

### Problema: Notificaciones no funcionan

**Sintoma:** No aparecen notificaciones desktop

**Solucion:**
1. Verificar que plyer este instalado: `pip install plyer`
2. En Windows: verificar que las notificaciones esten habilitadas en Configuracion
3. Ejecutar test manual:
   ```python
   from plyer import notification
   notification.notify(title="Test", message="Funciona")
   ```

### Problema: Scroll infinito en entradas

**Sintoma:** El extractor no para de hacer scroll

**Solucion:**
1. Verificar fecha_desde en configuracion
2. El corte temprano se activa despues de 10 filas consecutivas antiguas
3. Ajustar max_iter si es necesario en el codigo

### Logs para debugging

Habilitar logs detallados:

```bash
python scripts/monitor_cli.py --verificar-ahora --verbose
```

Esto mostrara:
- Cada entrada capturada con su fecha
- Entradas filtradas por ser antiguas
- Contador de filas consecutivas antiguas
- Momento del corte temprano

---

## Proximas mejoras (Roadmap)

- [ ] Interfaz web con Flask/FastAPI
- [ ] Exportacion de reportes (PDF, Excel)
- [ ] Dashboard de estadisticas
- [ ] Soporte para multiples cuentas
- [ ] Notificaciones por email/Telegram
- [ ] API REST para integracion externa
- [ ] Tests unitarios completos
- [ ] Docker container

---

## Licencia

[Agregar licencia aqui]

## Contacto

[Agregar informacion de contacto]
