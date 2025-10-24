# Aplicación Web del Monitor PJN

Interfaz web Flask para gestionar y visualizar el monitoreo de expedientes y entradas del PJN.

## 🚀 Inicio Rápido

### Ejecución Simple (Recomendado)

```bash
# Desde el directorio raíz del proyecto
cd /Users/davidalejandroliva/PycharmProjects/sintaXis

# Linux/macOS
python3 Sistema_v5/web_app/run_app.py

# Windows
python Sistema_v5\web_app\run_app.py
```

Luego abre en tu navegador: **http://localhost:8080**

> **Nota**: El puerto 8080 se usa por defecto para evitar conflictos con AirPlay Receiver en macOS (que usa el puerto 5000).

---

## 📋 Características

- 📊 **Dashboard** con estadísticas en tiempo real
- 📋 **Visualización** de entradas y expedientes
- ⚙️ **Configuración interactiva** del monitor
- 🔄 **Control** de inicio/detención del monitor
- 📈 **API REST** para métricas
- 📝 **Visualización de logs**

---

## 🔧 Configuración

### Variables de Entorno

Puedes personalizar la ejecución con variables de entorno:

| Variable | Descripción | Default |
|----------|-------------|---------|
| `FLASK_PORT` | Puerto del servidor web | `8080` |
| `FLASK_HOST` | Host del servidor | `127.0.0.1` |
| `FLASK_DEBUG` | Modo debug (true/false) | `true` |

### Ejemplos de Uso

```bash
# Cambiar puerto
FLASK_PORT=9000 python3 Sistema_v5/web_app/run_app.py

# Modo producción (sin debug)
FLASK_DEBUG=false python3 Sistema_v5/web_app/run_app.py

# Accesible desde red local
FLASK_HOST=0.0.0.0 python3 Sistema_v5/web_app/run_app.py

# Combinación (Windows - PowerShell)
$env:FLASK_PORT=9000; python Sistema_v5\web_app\run_app.py

# Combinación (Windows - CMD)
set FLASK_PORT=9000 && python Sistema_v5\web_app\run_app.py
```

---

## 🌐 Rutas Disponibles

### Páginas Web

| Ruta | Descripción |
|------|-------------|
| `/` | Redirige al dashboard |
| `/dashboard` | Dashboard principal con estadísticas |
| `/entradas` | Listado completo de entradas |
| `/expedientes` | Listado completo de expedientes |
| `/config` | Configuración del monitor |
| `/logs` | Visualización de logs |

### API REST

#### Estadísticas y Métricas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/stats` | Estadísticas actuales |
| GET | `/api/metrics` | Métricas resumidas (últimas 24h) |
| GET | `/api/activity` | Actividad reciente del monitor |

#### Control del Monitor

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/monitor/status` | Estado actual del monitor |
| POST | `/api/monitor/start` | Iniciar el monitor con icono en bandeja |
| POST | `/api/monitor/stop` | Detener el monitor |
| POST | `/api/monitor/verify/entradas` | Verificación manual de entradas |
| POST | `/api/monitor/verify/expedientes` | Verificación manual de expedientes |

> **💡 Importante**: Cuando inicias el monitor desde la app web, se ejecuta `ejecutar_monitor_universal.py` que muestra un **icono en la bandeja del sistema** (macOS: barra superior, Windows/Linux: system tray). Puedes hacer click derecho en el icono para ver opciones adicionales.

#### Configuración

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/config/update` | Actualizar configuración |
| GET | `/config/download` | Descargar archivo de configuración |
| POST | `/config/upload` | Cargar archivo de configuración |

---

## 🛠️ Solución de Problemas

### Puerto en Uso

**Error**: `Address already in use`

**Soluciones**:

1. **Usar otro puerto** (recomendado):
   ```bash
   FLASK_PORT=9000 python3 Sistema_v5/web_app/run_app.py
   ```

2. **Identificar y detener el proceso**:
   ```bash
   # Linux/macOS
   lsof -i :8080              # Ver qué usa el puerto
   kill -9 $(lsof -ti :8080)  # Detener proceso

   # Windows
   netstat -ano | findstr :8080      # Ver qué usa el puerto
   taskkill /PID [numero] /F         # Detener proceso
   ```

3. **En macOS (puerto 5000)**: Desactiva AirPlay Receiver
   - Ajustes del Sistema → General → AirDrop & Handoff → Desactivar "AirPlay Receiver"

### Error de Importación

**Error**: `No module named 'pjn'` o `ImportError`

**Soluciones**:

1. **Verifica el directorio de ejecución**:
   ```bash
   # Debe ejecutarse desde la raíz del proyecto
   cd /Users/davidalejandroliva/PycharmProjects/sintaXis
   python3 Sistema_v5/web_app/run_app.py
   ```

2. **Verifica el entorno virtual**:
   ```bash
   # Verifica que estás usando el Python correcto
   which python3

   # Debe apuntar a: /Users/davidalejandroliva/PycharmProjects/sintaXis/.venv1/bin/python3
   ```

### No Aparecen Datos

**Problema**: La aplicación carga pero no muestra entradas ni expedientes.

**Soluciones**:

1. **Verifica que existen los archivos de datos**:
   ```bash
   ls -la Sistema_v5/data/
   ```

2. **Ejecuta el monitor al menos una vez** para generar datos:
   ```bash
   python3 Sistema_v5/ejecutar_monitor_continuo.py
   ```

3. **Verifica el archivo de configuración**:
   ```bash
   cat Sistema_v5/config/monitor.json
   ```

### Error de Configuración

**Error**: `ConfigurationError` al iniciar

**Soluciones**:

1. **Verifica que existe el archivo de configuración**:
   ```bash
   ls Sistema_v5/config/monitor.json
   ```

2. **Si no existe, créalo con la configuración por defecto**:
   - Ejecuta el monitor una vez o
   - Copia el archivo de ejemplo si existe

---

## 🏗️ Arquitectura

```
web_app/
├── app.py              # Aplicación Flask principal (lógica completa)
├── run_app.py          # Script de inicio conveniente (wrapper)
├── README.md           # Esta documentación
├── templates/          # Plantillas HTML Jinja2
│   ├── dashboard.html      # Vista del dashboard
│   ├── entradas.html       # Listado de entradas
│   ├── expedientes.html    # Listado de expedientes
│   ├── config.html         # Configuración del monitor
│   ├── logs.html           # Visualización de logs
│   └── error.html          # Página de error
└── static/             # Archivos estáticos (CSS, JS, imágenes)
    └── (actualmente vacío - estilos inline)
```

### Diferencia entre `app.py` y `run_app.py`

- **`app.py`**: Aplicación Flask completa con toda la lógica (1067 líneas)
  - Todas las rutas web y API
  - Manejo de errores
  - Control del monitor
  - **Necesario** - es el core de la aplicación

- **`run_app.py`**: Script auxiliar para ejecutar fácilmente (118 líneas)
  - Configura puerto 8080 por defecto
  - Muestra información útil al iniciar
  - Manejo de errores mejorado
  - **Opcional** - es un wrapper conveniente

Puedes usar cualquiera de los dos:

```bash
# Opción 1: Usar run_app.py (más fácil, recomendado)
python3 Sistema_v5/web_app/run_app.py

# Opción 2: Usar app.py directamente (más control)
export FLASK_PORT=8080
python3 Sistema_v5/web_app/app.py
```

---

## 🔒 Seguridad

⚠️ **Importante**: Esta aplicación está diseñada para **uso local/interno**.

Para producción, considera:

- Cambiar `FLASK_HOST` a `127.0.0.1` (solo localhost)
- Desactivar modo debug: `FLASK_DEBUG=false`
- Implementar autenticación/autorización
- Usar un servidor WSGI (gunicorn, uWSGI, waitress)
- Configurar HTTPS con certificados SSL
- Usar un proxy reverso (nginx, Apache)

### Ejemplo de Producción con Waitress (multiplataforma)

```bash
# Instalar waitress
pip install waitress

# Ejecutar con waitress
python -c "from waitress import serve; from Sistema_v5.web_app.app import app; serve(app, host='127.0.0.1', port=8080)"
```

---

## 📝 Logs y Datos

### Ubicación de Archivos

```
Sistema_v5/
├── config/
│   └── monitor.json                    # Configuración del monitor
├── data/
│   ├── estado_monitor.json             # Estado actual
│   ├── historial_entradas.json         # Entradas conocidas
│   └── historial_expedientes.json      # Expedientes conocidos
└── logs/
    ├── monitor.log                     # Log general del monitor
    ├── monitor_runtime.json            # Info del proceso en ejecución
    └── monitor_web_actions.log         # Acciones desde la web
```

### Ver Logs en Tiempo Real

```bash
# Linux/macOS
tail -f Sistema_v5/logs/monitor.log

# Windows (PowerShell)
Get-Content Sistema_v5\logs\monitor.log -Wait -Tail 50
```

---

## 💻 Compatibilidad

✅ **Windows**: Completamente compatible
✅ **macOS**: Completamente compatible
✅ **Linux**: Completamente compatible

**Requisitos**:
- Python 3.8+
- Flask (instalado con el proyecto)
- Dependencias del proyecto sintaXis

---

## 🤝 Desarrollo

### Estructura del Código

El archivo `app.py` está organizado en secciones:

1. **Configuración** (líneas 1-75)
   - Imports
   - Configuración de rutas
   - Variables globales

2. **Utilidades** (líneas 76-290)
   - Funciones de configuración
   - Gestión de estado
   - Helpers de ejecución

3. **Rutas Web** (líneas 386-674)
   - Páginas HTML

4. **API REST** (líneas 677-776)
   - Endpoints JSON

5. **Control del Monitor** (líneas 779-1057)
   - Inicio/detención
   - Verificaciones manuales

### Ejecutar en Modo Debug

```bash
# El modo debug ya está activo por defecto en run_app.py
python3 Sistema_v5/web_app/run_app.py

# Cambios en el código se recargan automáticamente
# Ver errores detallados en el navegador
```

---

## 📚 Recursos Adicionales

- **Documentación Flask**: https://flask.palletsprojects.com/
- **Sistema Monitor PJN**: Ver `Sistema_v5/README.md` (si existe)
- **Configuración**: Ver `Sistema_v5/config/monitor.json.example` (si existe)

---

## ❓ Preguntas Frecuentes

### ¿Por qué puerto 8080 y no 5000?

El puerto 5000 está ocupado por AirPlay Receiver en macOS por defecto. El puerto 8080 es una alternativa común y evita este conflicto.

### ¿Puedo acceder desde otro dispositivo en mi red?

Sí, configura `FLASK_HOST=0.0.0.0`:

```bash
FLASK_HOST=0.0.0.0 python3 Sistema_v5/web_app/run_app.py
```

Luego accede desde otro dispositivo usando: `http://[IP-de-tu-computadora]:8080`

### ¿Cómo desactivo el modo debug?

```bash
FLASK_DEBUG=false python3 Sistema_v5/web_app/run_app.py
```

### ¿Funciona sin conexión a internet?

Sí, la aplicación es completamente local y no requiere internet (excepto para acceder al portal PJN para monitorear).

---

**Autor**: Sistema de monitoreo PJN - Sistema_v5