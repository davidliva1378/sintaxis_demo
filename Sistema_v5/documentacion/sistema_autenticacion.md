# Sistema de Autenticación - Sistema_v5

**Última actualización:** 2025-10-16
**Versión:** 5.5.1

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura](#arquitectura)
3. [Flujo de Autenticación](#flujo-de-autenticación)
4. [Uso Básico](#uso-básico)
5. [Logging](#logging)
6. [Configuración](#configuración)
7. [Manejo de Errores](#manejo-de-errores)
8. [Comparación con Sistema_v3](#comparación-con-sistemav3)

---

## Descripción General

Sistema_v5 implementa un sistema robusto de **autenticación automática con persistencia de sesión** para el portal PJN. El sistema:

- ✅ Reutiliza sesiones guardadas automáticamente
- ✅ Detecta sesiones expiradas y realiza re-login transparente
- ✅ Usa selectores centralizados (`selectores.py`)
- ✅ Logging completo del proceso de autenticación
- ✅ Manejo de errores con excepciones tipadas
- ✅ Configuración centralizada desde `config.py`

**Ubicación:** `Sistema_v5/pjn/scraping/base.py`

---

## Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────┐
│  obtener_pagina_autenticada()                  │
│  Context manager principal                      │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────────┐
│ _obtener│  │ _leer_  │  │ _crear_     │
│ credenc.│  │ storage │  │ contexto()  │
└─────────┘  └─────────┘  └─────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────────┐
│ _realizar│  │ _verif. │  │ _guardar_   │
│ _login() │  │ _sesion │  │ storage...  │
└─────────┘  └─────────┘  └─────────────┘
```

### Funciones Clave

| Función | Propósito | Ubicación |
|---------|-----------|-----------|
| `obtener_pagina_autenticada()` | Context manager principal | `base.py:257` |
| `_obtener_credenciales()` | Validar PJN_USER y PJN_PASSWORD | `base.py:144` |
| `_realizar_login()` | Ejecutar login automático | `base.py:200` |
| `_verificar_sesion()` | Validar sesión activa | `base.py:236` |
| `_leer_storage_state()` | Cargar sesión guardada | `base.py:175` |
| `_guardar_storage_state()` | Persistir sesión | `base.py:185` |

---

## Flujo de Autenticación

### Diagrama de Flujo

```
┌─────────────────────────────────────────────┐
│ 1. Verificar credenciales PJN_USER/PASSWORD │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│ 2. Buscar archivo pjn_storage_state.json   │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴────────┐
         │  ¿Existe?      │
         └───────┬────────┘
          NO     │     SÍ
    ┌────────────┘     │
    │                  │
┌───▼──────────────┐   │
│ 3a. LOGIN NUEVO  │   │
│  - Lanzar browser│   │
│  - Ir a URL login│   │
│  - Fill username │   │
│  - Fill password │   │
│  - Click login   │   │
│  - Wait "Menú"   │   │
│  - Guardar sesión│   │
└───┬──────────────┘   │
    │                  │
    └────────┬─────────┘
             │
┌────────────▼──────────────────────────────┐
│ 4. Crear browser con storage_state       │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│ 5. Verificar sesión (_verificar_sesion)  │
│    - Buscar "text='Menú'" (5 segundos)   │
│    - Si no existe, buscar campo username │
└────────────┬──────────────────────────────┘
             │
      ┌──────┴───────┐
      │ ¿Sesión OK?  │
      └──────┬───────┘
        SÍ   │   NO
    ┌────────┘   │
    │            │
    │   ┌────────▼─────────────────────┐
    │   │ 6. RE-LOGIN AUTOMÁTICO       │
    │   │    - Cerrar browser          │
    │   │    - Borrar sesión expirada  │
    │   │    - Login nuevo (paso 3a)   │
    │   └────────┬─────────────────────┘
    │            │
    │   ┌────────▼─────────────────────┐
    │   │ 7. Verificar nuevamente      │
    │   │    Si falla → SesionInvalida │
    │   └────────┬─────────────────────┘
    │            │
    └────────────┘
             │
┌────────────▼──────────────────────────────┐
│ 8. Yield (page, context, browser)        │
│    Usuario trabaja con la sesión         │
└────────────┬──────────────────────────────┘
             │
┌────────────▼──────────────────────────────┐
│ 9. Cleanup automático (finally)          │
│    - Cerrar page, context, browser       │
└───────────────────────────────────────────┘
```

---

## Uso Básico

### Ejemplo Simple

```python
from pjn.scraping.base import obtener_pagina_autenticada

async def mi_script():
    # Context manager - maneja login y cleanup automático
    async with obtener_pagina_autenticada() as (page, context, browser):
        # Aquí la página YA está logueada
        await page.goto("https://portalpjn.pjn.gov.ar/consultas")

        # Hacer scraping...
        resultados = await page.query_selector_all(".resultados")

        # Al salir del 'with', se cierra todo automáticamente
```

### Con Parámetros Personalizados

```python
from pathlib import Path

async with obtener_pagina_autenticada(
    usuario="mi_usuario",              # Override de PJN_USER
    contraseña="mi_password",          # Override de PJN_PASSWORD
    session_file=Path("mi_sesion.json"), # Archivo custom
    headless=True,                     # Modo headless
) as (page, ctx, browser):
    await page.goto("https://...")
```

### Con Variables de Entorno

```bash
# .env o shell
export PJN_USER="20123456789"
export PJN_PASSWORD="mi_password_seguro"
```

```python
# Usa automáticamente las variables de entorno
async with obtener_pagina_autenticada() as (page, _, _):
    # Ya está logueado
    pass
```

---

## Logging

**Versión 5.5.1** incluye logging completo del proceso de autenticación.

### Niveles de Logging

| Nivel | Cuándo se usa | Ejemplo |
|-------|--------------|---------|
| **INFO** | Eventos importantes del flujo normal | "Login exitoso, guardando sesión" |
| **WARNING** | Situaciones recuperables | "Sesión expirada - realizando re-login" |
| **ERROR** | Fallos críticos | "Login falló después de reintentar" |
| **DEBUG** | Detalles técnicos | "Verificando validez de la sesión..." |

### Mensajes de Log por Escenario

#### 🆕 Primera vez (sin sesión guardada)

```
WARNING - No hay sesión guardada en pjn_storage_state.json - realizando login inicial
INFO    - Iniciando nuevo login en https://portalpjn.pjn.gov.ar/inicio
DEBUG   - Página de login cargada, rellenando credenciales
INFO    - Credenciales enviadas, esperando confirmación de login...
INFO    - Login exitoso, guardando sesión en pjn_storage_state.json
INFO    - Sesión autenticada exitosamente - página lista para usar
```

#### ✅ Sesión válida existente

```
INFO    - Reutilizando sesión guardada desde pjn_storage_state.json
DEBUG   - Verificando validez de la sesión...
DEBUG   - Sesión verificada correctamente - elemento de confirmación encontrado
INFO    - Sesión autenticada exitosamente - página lista para usar
```

#### 🔄 Sesión expirada (re-login automático)

```
INFO    - Reutilizando sesión guardada desde pjn_storage_state.json
DEBUG   - Verificando validez de la sesión...
DEBUG   - Elemento de confirmación no encontrado, verificando si hay formulario de login
WARNING - Sesión expirada - formulario de login visible
WARNING - Sesión inválida o expirada - realizando re-login automático
INFO    - Iniciando nuevo login en https://portalpjn.pjn.gov.ar/inicio
DEBUG   - Página de login cargada, rellenando credenciales
INFO    - Credenciales enviadas, esperando confirmación de login...
INFO    - Login exitoso, guardando sesión en pjn_storage_state.json
INFO    - Sesión autenticada exitosamente - página lista para usar
```

### Configurar Nivel de Logging

**Para desarrollo/debugging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)  # Muestra todos los mensajes
```

**Para producción:**
```python
import logging
logging.basicConfig(level=logging.INFO)  # Solo mensajes importantes
```

---

## Configuración

### Desde `config.py`

```python
from pjn.config import Config, AuthConfig, BrowserConfig, set_config

# Configuración personalizada
config = Config(
    auth=AuthConfig(
        login_url="https://portalpjn.pjn.gov.ar/inicio",
        session_file_name="mi_sesion_custom.json",
    ),
    browser=BrowserConfig(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    ),
)

set_config(config)
```

### Variables de Entorno Soportadas

| Variable | Propósito | Valor por defecto |
|----------|-----------|-------------------|
| `PJN_USER` | Usuario para login (CUIL) | (requerido) |
| `PJN_PASSWORD` | Contraseña | (requerido) |
| `PJN_LOGIN_URL` | URL del portal | `https://portalpjn.pjn.gov.ar/inicio` |
| `PJN_HEADLESS` | Modo headless (1/true/yes) | `false` |

### Archivo de Sesión

**Ubicación por defecto:** `Sistema_v5/pjn/scraping/pjn_storage_state.json`

**Contenido:**
```json
{
  "cookies": [
    {
      "name": "KEYCLOAK_SESSION",
      "value": "...",
      "domain": "portalpjn.pjn.gov.ar",
      "expires": 1729123456
    }
  ],
  "origins": [
    {
      "origin": "https://portalpjn.pjn.gov.ar",
      "localStorage": [...]
    }
  ]
}
```

**Gestión:**
- ✅ Se crea automáticamente en el primer login
- ✅ Se reutiliza en ejecuciones posteriores
- ✅ Se borra automáticamente si expira
- ✅ Se puede compartir entre scripts (cuidado con concurrencia)

---

## Manejo de Errores

### Excepciones Personalizadas

```python
from pjn.exceptions import CredencialesFaltantes, SesionInvalida

try:
    async with obtener_pagina_autenticada() as (page, _, _):
        await page.goto("...")

except CredencialesFaltantes:
    print("❌ Configurar PJN_USER y PJN_PASSWORD")

except SesionInvalida:
    print("❌ Login falló después de reintentos")
    # Esto es raro, normalmente el re-login funciona
```

### Jerarquía de Excepciones

```
PJNError
└── AutenticacionError
    ├── CredencialesFaltantes
    └── SesionInvalida
```

### Cuándo se Lanzan

| Excepción | Cuándo | Solución |
|-----------|--------|----------|
| `CredencialesFaltantes` | Falta `PJN_USER` o `PJN_PASSWORD` | Configurar variables de entorno |
| `SesionInvalida` | Login falló y re-login también falló | Verificar credenciales, revisar logs |

---

## Comparación con Sistema_v3

| Aspecto | Sistema_v3 (`auto_login.py`) | Sistema_v5 (`base.py`) |
|---------|------------------------------|------------------------|
| **Selectores** | Hardcoded en el archivo | Importados de `selectores.py` ✅ |
| **Configuración** | Hardcoded | Desde `config.py` ✅ |
| **Excepciones** | Genéricas (`EnvironmentError`) | Tipadas (`CredencialesFaltantes`) ✅ |
| **Logging** | `print()` con emojis | Logging estructurado ✅ |
| **Archivo sesión** | `estado_sesion.json` | `pjn_storage_state.json` |
| **API** | Dual sync/async | Solo async (más correcto) ✅ |
| **Modularidad** | Todo en un archivo | Funciones privadas reutilizables ✅ |
| **Re-login** | Detección y re-login automático ✅ | Detección y re-login automático ✅ |
| **Verificación** | Busca "Menú" ✅ | Busca "Menú" + campo username ✅ |

### Migración de v3 a v5

**Antes (v3):**
```python
from Sistema_v3.web.auto_login import reutilizar_sesion_async

async with reutilizar_sesion_async() as (page, ctx, browser):
    await page.goto("https://...")
```

**Ahora (v5):**
```python
from pjn.scraping.base import obtener_pagina_autenticada

async with obtener_pagina_autenticada() as (page, ctx, browser):
    await page.goto("https://...")
```

**Cambios:**
1. ✅ Import path diferente
2. ✅ Nombre de función diferente
3. ✅ Misma API (context manager async)
4. ✅ Archivo de sesión diferente (no interferencia)

---

## Referencias

- **Código fuente:** `Sistema_v5/pjn/scraping/base.py` (líneas 200-355)
- **Selectores:** `Sistema_v5/pjn/selectores.py` (clase `AutenticacionSelectores`)
- **Configuración:** `Sistema_v5/pjn/config.py` (clase `AuthConfig`)
- **Excepciones:** `Sistema_v5/pjn/exceptions.py`
- **Tests:** Pendiente

---

**Última actualización:** 2025-10-16
**Versión:** 5.5.1
