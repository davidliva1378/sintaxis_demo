# Monitor PJN - System Tray (Bandeja del Sistema) - Multiplataforma

**Versión:** 5.6
**Fecha:** 2025-10-17
**Soporte:** Windows, macOS, Linux

---

## 🎯 Descripción

El **System Tray** (indicador de bandeja del sistema) permite controlar el Monitor PJN desde un icono en la barra de tareas/menú sin necesidad de mantener una terminal abierta.

### Características

✅ **Multiplataforma** - Windows, macOS y Linux
✅ **Icono en la bandeja/menu bar** - Implementaciones nativas por OS
✅ **Menú contextual** completo
✅ **Estados visuales** - Emojis de colores según actividad
✅ **Verificación manual** - Click para verificar ahora
✅ **Acceso rápido a datos** - Abrir carpeta con un click
✅ **Control completo** - Iniciar, detener, ver estado
✅ **Ejecución en segundo plano** - No requiere terminal visible
✅ **Auto-detección de OS** - Script universal que elige la mejor implementación

---

## 🚀 Inicio Rápido

### Opción 1: Script Universal (Recomendado)

El script universal detecta automáticamente tu sistema operativo:

```bash
python ejecutar_monitor_universal.py
```

Instalará las dependencias correctas según tu OS.

### Opción 2: Por Sistema Operativo

#### Windows
```bash
pip install pystray pillow
python ejecutar_monitor_tray.py
```

#### macOS
```bash
pip install rumps
python ejecutar_monitor_statusbar.py
```

#### Linux
```bash
pip install pystray pillow
python ejecutar_monitor_tray.py
```

### 3. Usar el Icono

**Windows/Linux:**
- **Click derecho** en el icono de la bandeja → Ver menú

**macOS:**
- **Click** en el icono 🟢 del menu bar → Ver menú

**Menú disponible:**
- **Verificar ahora** → Ejecuta verificación inmediata
- **Estado** → Ver última verificación y errores
- **Abrir carpeta de datos** → Ver archivos guardados
- **Salir** → Detener monitor

---

## 🎨 Estados del Icono

El icono cambia de color según el estado del monitor:

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Monitor activo, sin cambios |
| 🟡 Amarillo | Verificando o cambios detectados |
| 🔴 Rojo | Error durante verificación |
| ⚪ Gris | Monitor inactivo |

**Comportamiento:**
- El icono cambia a **amarillo** durante verificaciones
- Si detecta nuevas entradas/expedientes, permanece **amarillo** 3 segundos
- Si hay error, cambia a **rojo** 3 segundos
- Luego vuelve a **verde** automáticamente

---

## 📋 Menú Contextual

### Opciones Disponibles

```
┌─────────────────────────────┐
│ Monitor PJN                 │  ← Título (no clickeable)
├─────────────────────────────┤
│ Verificar ahora             │  ← Ejecuta verificación inmediata
│ Estado                      │  ← Muestra estado del monitor
├─────────────────────────────┤
│ Iniciar / Detener           │  ← Control del scheduler (si existe)
├─────────────────────────────┤
│ Abrir carpeta de datos      │  ← Abre explorador de archivos
│ Ver logs                    │  ← (TODO) Visualizador de logs
├─────────────────────────────┤
│ Salir                       │  ← Detener monitor y cerrar
└─────────────────────────────┘
```

### Detalle de Opciones

#### 🔄 Verificar ahora

Ejecuta una verificación inmediata de:
- Entradas (si está habilitado)
- Expedientes (si está habilitado)

**Feedback visual:**
- Icono cambia a amarillo durante verificación
- Notificación del sistema si hay cambios
- Vuelve a verde al finalizar

#### 📊 Estado

Muestra información del monitor:
- Estado running (activo/inactivo)
- Última verificación de entradas
- Última verificación de expedientes
- Errores consecutivos

**Output:**
```
=== Estado del Monitor PJN ===
Running: True
Última verificación entradas: 2025-10-17T14:30:00
Última verificación expedientes: 2025-10-17T14:25:00
Errores consecutivos (entradas): 0
Errores consecutivos (expedientes): 0
```

#### 🚦 Iniciar / Detener

Control del scheduler (solo si se pasó scheduler al crear el tray):
- **Iniciar:** Activa verificaciones periódicas
- **Detener:** Pausa verificaciones periódicas

**Nota:** Actualmente en desarrollo.

#### 📁 Abrir carpeta de datos

Abre el explorador de archivos en la carpeta de datos del monitor:
- **Windows:** Abre Explorer
- **macOS:** Abre Finder
- **Linux:** Abre gestor de archivos predeterminado

**Carpeta por defecto:** `data/monitor/`

Contiene:
- `estado_monitor.json` - Estado del monitor
- `historial_entradas.json` - Entradas conocidas
- `historial_expedientes.json` - Expedientes conocidos

#### 📝 Ver logs

**Estado:** 🚧 En desarrollo

Abrirá un visualizador de logs en tiempo real.

#### ❌ Salir

Detiene el monitor y cierra la aplicación:
1. Detiene el scheduler (si existe)
2. Marca el monitor como no running
3. Cierra el icono de bandeja
4. Sale de la aplicación

---

## 💻 Uso Programático

### Ejemplo Básico

```python
import asyncio
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN
from pjn.monitor.scheduler import SchedulerMonitor
from pjn.monitor.tray import MonitorSystemTray

async def main():
    # Configuración
    config = MonitorConfig(
        modo="automatico",
        headless=True,  # Recomendado con tray
        verificar_entradas=True,
        verificar_expedientes=True
    )

    # Monitor y scheduler
    monitor = MonitorPJN(config)
    monitor.running = True
    scheduler = SchedulerMonitor(monitor)

    # System tray
    tray = MonitorSystemTray(monitor, scheduler)

    # Event loop
    loop = asyncio.get_event_loop()

    # Verificación inicial
    if config.verificar_entradas:
        await monitor.verificar_entradas()

    if config.verificar_expedientes:
        await monitor.verificar_expedientes()

    # Iniciar scheduler
    scheduler.iniciar()

    # Iniciar tray en thread separado
    tray.run_detached(loop)

    # Mantener corriendo
    while monitor.running and tray._running:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Ejemplo: Solo Tray (Sin Scheduler)

```python
# Solo con verificación manual
tray = MonitorSystemTray(monitor, scheduler=None)
tray.run_detached(loop)
```

### Ejemplo: Cambiar Color del Icono

```python
# Verde (OK)
tray.update_icon("green")

# Amarillo (actividad)
tray.update_icon("yellow")

# Rojo (error)
tray.update_icon("red")

# Gris (inactivo)
tray.update_icon("gray")
```

---

## 🛠️ Configuración

### Variables de Entorno

El system tray usa la configuración del monitor:

```bash
# .env
MONITOR_MODO=automatico
MONITOR_HEADLESS=true
MONITOR_NOTIF_ENTRADAS=true
```

### Archivo de Configuración

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true,
  "directorio_datos": "data/monitor"
}
```

**Recomendaciones para tray:**
- `headless: true` - No abrir ventana del navegador
- `notificar_nuevas_entradas: true` - Notificaciones desktop
- `notificar_cambios_expedientes: true` - Notificaciones desktop

---

## 🐛 Troubleshooting

### El icono no aparece

**Problema:** pystray o pillow no instalados

**Solución:**
```bash
pip install pystray pillow
```

**Verificar instalación:**
```python
from pjn.monitor.tray import TRAY_AVAILABLE
print(TRAY_AVAILABLE)  # Debe ser True
```

### El icono aparece pero no responde

**Problema:** Event loop bloqueado

**Solución:** Asegurar que el tray se ejecuta en thread separado:
```python
tray.run_detached(loop)  # NO usar tray.run()
```

### Verificación manual no funciona

**Problema:** Event loop no disponible

**Solución:** Pasar el loop al crear el tray:
```python
loop = asyncio.get_event_loop()
tray = MonitorSystemTray(monitor, scheduler)
tray.run_detached(loop)  # Pasa el loop automáticamente
```

### El icono desaparece al cerrar terminal

**Problema:** Script está en foreground

**Solución 1:** Mantener el script corriendo:
```python
while monitor.running and tray._running:
    await asyncio.sleep(1)
```

**Solución 2 (Linux/macOS):** Ejecutar en background:
```bash
nohup python ejecutar_monitor_tray.py &
```

**Solución 3 (Windows):** Crear tarea programada o usar pythonw.exe:
```bash
pythonw ejecutar_monitor_tray.py
```

### Error al abrir carpeta de datos

**Problema:** Carpeta no existe o permisos

**Solución:**
```bash
# Crear carpeta manualmente
mkdir -p data/monitor

# Verificar permisos
ls -la data/monitor
```

---

## 🔧 API Técnica

### Clase `MonitorSystemTray`

```python
class MonitorSystemTray:
    """Indicador de bandeja del sistema para el monitor PJN."""

    def __init__(
        self,
        monitor: MonitorPJN,
        scheduler: SchedulerMonitor | None = None
    ):
        """Inicializa el indicador de bandeja."""

    def run(self, event_loop: asyncio.AbstractEventLoop | None = None):
        """Inicia el indicador (bloqueante)."""

    def run_detached(self, event_loop: asyncio.AbstractEventLoop):
        """Inicia el indicador en thread separado (no bloqueante)."""

    def stop(self):
        """Detiene el indicador y el monitor."""

    def update_icon(self, color: str = "green"):
        """Actualiza el color del icono.

        Args:
            color: "green", "yellow", "red", "gray"
        """
```

### Función `create_icon_image`

```python
def create_icon_image(color: str = "green", size: int = 64) -> Image:
    """Crea una imagen de icono simple para la bandeja.

    Args:
        color: Color del icono
        size: Tamaño en píxeles

    Returns:
        Image: Imagen PIL
    """
```

---

## 📱 Plataformas Soportadas

| Plataforma | Implementación | Librería | Estado | Notas |
|------------|----------------|----------|--------|-------|
| **Windows 10/11** | `tray.py` | pystray | ✅ Compatible | Icono en system tray |
| **macOS** | `tray_macos.py` | rumps | ✅ Testeado | Icono en menu bar (nativo) |
| **Linux (GNOME)** | `tray.py` | pystray | ✅ Compatible | Requiere extensión de tray |
| **Linux (KDE)** | `tray.py` | pystray | ✅ Compatible | Soporte nativo |
| **Linux (XFCE)** | `tray.py` | pystray | ✅ Compatible | Soporte nativo |

### ¿Por qué dos implementaciones?

**pystray (Windows/Linux):**
- ✅ Multiplataforma genérico
- ✅ Funciona en Windows y Linux
- ⚠️ Problemas en macOS (framework de Python)

**rumps (macOS):**
- ✅ Nativo de macOS (APIs de Cocoa)
- ✅ Más confiable y mejor integrado
- ✅ UX superior en macOS
- ❌ Solo funciona en macOS

**Script universal:**
- ✅ Detecta el OS automáticamente
- ✅ Usa la mejor implementación para cada plataforma
- ✅ Experiencia consistente en todos los sistemas

---

## 🎯 Próximas Mejoras

- [ ] Icono personalizado (logo PJN)
- [ ] Sub-menús para opciones avanzadas
- [ ] Notificaciones ricas (con botones)
- [ ] Estadísticas en tooltip
- [ ] Historial de verificaciones en menú
- [ ] Configuración desde menú contextual
- [ ] Logs en tiempo real (ventana separada)

---

## 📚 Referencias

- **pystray:** https://github.com/moses-palmer/pystray
- **Pillow:** https://pillow.readthedocs.io/
- **Documentación completa:** [MONITOR.md](MONITOR.md)

---

**Última actualización:** 2025-10-17
