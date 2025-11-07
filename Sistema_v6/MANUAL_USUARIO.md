# Manual de Usuario - Sistema PJN v6

**Sistema de Gestión y Monitoreo del Portal Judicial Nacional de Argentina**

**Fecha**: 2025-11-05
**Versión**: 6.0.0
**Autores**: Equipo Sistema PJN v6

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación](#instalación)
   - [Instalación con Docker (Recomendada)](#instalación-con-docker-recomendada)
   - [Instalación Nativa](#instalación-nativa)
4. [Configuración Inicial](#configuración-inicial)
5. [Primer Uso](#primer-uso)
6. [Guía de Uso - Interfaz Web](#guía-de-uso---interfaz-web)
   - [Autenticación](#autenticación)
   - [Dashboard](#dashboard)
   - [Módulo Expedientes](#módulo-expedientes)
   - [Módulo Workspaces](#módulo-workspaces)
   - [Módulo Monitoreo](#módulo-monitoreo)
   - [Configuración de Usuario](#configuración-de-usuario)
7. [Guía de Uso - CLI](#guía-de-uso---cli)
8. [Guía de Uso - API REST](#guía-de-uso---api-rest)
9. [Flujos de Trabajo Comunes](#flujos-de-trabajo-comunes)
10. [Resolución de Problemas](#resolución-de-problemas)
11. [Mejores Prácticas](#mejores-prácticas)
12. [Preguntas Frecuentes (FAQ)](#preguntas-frecuentes-faq)
13. [Glosario](#glosario)
14. [Soporte y Contacto](#soporte-y-contacto)

---

## Introducción

### ¿Qué es Sistema PJN v6?

Sistema PJN v6 es una aplicación completa para **automatizar la extracción, gestión y monitoreo de expedientes judiciales** del Portal Judicial Nacional (PJN) de Argentina.

### Características Principales

- **Extracción Automática**: Obtiene expedientes, notificaciones (entradas) y actuaciones del PJN usando tecnología de web scraping
- **Filtrado Inteligente**: Filtra expedientes por dependencia, situación, carátula, fechas y más
- **Workspaces**: Organiza expedientes en espacios de trabajo personalizados con colores e iconos
- **Monitoreo Automático**: Detecta cambios en expedientes y notifica automáticamente
- **Múltiples Interfaces**: Interfaz web moderna, CLI y API REST
- **Seguridad**: Autenticación JWT, encriptación de credenciales PJN
- **Dark Mode**: Interfaz adaptable a tus preferencias visuales

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────┐
│           Sistema PJN v6                         │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐   ┌──────────────┐            │
│  │   Frontend   │   │   Backend    │            │
│  │  React + TS  │──▶│  FastAPI     │            │
│  │  (Puerto 80) │   │  (Puerto 8000)│           │
│  └──────────────┘   └──────┬───────┘            │
│                             │                    │
│                             ▼                    │
│                     ┌──────────────┐             │
│                     │  Playwright  │             │
│                     │   Scraper    │             │
│                     └──────┬───────┘             │
│                            │                     │
│                            ▼                     │
│                    ┌──────────────┐              │
│                    │   Portal     │              │
│                    │  Judicial    │              │
│                    │  Nacional    │              │
│                    └──────────────┘              │
│                                                  │
│  Almacenamiento:                                 │
│  - SQLite (usuarios, config)                     │
│  - JSON (expedientes, entradas, actuaciones)     │
│  - Archivos (PDFs descargados)                   │
└─────────────────────────────────────────────────┘
```

---

## Requisitos del Sistema

### Hardware Mínimo

- **CPU**: 2 núcleos
- **RAM**: 4 GB
- **Disco**: 10 GB libres (más espacio según cantidad de expedientes)
- **Red**: Conexión a internet estable

### Hardware Recomendado

- **CPU**: 4+ núcleos
- **RAM**: 8+ GB
- **Disco**: 50+ GB (SSD preferible)
- **Red**: Conexión de banda ancha

### Software

#### Para Instalación con Docker (Recomendada)
- **Docker** 20.10+
- **Docker Compose** 2.0+
- Sistema Operativo: Linux, macOS, o Windows 10/11

#### Para Instalación Nativa
- **Python** 3.10, 3.11 o 3.12
- **Node.js** 18+ con npm
- **Git**
- Sistema Operativo: Linux, macOS, o Windows 10/11

### Acceso al PJN

- **Credenciales válidas** del Portal Judicial Nacional (scw.pjn.gov.ar)
- Acceso a la sección de expedientes

---

## Instalación

### Instalación con Docker (Recomendada)

Esta es la forma más sencilla y rápida de instalar el sistema.

#### Paso 1: Instalar Docker

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

**macOS**:
```bash
# Con Homebrew
brew install --cask docker

# O descargar desde https://www.docker.com/products/docker-desktop
```

**Windows**:
Descargar e instalar Docker Desktop desde:
https://www.docker.com/products/docker-desktop

#### Paso 2: Verificar Instalación

```bash
docker --version
# Debe mostrar: Docker version 20.10+ o superior

docker-compose --version
# Debe mostrar: Docker Compose version 2.0+ o superior
```

#### Paso 3: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/sistema-pjn-v6.git
cd sistema-pjn-v6/Sistema_v6
```

#### Paso 4: Configurar Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```bash
# Crear archivo .env
cat > .env << 'EOF'
# Seguridad (CAMBIAR EN PRODUCCIÓN)
JWT_SECRET_KEY=tu-clave-secreta-jwt-muy-segura-cambiar-en-produccion
ENCRYPTION_FERNET_KEY=gZxdkgEN2wyl4L3A77Xkrwjzk_uRq6Orz8txZmbdXG4=

# Opcional: Configuración adicional
ENVIRONMENT=production
LOG_LEVEL=info
EOF
```

**IMPORTANTE**: En producción, genera una nueva clave Fernet:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Paso 5: Iniciar el Sistema

```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build
```

Este comando:
- Construye las imágenes de Docker
- Crea los contenedores
- Inicia el backend (puerto 8000)
- Inicia el frontend (puerto 80)
- Crea la base de datos SQLite

#### Paso 6: Verificar que Todo Funciona

```bash
# Ver estado de los servicios
docker-compose ps

# Debe mostrar:
# NAME                    STATUS
# sistema-pjn-backend     Up (healthy)
# sistema-pjn-frontend    Up (healthy)

# Ver logs
docker-compose logs -f
```

#### Paso 7: Acceder a la Aplicación

Abre tu navegador en:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Instalación Nativa

Si prefieres no usar Docker, puedes instalar el sistema directamente en tu máquina.

#### Paso 1: Instalar Python

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**macOS**:
```bash
# Con Homebrew
brew install python@3.11
```

**Windows**:
Descargar desde https://www.python.org/downloads/

#### Paso 2: Instalar Node.js

**Linux (Ubuntu/Debian)**:
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS**:
```bash
brew install node
```

**Windows**:
Descargar desde https://nodejs.org/

#### Paso 3: Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/sistema-pjn-v6.git
cd sistema-pjn-v6/Sistema_v6
```

#### Paso 4: Instalar Backend

```bash
# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Playwright (navegador para scraping)
playwright install chromium
```

#### Paso 5: Configurar Backend

```bash
# Crear archivo .env
cp .env.example .env

# Editar .env con tus valores
nano .env  # o el editor de tu preferencia
```

Contenido del `.env`:
```env
# Base de datos
DATABASE_URL=sqlite:///./data/sistema.db

# Seguridad
JWT_SECRET_KEY=tu-clave-secreta-jwt-muy-segura
ENCRYPTION_FERNET_KEY=tu-clave-fernet-generada

# CORS (para desarrollo local)
CORS_ORIGINS=http://localhost:5173,http://localhost

# Entorno
ENVIRONMENT=development
LOG_LEVEL=info
```

#### Paso 6: Inicializar Base de Datos

```bash
# Crear directorio de datos
mkdir -p data

# Inicializar base de datos
python scripts/init_db.py
```

#### Paso 7: Iniciar Backend

```bash
# Iniciar servidor FastAPI
uvicorn presentation.api.rest.main:app --reload --port 8000
```

El backend estará disponible en http://localhost:8000

#### Paso 8: Instalar Frontend

En una **nueva terminal**:

```bash
cd frontend

# Instalar dependencias
npm install

# Crear archivo .env
cp .env.example .env
```

Contenido del `.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_ENCRYPTION_KEY=tu-clave-para-encriptacion-cliente
```

#### Paso 9: Iniciar Frontend

```bash
# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en http://localhost:5173

---

## Configuración Inicial

### Crear Cuenta de Usuario

1. Abre el navegador en http://localhost (Docker) o http://localhost:5173 (nativo)
2. En la pantalla de login, haz clic en **"Crear cuenta"**
3. Completa el formulario:
   - **Nombre**: Tu nombre completo
   - **Email**: Tu correo electrónico (será tu usuario)
   - **Contraseña**: Mínimo 8 caracteres, incluye mayúsculas, minúsculas y números
   - **Confirmar contraseña**: Repite la contraseña
4. Haz clic en **"Registrarse"**
5. Serás redirigido automáticamente al Dashboard

### Configurar Credenciales del PJN

Para que el sistema pueda extraer expedientes del Portal Judicial Nacional, debes configurar tus credenciales:

1. En el menú lateral, haz clic en **"Configuración"** (icono de engranaje)
2. Ve a la pestaña **"Credenciales PJN"**
3. Completa el formulario:
   - **Usuario PJN**: Tu usuario del portal scw.pjn.gov.ar
   - **Contraseña PJN**: Tu contraseña del portal
4. Haz clic en **"Guardar Credenciales"**

**Seguridad**:
- Las credenciales se encriptan en el cliente antes de enviarse al servidor
- En el servidor se vuelven a encriptar con Fernet antes de guardarse en la base de datos
- Nunca se almacenan en texto plano

### Verificar Conexión al PJN

1. Ve al módulo **"Expedientes"** en el menú lateral
2. Haz clic en **"Extraer Expedientes"**
3. Si las credenciales son correctas:
   - Verás una barra de progreso
   - El sistema extraerá los expedientes de tu lista
   - Los expedientes aparecerán en la tabla

Si hay error:
- Verifica que las credenciales del PJN sean correctas
- Asegúrate de tener conexión a internet
- Consulta la sección de [Resolución de Problemas](#resolución-de-problemas)

---

## Primer Uso

### Tutorial Básico: Extracción de Expedientes

Sigue estos pasos para tu primera extracción:

#### 1. Login
```
✓ Abrir http://localhost
✓ Ingresar email y contraseña
✓ Clic en "Iniciar Sesión"
```

#### 2. Configurar Credenciales PJN
```
✓ Ir a Configuración → Credenciales PJN
✓ Ingresar usuario y contraseña del PJN
✓ Guardar
```

#### 3. Extraer Expedientes
```
✓ Ir a Expedientes
✓ Clic en "Extraer Expedientes"
✓ Esperar a que termine (puede tardar 1-5 minutos)
✓ Ver lista de expedientes en la tabla
```

#### 4. Ver Detalles de un Expediente
```
✓ Clic en "Ver Detalles" en cualquier expediente
✓ Ver información completa: partes, caratula, situación, etc.
✓ Clic en "Extraer Actuaciones" para obtener todas las actuaciones
```

#### 5. Crear un Workspace
```
✓ Ir a Workspaces
✓ Clic en "Nuevo Workspace"
✓ Ingresar nombre y descripción
✓ Elegir color e icono
✓ Agregar expedientes al workspace
```

#### 6. Configurar Monitoreo
```
✓ Ir a Monitoreo
✓ Seleccionar un expediente
✓ Elegir frecuencia de monitoreo (ej: cada 1 hora)
✓ Elegir horario (ej: 8:00 - 20:00)
✓ Activar monitoreo
```

---

## Guía de Uso - Interfaz Web

### Autenticación

#### Registro de Nuevo Usuario

1. **Acceder a la Página de Registro**
   - Abre http://localhost en tu navegador
   - Haz clic en **"Crear cuenta"** debajo del formulario de login

2. **Completar el Formulario**
   ```
   Nombre:            [Tu nombre completo]
   Email:             [tu@email.com]
   Contraseña:        [••••••••]  (min. 8 caracteres)
   Confirmar:         [••••••••]
   ```

3. **Validaciones**
   - Email debe ser válido
   - Contraseña mínimo 8 caracteres
   - Debe incluir mayúsculas, minúsculas y números
   - Las contraseñas deben coincidir

4. **Crear Cuenta**
   - Haz clic en **"Registrarse"**
   - Si todo es correcto, serás redirigido al Dashboard
   - Tu sesión se iniciará automáticamente

#### Iniciar Sesión

1. **Acceder a la Página de Login**
   - Abre http://localhost en tu navegador

2. **Ingresar Credenciales**
   ```
   Email:      [tu@email.com]
   Contraseña: [••••••••]
   ```

3. **Opción "Recordarme"**
   - Marca esta opción para mantener la sesión activa
   - Tu sesión no expirará al cerrar el navegador
   - Recomendado solo en computadoras personales

4. **Iniciar Sesión**
   - Haz clic en **"Iniciar Sesión"**
   - Serás redirigido al Dashboard

#### Cerrar Sesión

1. Haz clic en tu nombre en la esquina superior derecha
2. Selecciona **"Cerrar Sesión"**
3. Serás redirigido a la página de login
4. Tu token de sesión se eliminará del navegador

### Dashboard

El Dashboard es la página principal después del login.

#### Componentes del Dashboard

```
┌─────────────────────────────────────────────────┐
│  Dashboard                             [Avatar] │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ Expedientes  │  │  Workspaces  │             │
│  │    Total     │  │    Total     │             │
│  │      42      │  │      5       │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Monitores   │  │   Entradas   │             │
│  │   Activos    │  │   Recientes  │             │
│  │      8       │  │      12      │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  📊 Gráfico de Expedientes por Dependencia      │
│  ┌──────────────────────────────────────┐       │
│  │  ████████████ CNM (15)               │       │
│  │  ███████ CFed (8)                    │       │
│  │  █████ ST (5)                        │       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  📋 Actividad Reciente                          │
│  • Expediente CNM 1234/2024 actualizado         │
│  • Nueva actuación en CFed 5678/2023            │
│  • Workspace "Urgentes" modificado              │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### Estadísticas

Las tarjetas muestran:
- **Expedientes**: Cantidad total extraídos
- **Workspaces**: Espacios de trabajo creados
- **Monitores Activos**: Expedientes siendo monitoreados
- **Entradas Recientes**: Notificaciones nuevas del PJN

#### Gráficos

- **Por Dependencia**: Cantidad de expedientes por organismo
- **Por Situación**: Estados procesales (A sentencia, En trámite, etc.)
- **Línea de Tiempo**: Actividad de extracción/monitoreo

#### Acciones Rápidas

Desde el Dashboard puedes:
- Hacer clic en cada tarjeta para ir al módulo correspondiente
- Ver actividad reciente
- Acceder a acciones frecuentes

### Módulo Expedientes

El módulo de expedientes permite extraer, filtrar, buscar y gestionar expedientes del PJN.

#### Vista Principal

```
┌─────────────────────────────────────────────────┐
│  Expedientes                                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  [Extraer Expedientes]  [Filtros ▼]  [🔍 Buscar]│
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ Expediente      │ Dependencia │ Situación│   │
│  ├──────────────────────────────────────────┤   │
│  │ CNM 1234/2024   │ CNM         │ Trámite  │   │
│  │ CFed 5678/2023  │ CFed BA     │ Sentencia│   │
│  │ ST 9012/2022    │ ST          │ Archivo  │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  Mostrando 1-10 de 42 expedientes   [< 1 2 3 >] │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### Extraer Expedientes

1. **Iniciar Extracción**
   - Haz clic en **"Extraer Expedientes"**
   - Aparecerá un modal de confirmación

2. **Opciones de Extracción**
   ```
   [ ] Extraer solo página actual (más rápido)
   [x] Extraer todas las páginas (completo)
   [ ] Actualizar expedientes existentes
   ```

3. **Progreso**
   - Verás una barra de progreso
   - Muestra: "Extrayendo página 3 de 8..."
   - Puedes cancelar en cualquier momento

4. **Resultado**
   - Los expedientes aparecen en la tabla
   - Se muestran datos básicos: número, dependencia, caratula, situación
   - Se guardan automáticamente en el sistema

#### Filtrar Expedientes

1. **Abrir Panel de Filtros**
   - Haz clic en **"Filtros"**
   - Se despliega el panel lateral

2. **Filtros Disponibles**
   ```
   Dependencia:        [Seleccionar...▼]
                       • Todas
                       • CNM
                       • CFed BA
                       • CFed Rosario
                       • ST
                       • ...

   Situación:          [Seleccionar...▼]
                       • Todas
                       • En trámite
                       • A sentencia
                       • Archivado
                       • ...

   Carátula:           [Buscar en carátula...]

   Fecha desde:        [📅 dd/mm/aaaa]
   Fecha hasta:        [📅 dd/mm/aaaa]

   Días sin actividad: [Solo con actividad reciente]
                       [ ] Últimos 7 días
                       [ ] Últimos 30 días
                       [ ] Últimos 90 días

   Partes:             [Nombre de parte...]
   ```

3. **Aplicar Filtros**
   - Selecciona los criterios deseados
   - Haz clic en **"Aplicar Filtros"**
   - La tabla se actualiza con los resultados

4. **Limpiar Filtros**
   - Haz clic en **"Limpiar Filtros"**
   - Se muestran todos los expedientes nuevamente

#### Ver Detalles de Expediente

1. **Acceder a Detalles**
   - Haz clic en **"Ver Detalles"** en cualquier expediente
   - O haz clic directamente en el número del expediente

2. **Información Mostrada**
   ```
   ┌─────────────────────────────────────────────┐
   │  Expediente CNM 1234/2024                    │
   ├─────────────────────────────────────────────┤
   │                                              │
   │  📋 Información General                      │
   │  Dependencia:     CNM - Cámara Nacional...   │
   │  Situación:       En trámite                 │
   │  Carátula:        SMITH, JOHN C/ ...         │
   │  Fecha inicio:    15/03/2024                 │
   │  Última act.:     02/11/2024                 │
   │                                              │
   │  👥 Partes                                   │
   │  • SMITH, JOHN (Actor)                       │
   │  • DOE, JANE (Demandado)                     │
   │  • ...                                       │
   │                                              │
   │  📑 Actuaciones (23)  [Extraer Actuaciones]  │
   │  ┌──────────────────────────────────────┐   │
   │  │ Fecha       │ Tipo      │ Descripción│   │
   │  ├──────────────────────────────────────┤   │
   │  │ 02/11/2024  │ Proveído  │ Se provee...│   │
   │  │ 28/10/2024  │ Escrito   │ Presenta...│   │
   │  │ ...                                  │   │
   │  └──────────────────────────────────────┘   │
   │                                              │
   │  [⬅ Volver]  [📁 Agregar a Workspace]       │
   │              [🔔 Monitorear]                 │
   │                                              │
   └─────────────────────────────────────────────┘
   ```

#### Extraer Actuaciones

1. **Desde Detalles del Expediente**
   - Haz clic en **"Extraer Actuaciones"**
   - Aparece un modal de confirmación

2. **Opciones**
   ```
   [x] Extraer actuaciones actuales
   [x] Extraer actuaciones históricas
   [ ] Descargar archivos adjuntos (PDFs)
   ```

3. **Proceso**
   - El sistema navega al expediente en el PJN
   - Extrae las actuaciones de ambos tabs (actuales e históricas)
   - Parsea la información
   - Opcionalmente descarga PDFs adjuntos

4. **Resultado**
   - Las actuaciones aparecen en la tabla
   - Se muestran ordenadas por fecha (más reciente primero)
   - Los PDFs se guardan en el workspace (si se seleccionó esa opción)

#### Búsqueda Rápida

1. **Usar Barra de Búsqueda**
   - Escribe en el campo de búsqueda: 🔍
   - La búsqueda es instantánea (mientras escribes)

2. **Criterios de Búsqueda**
   - Número de expediente (ej: "1234/2024")
   - Dependencia (ej: "CNM")
   - Carátula (ej: "SMITH")
   - Cualquier texto en los datos del expediente

3. **Resultados**
   - Se filtran en tiempo real
   - Resalta las coincidencias encontradas

### Módulo Workspaces

Los workspaces te permiten organizar expedientes en grupos personalizados.

#### Vista Principal

```
┌─────────────────────────────────────────────────┐
│  Workspaces                                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  [+ Nuevo Workspace]                [Vista: Grid]│
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ 📂 Urgentes  │  │ ⭐ Priorita. │             │
│  │              │  │              │             │
│  │ 12 expedien. │  │ 8 expedien.  │             │
│  │ Actualizado  │  │ Actualizado  │             │
│  │ hace 2h      │  │ hace 5h      │             │
│  │              │  │              │             │
│  │ [Abrir] [⋮]  │  │ [Abrir] [⋮]  │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │ 💼 Laborales │  │ 🏛️ Civiles   │             │
│  │              │  │              │             │
│  │ 15 expedien. │  │ 20 expedien. │             │
│  │ Actualizado  │  │ Actualizado  │             │
│  │ hace 1d      │  │ hace 3d      │             │
│  │              │  │              │             │
│  │ [Abrir] [⋮]  │  │ [Abrir] [⋮]  │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### Crear Workspace

1. **Iniciar Creación**
   - Haz clic en **"+ Nuevo Workspace"**
   - Se abre un modal

2. **Completar Formulario**
   ```
   Nombre:       [Ej: Casos Urgentes]
   Descripción:  [Ej: Expedientes con fechas próximas]

   Color:        🔴 🟠 🟡 🟢 🔵 🟣 ⚫ ⚪
                 [Selecciona un color]

   Icono:        📂 ⭐ 💼 🏛️ 📌 🔥 ⚖️ 📋
                 [Selecciona un icono]
   ```

3. **Guardar**
   - Haz clic en **"Crear Workspace"**
   - El workspace aparece en la lista
   - Puedes empezar a agregar expedientes

#### Agregar Expedientes a Workspace

**Método 1: Desde el Módulo Expedientes**
1. En la lista de expedientes, haz clic en el menú (⋮) de un expediente
2. Selecciona **"Agregar a Workspace"**
3. Marca los workspaces donde quieres agregarlo
4. Haz clic en **"Agregar"**

**Método 2: Desde Detalles del Expediente**
1. Abre los detalles de un expediente
2. Haz clic en **"📁 Agregar a Workspace"**
3. Selecciona los workspaces
4. Confirma

**Método 3: Desde el Workspace**
1. Abre un workspace
2. Haz clic en **"+ Agregar Expedientes"**
3. Busca y selecciona expedientes
4. Haz clic en **"Agregar Seleccionados"**

#### Ver Workspace

1. **Abrir Workspace**
   - Haz clic en **"Abrir"** en cualquier workspace
   - O haz clic directamente en la tarjeta

2. **Vista de Detalles**
   ```
   ┌─────────────────────────────────────────────┐
   │  📂 Casos Urgentes                  [⋮]     │
   │  Expedientes con fechas próximas             │
   ├─────────────────────────────────────────────┤
   │                                              │
   │  12 expedientes                              │
   │  Última actualización: hace 2 horas          │
   │                                              │
   │  [+ Agregar Expedientes]  [🔍 Buscar]       │
   │                                              │
   │  ┌──────────────────────────────────────┐   │
   │  │ Expediente      │ Dependencia │ Acc. │   │
   │  ├──────────────────────────────────────┤   │
   │  │ CNM 1234/2024   │ CNM         │ [⋮]  │   │
   │  │ CFed 5678/2023  │ CFed BA     │ [⋮]  │   │
   │  │ ...                                  │   │
   │  └──────────────────────────────────────┘   │
   │                                              │
   │  [⬅ Volver a Workspaces]                    │
   │                                              │
   └─────────────────────────────────────────────┘
   ```

3. **Acciones Disponibles**
   - Ver todos los expedientes del workspace
   - Agregar más expedientes
   - Quitar expedientes (sin eliminarlos del sistema)
   - Editar workspace (nombre, descripción, color, icono)
   - Eliminar workspace (no elimina los expedientes)

#### Editar Workspace

1. En la tarjeta del workspace, haz clic en el menú (⋮)
2. Selecciona **"Editar"**
3. Modifica nombre, descripción, color o icono
4. Haz clic en **"Guardar Cambios"**

#### Eliminar Workspace

1. En la tarjeta del workspace, haz clic en el menú (⋮)
2. Selecciona **"Eliminar"**
3. Confirma la acción

**IMPORTANTE**: Eliminar un workspace NO elimina los expedientes. Solo elimina la agrupación.

### Módulo Monitoreo

El módulo de monitoreo te permite detectar cambios automáticamente en expedientes.

#### Vista Principal

```
┌─────────────────────────────────────────────────┐
│  Monitoreo                                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  Tabs: [📋 Configurados] [📊 Historial]         │
│                                                  │
│  [+ Nuevo Monitor]                               │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ Expediente      │ Frecuencia │ Estado   │   │
│  ├──────────────────────────────────────────┤   │
│  │ CNM 1234/2024   │ Cada 1h    │ 🟢 Activo│   │
│  │ CFed 5678/2023  │ Cada 6h    │ ⏸️ Pausado│   │
│  │ ST 9012/2022    │ Cada 24h   │ 🟢 Activo│   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  8 monitores activos                             │
│  2 monitores pausados                            │
│  Último chequeo: hace 15 minutos                 │
│                                                  │
└─────────────────────────────────────────────────┘
```

#### Crear Monitor

1. **Iniciar Configuración**
   - Haz clic en **"+ Nuevo Monitor"**
   - O desde detalles de expediente: **"🔔 Monitorear"**

2. **Seleccionar Expediente**
   ```
   Expediente:  [Buscar expediente...▼]
                • CNM 1234/2024
                • CFed 5678/2023
                • ...
   ```

3. **Configurar Frecuencia**
   ```
   Frecuencia de chequeo:
   ( ) Cada 5 minutos   (solo para testing)
   ( ) Cada 15 minutos
   (•) Cada 1 hora      ← Recomendado
   ( ) Cada 3 horas
   ( ) Cada 6 horas
   ( ) Cada 12 horas
   ( ) Cada 24 horas
   ( ) Manual
   ```

4. **Configurar Horario**
   ```
   Horario activo:
   [x] Respetar horario laboral

   Desde: [08:00]
   Hasta: [20:00]

   Días activos:
   [x] Lunes     [x] Martes    [x] Miércoles
   [x] Jueves    [x] Viernes   [ ] Sábado
   [ ] Domingo
   ```

5. **Configurar Notificaciones**
   ```
   Notificar cuando:
   [x] Haya nueva actuación
   [x] Cambie la situación
   [ ] Cambie cualquier dato

   Método de notificación:
   [x] Notificación en la aplicación
   [x] Notificación del sistema (desktop)
   [ ] Email (próximamente)
   [ ] Telegram (próximamente)
   ```

6. **Guardar**
   - Haz clic en **"Crear Monitor"**
   - El monitor aparece en la lista
   - Comienza a funcionar según la frecuencia configurada

#### Ver Historial de Cambios

1. **Abrir Pestaña Historial**
   - Haz clic en la pestaña **"📊 Historial"**

2. **Vista de Historial**
   ```
   ┌─────────────────────────────────────────────┐
   │  📊 Historial de Cambios                     │
   ├─────────────────────────────────────────────┤
   │                                              │
   │  Filtros: [Todos los expedientes▼]          │
   │           [Últimos 7 días▼]                 │
   │                                              │
   │  ┌──────────────────────────────────────┐   │
   │  │ 🟢 CNM 1234/2024                     │   │
   │  │ 02/11/2024 15:30                     │   │
   │  │ Nueva actuación: "Se provee..."      │   │
   │  │ [Ver detalles]                       │   │
   │  └──────────────────────────────────────┘   │
   │                                              │
   │  ┌──────────────────────────────────────┐   │
   │  │ 🔵 CFed 5678/2023                    │   │
   │  │ 01/11/2024 09:15                     │   │
   │  │ Cambió situación: Trámite → Sentencia│   │
   │  │ [Ver detalles]                       │   │
   │  └──────────────────────────────────────┘   │
   │                                              │
   └─────────────────────────────────────────────┘
   ```

3. **Detalles de Cambio**
   - Haz clic en **"Ver detalles"** en cualquier cambio
   - Muestra qué cambió exactamente (diff de datos)
   - Link al expediente afectado

#### Pausar/Reanudar Monitor

1. En la lista de monitores, haz clic en el menú (⋮) del monitor
2. Selecciona **"Pausar"** o **"Reanudar"**
3. Un monitor pausado no realiza chequeos
4. Puedes reanudarlo en cualquier momento

#### Editar Monitor

1. Haz clic en el menú (⋮) del monitor
2. Selecciona **"Editar"**
3. Modifica frecuencia, horario o notificaciones
4. Haz clic en **"Guardar Cambios"**

#### Eliminar Monitor

1. Haz clic en el menú (⋮) del monitor
2. Selecciona **"Eliminar"**
3. Confirma la acción
4. El expediente deja de ser monitoreado

### Configuración de Usuario

El módulo de configuración te permite personalizar tu cuenta y preferencias.

#### Acceder a Configuración

- Haz clic en **"Configuración"** (icono ⚙️) en el menú lateral
- O haz clic en tu avatar → **"Configuración"**

#### Pestaña: Perfil de Usuario

```
┌─────────────────────────────────────────────┐
│  👤 Perfil de Usuario                        │
├─────────────────────────────────────────────┤
│                                              │
│  Nombre:     [John Doe          ]            │
│  Email:      [john@example.com  ]            │
│  Rol:        Administrador (no editable)     │
│                                              │
│  Fecha de registro: 15/10/2024               │
│  Último acceso: 05/11/2024 14:30             │
│                                              │
│  [Guardar Cambios]                           │
│                                              │
└─────────────────────────────────────────────┘
```

**Acciones**:
- Modificar nombre
- Ver información de la cuenta
- No se puede cambiar el email (es tu identificador único)

#### Pestaña: Credenciales PJN

```
┌─────────────────────────────────────────────┐
│  🔑 Credenciales PJN                         │
├─────────────────────────────────────────────┤
│                                              │
│  Estado: ✅ Credenciales configuradas        │
│                                              │
│  Usuario PJN:    [tu_usuario_pjn]            │
│  Contraseña PJN: [••••••••••••••] [👁️]       │
│                                              │
│  ⚠️ Importante:                              │
│  • Estas credenciales se usan para acceder   │
│    al Portal Judicial Nacional               │
│  • Se almacenan encriptadas                  │
│  • Solo tú puedes verlas y modificarlas      │
│                                              │
│  Última verificación: 05/11/2024 12:00       │
│  Estado de conexión: ✅ Conectado            │
│                                              │
│  [Guardar Credenciales]  [Probar Conexión]   │
│  [Eliminar Credenciales]                     │
│                                              │
└─────────────────────────────────────────────┘
```

**Acciones**:
- **Guardar Credenciales**: Almacena o actualiza credenciales PJN
- **Probar Conexión**: Verifica que las credenciales funcionen
- **Eliminar Credenciales**: Borra credenciales del sistema
- **Mostrar/Ocultar Contraseña**: Toggle del icono del ojo

#### Pestaña: Cambiar Contraseña

```
┌─────────────────────────────────────────────┐
│  🔒 Cambiar Contraseña                       │
├─────────────────────────────────────────────┤
│                                              │
│  Contraseña actual:     [••••••••] [👁️]      │
│  Nueva contraseña:      [••••••••] [👁️]      │
│  Confirmar contraseña:  [••••••••] [👁️]      │
│                                              │
│  ✅ Requisitos de seguridad:                 │
│  ✓ Mínimo 8 caracteres                       │
│  ✓ Al menos una mayúscula                    │
│  ✓ Al menos una minúscula                    │
│  ✓ Al menos un número                        │
│  ✗ Las contraseñas coinciden                 │
│                                              │
│  [Cambiar Contraseña]                        │
│                                              │
└─────────────────────────────────────────────┘
```

**Validaciones**:
- La contraseña actual debe ser correcta
- La nueva contraseña debe cumplir requisitos
- Las nuevas contraseñas deben coincidir
- Se muestran checks en tiempo real

#### Pestaña: Preferencias

```
┌─────────────────────────────────────────────┐
│  ⚙️ Preferencias de la Aplicación            │
├─────────────────────────────────────────────┤
│                                              │
│  🎨 Apariencia                               │
│  Tema:  ( ) Claro  (•) Oscuro  ( ) Sistema   │
│                                              │
│  🔔 Notificaciones                           │
│  [ ] Notificaciones de escritorio            │
│  [ ] Sonido en notificaciones                │
│  [ ] Notificaciones por email                │
│                                              │
│  📋 Expedientes                              │
│  Elementos por página: [20 ▼]                │
│  Vista por defecto:    [Tabla ▼]             │
│  Auto-refresh:         [5 minutos ▼]         │
│                                              │
│  🔍 Monitoreo                                │
│  Frecuencia por defecto: [Cada 1 hora ▼]     │
│  Horario por defecto:    [08:00 - 20:00]     │
│  [x] Solo días hábiles                       │
│                                              │
│  💾 Almacenamiento                           │
│  [x] Descargar PDFs automáticamente          │
│  Tamaño máximo por PDF: [10 MB ▼]            │
│                                              │
│  [Guardar Preferencias]  [Restaurar]         │
│                                              │
└─────────────────────────────────────────────┘
```

**Opciones**:
- **Tema**: Cambiar entre claro/oscuro/automático según sistema
- **Notificaciones**: Configurar tipos de notificaciones
- **Expedientes**: Personalizar vistas y paginación
- **Monitoreo**: Configuración por defecto para nuevos monitores
- **Almacenamiento**: Control de descarga de archivos

---

## Guía de Uso - CLI

La interfaz de línea de comandos (CLI) es útil para automatización y scripting.

### Comandos Básicos

#### Ver Ayuda

```bash
python -m presentation.cli.main --help
```

Muestra todos los comandos disponibles.

#### Extraer Expedientes

```bash
# Extraer todos los expedientes
python -m presentation.cli.main extraer-expedientes

# Con opciones
python -m presentation.cli.main extraer-expedientes \
    --max-paginas 5 \
    --output expedientes.json
```

**Opciones**:
- `--max-paginas N`: Límite de páginas a extraer
- `--output FILE`: Guardar en archivo específico
- `--formato json|excel`: Formato de salida

#### Extraer Entradas (Notificaciones)

```bash
python -m presentation.cli.main extraer-entradas

# Con límite
python -m presentation.cli.main extraer-entradas --max-items 50
```

#### Extraer Actuaciones

```bash
# De un expediente específico
python -m presentation.cli.main extraer-actuaciones "CNM 1234/2024"

# Con descarga de PDFs
python -m presentation.cli.main extraer-actuaciones \
    "CNM 1234/2024" \
    --descargar-pdfs
```

#### Filtrar Expedientes

```bash
# Filtrar por dependencia
python -m presentation.cli.main filtrar \
    --dependencia "CNM"

# Filtrar por múltiples criterios
python -m presentation.cli.main filtrar \
    --dependencia "CNM" \
    --situacion "A sentencia" \
    --dias-activos 30 \
    --caratula "SMITH"
```

**Opciones de filtrado**:
- `--dependencia TEXT`: Filtrar por dependencia
- `--situacion TEXT`: Filtrar por situación
- `--caratula TEXT`: Buscar en carátula
- `--parte TEXT`: Buscar en partes
- `--dias-activos N`: Solo expedientes con actividad en últimos N días
- `--fecha-desde YYYY-MM-DD`: Desde fecha
- `--fecha-hasta YYYY-MM-DD`: Hasta fecha

#### Crear Workspace

```bash
python -m presentation.cli.main crear-workspace \
    --nombre "Casos Urgentes" \
    --descripcion "Expedientes prioritarios"
```

#### Listar Expedientes

```bash
# Listar todos
python -m presentation.cli.main listar

# Con formato
python -m presentation.cli.main listar --formato table
python -m presentation.cli.main listar --formato json
```

### Ejemplos de Uso

#### Extraer y Filtrar en Pipeline

```bash
# Extraer expedientes y filtrar CNM
python -m presentation.cli.main extraer-expedientes && \
python -m presentation.cli.main filtrar --dependencia "CNM"
```

#### Monitoreo Automático con Cron

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada hora
0 * * * * cd /ruta/a/sistema-v6 && \
  /ruta/a/venv/bin/python -m presentation.cli.main extraer-expedientes \
  >> /var/log/sistema-pjn.log 2>&1
```

#### Script de Backup

```bash
#!/bin/bash
# backup-expedientes.sh

FECHA=$(date +%Y%m%d)
BACKUP_DIR="backups/$FECHA"

mkdir -p "$BACKUP_DIR"

# Extraer expedientes
python -m presentation.cli.main extraer-expedientes \
    --output "$BACKUP_DIR/expedientes.json"

# Comprimir
tar -czf "backup-$FECHA.tar.gz" "$BACKUP_DIR"

echo "Backup completado: backup-$FECHA.tar.gz"
```

---

## Guía de Uso - API REST

La API REST permite integrar el sistema con otras aplicaciones.

### Acceder a la Documentación

Una vez iniciado el backend:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Autenticación

La API usa autenticación JWT (JSON Web Tokens).

#### 1. Registrar Usuario

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

Respuesta:
```json
{
  "user": {
    "id": 1,
    "nombre": "John Doe",
    "email": "john@example.com",
    "rol": "user"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

Respuesta (igual que registro).

#### 3. Usar Token

Incluye el token en el header `Authorization`:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Endpoints Principales

#### Health Check

```bash
GET /api/v1/health
```

Verifica que el API esté funcionando.

#### Expedientes

**Extraer expedientes**:
```bash
POST /api/v1/expedientes/extraer
Authorization: Bearer {token}

{
  "max_paginas": 5,
  "actualizar_existentes": false
}
```

**Listar expedientes**:
```bash
GET /api/v1/expedientes
Authorization: Bearer {token}

Query params:
  - skip: int (default 0)
  - limit: int (default 100)
  - dependencia: str (optional)
  - situacion: str (optional)
```

**Obtener expediente**:
```bash
GET /api/v1/expedientes/{id}
Authorization: Bearer {token}
```

**Filtrar expedientes**:
```bash
POST /api/v1/expedientes/filtrar
Authorization: Bearer {token}

{
  "dependencia": "CNM",
  "situacion": "A sentencia",
  "dias_activos": 30
}
```

#### Actuaciones

**Extraer actuaciones**:
```bash
POST /api/v1/actuaciones/extraer
Authorization: Bearer {token}

{
  "numero_expediente": "CNM 1234/2024",
  "descargar_archivos": true
}
```

#### Workspaces

**Crear workspace**:
```bash
POST /api/v1/workspaces
Authorization: Bearer {token}

{
  "nombre": "Casos Urgentes",
  "descripcion": "Expedientes prioritarios",
  "color": "red",
  "icono": "folder"
}
```

**Agregar expediente a workspace**:
```bash
POST /api/v1/workspaces/{workspace_id}/expedientes
Authorization: Bearer {token}

{
  "expediente_id": 123
}
```

#### Monitoreo

**Crear monitor**:
```bash
POST /api/v1/monitoreo
Authorization: Bearer {token}

{
  "expediente_id": 123,
  "frecuencia_minutos": 60,
  "horario_desde": "08:00",
  "horario_hasta": "20:00",
  "dias_activos": [1, 2, 3, 4, 5],
  "notificar_actuaciones": true,
  "notificar_cambios_situacion": true
}
```

### Ejemplos con Python

#### Usando `requests`

```python
import requests

# Config
BASE_URL = "http://localhost:8000"
email = "john@example.com"
password = "SecurePass123"

# 1. Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"email": email, "password": password}
)
token = response.json()["access_token"]

# 2. Headers con token
headers = {"Authorization": f"Bearer {token}"}

# 3. Extraer expedientes
response = requests.post(
    f"{BASE_URL}/api/v1/expedientes/extraer",
    json={"max_paginas": 3},
    headers=headers
)
print(response.json())

# 4. Listar expedientes
response = requests.get(
    f"{BASE_URL}/api/v1/expedientes",
    params={"limit": 10, "dependencia": "CNM"},
    headers=headers
)
expedientes = response.json()
print(f"Total: {len(expedientes)}")
```

#### Usando `httpx` (async)

```python
import httpx
import asyncio

async def main():
    BASE_URL = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # Login
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "john@example.com", "password": "SecurePass123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Extraer expedientes
        response = await client.post(
            f"{BASE_URL}/api/v1/expedientes/extraer",
            json={"max_paginas": 5},
            headers=headers
        )
        print(response.json())

asyncio.run(main())
```

---

## Flujos de Trabajo Comunes

### Flujo 1: Monitoreo Diario de Expedientes

**Objetivo**: Revisar cambios en expedientes cada mañana.

**Pasos**:
1. **Configurar monitores** (una sola vez):
   - Ir a Monitoreo → + Nuevo Monitor
   - Agregar expedientes importantes
   - Frecuencia: Cada 1 hora
   - Horario: 08:00 - 20:00
   - Días: Lunes a Viernes

2. **Revisar notificaciones** (diario):
   - Abrir la aplicación
   - Ver notificaciones en el Dashboard
   - Hacer clic en cada notificación para ver detalles

3. **Revisar historial**:
   - Ir a Monitoreo → Historial
   - Filtrar por "Últimas 24 horas"
   - Ver todos los cambios detectados

### Flujo 2: Organización por Cliente

**Objetivo**: Organizar expedientes por cliente/empresa.

**Pasos**:
1. **Crear workspaces por cliente**:
   - Ir a Workspaces
   - Crear "Cliente A" (color azul, icono 💼)
   - Crear "Cliente B" (color rojo, icono 🏢)
   - Etc.

2. **Asignar expedientes**:
   - Ir a Expedientes
   - Para cada expediente, menú (⋮) → Agregar a Workspace
   - Seleccionar workspace del cliente

3. **Trabajar por cliente**:
   - Abrir workspace del cliente
   - Ver solo sus expedientes
   - Extraer actuaciones según necesidad

### Flujo 3: Preparación para Audiencia

**Objetivo**: Reunir información completa de un expediente para audiencia.

**Pasos**:
1. **Buscar expediente**:
   - Ir a Expedientes
   - Buscar por número o carátula
   - Abrir detalles

2. **Extraer información completa**:
   - Clic en "Extraer Actuaciones"
   - Marcar "Descargar archivos adjuntos"
   - Esperar a que termine

3. **Revisar documentación**:
   - Ver todas las actuaciones en orden cronológico
   - Descargar PDFs importantes
   - Tomar notas

4. **Crear workspace temporal**:
   - Crear workspace "Audiencia [Fecha]"
   - Agregar este expediente
   - Agregar expedientes relacionados

### Flujo 4: Reporte Semanal

**Objetivo**: Generar reporte de actividad semanal.

**Pasos**:
1. **Extraer datos actualizados**:
   ```bash
   # Vía CLI
   python -m presentation.cli.main extraer-expedientes --output reporte.json
   ```

2. **Filtrar por actividad reciente**:
   ```bash
   python -m presentation.cli.main filtrar \
       --dias-activos 7 \
       --output reporte-semanal.json
   ```

3. **Revisar en interfaz web**:
   - Ir a Expedientes
   - Aplicar filtro: "Últimos 7 días"
   - Revisar cada expediente con actividad

4. **Exportar datos**:
   - Usar API REST para obtener datos en JSON
   - Procesar con script personalizado
   - Generar PDF/Excel con reporte

### Flujo 5: Integración con Sistema Externo

**Objetivo**: Sincronizar expedientes con sistema de gestión propio.

**Pasos**:
1. **Extraer vía API**:
   ```python
   import requests

   # Login
   token = login(email, password)

   # Obtener todos los expedientes
   expedientes = get_expedientes(token)

   # Para cada expediente
   for exp in expedientes:
       # Sincronizar con tu sistema
       actualizar_en_mi_sistema(exp)
   ```

2. **Programar sincronización**:
   - Crear script de sincronización
   - Agregar a cron/scheduler
   - Ejecutar automáticamente cada N horas

3. **Monitorear errores**:
   - Revisar logs de sincronización
   - Configurar alertas por email
   - Mantener registro de fallos

---

## Resolución de Problemas

### Problema: No puedo iniciar sesión

**Síntomas**:
- Error "Credenciales incorrectas"
- Error "Email no existe"

**Soluciones**:
1. **Verificar credenciales**:
   - Asegúrate de usar el email correcto
   - La contraseña es case-sensitive
   - Verifica que no haya espacios al inicio/final

2. **Verificar que el usuario existe**:
   ```bash
   # Con Docker
   docker-compose exec backend python -c "
   from infrastructure.config.database import get_db
   from infrastructure.adapters.storage.auth_repository import AuthRepository
   db = next(get_db())
   repo = AuthRepository(db)
   users = repo.listar_usuarios()
   for u in users:
       print(f'{u.email} - {u.nombre}')
   "
   ```

3. **Recrear usuario**:
   - Registrarse nuevamente con email diferente
   - O resetear base de datos (perderás todos los datos)

### Problema: "Error al conectar con PJN"

**Síntomas**:
- Al extraer expedientes: "No se pudo conectar"
- Timeout al hacer login en PJN

**Soluciones**:
1. **Verificar credenciales PJN**:
   - Ir a Configuración → Credenciales PJN
   - Clic en "Probar Conexión"
   - Si falla, actualizar credenciales

2. **Verificar conexión a internet**:
   ```bash
   ping scw.pjn.gov.ar
   ```

3. **Verificar que el PJN esté disponible**:
   - Abrir https://scw.pjn.gov.ar en navegador
   - Intentar login manual
   - Si el sitio está caído, esperar

4. **Verificar Playwright**:
   ```bash
   # Reinstalar Playwright
   playwright install chromium
   ```

### Problema: Extracción muy lenta

**Síntomas**:
- La extracción tarda más de 10 minutos
- Progreso se queda detenido

**Soluciones**:
1. **Limitar páginas**:
   - En lugar de extraer todo, usa "max_paginas"
   - Extrae de a páginas pequeñas

2. **Verificar recursos del sistema**:
   ```bash
   # Ver uso de CPU/RAM
   top
   # o
   htop
   ```

3. **Aumentar timeout**:
   - Editar `.env`:
   ```env
   SCRAPER_TIMEOUT=120000  # 2 minutos
   SCRAPER_NAVIGATION_TIMEOUT=60000  # 1 minuto
   ```

4. **Revisar logs**:
   ```bash
   # Docker
   docker-compose logs -f backend

   # Nativo
   # Ver terminal donde corre uvicorn
   ```

### Problema: PDFs no se descargan

**Síntomas**:
- Actuaciones aparecen pero sin PDFs
- Error al descargar archivos

**Soluciones**:
1. **Verificar permisos**:
   ```bash
   # Verificar que el directorio data/ sea escribible
   ls -la data/
   chmod -R 755 data/
   ```

2. **Verificar espacio en disco**:
   ```bash
   df -h
   ```

3. **Revisar configuración**:
   - Ir a Configuración → Preferencias
   - Verificar "Descargar PDFs automáticamente"
   - Ajustar tamaño máximo de archivo

### Problema: Docker no inicia

**Síntomas**:
- `docker-compose up` falla
- Contenedores no arrancan

**Soluciones**:
1. **Verificar puerto 80 disponible**:
   ```bash
   # macOS/Linux
   sudo lsof -i :80

   # Si está ocupado, cambiar puerto en docker-compose.yml:
   ports:
     - "8080:80"  # Usar puerto 8080
   ```

2. **Verificar puerto 8000 disponible**:
   ```bash
   sudo lsof -i :8000
   ```

3. **Limpiar contenedores viejos**:
   ```bash
   docker-compose down -v
   docker system prune -a
   docker-compose up -d --build
   ```

4. **Ver logs de error**:
   ```bash
   docker-compose logs
   ```

### Problema: Base de datos corrupta

**Síntomas**:
- Error "database is locked"
- Error al guardar datos

**Soluciones**:
1. **Detener todo**:
   ```bash
   # Docker
   docker-compose down

   # Nativo
   # Detener frontend y backend (Ctrl+C)
   ```

2. **Backup de la base de datos**:
   ```bash
   cp data/sistema.db data/sistema.db.backup
   ```

3. **Eliminar archivos temporales**:
   ```bash
   rm data/sistema.db-shm
   rm data/sistema.db-wal
   ```

4. **Reiniciar**:
   ```bash
   # Docker
   docker-compose up -d

   # Nativo
   # Iniciar backend y frontend nuevamente
   ```

5. **Si persiste, recrear DB**:
   ```bash
   rm data/sistema.db
   python scripts/init_db.py
   ```
   **⚠️ ADVERTENCIA**: Esto borrará todos los usuarios y configuraciones.

### Problema: Frontend muestra página en blanco

**Síntomas**:
- Página totalmente blanca
- Sin errores visibles

**Soluciones**:
1. **Abrir consola del navegador**:
   - Chrome/Edge: F12 o Ctrl+Shift+I
   - Revisar errores en la pestaña "Console"

2. **Verificar que backend esté corriendo**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

3. **Limpiar caché del navegador**:
   - Chrome: Ctrl+Shift+Del → Limpiar caché
   - O abrir en modo incógnito

4. **Reconstruir frontend**:
   ```bash
   # Docker
   docker-compose build --no-cache frontend
   docker-compose up -d frontend

   # Nativo
   cd frontend
   rm -rf node_modules dist
   npm install
   npm run dev
   ```

### Problema: Monitores no se ejecutan

**Síntomas**:
- Monitores activos pero no detectan cambios
- Historial vacío

**Soluciones**:
1. **Verificar que el scheduler esté corriendo**:
   ```bash
   # Revisar logs del backend
   docker-compose logs -f backend | grep "scheduler"
   ```

2. **Verificar horario**:
   - Asegúrate de estar dentro del horario configurado
   - Verificar que sea un día activo

3. **Forzar chequeo manual**:
   - Ir al monitor
   - Menú (⋮) → "Chequear ahora"

4. **Reiniciar backend**:
   ```bash
   docker-compose restart backend
   ```

---

## Mejores Prácticas

### Seguridad

1. **Cambiar claves por defecto**:
   ```env
   # Generar nueva clave JWT
   JWT_SECRET_KEY=clave-super-secreta-aleatoria-larga-y-compleja

   # Generar nueva clave Fernet
   ENCRYPTION_FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   ```

2. **Usar HTTPS en producción**:
   - Configurar proxy reverso (Nginx/Apache)
   - Obtener certificado SSL (Let's Encrypt)
   - Forzar redirección HTTP → HTTPS

3. **Contraseñas fuertes**:
   - Mínimo 12 caracteres en producción
   - Incluir mayúsculas, minúsculas, números y símbolos
   - No reutilizar contraseñas

4. **Backups regulares**:
   ```bash
   # Backup diario de la base de datos
   cp data/sistema.db backups/sistema-$(date +%Y%m%d).db
   ```

5. **No compartir credenciales del PJN**:
   - Cada usuario debe tener sus propias credenciales
   - No usar cuentas compartidas

### Performance

1. **Limitar extracciones grandes**:
   - Usa `max_paginas` para extracciones parciales
   - Extrae de a poco en lugar de todo junto

2. **Configurar monitores inteligentemente**:
   - No uses frecuencias muy bajas (cada 5 min) sin necesidad
   - Usa horario laboral (08:00 - 20:00)
   - Solo días hábiles si no es necesario fines de semana

3. **Limpiar datos antiguos**:
   ```bash
   # Eliminar expedientes muy viejos si no se necesitan
   # (crear script personalizado)
   ```

4. **Usar Docker en producción**:
   - Mejor aislamiento
   - Más fácil de escalar
   - Menos problemas de dependencias

### Organización

1. **Usar workspaces**:
   - Organiza por cliente
   - O por tipo de caso (laboral, civil, penal)
   - O por urgencia (urgente, normal, archivo)

2. **Nombrar consistentemente**:
   - Workspaces: "Cliente - Tipo" (ej: "Empresa A - Laborales")
   - Monitores: descripción clara de qué se monitorea

3. **Documentar configuración**:
   - Mantén un archivo README con configuraciones específicas
   - Documenta frecuencias de monitoreo y por qué

4. **Revisar periódicamente**:
   - Limpia workspaces que no uses
   - Elimina monitores innecesarios
   - Actualiza datos viejos

### Mantenimiento

1. **Actualizar regularmente**:
   ```bash
   # Pull última versión
   git pull

   # Reconstruir
   docker-compose up -d --build
   ```

2. **Monitorear logs**:
   ```bash
   # Revisar logs de errores semanalmente
   docker-compose logs backend | grep ERROR
   ```

3. **Verificar espacio en disco**:
   ```bash
   # Revisar uso mensualmente
   du -sh data/
   ```

4. **Testing de credenciales**:
   - Probar conexión al PJN mensualmente
   - Actualizar credenciales si expiran

---

## Preguntas Frecuentes (FAQ)

### General

**P: ¿Es legal usar este sistema?**
R: Sí. El sistema extrae información que ya es accesible manualmente en el Portal Judicial Nacional. Solo automatiza el proceso. Sin embargo, debes respetar los términos de uso del PJN y solo acceder con tus credenciales legítimas.

**P: ¿Puedo usar el sistema para múltiples usuarios?**
R: Sí. El sistema soporta múltiples usuarios. Cada uno debe registrarse con su propio email y configurar sus credenciales del PJN.

**P: ¿Los datos se guardan en la nube?**
R: No. Todos los datos se almacenan localmente en tu servidor. No hay ninguna conexión a servicios externos excepto al PJN.

**P: ¿Funciona en Windows?**
R: Sí. Puedes usar Docker en Windows 10/11 con WSL2, o instalación nativa con Python.

### Instalación

**P: ¿Qué es más fácil, Docker o nativo?**
R: Docker es más fácil y recomendado. Con 4 comandos tienes todo funcionando. La instalación nativa requiere más pasos manuales.

**P: ¿Puedo instalar en un servidor remoto?**
R: Sí. Puedes instalar en cualquier servidor Linux con Docker. Recuerda configurar firewall y HTTPS.

**P: ¿Necesito conocimientos de programación?**
R: No para usar la interfaz web. Sí si quieres usar la CLI o API, pero los ejemplos están documentados.

### Uso

**P: ¿Cuánto tarda en extraer expedientes?**
R: Depende de cuántos expedientes tengas. Aproximadamente 1-2 minutos por página de 15 expedientes. Si tienes 100 expedientes (7 páginas), unos 10 minutos.

**P: ¿Puedo cancelar una extracción en progreso?**
R: En la interfaz web puedes cerrar el modal, pero el proceso seguirá en el backend. Mejor dejar que termine o reiniciar el backend.

**P: ¿Los monitores funcionan si cierro el navegador?**
R: Sí. Los monitores se ejecutan en el backend (servidor), no en el navegador. Puedes cerrar el navegador sin problema.

**P: ¿Cuántos expedientes puedo monitorear simultáneamente?**
R: No hay un límite estricto, pero recomiendodel 20-50 para evitar sobrecarga del servidor. Depende del hardware.

### Credenciales

**P: ¿Mis credenciales del PJN están seguras?**
R: Sí. Se encriptan dos veces: una en el cliente (navegador) antes de enviarlas, y otra en el servidor antes de guardarlas. Nunca se almacenan en texto plano.

**P: ¿Puedo usar credenciales de múltiples cuentas del PJN?**
R: Actualmente no. Cada usuario del sistema puede configurar una sola cuenta PJN. Si necesitas múltiples cuentas PJN, crea múltiples usuarios en el sistema.

**P: ¿Qué pasa si cambio mi contraseña del PJN?**
R: Debes actualizar las credenciales en Configuración → Credenciales PJN.

### Workspaces

**P: ¿Un expediente puede estar en múltiples workspaces?**
R: Sí. Un expediente puede pertenecer a todos los workspaces que quieras.

**P: ¿Eliminar un workspace elimina los expedientes?**
R: No. Eliminar un workspace solo elimina la agrupación. Los expedientes permanecen en el sistema.

**P: ¿Cuántos workspaces puedo crear?**
R: No hay límite. Crea los que necesites para organizarte.

### Monitoreo

**P: ¿Con qué frecuencia debo monitorear?**
R: Depende de la urgencia. Para casos normales, cada 1-6 horas es suficiente. Para casos urgentes, cada 15 minutos a 1 hora.

**P: ¿El monitoreo consume muchos recursos?**
R: Cada chequeo es similar a una extracción manual. Si tienes 10 monitores cada 1 hora, son 240 chequeos al día. Usa frecuencias razonables.

**P: ¿Puedo recibir notificaciones por email?**
R: La funcionalidad está planificada pero aún no implementada. Actualmente solo notificaciones en la app y del sistema operativo.

### Problemas Técnicos

**P: ¿Qué hago si algo no funciona?**
R:
1. Revisa la sección [Resolución de Problemas](#resolución-de-problemas)
2. Revisa los logs: `docker-compose logs`
3. Reinicia el sistema: `docker-compose restart`
4. Si persiste, reporta el issue en GitHub

**P: ¿Cómo reporto un bug?**
R: Abre un issue en GitHub con:
- Descripción del problema
- Pasos para reproducirlo
- Logs relevantes
- Versión del sistema

**P: ¿Cómo actualizo a una nueva versión?**
R:
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Performance

**P: ¿Cuánto espacio en disco necesito?**
R: Base: 2-3 GB para el sistema. Datos: depende de cuántos expedientes y PDFs. Calcula 5-10 MB por expediente con PDFs. Para 100 expedientes: ~1 GB.

**P: ¿Puedo correr esto en una Raspberry Pi?**
R: Técnicamente sí, pero será lento. Recomendamos mínimo 4 GB de RAM. Raspberry Pi 4 con 8 GB puede funcionar aceptablemente.

---

## Glosario

### Términos del Sistema

- **Expediente**: Causa judicial en el Portal Judicial Nacional
- **Actuación**: Movimiento o acción registrada en un expediente (proveídos, escritos, oficios, etc.)
- **Entrada**: Notificación recibida en la bandeja del PJN
- **Workspace**: Espacio de trabajo para organizar expedientes
- **Monitor**: Configuración de monitoreo automático para un expediente
- **Extracción**: Proceso de obtener datos del PJN mediante web scraping
- **Scraping**: Técnica para extraer datos de sitios web automáticamente

### Términos Judiciales

- **Carátula**: Nombre del expediente (partes involucradas)
- **Dependencia**: Organismo judicial (ej: CNM, CFed, ST)
- **Situación**: Estado procesal del expediente (ej: "En trámite", "A sentencia")
- **Parte**: Persona o entidad involucrada en el expediente (actor, demandado, etc.)
- **Proveído**: Resolución judicial breve
- **Sentencia**: Resolución final del juez
- **Oficio**: Comunicación oficial entre organismos

### Términos Técnicos

- **API**: Application Programming Interface (interfaz para integración)
- **CLI**: Command Line Interface (interfaz de línea de comandos)
- **JWT**: JSON Web Token (token de autenticación)
- **Docker**: Plataforma de contenedores
- **Frontend**: Interfaz de usuario (lo que ves en el navegador)
- **Backend**: Servidor (lógica y procesamiento)
- **Endpoint**: URL de la API para una acción específica
- **Token**: Credencial de autenticación
- **Healthcheck**: Verificación de que el sistema esté funcionando

---

## Soporte y Contacto

### Documentación

- **Manual de Usuario**: Este archivo
- **Docker**: [DOCKER.md](DOCKER.md)
- **README**: [README.md](README.md)
- **API Docs**: http://localhost:8000/docs

### Reportar Problemas

**GitHub Issues**: https://github.com/tu-usuario/sistema-pjn-v6/issues

Al reportar un issue, incluye:
1. Descripción detallada del problema
2. Pasos para reproducirlo
3. Logs relevantes
4. Versión del sistema
5. Sistema operativo

### Solicitar Funcionalidades

Abre un "Feature Request" en GitHub Issues describiendo:
- Qué funcionalidad deseas
- Por qué sería útil
- Cómo la imaginas funcionando

### Contribuir

¿Quieres contribuir código?
1. Fork el repositorio
2. Crea una rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Haz commits siguiendo [Conventional Commits](https://www.conventionalcommits.org/)
4. Push y abre un Pull Request

### Contacto

- **Email**: dev@sistemapjn.com
- **Discord**: [Servidor de la comunidad](#) *(próximamente)*

---

## Agradecimientos

Este sistema fue desarrollado con el objetivo de facilitar el trabajo de profesionales del derecho y estudiantes, automatizando tareas repetitivas y permitiendo enfocarse en lo importante: el análisis y la estrategia legal.

**Desarrollado con**:
- Python, FastAPI, Playwright
- React, TypeScript, Tailwind CSS
- Docker, SQLite
- Y mucho ☕

---

**Última actualización**: 2025-11-05
**Versión del Manual**: 1.0.0
**Versión del Sistema**: 6.0.0

---

¿Encontraste útil este manual? ⭐ Deja una estrella en GitHub

¿Tienes sugerencias? 💡 Abre un issue

¿Quieres contribuir? 🤝 Envía un pull request

---

**Hecho con ❤️ para la comunidad legal argentina**
