# Documentación del Sistema PJN v6

**Índice completo de toda la documentación disponible**

---

## 📖 Documentación de Usuario

### 🚀 Para Empezar

**[Guía de Inicio Rápido](../INICIO_RAPIDO.md)**
- 5 minutos para tener el sistema funcionando
- Instalación con Docker (la más fácil)
- Primera configuración
- Primera extracción de expedientes
- Comandos básicos más usados
- Solución a problemas comunes

**Recomendado para**: Nuevos usuarios, instalación rápida

---

**[Manual de Usuario Completo](../MANUAL_USUARIO.md)** - **93 páginas**
- Guía exhaustiva de todas las funcionalidades
- Instalación (Docker y nativa)
- Configuración inicial detallada
- Guía completa de cada módulo:
  - Autenticación
  - Dashboard
  - Expedientes
  - Workspaces
  - Monitoreo
  - Configuración de usuario
- Guía de CLI (línea de comandos)
- Guía de API REST
- Flujos de trabajo comunes
- Resolución de problemas (troubleshooting)
- Mejores prácticas
- FAQ (Preguntas Frecuentes)
- Glosario de términos

**Recomendado para**: Todos los usuarios, referencia completa

---

### 🐳 Deployment

**[Guía de Docker](../DOCKER.md)** - **608 líneas**
- Requisitos del sistema
- Instalación de Docker en diferentes OS
- Inicio rápido con Docker Compose
- Arquitectura de contenedores
- Configuración de variables de entorno
- Comandos útiles de Docker
- Troubleshooting específico de Docker
- Mejores prácticas de producción
- Resource limits y monitoreo
- Backups y actualización
- Logs centralizados

**Recomendado para**: Deployment en producción, administradores de sistemas

---

## 💻 Documentación Técnica

### Backend

**[README Principal](../README.md)**
- Descripción general del proyecto
- Arquitectura Clean Architecture
- Estado del proyecto (100% completo)
- Instalación del backend
- Estructura de directorios
- Principios de diseño (SOLID, DDD)
- Testing
- Roadmap

**Recomendado para**: Desarrolladores, arquitectura del sistema

---

### Frontend

**[Plan de Web UI](WEB_UI_PLAN.md)** - **Documento maestro del frontend**
- Las 12 fases de desarrollo (100% completadas)
- Stack tecnológico completo
- Resumen de todos los componentes implementados
- Tiempo de desarrollo: 33 horas
- 200+ archivos creados
- 15,000+ líneas de código
- Documentación de testing y Docker

**Recomendado para**: Desarrolladores frontend, overview completo

---

**[Frontend README](../frontend/README.md)**
- Stack tecnológico
- Instalación y configuración
- Comandos de desarrollo
- Estructura del proyecto
- Características implementadas
- Variables de entorno
- API endpoints consumidos

**Recomendado para**: Desarrolladores frontend, quick reference

---

**[UX Improvements](../frontend/UX_IMPROVEMENTS.md)** - **350+ líneas**
- Guía completa de mejoras de UX
- Loading states (spinners, skeletons)
- Error handling (error boundaries)
- Empty states
- Toast notifications
- Animaciones CSS
- Patrones de diseño
- Ejemplos de implementación

**Recomendado para**: Diseñadores, desarrolladores frontend

---

**[Testing Guide](../frontend/TESTING.md)** - **500+ líneas**
- Configuración de Vitest
- Setup global de tests
- Utilities y factories
- Tests de componentes UI
- Tests de componentes comunes
- Tests de stores (Zustand)
- Tests de librerías
- Tests de integración
- Cobertura actual: 58 tests implementados

**Recomendado para**: Desarrolladores, QA, testing

---

## 🔧 Documentación de Desarrollo

### Testing

**[Integration Tests - Scraping](../tests/integration/infrastructure/adapters/scraping/README.md)**
- Tests de integración del módulo de scraping
- Requisitos y configuración
- Cómo ejecutar los tests
- Tests disponibles:
  - Inicialización del scraper
  - Extracción de expedientes
  - Extracción de entradas
  - Extracción de actuaciones
- Estructura de los tests

**Recomendado para**: Desarrolladores, testing de integración

---

## 📊 Diagramas y Arquitectura

### Arquitectura General

```
Sistema_v6/
├── core/                    # Domain Layer (entidades, value objects)
├── application/             # Application Layer (use cases, ports)
├── infrastructure/          # Infrastructure Layer (adapters, scraping)
├── presentation/            # Presentation Layer (CLI, API, MCP)
├── frontend/                # Web UI (React + TypeScript)
├── tests/                   # Tests unitarios e integración
└── docs/                    # Documentación
```

### Stack Completo

**Backend**:
- Python 3.11
- FastAPI 0.104+
- Playwright 1.50 (scraping)
- SQLAlchemy 2.0 (ORM)
- SQLite (base de datos)
- Pydantic (validación)
- APScheduler (tareas programadas)

**Frontend**:
- React 18.3
- TypeScript 5
- Vite 5 (build tool)
- Tailwind CSS 3 + shadcn/ui
- Zustand 4 (state management)
- React Query 5 (data fetching)
- React Router v6
- React Hook Form + Zod
- Axios (HTTP client)

**DevOps**:
- Docker + Docker Compose
- Nginx (reverse proxy)
- Vitest (testing)

---

## 📝 Documentos por Categoría

### Para Usuarios Finales

1. [Guía de Inicio Rápido](../INICIO_RAPIDO.md) - **Empieza aquí**
2. [Manual de Usuario Completo](../MANUAL_USUARIO.md) - **Referencia completa**
3. [Guía de Docker](../DOCKER.md) - **Para instalación/deployment**

### Para Desarrolladores

4. [README Principal](../README.md) - **Overview del proyecto**
5. [Plan de Web UI](WEB_UI_PLAN.md) - **Desarrollo del frontend**
6. [Frontend README](../frontend/README.md) - **Setup frontend**
7. [UX Improvements](../frontend/UX_IMPROVEMENTS.md) - **Patrones UX**
8. [Testing Guide](../frontend/TESTING.md) - **Guía de testing**

### Para Administradores de Sistemas

9. [Guía de Docker](../DOCKER.md) - **Deployment**
10. [Manual de Usuario - Troubleshooting](../MANUAL_USUARIO.md#resolución-de-problemas) - **Solución de problemas**
11. [Manual de Usuario - Mejores Prácticas](../MANUAL_USUARIO.md#mejores-prácticas) - **Configuración óptima**

---

## 🎯 Guía de Lectura Recomendada

### Soy un usuario nuevo
```
1. Guía de Inicio Rápido (5 min)
2. Manual de Usuario - Primer Uso (10 min)
3. Manual de Usuario - Módulo Expedientes (15 min)
4. Manual de Usuario - Resto de módulos (según necesidad)
```

### Soy desarrollador frontend
```
1. README Principal (overview)
2. Frontend README (setup)
3. Plan de Web UI (arquitectura completa)
4. UX Improvements (patrones)
5. Testing Guide (testing)
```

### Soy desarrollador backend
```
1. README Principal (arquitectura)
2. Código en core/, application/, infrastructure/
3. Tests de integración
4. API Docs (http://localhost:8000/docs)
```

### Soy administrador de sistemas
```
1. Guía de Docker (instalación y comandos)
2. Manual de Usuario - Configuración Inicial
3. Manual de Usuario - Troubleshooting
4. Manual de Usuario - Mejores Prácticas
```

---

## 📏 Estadísticas de Documentación

| Documento | Líneas | Páginas aprox. | Audiencia |
|-----------|--------|----------------|-----------|
| Manual de Usuario | ~1,200 | 93 | Usuarios finales |
| Guía de Inicio Rápido | ~300 | 12 | Nuevos usuarios |
| Guía de Docker | 608 | 26 | Administradores |
| Plan de Web UI | ~800 | 40 | Desarrolladores |
| UX Improvements | ~350 | 15 | Diseñadores/Devs |
| Testing Guide | ~500 | 22 | Desarrolladores |
| **TOTAL** | **~3,800** | **~208** | - |

---

## 🔗 Enlaces Rápidos

### Documentación Online
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Repositorio
- **GitHub**: https://github.com/tu-usuario/sistema-pjn-v6
- **Issues**: https://github.com/tu-usuario/sistema-pjn-v6/issues
- **Discussions**: https://github.com/tu-usuario/sistema-pjn-v6/discussions

### Referencias Externas
- [Portal Judicial Nacional](https://scw.pjn.gov.ar/)
- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación React](https://react.dev/)
- [Documentación Docker](https://docs.docker.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 🆘 ¿Necesitas Ayuda?

### Busco información sobre...

**Instalación**:
- [Guía de Inicio Rápido](../INICIO_RAPIDO.md)
- [Manual de Usuario - Instalación](../MANUAL_USUARIO.md#instalación)
- [Guía de Docker](../DOCKER.md)

**Uso del sistema**:
- [Manual de Usuario - Guía de Uso](../MANUAL_USUARIO.md#guía-de-uso---interfaz-web)

**Problemas técnicos**:
- [Manual de Usuario - Resolución de Problemas](../MANUAL_USUARIO.md#resolución-de-problemas)
- [Manual de Usuario - FAQ](../MANUAL_USUARIO.md#preguntas-frecuentes-faq)
- [Guía de Docker - Troubleshooting](../DOCKER.md#troubleshooting)

**Desarrollo**:
- [README Principal](../README.md)
- [Frontend README](../frontend/README.md)
- [Testing Guide](../frontend/TESTING.md)

**API Integration**:
- [Manual de Usuario - Guía de Uso API REST](../MANUAL_USUARIO.md#guía-de-uso---api-rest)
- API Docs: http://localhost:8000/docs

---

## 📅 Última Actualización

- **Fecha**: 2025-11-05
- **Versión del Sistema**: 6.0.0
- **Documentación**: Completa y actualizada

---

## ✨ Contribuir a la Documentación

¿Encontraste un error o falta información?

1. Abre un issue en GitHub
2. O envía un Pull Request con mejoras
3. Sigue el estilo de Markdown existente
4. Actualiza este índice si agregas nuevos documentos

---

**Hecho con ❤️ para la comunidad legal argentina**
