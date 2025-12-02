# Sistema de Vencimientos - Documentación Completa

**Versión:** 6.0
**Última actualización:** 2025-12-02
**Estado:** Producción

---

## Tabla de Contenidos

1. [Descripción General](#1-descripción-general)
2. [Arquitectura](#2-arquitectura)
3. [Detección Automática](#3-detección-automática)
4. [Cálculo de Días Hábiles](#4-cálculo-de-días-hábiles)
5. [API REST](#5-api-rest)
6. [Frontend](#6-frontend)
7. [Base de Datos](#7-base-de-datos)
8. [Configuración](#8-configuración)
9. [Caché y Optimización](#9-caché-y-optimización)
10. [Sistema de Notificaciones](#10-sistema-de-notificaciones)
11. [Herramientas MCP](#11-herramientas-mcp)

---

## 1. Descripción General

El sistema de vencimientos de sintaXis detecta, gestiona y notifica plazos procesales de manera automática. Utiliza un enfoque **híbrido** (regex + LLM) para identificar vencimientos durante la ingesta de actuaciones judiciales.

### Características Principales

| Característica | Estado |
|----------------|--------|
| Detección automática regex | ✅ |
| Análisis LLM (Ollama) | ✅ |
| Cálculo días hábiles | ✅ |
| Gestión de feriados | ✅ |
| CRUD manual | ✅ |
| Filtrado backend | ✅ |
| Paginación infinita | ✅ |
| Caché con TTL | ✅ |
| Notificaciones | ✅ |

### Niveles de Urgencia

| Nivel | Días Restantes | Color |
|-------|----------------|-------|
| `vencido` | < 0 | Negro |
| `critico` | 0-1 | Rojo |
| `urgente` | 2-3 | Naranja |
| `proximo` | 4-7 | Amarillo |
| `normal/futuro` | > 7 | Verde |

---

## 2. Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  VencimientosPage.tsx     │  VencimientosWidget.tsx  │  AgendaPage.tsx  │
│  - Infinite scroll        │  - Dashboard widget      │  - Tab integrado │
│  - Filtros                │  - Urgentes (5)          │  - Acciones      │
├─────────────────────────────────────────────────────────────────────────┤
│                          vencimientosStore.ts                            │
│                          vencimientosApi.ts                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  /api/v1/vencimientos                                                    │
│  ├── GET  /                    # Listar con filtros + caché             │
│  ├── GET  /estadisticas        # Estadísticas globales                  │
│  ├── GET  /{id}                # Obtener por ID                         │
│  ├── POST /                    # Crear manual                           │
│  ├── PUT  /{id}                # Actualizar                             │
│  ├── DELETE /{id}              # Eliminar                               │
│  ├── POST /{id}/atender        # Marcar atendido                        │
│  └── POST /{id}/cancelar       # Cancelar                               │
├─────────────────────────────────────────────────────────────────────────┤
│  VencimientosCache (TTL 60s)   │   FeriadosService                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              MySQL                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  vencimientos       │  feriados        │  alertas_vencimientos          │
│  notificaciones     │  feria_judicial  │  configuracion_alertas         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detección Automática

### 3.1 Flujo de Detección

```
Actuación PDF/Texto
        │
        ▼
┌─────────────────────┐
│  Analizador Híbrido │
│  (regex + LLM)      │
└─────────────────────┘
        │
        ├─── Patrones Regex ──▶ Confianza: 0.95
        │
        └─── Ollama LLM ──────▶ Confianza: 0.85
                │
                ▼
┌─────────────────────┐
│  Calcular Fecha     │
│  Vencimiento        │
│  (días hábiles)     │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Persistir en BD    │
│  tabla: vencimientos│
└─────────────────────┘
```

### 3.2 Patrones Regex Soportados

| Tipo | Patrón | Plazo Default |
|------|--------|---------------|
| `CEDULA_ELECTRONICA` | `c[eé]dula.*electr[oó]nic` | 3 días |
| `CEDULA_FISICA` | `c[eé]dula.*f[ií]sic` | 5 días |
| `TRASLADO` | `traslad.*?(\d+)\s*d[ií]as?` | Variable |
| `ALEGATO` | `alegat.*?(\d+)\s*d[ií]as?` | Variable |
| `PRESENTACION` | `present.*?(\d+)\s*d[ií]as?` | Variable |
| `APELACION` | `apela.*?(\d+)\s*d[ií]as?` | 5 días |
| `RECURSO` | `recurso.*?(\d+)` | 10 días |
| `AUDIENCIA` | `audiencia.*?(\d{1,2})[/-](\d{1,2})` | Fecha fija |
| `OTRO` | Plazo genérico | Variable |

### 3.3 Archivo Principal

**Ubicación:** `core/procesador_pdf/analizador_vencimientos.py`

```python
class AnalizadorVencimientos:
    """
    Detecta vencimientos en texto de actuaciones.
    Usa enfoque híbrido: regex (rápido) + LLM (complejo).
    """

    def analizar(self, texto: str, fecha_actuacion: date) -> List[Vencimiento]:
        # 1. Intentar regex primero
        vencimientos = self._analizar_con_regex(texto)

        # 2. Si no encuentra o confianza baja, usar LLM
        if not vencimientos or self._necesita_llm(texto):
            vencimientos_llm = self._analizar_con_llm(texto)
            vencimientos.extend(vencimientos_llm)

        # 3. Calcular fechas de vencimiento
        for v in vencimientos:
            v.fecha_vencimiento = self._calcular_vencimiento(
                fecha_actuacion, v.plazo_dias, v.dias_habiles
            )

        return vencimientos
```

---

## 4. Cálculo de Días Hábiles

### 4.1 Servicio de Feriados

**Ubicación:** `application/services/feriados_service.py`

El servicio considera:
- **Fines de semana:** Sábados y domingos
- **Feriados nacionales:** Cargados desde BD
- **Feria judicial:** Enero (vacaciones judiciales)
- **Feriados locales:** Por jurisdicción

### 4.2 Optimización Batch

```python
class FeriadosService:
    def es_dia_habil_optimizado(
        self,
        fecha: date,
        feriados_set: set,  # Pre-cargados como set
        ferias: List[Tuple[date, date]]  # Rangos de feria
    ) -> bool:
        """
        Versión optimizada para consultas batch.
        Usa set para búsquedas O(1).
        """
        if fecha.weekday() >= 5:  # Fin de semana
            return False
        if fecha in feriados_set:  # O(1) lookup
            return False
        if self._fecha_en_feria(fecha, ferias):
            return False
        return True

    def calcular_dias_habiles_batch(
        self,
        calculos: List[Tuple[date, int]]
    ) -> List[date]:
        """
        Calcula múltiples vencimientos con una sola carga de datos.
        """
        # Cargar feriados una vez
        min_fecha = min(c[0] for c in calculos)
        max_plazo = max(c[1] for c in calculos)
        max_fecha = min_fecha + timedelta(days=max_plazo * 2)

        feriados = self._cargar_feriados_rango(min_fecha, max_fecha)
        ferias = self._cargar_ferias_rango(min_fecha, max_fecha)

        # Calcular todos
        return [
            self._calcular_fecha_habil(inicio, dias, feriados, ferias)
            for inicio, dias in calculos
        ]
```

### 4.3 Tabla de Feriados

```sql
CREATE TABLE feriados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fecha DATE NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('nacional', 'provincial', 'judicial') DEFAULT 'nacional',
    jurisdiccion VARCHAR(50) DEFAULT NULL,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_fecha (fecha)
);

CREATE TABLE feria_judicial (
    id INT PRIMARY KEY AUTO_INCREMENT,
    anio INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    descripcion VARCHAR(100),
    UNIQUE KEY uk_anio (anio)
);
```

---

## 5. API REST

### 5.1 Endpoints Principales

**Base URL:** `/api/v1/vencimientos`

#### Listar Vencimientos

```http
GET /api/v1/vencimientos?expediente=FRE_001&estado=pendiente&limite=50&offset=0
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `expediente` | string | Filtrar por número de expediente |
| `tipo` | enum | CEDULA_ELECTRONICA, TRASLADO, etc. |
| `estado` | enum | pendiente, atendido, vencido, cancelado |
| `urgencia` | enum | vencido, critico, urgente, proximo, futuro |
| `desde` | date | Fecha desde (YYYY-MM-DD) |
| `hasta` | date | Fecha hasta (YYYY-MM-DD) |
| `solo_pendientes` | bool | Solo mostrar pendientes |
| `limite` | int | Máximo de resultados (1-500) |
| `offset` | int | Offset para paginación |
| `use_cache` | bool | Usar caché (default: true) |

**Response:**

```json
{
  "vencimientos": [
    {
      "id": 123,
      "expediente_numero": "FRE_001234_2024",
      "tipo": "CEDULA_ELECTRONICA",
      "descripcion": "Cédula de notificación electrónica",
      "fecha_notificacion": "2024-12-01",
      "plazo_dias": 3,
      "fecha_vencimiento": "2024-12-04",
      "dias_habiles": true,
      "estado": "pendiente",
      "dias_restantes": 2,
      "nivel_urgencia": "urgente",
      "confianza": 0.95,
      "created_at": "2024-12-01T10:30:00Z",
      "updated_at": "2024-12-01T10:30:00Z"
    }
  ],
  "total": 150,
  "pendientes": 45,
  "vencidos": 10,
  "atendidos": 95
}
```

#### Estadísticas

```http
GET /api/v1/vencimientos/estadisticas
```

**Response:**

```json
{
  "total": 150,
  "pendientes": 45,
  "vencidos": 10,
  "atendidos": 90,
  "cancelados": 5,
  "criticos_hoy": 3,
  "urgentes_3_dias": 8,
  "proximos_7_dias": 15,
  "por_tipo": {
    "CEDULA_ELECTRONICA": 50,
    "TRASLADO": 30,
    "ALEGATO": 25,
    "OTRO": 45
  }
}
```

#### Crear Vencimiento Manual

```http
POST /api/v1/vencimientos
Content-Type: application/json

{
  "expediente_numero": "FRE_001234_2024",
  "tipo": "TRASLADO",
  "descripcion": "Traslado de demanda",
  "fecha_notificacion": "2024-12-01",
  "plazo_dias": 15,
  "fecha_vencimiento": "2024-12-20",
  "dias_habiles": true
}
```

#### Marcar como Atendido

```http
POST /api/v1/vencimientos/123/atender?notas=Contestación presentada
```

#### Cancelar Vencimiento

```http
POST /api/v1/vencimientos/123/cancelar?notas=Expediente archivado
```

### 5.2 Códigos de Estado

| Código | Significado |
|--------|-------------|
| 200 | OK |
| 201 | Creado |
| 400 | Parámetros inválidos |
| 404 | Vencimiento no encontrado |
| 500 | Error interno |

---

## 6. Frontend

### 6.1 Componentes Principales

| Componente | Ubicación | Descripción |
|------------|-----------|-------------|
| `VencimientosPage` | `pages/vencimientos/` | Página principal con infinite scroll |
| `VencimientosWidget` | `components/dashboard/` | Widget para dashboard |
| `VencimientosExpedientePanel` | `components/expedientes/` | Panel en detalle expediente |
| `VencimientoCard` | `components/vencimientos/` | Tarjeta individual |

### 6.2 Store (Zustand)

**Ubicación:** `stores/vencimientosStore.ts`

```typescript
interface VencimientosState {
  vencimientos: VencimientoUrgente[]
  estadisticas: EstadisticasVencimientosSimple | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchVencimientos: (filtros?: FiltrosVencimientos) => Promise<void>
  fetchEstadisticas: () => Promise<void>
  marcarAtendido: (id: number, notas?: string) => Promise<void>
  cancelar: (id: number, notas?: string) => Promise<void>
  refetch: () => Promise<void>
}
```

### 6.3 Tipos

**Ubicación:** `types/vencimiento.ts`

```typescript
export type TipoVencimiento =
  | 'cedula_electronica'
  | 'cedula_fisica'
  | 'traslado'
  | 'alegato'
  | 'presentacion'
  | 'otro'

export type EstadoVencimiento = 'pendiente' | 'atendido' | 'vencido' | 'cancelado'

export type NivelUrgencia = 'vencido' | 'critico' | 'urgente' | 'proximo' | 'normal'

export interface VencimientoUrgente {
  id: number
  actuacion_id: number
  expediente_numero: string
  tipo: string
  fecha_vencimiento: string
  dias_restantes: number
  nivel_urgencia: NivelUrgencia
  descripcion?: string
  actuacion_tipo: string
  actuacion_detalle: string
  fecha_notificacion?: string
}

export interface FiltrosVencimientos {
  estado?: EstadoVencimiento
  tipo?: TipoVencimiento
  nivel_urgencia?: NivelUrgencia | 'todos'
  expediente?: string
  dias_desde?: number
  dias_hasta?: number
  limite?: number
  offset?: number
  ocultarVencidos?: boolean
}
```

### 6.4 Colores de Urgencia

```typescript
export const COLORES_URGENCIA: Record<NivelUrgencia, string> = {
  vencido: 'bg-black text-white',
  critico: 'bg-red-600 text-white',
  urgente: 'bg-orange-500 text-white',
  proximo: 'bg-yellow-400 text-gray-900',
  normal: 'bg-green-500 text-white'
}
```

### 6.5 Paginación Infinita

```typescript
// VencimientosPage.tsx
const ITEMS_PER_PAGE = 50

const cargarMas = useCallback(async () => {
  if (isLoadingMore || !hasMore) return

  setIsLoadingMore(true)
  const response = await vencimientosApi.getVencimientos({
    ...filtrosActuales,
    limite: ITEMS_PER_PAGE,
    offset: offset
  })

  setVencimientos(prev => [...prev, ...response.vencimientos])
  setOffset(prev => prev + response.vencimientos.length)
  setHasMore(response.vencimientos.length === ITEMS_PER_PAGE)
  setIsLoadingMore(false)
}, [isLoadingMore, hasMore, offset, filtrosActuales])
```

---

## 7. Base de Datos

### 7.1 Tabla Principal

```sql
CREATE TABLE vencimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expediente_numero VARCHAR(50) NOT NULL,
    actuacion_id INT,
    tipo ENUM(
        'CEDULA_ELECTRONICA', 'CEDULA_FISICA', 'TRASLADO',
        'ALEGATO', 'PRESENTACION', 'APELACION', 'RECURSO',
        'AUDIENCIA', 'OTRO'
    ) NOT NULL,
    descripcion TEXT,
    fecha_notificacion DATE NOT NULL,
    plazo_dias INT NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    dias_habiles BOOLEAN DEFAULT TRUE,
    texto_fuente TEXT,
    confianza DECIMAL(3,2) DEFAULT 1.00,
    estado ENUM('pendiente', 'atendido', 'vencido', 'cancelado') DEFAULT 'pendiente',
    notas TEXT,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_expediente (expediente_numero),
    INDEX idx_fecha_vencimiento (fecha_vencimiento),
    INDEX idx_estado (estado),
    INDEX idx_tipo (tipo),
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE SET NULL
);
```

### 7.2 Vista para Consultas

```sql
CREATE VIEW v_vencimientos_urgentes AS
SELECT
    v.*,
    DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes,
    CASE
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) < 0 THEN 'vencido'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 1 THEN 'critico'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 3 THEN 'urgente'
        WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7 THEN 'proximo'
        ELSE 'futuro'
    END as nivel_urgencia,
    a.tipo as actuacion_tipo,
    a.detalle as actuacion_detalle
FROM vencimientos v
LEFT JOIN actuaciones a ON v.actuacion_id = a.id
WHERE v.estado = 'pendiente'
ORDER BY v.fecha_vencimiento ASC;
```

---

## 8. Configuración

### 8.1 Configuración en Settings

**Ubicación:** `infrastructure/config/settings.py`

```python
class Settings:
    # Vencimientos
    VENCIMIENTO_CACHE_TTL: int = 60  # segundos
    VENCIMIENTO_DEFAULT_LIMITE: int = 100
    VENCIMIENTO_MAX_LIMITE: int = 500

    # Análisis híbrido
    VENCIMIENTO_USAR_LLM: bool = True
    VENCIMIENTO_LLM_MODEL: str = "llama3.2"
    VENCIMIENTO_CONFIANZA_MINIMA: float = 0.7

    # Notificaciones
    ALERTAS_VERIFICAR_CADA_MINUTOS: int = 60
    ALERTAS_DIAS_ANTICIPACION: List[int] = [3, 1, 0]
```

### 8.2 Configuración de Usuario (Frontend)

```typescript
// ConfiguracionVencimientos.tsx
interface ConfigVencimientos {
  analisis_habilitado: boolean
  usar_llm: boolean
  plazo_cedula_electronica: number  // días
  plazo_cedula_fisica: number
  plazo_traslado_default: number
  dias_anticipacion_alerta: number[]
}
```

---

## 9. Caché y Optimización

### 9.1 Caché de Vencimientos

**Ubicación:** `presentation/api/rest/routers/vencimientos.py`

```python
class VencimientosCache:
    """
    Caché en memoria con TTL de 60 segundos.
    Thread-safe con Lock.
    """

    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def _make_key(self, **kwargs) -> str:
        """Genera clave MD5 desde parámetros ordenados."""
        sorted_items = sorted(kwargs.items())
        return hashlib.md5(str(sorted_items).encode()).hexdigest()

    def get(self, **kwargs) -> Optional[Any]:
        """Retorna valor si existe y no expiró."""
        key = self._make_key(**kwargs)
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    return value
                del self._cache[key]
        return None

    def set(self, value: Any, **kwargs) -> None:
        """Guarda valor con timestamp."""
        key = self._make_key(**kwargs)
        with self._lock:
            self._cache[key] = (value, time.time())

    def invalidate(self) -> None:
        """Invalida todo el caché."""
        with self._lock:
            self._cache.clear()
```

### 9.2 Invalidación Automática

El caché se invalida automáticamente en operaciones de escritura:

```python
@router.post("")
async def crear_vencimiento(request: VencimientoCreate):
    # ... crear ...
    _vencimientos_cache.invalidate()
    return response

@router.put("/{vencimiento_id}")
async def actualizar_vencimiento(vencimiento_id: int, request: VencimientoUpdate):
    # ... actualizar ...
    _vencimientos_cache.invalidate()
    return response

@router.delete("/{vencimiento_id}")
async def eliminar_vencimiento(vencimiento_id: int):
    # ... eliminar ...
    _vencimientos_cache.invalidate()
    return {"mensaje": "Eliminado"}
```

### 9.3 Forzar Datos Frescos

```http
GET /api/v1/vencimientos?use_cache=false
```

---

## 10. Sistema de Notificaciones

### 10.1 Tablas

```sql
-- Alertas de vencimientos
CREATE TABLE alertas_vencimientos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vencimiento_id INT NOT NULL,
    tipo_alerta ENUM('3_dias', '1_dia', 'hoy', 'vencido') NOT NULL,
    enviada BOOLEAN DEFAULT FALSE,
    fecha_envio DATETIME,
    canal ENUM('email', 'push', 'in_app') DEFAULT 'in_app',
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vencimiento_id) REFERENCES vencimientos(id) ON DELETE CASCADE,
    UNIQUE KEY uk_vencimiento_tipo (vencimiento_id, tipo_alerta)
);

-- Notificaciones de usuario
CREATE TABLE notificaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT,
    tipo ENUM('alerta', 'info', 'exito', 'error') DEFAULT 'info',
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT,
    leida BOOLEAN DEFAULT FALSE,
    fecha_lectura DATETIME,
    expediente_numero VARCHAR(50),
    vencimiento_id INT,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    expira_en DATETIME,
    INDEX idx_usuario_leida (usuario_id, leida),
    INDEX idx_creado (creado_en)
);

-- Configuración de alertas por usuario
CREATE TABLE configuracion_alertas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    alertas_email BOOLEAN DEFAULT TRUE,
    alertas_push BOOLEAN DEFAULT TRUE,
    alertas_in_app BOOLEAN DEFAULT TRUE,
    dias_anticipacion JSON DEFAULT '[3, 1, 0]',
    hora_envio TIME DEFAULT '08:00:00',
    activo BOOLEAN DEFAULT TRUE,
    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_usuario (usuario_id)
);
```

### 10.2 Endpoints de Notificaciones

**Base URL:** `/api/v1/notificaciones`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Listar notificaciones |
| `/estadisticas` | GET | Estadísticas |
| `/no-leidas/count` | GET | Contador para polling |
| `/{id}/leer` | POST | Marcar como leída |
| `/leer-todas` | POST | Marcar todas leídas |
| `/configuracion` | GET | Obtener configuración |
| `/configuracion` | PUT | Actualizar configuración |
| `/verificar-vencimientos` | POST | Generar alertas manualmente |

### 10.3 Servicio de Alertas

**Ubicación:** `application/services/alertas_service.py`

```python
class AlertasService:
    async def verificar_y_crear_alertas(self) -> List[Alerta]:
        """
        Verifica vencimientos próximos y crea alertas pendientes.
        Ejecutar periódicamente (ej: cada hora).
        """
        alertas_creadas = []

        # Obtener vencimientos que necesitan alerta
        vencimientos = await self._obtener_vencimientos_para_alertar()

        for v in vencimientos:
            dias = v.dias_restantes

            # Determinar tipo de alerta
            if dias <= 0:
                tipo = 'hoy' if dias == 0 else 'vencido'
            elif dias <= 1:
                tipo = '1_dia'
            elif dias <= 3:
                tipo = '3_dias'
            else:
                continue

            # Crear si no existe
            if not await self._alerta_existe(v.id, tipo):
                alerta = await self._crear_alerta(v, tipo)
                alertas_creadas.append(alerta)

                # Crear notificación in-app
                await self._crear_notificacion(v, tipo)

        return alertas_creadas
```

---

## 11. Herramientas MCP

### 11.1 Tools Disponibles

El servidor MCP expone las siguientes herramientas para vencimientos:

| Tool | Descripción | Parámetros |
|------|-------------|------------|
| `vencimientos_pendientes` | Lista vencimientos pendientes | `expediente_numero?`, `limite?` |
| `vencimientos_urgentes` | Vencimientos próximos a vencer | `dias` (default: 7), `limite?` |
| `vencimientos_vencidos` | Vencimientos pasados de fecha | `expediente_numero?`, `limite?` |
| `proximos_vencimientos` | Calendario agrupado | `dias`, `agrupar_por` |
| `resumen_vencimientos` | Estadísticas generales | - |
| `atender_vencimiento` | Marcar como atendido | `vencimiento_id`, `notas?` |
| `cancelar_vencimiento` | Cancelar vencimiento | `vencimiento_id`, `notas?` |
| `verificar_dia_habil` | Verificar si fecha es hábil | `fecha` |
| `calcular_vencimiento` | Calcular fecha dado plazo | `fecha_inicio`, `dias`, `dias_habiles?` |
| `feriados/{anio}` | Lista de feriados por año | `anio` |

### 11.2 Ejemplo de Uso

```json
// Consultar vencimientos urgentes
{
  "tool": "vencimientos_urgentes",
  "arguments": {
    "dias": 3,
    "limite": 10
  }
}

// Marcar como atendido
{
  "tool": "atender_vencimiento",
  "arguments": {
    "vencimiento_id": 123,
    "notas": "Contestación de demanda presentada"
  }
}

// Calcular fecha de vencimiento
{
  "tool": "calcular_vencimiento",
  "arguments": {
    "fecha_inicio": "2024-12-02",
    "dias": 15,
    "dias_habiles": true
  }
}
```

---

## Archivos Clave

### Backend

| Archivo | Propósito |
|---------|-----------|
| `core/procesador_pdf/analizador_vencimientos.py` | Detección automática |
| `core/config/vencimientos_config.py` | Configuración |
| `application/services/feriados_service.py` | Días hábiles |
| `application/services/alertas_service.py` | Sistema de alertas |
| `presentation/api/rest/routers/vencimientos.py` | Endpoints REST |
| `presentation/api/rest/routers/notificaciones.py` | Notificaciones |

### Frontend

| Archivo | Propósito |
|---------|-----------|
| `pages/vencimientos/VencimientosPage.tsx` | Página principal |
| `components/dashboard/VencimientosWidget.tsx` | Widget dashboard |
| `components/vencimientos/VencimientoCard.tsx` | Tarjeta individual |
| `stores/vencimientosStore.ts` | Estado global |
| `api/vencimientosApi.ts` | Cliente API |
| `types/vencimiento.ts` | Tipos TypeScript |

---

**Fin de la Documentación**
