# Monitor PJN - Guía de Instalación Multiplataforma

**Versión:** 5.6
**Fecha:** 2025-10-17
**Soporta:** Windows, macOS, Linux

---

## 🎯 Introducción

El Monitor PJN con System Tray funciona en **Windows, macOS y Linux**. Esta guía te ayudará a instalarlo en cualquier sistema operativo.

---

## 🪟 Instalación en Windows

### Requisitos
- Windows 10 o superior
- Python 3.11+ instalado
- pip actualizado

### Paso 1: Clonar o descargar el proyecto

```powershell
cd C:\Users\TuUsuario\Projects
git clone <url-del-repo>
cd sintaXis/Sistema_v5
```

### Paso 2: Crear entorno virtual

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Paso 3: Instalar dependencias

```powershell
pip install playwright apscheduler python-dotenv
pip install pystray pillow
playwright install chromium
```

### Paso 4: Configurar credenciales

Crear archivo `.env` en la raíz del proyecto:

```
PJN_USER=tu_usuario_pjn
PJN_PASSWORD=tu_contraseña_pjn
```

### Paso 5: Configurar monitor

Editar `config/monitor.json`:

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true
}
```

### Paso 6: Ejecutar

```powershell
python -m Sistema_v5.ejecutar_monitor_tray
```

**Resultado:**
- Icono aparece en la **bandeja del sistema** (system tray, esquina inferior derecha)
- Click derecho para ver el menú

### Ejecutar al inicio (Windows)

1. Crear acceso directo de `ejecutar_monitor_tray.py`
2. Presionar `Win + R` → `shell:startup`
3. Copiar el acceso directo en esa carpeta apuntando a `python -m Sistema_v5.ejecutar_monitor_tray`

---

## 🍎 Instalación en macOS

### Requisitos
- macOS 11 (Big Sur) o superior
- Python 3.11+ instalado (recomendado: framework version)
- pip actualizado

### Paso 1: Clonar proyecto

```bash
cd ~/Projects
git clone <url-del-repo>
cd sintaXis/Sistema_v5
```

### Paso 2: Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar dependencias

```bash
pip install playwright apscheduler python-dotenv
pip install rumps
playwright install chromium
```

**Nota:** En macOS usamos `rumps` en lugar de `pystray` para mejor compatibilidad.

### Paso 4: Configurar credenciales

Crear archivo `.env` en la raíz:

```bash
touch .env
nano .env
```

Contenido:
```
PJN_USER=tu_usuario_pjn
PJN_PASSWORD=tu_contraseña_pjn
```

### Paso 5: Configurar monitor

Editar `config/monitor.json`:

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true
}
```

### Paso 6: Ejecutar

```bash
python -m Sistema_v5.ejecutar_monitor_statusbar
```

**Resultado:**
- Icono 🟢 aparece en el **menu bar** (barra superior derecha)
- Click en el icono para ver el menú

### Ejecutar al inicio (macOS)

**Opción 1: Login Items**
1. Abrir **Preferencias del Sistema** → **Usuarios y Grupos**
2. Seleccionar tu usuario → **Login Items**
3. Click en **+** → Agregar el script
4. Marcar "Hide" para que no abra terminal

**Opción 2: LaunchAgent** (Recomendado)

Crear archivo `~/Library/LaunchAgents/com.monitor.pjn.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.monitor.pjn</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/TuUsuario/Projects/sintaXis/Sistema_v5/.venv/bin/python</string>
        <string>-m</string>
        <string>Sistema_v5.ejecutar_monitor_statusbar</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/monitor_pjn.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/monitor_pjn_error.log</string>
</dict>
</plist>
```

Cargar el agente:
```bash
launchctl load ~/Library/LaunchAgents/com.monitor.pjn.plist
```

---

## 🐧 Instalación en Linux

### Requisitos
- Ubuntu 20.04+ / Debian 11+ / Fedora 35+ / Arch Linux
- Python 3.11+ instalado
- pip actualizado
- Entorno de escritorio con soporte de system tray (GNOME, KDE, XFCE, etc.)

### Paso 1: Instalar dependencias del sistema

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-pip python3-venv
sudo apt install python3-tk  # Para pystray
```

**Fedora:**
```bash
sudo dnf install python3-pip python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S python-pip tk
```

### Paso 2: Clonar proyecto

```bash
cd ~/Projects
git clone <url-del-repo>
cd sintaXis/Sistema_v5
```

### Paso 3: Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 4: Instalar dependencias Python

```bash
pip install playwright apscheduler python-dotenv
pip install pystray pillow
playwright install chromium
playwright install-deps chromium  # Dependencias del sistema
```

### Paso 5: Configurar credenciales

```bash
touch .env
nano .env
```

Contenido:
```
PJN_USER=tu_usuario_pjn
PJN_PASSWORD=tu_contraseña_pjn
```

### Paso 6: Configurar monitor

Editar `config/monitor.json`:

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true
}
```

### Paso 7: Ejecutar

```bash
python -m Sistema_v5.ejecutar_monitor_tray
```

**Resultado:**
- Icono aparece en el **system tray** (ubicación depende del DE)
- Click derecho para ver el menú

### Notas por Desktop Environment

**GNOME:**
- Requiere extensión "AppIndicator Support"
- Instalar desde: https://extensions.gnome.org/extension/615/appindicator-support/

**KDE Plasma:**
- Soporte nativo de system tray
- Sin configuración adicional

**XFCE:**
- Soporte nativo
- Verificar que "Notification Area" esté habilitado en el panel

### Ejecutar al inicio (Linux)

**Systemd User Service** (Recomendado)

Crear `~/.config/systemd/user/monitor-pjn.service`:

```ini
[Unit]
Description=Monitor PJN - Sistema de monitoreo
After=network.target

[Service]
Type=simple
ExecStart=/home/tuusuario/Projects/sintaXis/Sistema_v5/.venv/bin/python -m Sistema_v5.ejecutar_monitor_tray
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=default.target
```

Habilitar y arrancar:
```bash
systemctl --user enable monitor-pjn
systemctl --user start monitor-pjn
```

---

## 🌐 Script Universal (Todas las plataformas)

Para no preocuparte por el sistema operativo, usa el **script universal**:

```bash
python -m Sistema_v5.ejecutar_monitor_universal
```

Este script:
- ✅ Detecta automáticamente tu OS
- ✅ Usa la implementación correcta (rumps en macOS, pystray en otros)
- ✅ Muestra mensajes de error claros si faltan dependencias

---

## 🔧 Troubleshooting por Plataforma

### Windows

**Problema:** Icono no aparece
- **Solución:** Verificar que las notificaciones de bandeja estén habilitadas
- Configuración → Sistema → Notificaciones → Seleccionar qué iconos aparecen

**Problema:** Error al importar pystray
- **Solución:** Reinstalar dependencias
  ```powershell
  pip uninstall pystray pillow
  pip install pystray pillow
  ```

### macOS

**Problema:** Icono no aparece
- **Solución:** Verificar permisos de accesibilidad
- Preferencias del Sistema → Privacidad → Accesibilidad → Agregar Terminal/Python

**Problema:** Error "no module named rumps"
- **Solución:** Instalar rumps
  ```bash
  pip install rumps
  ```

**Problema:** Icono desaparece al cerrar terminal
- **Solución:** Ejecutar con nohup o crear LaunchAgent (ver arriba)

### Linux

**Problema:** Icono no visible (GNOME)
- **Solución:** Instalar extensión AppIndicator Support
- https://extensions.gnome.org/extension/615/appindicator-support/

**Problema:** Error de dependencias de Playwright
- **Solución:** Instalar dependencias del sistema
  ```bash
  playwright install-deps chromium
  ```

**Problema:** Permission denied al ejecutar
- **Solución:** Dar permisos de ejecución
  ```bash
  chmod +x ejecutar_monitor_tray.py
  ```

---

## 📊 Resumen de Dependencias

| Componente | Windows | macOS | Linux |
|------------|---------|-------|-------|
| Python | 3.11+ | 3.11+ | 3.11+ |
| playwright | ✅ | ✅ | ✅ |
| apscheduler | ✅ | ✅ | ✅ |
| python-dotenv | ✅ | ✅ | ✅ |
| **System Tray** | pystray + pillow | **rumps** | pystray + pillow |
| Chromium | ✅ | ✅ | ✅ + deps |

---

## 🎯 Próximos Pasos

Después de instalar:

1. **Configurar intervalos** en `config/monitor.json`
2. **Probar verificación manual** desde el menú
3. **Verificar archivos generados** en `data/monitor/`
4. **Configurar inicio automático** (opcional)
5. **Cambiar a headless=true** para producción

---

**Última actualización:** 2025-10-17
