# Plan de Optimización Sistema SintaXis v6

**Fecha de creación:** 2025-11-18
**Versión:** 1.0
**Sistema:** SintaXis v6 - Gestión de Expedientes PJN
**Stack:** FastAPI (Backend) + React/TypeScript (Frontend)

---

## Resumen Ejecutivo

Este documento detalla el plan completo de optimización y mejoras para el sistema SintaXis v6, basado en una revisión exhaustiva del código backend y frontend. Los hallazgos se organizan por severidad y área, con acciones específicas para cada issue identificado.

**Total de Issues Identificados:** 35+
**Severidad Crítica:** 7 issues
**Severidad Alta:** 8 issues
**Severidad Media:** 15+ issues
**Coverage de Tests Actual:** <40%
**Meta de Coverage:** 80%

---

## Índice

1. [Fase 1: Seguridad Crítica](#fase-1-seguridad-crítica)
2. [Fase 2: Rendimiento Backend](#fase-2-rendimiento-backend)
3. [Fase 3: Optimización Frontend](#fase-3-optimización-frontend)
4. [Fase 4: Calidad de Código](#fase-4-calidad-de-código)
5. [Fase 5: Testing](#fase-5-testing)
6. [Fase 6: Logging y Monitoreo](#fase-6-logging-y-monitoreo)
7. [Fase 7: Infraestructura](#fase-7-infraestructura)
8. [Fase 8: Documentación](#fase-8-documentación)
9. [Checklist Pre-Deployment](#checklist-pre-deployment)
10. [Métricas de Éxito](#métricas-de-éxito)

---

## Fase 1: Seguridad Crítica

**Prioridad:** 🔴 CRÍTICA - Resolver antes de producción
**Estimación:** Alta complejidad
**Dependencias:** Ninguna

### SEC-001: Configurar CORS con Orígenes Específicos

**Archivo:** `app.py:29`
**Issue:** CORS configurado con wildcard (*), permite cualquier origen

**Acciones:**
- [ ] Agregar variable de entorno `ALLOWED_ORIGINS` en `.env.example`
- [ ] Modificar `app.py` para leer lista de orígenes desde `settings.cors.allowed_origins`
- [ ] Actualizar `infrastructure/config/settings.py` para parsear lista de orígenes
- [ ] En desarrollo: usar `["http://localhost:5173", "http://localhost:3000"]`
- [ ] En producción: usar solo dominios verificados

**Código sugerido:**
```python
# app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,  # Lista específica
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Tests:**
- [ ] Test que verifique que solo orígenes permitidos pueden acceder
- [ ] Test que rechace requests de orígenes no autorizados

---

### SEC-002: JWT Secret Key Obligatorio

**Archivo:** `infrastructure/config/settings.py:301`
**Issue:** Secret key con valor por defecto débil

**Acciones:**
- [ ] Modificar `JWTSettings` para que `secret_key` sea obligatorio en producción
- [ ] Agregar validación que falle si se usa el valor por defecto en producción
- [ ] Generar secret key seguro con: `openssl rand -hex 32`
- [ ] Documentar en `.env.example` con placeholder

**Código sugerido:**
```python
class JWTSettings(BaseModel):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @field_validator('secret_key')
    def validate_secret_key(cls, v):
        default_key = "your-secret-key-change-this-in-production-use-env-var"
        if v == default_key and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Must set JWT_SECRET_KEY in production")
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
```

**Tests:**
- [ ] Test que falle si se usa secret key por defecto en producción
- [ ] Test que acepte secret key válido

---

### SEC-003: Remover .env del Repositorio

**Archivo:** `.env` (raíz)
**Issue:** Archivo con credenciales potencialmente versionado

**Acciones:**
- [ ] Verificar si `.env` está en `.gitignore`
- [ ] Si no está, agregarlo: `echo ".env" >> .gitignore`
- [ ] Crear `.env.example` completo con todos los campos necesarios
- [ ] Remover `.env` del historial si fue commiteado: `git filter-branch` o `BFG Repo-Cleaner`
- [ ] Documentar proceso de setup en README

**Contenido `.env.example`:**
```bash
# Entorno
ENVIRONMENT=development

# Base de datos
DATABASE_URL=sqlite:///./sintaxis.db

# Seguridad
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32
FERNET_KEY=generate-with-python-cryptography-fernet-generate-key

# PJN (opcional - preferir credenciales por usuario)
PJN_USERNAME=
PJN_PASSWORD=

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000

# Redis (para sesiones)
REDIS_URL=redis://localhost:6379/0
```

**Tests:**
- [ ] Verificar que `.env` no está en git
- [ ] Verificar que `.env.example` existe y está completo

---

### SEC-004: Fernet Key Obligatorio en Producción

**Archivo:** `infrastructure/security/encryption.py:16-23`
**Issue:** Fernet key se genera automáticamente sin persistencia

**Acciones:**
- [ ] Modificar `get_encryption_key()` para fallar si no hay key en producción
- [ ] Crear script de setup: `scripts/generate_encryption_key.py`
- [ ] Documentar proceso de generación en README
- [ ] Agregar validación en startup de la aplicación

**Código sugerido:**
```python
def get_encryption_key() -> bytes:
    settings = get_settings()

    if settings.encryption.fernet_key:
        return settings.encryption.fernet_key.encode()

    # En producción, fallar si no hay key
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError(
            "FERNET_KEY must be set in production. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    # Solo en desarrollo, generar y advertir
    logger.warning("Generating temporary Fernet key for development")
    return Fernet.generate_key()
```

**Script de generación:**
```python
# scripts/generate_encryption_key.py
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print(f"FERNET_KEY={key.decode()}")
    print("\nAdd this to your .env file")
```

**Tests:**
- [ ] Test que falle sin key en producción
- [ ] Test que genere key temporal en desarrollo

---

### SEC-005: Implementar Verificación de Permisos Admin

**Archivo:** `presentation/api/rest/routers/admin.py:70-79`
**Issue:** Verificación de superuser retorna siempre True (TODO)

**Acciones:**
- [ ] Agregar campo `is_admin: bool` o `role: str` al modelo User
- [ ] Crear migración de BD para agregar el campo
- [ ] Implementar función `get_current_admin_user()` similar a `get_current_user()`
- [ ] Reemplazar `verify_superuser()` con dependency injection
- [ ] Actualizar todos los endpoints admin para usar el nuevo dependency

**Código sugerido:**
```python
# infrastructure/security/jwt.py
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica que el usuario actual sea administrador."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return current_user

# routers/admin.py
@router.post("/reset-sistema")
async def reset_sistema(
    admin_user: User = Depends(get_current_admin_user),  # ← Verificación real
    repo: ExpedienteRepository = Depends(get_expediente_repo)
):
    # ... lógica del endpoint
```

**Migración BD:**
```python
# alembic/versions/xxx_add_is_admin.py
def upgrade():
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), default=False))
    # Hacer admin al primer usuario o usuario específico
    op.execute("UPDATE users SET is_admin = true WHERE username = 'admin'")

def downgrade():
    op.drop_column('users', 'is_admin')
```

**Tests:**
- [ ] Test que admin puede acceder a endpoints protegidos
- [ ] Test que usuario normal recibe 403 en endpoints admin
- [ ] Test que usuario sin autenticar recibe 401

---

### SEC-007: Implementar Rate Limiting

**Archivo:** `presentation/api/rest/routers/auth.py`
**Issue:** No hay protección contra fuerza bruta en login

**Acciones:**
- [ ] Instalar `slowapi`: `pip install slowapi`
- [ ] Configurar limiter en `app.py`
- [ ] Aplicar límites a endpoints de autenticación
- [ ] Configurar límites diferentes para desarrollo/producción
- [ ] Agregar header `X-RateLimit-*` en respuestas

**Código sugerido:**
```python
# app.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# routers/auth.py
from app import limiter

@router.post("/login")
@limiter.limit("5/minute")  # 5 intentos por minuto por IP
async def login(
    request: Request,  # Necesario para slowapi
    credentials: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    # ... lógica de login
```

**Configuración por entorno:**
```python
# settings.py
class SecuritySettings(BaseModel):
    login_rate_limit: str = "5/minute"  # Producción
    # En desarrollo: "100/minute"
```

**Tests:**
- [ ] Test que permita 5 requests y bloquee el 6to
- [ ] Test que reset después de 1 minuto
- [ ] Test que retorne headers de rate limit correctos

---

### SEC-006: Eliminar Prints de Secretos

**Archivos:** Múltiples (`encryption.py:22`, etc.)
**Issue:** Secretos se imprimen en stdout/logs

**Acciones:**
- [ ] Buscar todos los `print()` statements en código de producción
- [ ] Reemplazar con logging apropiado
- [ ] Configurar niveles de log (INFO, WARNING, ERROR)
- [ ] Nunca loggear valores de secretos, solo advertencias genéricas
- [ ] Configurar formatter de logs para incluir timestamp, level, module

**Código sugerido:**
```python
# Antes
print(f"WARNING: Fernet key generada automáticamente: {_fernet_key.decode()}")

# Después
logger.warning("Fernet key generada automáticamente para desarrollo. Configure FERNET_KEY en producción.")
```

**Configurar logging:**
```python
# infrastructure/config/logging.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log')
        ]
    )

    # Reducir verbosidad de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
```

**Tests:**
- [ ] Test que verifique que no hay prints en código de producción
- [ ] Test que verifique formato de logs

---

### SEC-008: Usar Credenciales por Usuario

**Archivo:** `presentation/api/rest/routers/extraccion_masiva.py:98-109`
**Issue:** Sistema usa credenciales globales en lugar de por usuario

**Acciones:**
- [ ] Modificar `_get_credentials()` para recibir usuario autenticado
- [ ] Obtener credenciales desde `current_user.pjn_username` y `pjn_password`
- [ ] Desencriptar usando `decrypt_password()`
- [ ] Remover fallback a variables de entorno globales
- [ ] Validar que usuario tenga credenciales configuradas

**Código sugerido:**
```python
async def _get_credentials(current_user: User) -> tuple[str, str]:
    """Obtiene credenciales PJN del usuario autenticado."""
    if not current_user.pjn_username or not current_user.pjn_password_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe configurar sus credenciales PJN en el perfil"
        )

    username = current_user.pjn_username
    password = decrypt_password(current_user.pjn_password_encrypted)

    return username, password

@router.post("/iniciar")
async def iniciar_extraccion(
    request: IniciarExtraccionRequest,
    current_user: User = Depends(get_current_user),
    repo: ExpedienteRepository = Depends(get_expediente_repo)
):
    username, password = await _get_credentials(current_user)
    # ... resto de lógica
```

**Tests:**
- [ ] Test que falle si usuario no tiene credenciales
- [ ] Test que use credenciales del usuario autenticado
- [ ] Test que desencripte correctamente

---

## Fase 2: Rendimiento Backend

**Prioridad:** 🟠 ALTA
**Estimación:** Media complejidad
**Dependencias:** Ninguna

### PERF-001: Migrar Sesiones a Redis

**Archivo:** `presentation/api/rest/routers/extraccion_masiva.py:94-95`
**Issue:** Sesiones en memoria, no persisten y no escalan

**Acciones:**
- [ ] Instalar `redis` y `aioredis`: `pip install redis aioredis`
- [ ] Agregar configuración Redis en settings
- [ ] Crear `infrastructure/cache/redis_client.py`
- [ ] Crear `infrastructure/cache/session_store.py` con interfaz
- [ ] Migrar `_sesiones` dict a SessionStore
- [ ] Agregar TTL automático (ej. 24 horas)
- [ ] Serializar con `json.dumps()` para almacenar en Redis

**Código sugerido:**
```python
# infrastructure/cache/session_store.py
import json
import aioredis
from typing import Optional
from datetime import timedelta

class SessionStore:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = timedelta(hours=24)

    async def set(self, session_id: str, session_data: dict):
        """Guarda sesión con TTL."""
        await self.redis.setex(
            f"session:{session_id}",
            self.ttl,
            json.dumps(session_data)
        )

    async def get(self, session_id: str) -> Optional[dict]:
        """Obtiene sesión."""
        data = await self.redis.get(f"session:{session_id}")
        return json.loads(data) if data else None

    async def delete(self, session_id: str):
        """Elimina sesión."""
        await self.redis.delete(f"session:{session_id}")

    async def exists(self, session_id: str) -> bool:
        """Verifica si sesión existe."""
        return await self.redis.exists(f"session:{session_id}")

# DI container
async def get_session_store() -> SessionStore:
    settings = get_settings()
    return SessionStore(settings.redis_url)

# routers/extraccion_masiva.py
@router.post("/iniciar")
async def iniciar_extraccion(
    request: IniciarExtraccionRequest,
    session_store: SessionStore = Depends(get_session_store)
):
    session_id = str(uuid.uuid4())
    session_data = {
        "id": session_id,
        "estado": "iniciando",
        "total_expedientes": len(request.expedientes),
        # ... más datos
    }
    await session_store.set(session_id, session_data)
```

**Docker Compose para desarrollo:**
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

**Tests:**
- [ ] Test que guarde sesión en Redis
- [ ] Test que recupere sesión correctamente
- [ ] Test que sesión expire después de TTL
- [ ] Test que funcione con múltiples workers

---

### PERF-002: Implementar Paginación

**Archivo:** `presentation/api/rest/routers/expedientes.py:165-223`
**Issue:** Endpoint retorna todos los expedientes sin límite

**Acciones:**
- [ ] Agregar parámetros `skip: int = 0` y `limit: int = 100` a endpoint
- [ ] Modificar `repo.obtener_todos()` para aceptar paginación
- [ ] Implementar paginación en SQLAlchemy: `query.offset(skip).limit(limit)`
- [ ] Agregar conteo total: `query.count()`
- [ ] Retornar metadata de paginación en respuesta
- [ ] Actualizar frontend para manejar paginación

**Código sugerido:**
```python
# Modelo de respuesta
class PaginationMetadata(BaseModel):
    total: int
    skip: int
    limit: int
    has_more: bool

class ListarExpedientesResponse(BaseModel):
    success: bool
    expedientes: list[ExpedienteResponse]
    pagination: PaginationMetadata
    error: Optional[str] = None

# Endpoint
@router.get("", response_model=ListarExpedientesResponse)
async def listar_expedientes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=500, description="Máximo de registros a retornar"),
    activos_solo: bool = False,
    dias: int = 30,
    repo: ExpedienteRepository = Depends(get_expediente_repo)
):
    # Obtener total
    total = await repo.contar_todos()

    # Obtener página
    expedientes = await repo.obtener_todos(
        skip=skip,
        limit=limit,
        activos_solo=activos_solo,
        dias=dias
    )

    return ListarExpedientesResponse(
        success=True,
        expedientes=[...],
        pagination=PaginationMetadata(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total
        )
    )

# Repository
async def obtener_todos(
    self,
    skip: int = 0,
    limit: int = 100,
    activos_solo: bool = False,
    dias: int = 30
) -> list[Expediente]:
    query = self.session.query(ExpedienteModel)

    if activos_solo:
        query = query.filter(ExpedienteModel.activo == True)

    # ... más filtros

    return query.offset(skip).limit(limit).all()

async def contar_todos(self) -> int:
    """Retorna total de expedientes."""
    return self.session.query(ExpedienteModel).count()
```

**Frontend:**
```typescript
// Actualizar API call
const fetchExpedientes = async (page: number = 1, limit: number = 100) => {
  const skip = (page - 1) * limit;
  const response = await api.get(`/expedientes?skip=${skip}&limit=${limit}`);
  return response.data;
};
```

**Tests:**
- [ ] Test que retorne primera página correctamente
- [ ] Test que respete límite máximo
- [ ] Test que skip funcione correctamente
- [ ] Test metadata de paginación

---

### PERF-003: Agregar Índices de Base de Datos

**Archivo:** `infrastructure/persistence/database/models.py`
**Issue:** Sin índices en campos de búsqueda frecuente

**Acciones:**
- [ ] Identificar queries más frecuentes
- [ ] Agregar índices en: `username`, `created_at`, `numero_expediente`
- [ ] Crear índice compuesto para: `(username, created_at)`
- [ ] Usar SQLAlchemy Index() en modelos
- [ ] Crear migración de Alembic para índices
- [ ] Verificar performance con EXPLAIN en queries

**Código sugerido:**
```python
# models.py
from sqlalchemy import Index

class ExpedienteModel(Base):
    __tablename__ = "expedientes"

    # ... campos existentes

    # Índices
    __table_args__ = (
        Index('idx_expedientes_username', 'username'),
        Index('idx_expedientes_created_at', 'created_at'),
        Index('idx_expedientes_numero', 'numero_expediente'),
        Index('idx_expedientes_user_created', 'username', 'created_at'),
        Index('idx_expedientes_activo', 'activo'),
    )
```

**Migración:**
```python
# alembic/versions/xxx_add_indexes.py
def upgrade():
    op.create_index('idx_expedientes_username', 'expedientes', ['username'])
    op.create_index('idx_expedientes_created_at', 'expedientes', ['created_at'])
    op.create_index('idx_expedientes_numero', 'expedientes', ['numero_expediente'])
    op.create_index('idx_expedientes_user_created', 'expedientes', ['username', 'created_at'])
    op.create_index('idx_expedientes_activo', 'expedientes', ['activo'])

def downgrade():
    op.drop_index('idx_expedientes_activo', 'expedientes')
    op.drop_index('idx_expedientes_user_created', 'expedientes')
    op.drop_index('idx_expedientes_numero', 'expedientes')
    op.drop_index('idx_expedientes_created_at', 'expedientes')
    op.drop_index('idx_expedientes_username', 'expedientes')
```

**Tests:**
- [ ] Test de performance antes/después de índices
- [ ] Verificar que queries usen índices (EXPLAIN)

---

## Fase 3: Optimización Frontend

**Prioridad:** 🟠 ALTA
**Estimación:** Alta complejidad
**Dependencias:** Ninguna

### PERF-004: Refactorizar ExtraccionMasivaDialog

**Archivo:** `frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx` (1700 líneas)
**Issue:** Componente muy grande, re-renders innecesarios

**Acciones:**
- [ ] Dividir en 4 sub-componentes principales:
  - `ConfigPanel.tsx` - Configuración de filtros
  - `ProgressPanel.tsx` - Barra de progreso y estado
  - `FilterPanel.tsx` - Filtros avanzados
  - `ResultsTable.tsx` - Tabla de resultados
- [ ] Extraer hooks personalizados:
  - `useExtraccionMasiva.ts` - Lógica de extracción
  - `useWebSocketProgress.ts` - Conexión WebSocket
  - `useFilteredExpedientes.ts` - Filtrado y ordenamiento
- [ ] Usar `React.memo()` en componentes puros
- [ ] Usar `useCallback()` para handlers
- [ ] Mover estado a Context si es compartido

**Estructura sugerida:**
```
components/expedientes/
  ExtraccionMasivaDialog/
    index.tsx (componente principal, orquestador)
    ConfigPanel.tsx
    ProgressPanel.tsx
    FilterPanel.tsx
    ResultsTable.tsx
    hooks/
      useExtraccionMasiva.ts
      useWebSocketProgress.ts
      useFilteredExpedientes.ts
    types.ts (tipos compartidos)
```

**Ejemplo ConfigPanel.tsx:**
```typescript
import React, { memo } from 'react';

interface ConfigPanelProps {
  onConfigChange: (config: ExtraccionConfig) => void;
  initialConfig: ExtraccionConfig;
}

export const ConfigPanel = memo(({ onConfigChange, initialConfig }: ConfigPanelProps) => {
  // Lógica solo de configuración
  // ...

  return (
    <div className="config-panel">
      {/* UI de configuración */}
    </div>
  );
});

ConfigPanel.displayName = 'ConfigPanel';
```

**Ejemplo useExtraccionMasiva.ts:**
```typescript
export const useExtraccionMasiva = () => {
  const [estado, setEstado] = useState<EstadoExtraccion>('idle');
  const [progreso, setProgreso] = useState<number>(0);

  const iniciarExtraccion = useCallback(async (config: ExtraccionConfig) => {
    setEstado('extrayendo');
    // Lógica de extracción
  }, []);

  const cancelarExtraccion = useCallback(() => {
    // Lógica de cancelación
  }, []);

  return {
    estado,
    progreso,
    iniciarExtraccion,
    cancelarExtraccion
  };
};
```

**Tests:**
- [ ] Test de cada sub-componente aisladamente
- [ ] Test de integración del componente principal
- [ ] Test que no haya re-renders innecesarios (React DevTools)

---

### FE-003: Implementar Lazy Loading

**Archivo:** Frontend en general
**Issue:** Bundle inicial muy grande, todas las rutas cargadas al inicio

**Acciones:**
- [ ] Implementar `React.lazy()` para rutas principales
- [ ] Agregar `Suspense` con fallback de loading
- [ ] Lazy load componentes grandes (ExtraccionMasivaDialog, admin)
- [ ] Analizar bundle con `vite build --analyze`
- [ ] Separar vendors en chunks diferentes
- [ ] Configurar code splitting en vite.config.ts

**Código sugerido:**
```typescript
// App.tsx o router
import { lazy, Suspense } from 'react';

// Lazy load de rutas
const ExpedientesPage = lazy(() => import('./pages/ExpedientesPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const MonitoreoPage = lazy(() => import('./pages/MonitoreoPage'));

// Componente de loading
const PageLoader = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="spinner">Cargando...</div>
  </div>
);

// Router con Suspense
<BrowserRouter>
  <Suspense fallback={<PageLoader />}>
    <Routes>
      <Route path="/expedientes" element={<ExpedientesPage />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/monitoreo" element={<MonitoreoPage />} />
    </Routes>
  </Suspense>
</BrowserRouter>

// Lazy load de componentes grandes
const ExtraccionMasivaDialog = lazy(() =>
  import('./components/expedientes/ExtraccionMasivaDialog')
);

// Uso
{showDialog && (
  <Suspense fallback={<DialogLoader />}>
    <ExtraccionMasivaDialog />
  </Suspense>
)}
```

**Configuración Vite:**
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['@radix-ui/react-dialog', '@radix-ui/react-select'],
          'vendor-utils': ['date-fns', 'clsx', 'tailwind-merge']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
});
```

**Tests:**
- [ ] Verificar que chunks se cargan solo cuando se necesitan
- [ ] Medir bundle size antes/después
- [ ] Test de navegación con lazy loading

---

### PERF-005: Optimizar Re-renders

**Archivos:** Varios componentes
**Issue:** Componentes se re-renderizan innecesariamente

**Acciones:**
- [ ] Usar `React.memo()` en componentes que reciben props complejos
- [ ] Usar `useMemo()` para cálculos costosos
- [ ] Usar `useCallback()` para funciones pasadas como props
- [ ] Identificar re-renders con React DevTools Profiler
- [ ] Considerar Context API con selectores para estado global

**Ejemplo:**
```typescript
// Antes
const ExpedienteCard = ({ expediente, onSelect }) => {
  return (
    <div onClick={() => onSelect(expediente.id)}>
      {/* ... */}
    </div>
  );
};

// Después
const ExpedienteCard = memo(({ expediente, onSelect }) => {
  return (
    <div onClick={() => onSelect(expediente.id)}>
      {/* ... */}
    </div>
  );
}, (prevProps, nextProps) => {
  // Solo re-render si expediente cambió
  return prevProps.expediente.id === nextProps.expediente.id &&
         prevProps.expediente.updated_at === nextProps.expediente.updated_at;
});

// En componente padre
const ParentComponent = () => {
  const handleSelect = useCallback((id: string) => {
    // Lógica
  }, []); // Dependencias vacías si no usa estado externo

  const filteredExpedientes = useMemo(() => {
    return expedientes.filter(/* lógica costosa */);
  }, [expedientes, otrosDeps]);

  return (
    <>
      {filteredExpedientes.map(exp => (
        <ExpedienteCard
          key={exp.id}
          expediente={exp}
          onSelect={handleSelect}
        />
      ))}
    </>
  );
};
```

**Tests:**
- [ ] Test con React DevTools Profiler
- [ ] Contar re-renders antes/después

---

## Fase 4: Calidad de Código

**Prioridad:** 🟡 MEDIA
**Estimación:** Media complejidad
**Dependencias:** Fase 1 completada

### ERR-001: Excepciones Específicas del Dominio

**Archivos:** Múltiples routers
**Issue:** `Exception` genérico expone detalles internos

**Acciones:**
- [ ] Crear módulo `core/domain/exceptions.py`
- [ ] Definir excepciones específicas por caso de uso
- [ ] Crear handler global de excepciones en FastAPI
- [ ] Mapear excepciones a códigos HTTP apropiados
- [ ] Loggear excepciones con contexto

**Código sugerido:**
```python
# core/domain/exceptions.py
class DomainException(Exception):
    """Excepción base del dominio."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ExpedienteNotFoundError(DomainException):
    """Expediente no encontrado."""
    pass

class CredencialesInvalidasError(DomainException):
    """Credenciales PJN inválidas."""
    pass

class PermisosDenegadosError(DomainException):
    """Usuario no tiene permisos."""
    pass

class ExtraccionEnProcesoError(DomainException):
    """Ya hay una extracción en proceso."""
    pass

# app.py - Handler global
from core.domain.exceptions import DomainException

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    logger.error(
        f"Domain error: {exc.message}",
        extra={"details": exc.details, "path": request.url.path}
    )

    # Mapeo de excepciones a códigos HTTP
    status_map = {
        ExpedienteNotFoundError: status.HTTP_404_NOT_FOUND,
        CredencialesInvalidasError: status.HTTP_401_UNAUTHORIZED,
        PermisosDenegadosError: status.HTTP_403_FORBIDDEN,
        ExtraccionEnProcesoError: status.HTTP_409_CONFLICT,
    }

    status_code = status_map.get(type(exc), status.HTTP_400_BAD_REQUEST)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.message,
            # No incluir details en producción
        }
    )

# Uso en endpoint
@router.get("/{expediente_id}")
async def obtener_expediente(
    expediente_id: str,
    repo: ExpedienteRepository = Depends(get_expediente_repo)
):
    expediente = await repo.obtener_por_id(expediente_id)
    if not expediente:
        raise ExpedienteNotFoundError(
            f"Expediente {expediente_id} no encontrado",
            details={"expediente_id": expediente_id}
        )
    return expediente
```

**Tests:**
- [ ] Test que cada excepción retorne código HTTP correcto
- [ ] Test que mensaje de error sea apropiado para usuario
- [ ] Test que detalles internos no se expongan en producción

---

### DUP-001: Centralizar Lógica de Login PJN

**Archivos:**
- `extraccion_masiva/extractor_masivo.py:468`
- `extraccion_masiva/gestor_batch.py:488`

**Issue:** Lógica de login duplicada en múltiples lugares

**Acciones:**
- [ ] Crear módulo `infrastructure/external/pjn_auth.py`
- [ ] Implementar clase `PJNAuthenticator`
- [ ] Centralizar manejo de selectores
- [ ] Agregar retry logic
- [ ] Usar en todos los lugares que necesiten login

**Código sugerido:**
```python
# infrastructure/external/pjn_auth.py
from playwright.async_api import Page
import logging

logger = logging.getLogger(__name__)

class PJNAuthenticationError(Exception):
    """Error en autenticación con PJN."""
    pass

class PJNAuthenticator:
    """Maneja autenticación con Portal Judicial Nacional."""

    def __init__(self):
        self.login_url = "https://www.pjn.gov.ar/..."
        self.selectors = {
            'username': '#username',
            'password': '#password',
            'submit': '#submit',
            'error': '.error-message'
        }

    async def login(
        self,
        page: Page,
        username: str,
        password: str,
        max_retries: int = 3
    ) -> bool:
        """
        Realiza login en PJN.

        Args:
            page: Página de Playwright
            username: Usuario PJN
            password: Contraseña PJN
            max_retries: Número máximo de reintentos

        Returns:
            True si login exitoso

        Raises:
            PJNAuthenticationError: Si login falla
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Intento de login {attempt + 1}/{max_retries}")

                # Navegar a login
                await page.goto(self.login_url, wait_until="networkidle")

                # Llenar formulario
                await page.fill(self.selectors['username'], username)
                await page.fill(self.selectors['password'], password)

                # Submit
                await page.click(self.selectors['submit'])

                # Esperar navegación o error
                await page.wait_for_load_state("networkidle")

                # Verificar si hubo error
                if await page.query_selector(self.selectors['error']):
                    error_msg = await page.text_content(self.selectors['error'])
                    raise PJNAuthenticationError(f"Error de login: {error_msg}")

                # Verificar si login exitoso (buscar elemento que solo aparece autenticado)
                if await self._is_authenticated(page):
                    logger.info("Login exitoso")
                    return True

                raise PJNAuthenticationError("Login falló sin mensaje de error")

            except Exception as e:
                logger.warning(f"Intento {attempt + 1} falló: {str(e)}")
                if attempt == max_retries - 1:
                    raise PJNAuthenticationError(f"Login falló después de {max_retries} intentos")
                await asyncio.sleep(2)  # Esperar antes de reintentar

        return False

    async def _is_authenticated(self, page: Page) -> bool:
        """Verifica si la sesión está autenticada."""
        # Buscar elemento que solo aparece cuando estás logueado
        return await page.query_selector('.user-menu') is not None

# Uso
from infrastructure.external.pjn_auth import PJNAuthenticator

authenticator = PJNAuthenticator()
await authenticator.login(page, username, password)
```

**Tests:**
- [ ] Test de login exitoso
- [ ] Test de login con credenciales inválidas
- [ ] Test de retry logic
- [ ] Mock de Playwright page

---

### DUP-002: Utilidades de Fechas

**Archivo:** Frontend - múltiples componentes
**Issue:** Funciones de parseo/formato de fechas duplicadas

**Acciones:**
- [ ] Crear `frontend/src/utils/dates.ts`
- [ ] Centralizar funciones de parseo
- [ ] Centralizar funciones de formato
- [ ] Usar date-fns para operaciones complejas
- [ ] Agregar validaciones

**Código sugerido:**
```typescript
// frontend/src/utils/dates.ts
import { parse, format, isValid, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Parsea fecha en formato argentino DD/MM/YYYY
 */
export const parseFechaArgentina = (fecha: string): Date | null => {
  try {
    const parsed = parse(fecha, 'dd/MM/yyyy', new Date());
    return isValid(parsed) ? parsed : null;
  } catch {
    return null;
  }
};

/**
 * Formatea fecha a formato argentino DD/MM/YYYY
 */
export const formatFechaArgentina = (fecha: Date | string): string => {
  try {
    const dateObj = typeof fecha === 'string' ? parseISO(fecha) : fecha;
    return format(dateObj, 'dd/MM/yyyy', { locale: es });
  } catch {
    return '';
  }
};

/**
 * Formatea fecha con hora
 */
export const formatFechaHora = (fecha: Date | string): string => {
  try {
    const dateObj = typeof fecha === 'string' ? parseISO(fecha) : fecha;
    return format(dateObj, "dd/MM/yyyy 'a las' HH:mm", { locale: es });
  } catch {
    return '';
  }
};

/**
 * Valida formato de fecha argentino
 */
export const validarFechaArgentina = (fecha: string): boolean => {
  const regex = /^\d{2}\/\d{2}\/\d{4}$/;
  if (!regex.test(fecha)) return false;

  const parsed = parseFechaArgentina(fecha);
  return parsed !== null;
};

/**
 * Convierte fecha argentina a ISO para backend
 */
export const fechaArgentinaToISO = (fecha: string): string | null => {
  const parsed = parseFechaArgentina(fecha);
  return parsed ? parsed.toISOString() : null;
};
```

**Uso:**
```typescript
import { parseFechaArgentina, formatFechaArgentina } from '@/utils/dates';

// Antes
const fecha = new Date(fechaStr.split('/').reverse().join('-'));

// Después
const fecha = parseFechaArgentina(fechaStr);
```

**Tests:**
- [ ] Test de parseo de fechas válidas
- [ ] Test de parseo de fechas inválidas
- [ ] Test de formato
- [ ] Test de validación

---

### ANTI-003: Reemplazar Prints con Logging

**Archivos:** Múltiples
**Issue:** `print()` statements en código de producción

**Acciones:**
- [ ] Buscar todos los prints: `grep -r "print(" --include="*.py"`
- [ ] Reemplazar con `logger.info()`, `logger.warning()`, etc
- [ ] Remover prints de debugging
- [ ] Configurar logging en todos los módulos
- [ ] Agregar linter rule para prohibir print

**Script de búsqueda:**
```bash
# Encontrar todos los prints
grep -r "print(" --include="*.py" Sistema_v6/ > prints_found.txt
```

**Configuración de linter:**
```python
# .pylintrc o pyproject.toml
[tool.pylint.messages_control]
disable = [
    "print-statement",  # Prohibir print
]
```

**Tests:**
- [ ] Linter check que falle si hay prints
- [ ] Verificar que logging funciona correctamente

---

## Fase 5: Testing

**Prioridad:** 🟡 MEDIA
**Estimación:** Alta complejidad
**Dependencias:** Fases anteriores

### TEST-001: Tests de Seguridad

**Archivos:** `tests/unit/infrastructure/security/`
**Issue:** Módulos de seguridad sin tests

**Acciones:**
- [ ] Crear `tests/unit/infrastructure/security/test_encryption.py`
- [ ] Crear `tests/unit/infrastructure/security/test_jwt.py`
- [ ] Crear `tests/integration/test_auth_flow.py`
- [ ] Test de encriptación/desencriptación
- [ ] Test de generación y validación de JWT
- [ ] Test de rate limiting
- [ ] Test de permisos admin

**Ejemplos:**
```python
# tests/unit/infrastructure/security/test_encryption.py
import pytest
from infrastructure.security.encryption import encrypt_password, decrypt_password

def test_encrypt_decrypt_password():
    """Test que encriptación y desencriptación funcionen."""
    password = "mi-password-secreto"
    encrypted = encrypt_password(password)

    assert encrypted != password
    assert len(encrypted) > 0

    decrypted = decrypt_password(encrypted)
    assert decrypted == password

def test_different_encryptions():
    """Test que misma password genere diferentes encriptaciones."""
    password = "test-password"
    encrypted1 = encrypt_password(password)
    encrypted2 = encrypt_password(password)

    # Fernet incluye timestamp, así que son diferentes
    assert encrypted1 != encrypted2

    # Pero ambos desencriptan al mismo valor
    assert decrypt_password(encrypted1) == password
    assert decrypt_password(encrypted2) == password

# tests/unit/infrastructure/security/test_jwt.py
from datetime import timedelta
from infrastructure.security.jwt import create_access_token, decode_access_token

def test_create_and_decode_token():
    """Test creación y decodificación de JWT."""
    data = {"sub": "test@example.com", "user_id": "123"}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))

    decoded = decode_access_token(token)
    assert decoded["sub"] == "test@example.com"
    assert decoded["user_id"] == "123"

def test_expired_token():
    """Test que token expirado falle."""
    data = {"sub": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))

    with pytest.raises(JWTError):
        decode_access_token(token)

# tests/integration/test_auth_flow.py
from fastapi.testclient import TestClient

def test_login_flow(client: TestClient):
    """Test flujo completo de login."""
    # Crear usuario
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201

    # Login
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Usar token para endpoint protegido
    response = client.get(
        "/api/expedientes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_admin_access(client: TestClient, admin_token: str, user_token: str):
    """Test que solo admin pueda acceder a endpoints protegidos."""
    # Admin puede acceder
    response = client.post(
        "/api/admin/reset-sistema",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

    # Usuario normal no puede
    response = client.post(
        "/api/admin/reset-sistema",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
```

**Meta de Coverage:**
- [ ] Encryption: 100%
- [ ] JWT: 100%
- [ ] Auth endpoints: 90%+

---

### TEST-002: Tests de Componentes Frontend

**Archivos:** `tests/unit/components/`
**Issue:** Componentes sin tests unitarios

**Acciones:**
- [ ] Crear tests para componentes principales
- [ ] Usar React Testing Library
- [ ] Test de renders condicionales
- [ ] Test de interacciones de usuario
- [ ] Test de estados de loading/error

**Ejemplos:**
```typescript
// tests/unit/components/expedientes/ExpedienteCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ExpedienteCard } from '@/components/expedientes/ExpedienteCard';

describe('ExpedienteCard', () => {
  const mockExpediente = {
    id: '1',
    numero_expediente: 'EXP-001/2024',
    caratula: 'Test vs Test',
    fecha_creacion: '2024-01-15T10:00:00Z',
    activo: true
  };

  it('renderiza información del expediente', () => {
    render(<ExpedienteCard expediente={mockExpediente} />);

    expect(screen.getByText('EXP-001/2024')).toBeInTheDocument();
    expect(screen.getByText('Test vs Test')).toBeInTheDocument();
  });

  it('llama onSelect cuando se hace click', () => {
    const handleSelect = jest.fn();
    render(
      <ExpedienteCard
        expediente={mockExpediente}
        onSelect={handleSelect}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(handleSelect).toHaveBeenCalledWith('1');
  });

  it('muestra badge de activo', () => {
    render(<ExpedienteCard expediente={mockExpediente} />);
    expect(screen.getByText('Activo')).toBeInTheDocument();
  });

  it('muestra badge de inactivo', () => {
    const inactiveExp = { ...mockExpediente, activo: false };
    render(<ExpedienteCard expediente={inactiveExp} />);
    expect(screen.getByText('Inactivo')).toBeInTheDocument();
  });
});
```

**Meta de Coverage:**
- [ ] Componentes UI: 70%+
- [ ] Hooks personalizados: 80%+

---

### TEST-003: Tests E2E

**Archivos:** `tests/e2e/`
**Issue:** Sin tests de flujo completo

**Acciones:**
- [ ] Configurar Playwright para frontend tests
- [ ] Crear tests de flujos críticos
- [ ] Test de login → extracción → resultados
- [ ] Test de configuración de credenciales
- [ ] Test de administración

**Ejemplo:**
```typescript
// tests/e2e/extraccion-masiva.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Extracción Masiva', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:5173/login');
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'testpass');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/expedientes');
  });

  test('flujo completo de extracción', async ({ page }) => {
    // Abrir dialog
    await page.click('text=Extracción Masiva');
    await expect(page.locator('.dialog')).toBeVisible();

    // Configurar filtros
    await page.selectOption('#dependencia', 'JUZGADO CIVIL');
    await page.fill('#numero-desde', '1');
    await page.fill('#numero-hasta', '10');

    // Iniciar extracción
    await page.click('text=Iniciar Extracción');

    // Esperar progreso
    await expect(page.locator('.progress-bar')).toBeVisible();

    // Verificar resultados
    await page.waitForSelector('.resultados-tabla', { timeout: 60000 });
    const rows = await page.locator('.resultados-tabla tbody tr').count();
    expect(rows).toBeGreaterThan(0);
  });
});
```

---

## Fase 6: Logging y Monitoreo

**Prioridad:** 🟡 MEDIA
**Estimación:** Media complejidad
**Dependencias:** Fase 1

### LOG-001: Estandarizar Logging

**Archivos:** Todos
**Issue:** Logging inconsistente (mix de print y logging)

**Acciones:**
- [ ] Crear `infrastructure/config/logging.py`
- [ ] Configurar formatters consistentes
- [ ] Agregar request_id a contexto
- [ ] Configurar niveles por entorno
- [ ] Rotar logs automáticamente
- [ ] Integrar con Sentry (opcional)

**Código sugerido:**
```python
# infrastructure/config/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(
    level: str = "INFO",
    log_file: str = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
):
    """Configura logging para la aplicación."""

    # Crear directorio de logs
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Formato
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reducir verbosidad de librerías
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger

# Middleware para request_id
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# Agregar filtro a handlers
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())

# Middleware FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# En app.py
app.add_middleware(RequestIdMiddleware)
```

**Uso:**
```python
# En cualquier módulo
import logging

logger = logging.getLogger(__name__)

logger.info("Usuario autenticado correctamente", extra={
    "user_id": user.id,
    "username": user.username
})

logger.error("Error en extracción", extra={
    "expediente_id": exp_id,
    "error": str(e)
})
```

**Tests:**
- [ ] Test que request_id se propague
- [ ] Test que logs se rotan correctamente
- [ ] Test de niveles de logging

---

### LOG-003: Middleware de Trazabilidad

**Archivo:** Nuevo
**Issue:** Difícil debuggear sin correlación de requests

**Acciones:**
- [ ] Implementar middleware de logging de requests
- [ ] Loggear tiempo de respuesta
- [ ] Loggear errores con contexto completo
- [ ] Agregar X-Request-ID a headers

**Código en LOG-001 arriba**

---

## Fase 7: Infraestructura

**Prioridad:** 🟡 MEDIA
**Estimación:** Baja complejidad
**Dependencias:** Ninguna

### CONF-002: Docker Compose para Desarrollo

**Archivo:** Nuevo
**Issue:** Setup manual complejo

**Acciones:**
- [ ] Crear `docker-compose.yml`
- [ ] Servicios: API, Frontend, Redis, PostgreSQL (opcional)
- [ ] Volúmenes para persistencia
- [ ] Variables de entorno
- [ ] Network configuration
- [ ] Health checks

**Código sugerido:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Redis para sesiones
  redis:
    image: redis:7-alpine
    container_name: sintaxis_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # PostgreSQL (opcional, si migran de SQLite)
  postgres:
    image: postgres:15-alpine
    container_name: sintaxis_db
    environment:
      POSTGRES_DB: sintaxis
      POSTGRES_USER: sintaxis
      POSTGRES_PASSWORD: sintaxis_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sintaxis"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Backend API
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sintaxis_api
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://sintaxis:sintaxis_dev_password@postgres:5432/sintaxis
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - FERNET_KEY=${FERNET_KEY}
      - ALLOWED_ORIGINS=http://localhost:5173
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/venv  # No montar venv
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: sintaxis_frontend
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  redis_data:
  postgres_data:

networks:
  default:
    name: sintaxis_network
```

**Dockerfile para API:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**README de setup:**
```markdown
## Desarrollo con Docker Compose

1. Copiar `.env.example` a `.env` y configurar variables
2. Generar secrets:
   ```bash
   # JWT Secret
   openssl rand -hex 32

   # Fernet Key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
3. Levantar servicios:
   ```bash
   docker-compose up -d
   ```
4. Ver logs:
   ```bash
   docker-compose logs -f api
   ```
5. Ejecutar migraciones:
   ```bash
   docker-compose exec api alembic upgrade head
   ```
6. Acceder:
   - Frontend: http://localhost:5173
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
```

**Tests:**
- [ ] Verificar que todos los servicios levantan correctamente
- [ ] Verificar health checks
- [ ] Test de conectividad entre servicios

---

### CONF-001: Versiones Exactas de Dependencias

**Archivo:** `requirements.txt`
**Issue:** Versiones con `~=` pueden cambiar

**Acciones:**
- [ ] Generar `requirements-lock.txt` con versiones exactas
- [ ] Usar `pip freeze > requirements-lock.txt`
- [ ] En producción, instalar desde requirements-lock.txt
- [ ] En desarrollo, mantener requirements.txt con rangos
- [ ] Actualizar lock file periódicamente

**Proceso:**
```bash
# Desarrollo
pip install -r requirements.txt

# Generar lock
pip freeze > requirements-lock.txt

# Producción
pip install -r requirements-lock.txt
```

**CI/CD:**
```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: |
    pip install -r requirements-lock.txt
```

---

## Fase 8: Documentación

**Prioridad:** 🟢 BAJA
**Estimación:** Baja complejidad
**Dependencias:** Todas las fases anteriores

### ARCH-002: Documentar API

**Archivos:** Schemas de Pydantic
**Issue:** Falta documentación y ejemplos en OpenAPI

**Acciones:**
- [ ] Agregar docstrings a endpoints
- [ ] Agregar ejemplos a schemas Pydantic
- [ ] Configurar OpenAPI metadata
- [ ] Documentar códigos de error posibles

**Código sugerido:**
```python
# Metadata de API
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SintaXis API",
        version="2.0.0",
        description="""
        API para gestión de expedientes del Portal Judicial Nacional.

        ## Autenticación

        La API usa JWT (JSON Web Tokens) para autenticación.

        1. Obtener token: `POST /api/auth/login`
        2. Incluir en headers: `Authorization: Bearer {token}`

        ## Rate Limiting

        - Login: 5 requests/minuto
        - Otros endpoints: 100 requests/minuto
        """,
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Schemas con ejemplos
class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "usuario@example.com",
                    "password": "SecurePass123!"
                }
            ]
        }
    }

# Endpoints con documentación
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Autenticar usuario",
    description="""
    Autentica un usuario y retorna un token JWT.

    El token expira en 30 minutos por defecto.
    """,
    responses={
        200: {
            "description": "Login exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Credenciales inválidas",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Usuario o contraseña incorrectos"
                    }
                }
            }
        },
        429: {
            "description": "Too many requests",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Try again in 60 seconds."
                    }
                }
            }
        }
    }
)
async def login(credentials: LoginRequest):
    """Login endpoint."""
    pass
```

---

### Documentación de Interfaces TypeScript

**Archivos:** Frontend
**Issue:** Interfaces sin JSDoc

**Acciones:**
- [ ] Agregar JSDoc a todas las interfaces
- [ ] Documentar props de componentes
- [ ] Agregar ejemplos de uso

**Código sugerido:**
```typescript
/**
 * Representa un expediente del sistema.
 *
 * @interface Expediente
 * @property {string} id - ID único del expediente
 * @property {string} numero_expediente - Número de expediente (formato: XXX-0000/YYYY)
 * @property {string} caratula - Carátula del expediente
 * @property {string} fecha_creacion - Fecha de creación (ISO 8601)
 * @property {boolean} activo - Estado activo/inactivo
 *
 * @example
 * ```typescript
 * const expediente: Expediente = {
 *   id: "123",
 *   numero_expediente: "JUZ-0001/2024",
 *   caratula: "Pérez vs González",
 *   fecha_creacion: "2024-01-15T10:00:00Z",
 *   activo: true
 * };
 * ```
 */
export interface Expediente {
  id: string;
  numero_expediente: string;
  caratula: string;
  fecha_creacion: string;
  activo: boolean;
}

/**
 * Props del componente ExpedienteCard.
 *
 * @interface ExpedienteCardProps
 * @property {Expediente} expediente - Datos del expediente a mostrar
 * @property {(id: string) => void} [onSelect] - Callback cuando se selecciona
 * @property {boolean} [showActions=true] - Mostrar botones de acción
 */
export interface ExpedienteCardProps {
  expediente: Expediente;
  onSelect?: (id: string) => void;
  showActions?: boolean;
}
```

---

## Checklist Pre-Deployment

Antes de desplegar a producción, verificar:

### Seguridad
- [ ] CORS configurado con orígenes específicos (no wildcard)
- [ ] JWT_SECRET_KEY configurado con valor aleatorio fuerte
- [ ] FERNET_KEY configurado y persistido
- [ ] .env no está en repositorio
- [ ] .env.example está actualizado
- [ ] Rate limiting activado en endpoints de auth
- [ ] Verificación de permisos admin implementada
- [ ] Credenciales por usuario funcionando
- [ ] No hay prints de secretos en código
- [ ] Variables de entorno validadas en startup

### Base de Datos
- [ ] Migraciones aplicadas
- [ ] Índices creados
- [ ] Backups configurados
- [ ] Pool de conexiones configurado

### Performance
- [ ] Paginación implementada
- [ ] Sesiones en Redis
- [ ] Frontend con code splitting
- [ ] Assets optimizados (minificados)

### Monitoreo
- [ ] Logging configurado y funcionando
- [ ] Rotación de logs activada
- [ ] Request IDs en todos los logs
- [ ] Sentry configurado (opcional)
- [ ] Health check endpoint funcionando

### Tests
- [ ] Coverage >= 80% en módulos críticos
- [ ] Todos los tests pasando
- [ ] Tests E2E ejecutados

### Infraestructura
- [ ] Variables de entorno documentadas
- [ ] Docker/compose funcionando
- [ ] Health checks configurados
- [ ] SSL/TLS configurado
- [ ] Firewall configurado

---

## Métricas de Éxito

### Seguridad
- ✅ 0 vulnerabilidades críticas en scan de seguridad
- ✅ 100% de endpoints protegidos requieren autenticación
- ✅ Rate limiting funcionando en auth endpoints

### Performance
- ✅ Tiempo de respuesta API < 200ms (p95)
- ✅ Tiempo de carga inicial frontend < 3s
- ✅ Bundle size frontend < 500KB (gzipped)
- ✅ Queries DB con índices (0 full table scans)

### Calidad
- ✅ Coverage de tests >= 80%
- ✅ 0 errores de linting
- ✅ 0 warnings críticos de TypeScript
- ✅ Complejidad ciclomática < 10 en funciones

### Mantenibilidad
- ✅ 0 archivos > 500 líneas
- ✅ 0 funciones > 50 líneas
- ✅ Duplicación de código < 3%
- ✅ Documentación de API completa

---

## Notas de Implementación

### Orden Recomendado de Ejecución

1. **Día 1-2: Seguridad Crítica**
   - Implementar todos los issues críticos (SEC-001 a SEC-008)
   - Esto es bloqueante para cualquier deployment

2. **Día 3-4: Rendimiento Backend**
   - Redis para sesiones
   - Paginación
   - Índices BD

3. **Día 5-6: Refactoring Frontend**
   - Dividir componentes grandes
   - Lazy loading
   - Optimización de renders

4. **Día 7-8: Calidad de Código**
   - Excepciones del dominio
   - Eliminar duplicación
   - Logging estandarizado

5. **Día 9-12: Testing**
   - Tests de seguridad
   - Tests de componentes
   - Tests E2E

6. **Día 13-14: Infraestructura y Docs**
   - Docker Compose
   - Documentación API
   - Checklist pre-deployment

### Recursos Necesarios

- **Backend Developer:** 10-12 días
- **Frontend Developer:** 6-8 días
- **DevOps:** 2-3 días
- **QA/Testing:** 4-5 días

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Migración a Redis rompe sesiones existentes | Alta | Medio | Implementar migración gradual, mantener fallback |
| Refactoring de componentes introduce bugs | Media | Alto | Aumentar coverage de tests antes de refactoring |
| Cambios de seguridad rompen funcionalidad | Media | Alto | Testing exhaustivo en staging antes de producción |
| Performance no mejora como esperado | Baja | Medio | Benchmarking antes/después, iteración incremental |

---

## Conclusión

Este plan aborda 35+ issues identificados en la revisión del sistema, priorizados por severidad y organizados en fases lógicas. La implementación completa tomará aproximadamente 2-3 semanas con un equipo dedicado.

**Prioridad máxima:** Fase 1 (Seguridad Crítica) debe completarse antes de cualquier deployment a producción.

**Quick wins:** CONF-002 (Docker Compose), DUP-002 (Utilidades de fechas), ANTI-003 (Reemplazar prints) pueden implementarse rápidamente para mejorar DX.

**Mejora continua:** Después de completar este plan, establecer proceso de code review y testing obligatorio para mantener calidad.

---

**Última actualización:** 2025-11-18
**Próxima revisión:** Después de completar Fase 1
