# Sistema de Monitoreo PJN - Sistema v5

Sistema completo de web scraping y monitoreo para el Portal Judicial Nacional (PJN) de Argentina.

## 📂 Estructura del Proyecto

```
sintaXis/
├── Sistema_v5/              # Sistema principal (ÚNICA VERSIÓN ACTIVA)
│   ├── pjn/                 # Módulo principal de scraping
│   ├── configuracion/       # Sistema de configuración unificado
│   ├── extractor_inicial/   # Extracción inicial por lotes
│   ├── web_app/             # Aplicación web Flask
│   ├── tests/               # Tests unitarios e integración
│   ├── docs/                # Documentación completa
│   └── config/              # Archivos de configuración
├── .env.example             # Plantilla de variables de entorno
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Este archivo
```

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd sintaXis
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configurar credenciales

```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con tus credenciales
# PJN_USER=tu_usuario
# PJN_PASSWORD=tu_contraseña
```

### 5. Inicializar directorios

```bash
cd Sistema_v5
python inicializar_directorios.py
```

## 📖 Documentación Completa

Toda la documentación está en `Sistema_v5/docs/`:

- **[README.md](Sistema_v5/README.md)** - Guía completa del sistema
- **[CONFIGURADOR.md](Sistema_v5/CONFIGURADOR.md)** - Sistema de configuración
- **[docs/INVENTARIO_FUNCIONES.md](Sistema_v5/docs/INVENTARIO_FUNCIONES.md)** - Inventario completo de funciones
- **[docs/MONITOR.md](Sistema_v5/docs/MONITOR.md)** - Sistema de monitoreo

## 🎯 Uso Rápido

### Configuración Interactiva

```bash
cd Sistema_v5
python -m cli.configuracion wizard
```

### Ejecutar Monitor

```bash
# Monitor con interfaz de bandeja
python ejecutar_monitor_universal.py

# Dashboard web
python web_app/run_app.py
# Abrir: http://localhost:8080
```

### Extracción Inicial

```bash
python ejecutar_extraccion_inicial_v2.py
```

## 🔧 Configuración

El sistema usa archivos de configuración centralizados:

- `Sistema_v5/config/sistema.json` - Configuración principal
- `Sistema_v5/config/monitor.json` - Configuración del monitor (legacy)

Ver [CONFIGURADOR.md](Sistema_v5/CONFIGURADOR.md) para detalles completos.

## 🧪 Tests

```bash
cd Sistema_v5
pytest tests/
```

## 📊 Características Principales

- ✅ **Scraping Completo** - Expedientes, actuaciones y entradas
- ✅ **Monitoreo 24/7** - Detección de cambios automática
- ✅ **Circuit Breaker** - Resiliencia ante fallos
- ✅ **Web Dashboard** - Control desde navegador
- ✅ **System Tray** - Control desde bandeja del sistema
- ✅ **Configuración Unificada** - 50+ parámetros configurables
- ✅ **Multi-plataforma** - Windows, Linux, macOS

## 🔒 Seguridad

- ❌ **NO** commitear archivos `.env`
- ❌ **NO** commitear datos de expedientes (`.csv`, `.json`)
- ✅ **SÍ** usar variables de entorno para credenciales
- ✅ **SÍ** revisar `.gitignore` antes de commit

## 🤝 Contribuir

1. Crear rama desde `produccion_v3`
2. Hacer cambios y tests
3. Commit con mensajes descriptivos
4. Pull request a `produccion_v3`

## 📝 Versiones

- **v5.x** - Sistema actual (producción)
- **v4.x** - Obsoleto (eliminado)
- **v3.x** - Obsoleto (eliminado)

## 📞 Soporte

Para problemas o preguntas:
1. Revisar documentación en `Sistema_v5/docs/`
2. Revisar issues existentes
3. Crear nuevo issue con detalles

---

**Última actualización:** 2025-10-24
**Versión:** 5.x
**Rama:** produccion_v3
