# Docker - Sistema PJN v6

**Fecha**: 2025-11-05
**Versión**: 1.0.0

Guía completa para ejecutar Sistema PJN v6 con Docker y Docker Compose.

---

## 📋 Tabla de Contenidos

1. [Requisitos](#requisitos)
2. [Inicio Rápido](#inicio-rápido)
3. [Arquitectura](#arquitectura)
4. [Configuración](#configuración)
5. [Comandos](#comandos)
6. [Troubleshooting](#troubleshooting)
7. [Producción](#producción)

---

## 🔧 Requisitos

### Software Necesario

- **Docker** 20.10+
- **Docker Compose** 2.0+

### Instalación de Docker

#### macOS
```bash
# Usando Homebrew
brew install --cask docker

# O descargar desde
# https://www.docker.com/products/docker-desktop
```

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose
sudo apt-get install docker-compose-plugin
```

#### Windows
Descargar e instalar Docker Desktop desde:
https://www.docker.com/products/docker-desktop

### Verificar Instalación

```bash
docker --version
docker-compose --version
```

---

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```bash
# .env
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ENCRYPTION_FERNET_KEY=gZxdkgEN2wyl4L3A77Xkrwjzk_uRq6Orz8txZmbdXG4=
```

**⚠️ IMPORTANTE**: Cambia estas claves en producción. Para generar una nueva clave Fernet:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Iniciar los Servicios

```bash
# Construir y levantar todos los servicios
docker-compose up --build

# O en modo detached (background)
docker-compose up -d --build
```

### 3. Acceder a la Aplicación

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123456
```

---

## 🏗️ Arquitectura

### Servicios

```
┌─────────────────────────────────────────┐
│           Docker Network                │
│     (sistema-pjn-network)              │
│                                         │
│  ┌──────────────┐   ┌──────────────┐  │
│  │   Frontend   │   │   Backend    │  │
│  │              │   │              │  │
│  │  Nginx:80    │──▶│  Python:8000 │  │
│  │  React SPA   │   │  FastAPI     │  │
│  └──────────────┘   │  Playwright  │  │
│         │           │  SQLite      │  │
│         │           └──────────────┘  │
│         │                  │          │
│         ▼                  ▼          │
│    User Browser        data/ volume   │
└─────────────────────────────────────────┘
```

### Contenedores

#### Backend
- **Imagen Base**: `python:3.11-slim`
- **Puerto**: 8000
- **Servicios**:
  - FastAPI application
  - Playwright (Chromium)
  - SQLite database
- **Volumen**: `./data` montado en `/app/data`

#### Frontend
- **Build Stage**: `node:20-alpine` (compilación)
- **Runtime Stage**: `nginx:alpine` (servir archivos)
- **Puerto**: 80
- **Proxy**: Redirige `/api/*` al backend

---

## ⚙️ Configuración

### Variables de Entorno

#### Backend (docker-compose.yml)

```yaml
environment:
  # Application
  - ENVIRONMENT=production
  - LOG_LEVEL=info

  # Security
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - ENCRYPTION_FERNET_KEY=${ENCRYPTION_FERNET_KEY}

  # Database
  - DATABASE_URL=sqlite:///./data/sistema.db

  # CORS
  - CORS_ORIGINS=http://localhost,http://localhost:80
```

### Volúmenes

#### Base de Datos Persistente

```yaml
volumes:
  - ./data:/app/data
```

La base de datos SQLite se persiste en el host en `./data/sistema.db`.

#### Desarrollo (Código en Vivo)

Para desarrollo, descomenta en `docker-compose.yml`:

```yaml
volumes:
  - ./data:/app/data
  - ./:/app  # ← Descomentar para desarrollo
```

Luego recarga con:
```bash
docker-compose restart backend
```

---

## 📝 Comandos

### Construcción

```bash
# Construir solo backend
docker-compose build backend

# Construir solo frontend
docker-compose build frontend

# Construir todo sin cache
docker-compose build --no-cache
```

### Inicio y Parada

```bash
# Iniciar todos los servicios
docker-compose up

# Iniciar en background
docker-compose up -d

# Detener servicios
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar contenedores + volúmenes
docker-compose down -v
```

### Logs

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs backend

# Ver logs solo del frontend
docker-compose logs frontend

# Últimas 100 líneas
docker-compose logs --tail=100
```

### Estado de Servicios

```bash
# Ver estado de contenedores
docker-compose ps

# Ver procesos dentro de contenedores
docker-compose top
```

### Ejecutar Comandos

```bash
# Abrir shell en backend
docker-compose exec backend bash

# Ejecutar comando Python
docker-compose exec backend python -c "print('Hello')"

# Ejecutar script
docker-compose exec backend python scripts/init_db.py

# Abrir shell en frontend (Nginx)
docker-compose exec frontend sh
```

### Limpiar

```bash
# Limpiar contenedores detenidos
docker container prune

# Limpiar imágenes sin usar
docker image prune

# Limpiar todo (contenedores, imágenes, volúmenes, redes)
docker system prune -a --volumes
```

---

## 🐛 Troubleshooting

### Puerto 80 ya en uso

**Problema**: "port is already allocated"

**Solución 1**: Cambiar puerto en `docker-compose.yml`:
```yaml
ports:
  - "8080:80"  # Usar puerto 8080 en el host
```

**Solución 2**: Detener servicio que usa el puerto:
```bash
# macOS
sudo lsof -i :80
sudo kill -9 <PID>

# Linux
sudo netstat -tulpn | grep :80
sudo kill -9 <PID>
```

### Base de datos corrupta

**Problema**: "database is locked" o errores de SQLite

**Solución**:
```bash
# Detener servicios
docker-compose down

# Eliminar base de datos
rm data/sistema.db data/sistema.db-shm data/sistema.db-wal

# Reiniciar servicios (se recrea DB)
docker-compose up -d
```

### Frontend no carga

**Problema**: Página en blanco o error 404

**Solución**:
```bash
# Reconstruir frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Ver logs
docker-compose logs frontend
```

### Backend no responde

**Problema**: API no accesible en http://localhost:8000

**Solución**:
```bash
# Ver logs del backend
docker-compose logs backend

# Verificar que está corriendo
docker-compose ps

# Reiniciar backend
docker-compose restart backend

# Ver healthcheck
docker inspect sistema-pjn-backend | grep Health -A 10
```

### Playwright falla

**Problema**: "Executable doesn't exist at /root/.cache/ms-playwright/..."

**Solución**:
```bash
# Reconstruir imagen sin cache
docker-compose build --no-cache backend

# O ejecutar manualmente
docker-compose exec backend playwright install --with-deps chromium
```

### Cambios en código no se reflejan

**Problema**: Código actualizado pero container usa versión antigua

**Solución**:
```bash
# Reconstruir e iniciar
docker-compose up -d --build

# O forzar recreación
docker-compose up -d --force-recreate
```

---

## 🚢 Producción

### Mejores Prácticas

#### 1. Usar Secretos

**NO** hardcodear secretos en `docker-compose.yml`.

**Usar archivo .env**:
```bash
# .env (NO committear a Git!)
JWT_SECRET_KEY=<clave-aleatoria-muy-segura>
ENCRYPTION_FERNET_KEY=<clave-fernet-generada>
```

O usar Docker Secrets (Docker Swarm):
```yaml
secrets:
  jwt_secret:
    external: true
```

#### 2. Healthchecks

Ya configurados en `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/v1/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

#### 3. Resource Limits

Agregar en `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

#### 4. Logging

Configurar driver de logging:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 5. Network Security

Exponer solo puertos necesarios:

```yaml
ports:
  - "127.0.0.1:8000:8000"  # Solo localhost
```

#### 6. Backups

Hacer backup de la base de datos regularmente:

```bash
# Backup manual
docker-compose exec backend python -c "import shutil; shutil.copy('/app/data/sistema.db', '/app/data/backup-$(date +%Y%m%d).db')"

# O desde el host
cp data/sistema.db data/backup-$(date +%Y%m%d).db
```

### Deployment

#### Docker Swarm

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml sistema-pjn
```

#### Kubernetes

Ver `k8s/` (no incluido, requiere configuración adicional).

---

## 📊 Monitoreo

### Ver Recursos

```bash
# Stats de contenedores
docker stats

# Uso específico
docker stats sistema-pjn-backend sistema-pjn-frontend
```

### Logs Centralizados

#### Opción 1: Docker Logging Driver

```yaml
logging:
  driver: "syslog"
  options:
    syslog-address: "tcp://192.168.0.42:123"
```

#### Opción 2: ELK Stack

Integrar con Elasticsearch, Logstash, Kibana (no incluido).

---

## 🔄 Actualización

### Actualizar Aplicación

```bash
# 1. Pull cambios del código
git pull

# 2. Reconstruir imágenes
docker-compose build

# 3. Recrear contenedores
docker-compose up -d --force-recreate

# 4. Verificar logs
docker-compose logs -f
```

### Rollback

```bash
# 1. Detener servicios actuales
docker-compose down

# 2. Cambiar a versión anterior del código
git checkout <commit-hash>

# 3. Reconstruir y levantar
docker-compose up -d --build
```

---

## 📚 Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## 🆘 Soporte

### Comandos de Diagnóstico

```bash
# Información del sistema Docker
docker info

# Versiones
docker version
docker-compose version

# Inspeccionar contenedor
docker inspect sistema-pjn-backend

# Ver redes
docker network ls
docker network inspect sistema-pjn-network

# Ver volúmenes
docker volume ls
docker volume inspect <volume-name>
```

### Logs Detallados

```bash
# Logs con timestamps
docker-compose logs -t

# Logs desde una fecha
docker-compose logs --since="2024-01-01T00:00:00"

# Logs hasta una fecha
docker-compose logs --until="2024-01-02T00:00:00"
```

---

**Última actualización**: 2025-11-05
**Mantenedor**: Sistema PJN v6 Team
