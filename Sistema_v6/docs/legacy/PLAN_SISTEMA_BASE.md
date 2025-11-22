# Plan de Implementación: Sistema JSON BASE Permanente

## Resumen Ejecutivo

Este documento describe la implementación del **Sistema JSON BASE Permanente** para el monitoreo de expedientes del PJN. El sistema permitirá:

- Mantener un universo completo de expedientes (`listado_base.json`) que crece con cada extracción
- Detectar cambios en campos críticos: situación, última actuación, dependencia
- Visualizar comparaciones detalladas en la interfaz frontend
- Estrategia dual: extracciones parciales frecuentes + extracciones totales periódicas

---

## Estado Actual vs. Estado Objetivo

### Estado Actual (AS-IS)

**Backend:**
- ✅ Archivos timestamped: `listado_YYYY-MM-DD_HH-MM-SS.json`
- ✅ Comparación básica: detecta nuevos/eliminados por número
- ❌ NO detecta cambios en campos (situación, última actuación, dependencia)
- ❌ NO existe JSON BASE permanente
- ✅ Auto-busca archivo anterior para comparar (segundo más reciente)

**Frontend:**
- ✅ Muestra métricas básicas (total, nuevos, eliminados)
- ❌ Sección de comparación con datos hardcodeados (0s)
- ❌ NO consume `sesion.comparacion` del backend
- ❌ NO visualiza cambios detallados

### Estado Objetivo (TO-BE)

**Backend:**
- ✅ JSON BASE permanente: `listado_base.json` (nunca se elimina)
- ✅ Snapshots timestamped: `listado_YYYY-MM-DD_HH-MM-SS.json` (histórico)
- ✅ Comparación detallada: detecta cambios en situación, última actuación, dependencia
- ✅ Estrategia de merge: agregar nuevos + actualizar existentes
- ✅ API endpoint para consultar BASE

**Frontend:**
- ✅ Panel de comparación detallada con datos reales
- ✅ Visualización de cambios por tipo (nuevos, eliminados, modificados)
- ✅ Listas expandibles con detalles de cada cambio
- ✅ Indicadores visuales (badges, colores) para cada tipo de cambio
- ✅ Tipos TypeScript completos para comparación detallada

---

## Arquitectura del Sistema de 3 Capas

```
┌─────────────────────────────────────────────────────────────┐
│ CAPA 1: JSON BASE (Universo Completo)                      │
│ - Archivo: listado_base.json                               │
│ - Contenido: TODOS los expedientes conocidos               │
│ - Estrategia: ADD + UPDATE (nunca DELETE)                  │
│ - Crece indefinidamente                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ CAPA 2: JSON SISTEMA (Expedientes Seleccionados)           │
│ - Archivo: sistema_YYYY-MM-DD.json                         │
│ - Contenido: Subset seleccionado por el usuario            │
│ - Detalles completos: actuaciones, adjuntos, metadata      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ CAPA 3: WORKSPACE (Archivos de Trabajo)                    │
│ - Directorio: ./Sistema_v6/data/expedientes/               │
│ - Estructura: {id}_{numero}/actuaciones/adjuntos/          │
│ - Contenido: JSONs, PDFs, documentos del usuario           │
└─────────────────────────────────────────────────────────────┘
```

---

## Fases de Implementación

### FASE 1: Backend - Comparación Detallada ⚙️

**Objetivo:** Extender `comparar_con_base()` para detectar cambios en campos.

#### Archivo: `Sistema_v6/extraccion_masiva/models.py`

**Ubicación:** Agregar nuevos modelos después de `ExpedienteListado` (línea 48)

```python
@dataclass
class CambioSituacion:
    """Cambio en la situación de un expediente."""
    numero: str
    caratula: str
    situacion_anterior: str
    situacion_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "situacion_anterior": self.situacion_anterior,
            "situacion_nueva": self.situacion_nueva
        }


@dataclass
class CambioUltimaActuacion:
    """Cambio en la última actuación de un expediente."""
    numero: str
    caratula: str
    ultima_actuacion_anterior: str
    ultima_actuacion_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "ultima_actuacion_anterior": self.ultima_actuacion_anterior,
            "ultima_actuacion_nueva": self.ultima_actuacion_nueva
        }


@dataclass
class CambioDependencia:
    """Cambio en la dependencia de un expediente."""
    numero: str
    caratula: str
    dependencia_anterior: str
    dependencia_nueva: str

    def to_dict(self) -> Dict:
        return {
            "numero": self.numero,
            "caratula": self.caratula,
            "dependencia_anterior": self.dependencia_anterior,
            "dependencia_nueva": self.dependencia_nueva
        }


@dataclass
class ComparacionDetallada:
    """Comparación detallada entre listados."""
    nuevos: List[ExpedienteListado]
    eliminados: List[ExpedienteListado]
    cambios_situacion: List[CambioSituacion]
    cambios_ultima_actuacion: List[CambioUltimaActuacion]
    cambios_dependencia: List[CambioDependencia]
    total_cambios: int

    def to_dict(self) -> Dict:
        return {
            "nuevos": [e.to_dict() for e in self.nuevos],
            "eliminados": [e.to_dict() for e in self.eliminados],
            "cambios_situacion": [c.to_dict() for c in self.cambios_situacion],
            "cambios_ultima_actuacion": [c.to_dict() for c in self.cambios_ultima_actuacion],
            "cambios_dependencia": [c.to_dict() for c in self.cambios_dependencia],
            "total_cambios": self.total_cambios,
            "total_nuevos": len(self.nuevos),
            "total_eliminados": len(self.eliminados),
            "total_modificados": (
                len(self.cambios_situacion) +
                len(self.cambios_ultima_actuacion) +
                len(self.cambios_dependencia)
            )
        }
```

#### Archivo: `Sistema_v6/extraccion_masiva/extractor_masivo.py`

**Ubicación:** Reemplazar método `comparar_con_base()` (líneas 293-342)

```python
def comparar_con_base(
    self,
    listado_nuevo_path: str,
    listado_base_path: Optional[str] = None
) -> Optional[ComparacionDetallada]:
    """
    Compara un listado nuevo con el BASE y detecta cambios detallados.

    Cambios detectados:
    - Nuevos expedientes
    - Expedientes eliminados
    - Cambios en situación
    - Cambios en última actuación
    - Cambios en dependencia

    Args:
        listado_nuevo_path: Ruta al listado nuevo
        listado_base_path: Ruta al BASE (si None, busca automáticamente)

    Returns:
        ComparacionDetallada con todos los cambios detectados
    """
    from .models import (
        ComparacionDetallada,
        CambioSituacion,
        CambioUltimaActuacion,
        CambioDependencia,
        ExpedienteListado
    )

    # Auto-buscar BASE si no se proporciona
    if listado_base_path is None:
        # Buscar listado_base.json primero
        base_permanente = self.data_dir / "listado_base.json"
        if base_permanente.exists():
            listado_base_path = str(base_permanente)
        else:
            # Fallback: buscar segundo archivo más reciente
            archivos = sorted(self.data_dir.glob("listado_*.json"), reverse=True)
            if len(archivos) < 2:
                print("⚠️ No hay BASE para comparar (primera extracción)")
                return None
            listado_base_path = str(archivos[1])

    print(f"📊 Comparando con BASE: {listado_base_path}")

    # Cargar ambos listados
    try:
        with open(listado_base_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
        with open(listado_nuevo_path, 'r', encoding='utf-8') as f:
            nuevo_data = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando archivos para comparación: {e}")
        return None

    # Convertir a diccionarios indexados por número
    base_dict = {
        exp["numero"]: exp
        for exp in base_data.get("expedientes", [])
    }
    nuevo_dict = {
        exp["numero"]: exp
        for exp in nuevo_data.get("expedientes", [])
    }

    # Conjuntos de números
    numeros_base = set(base_dict.keys())
    numeros_nuevo = set(nuevo_dict.keys())

    # 1. NUEVOS
    nuevos_numeros = numeros_nuevo - numeros_base
    nuevos = [
        ExpedienteListado(**nuevo_dict[num])
        for num in nuevos_numeros
    ]

    # 2. ELIMINADOS
    eliminados_numeros = numeros_base - numeros_nuevo
    eliminados = [
        ExpedienteListado(**base_dict[num])
        for num in eliminados_numeros
    ]

    # 3. COMUNES (para detectar cambios)
    comunes = numeros_base & numeros_nuevo

    cambios_situacion = []
    cambios_ultima_actuacion = []
    cambios_dependencia = []

    for numero in comunes:
        exp_base = base_dict[numero]
        exp_nuevo = nuevo_dict[numero]

        # Detectar cambio en SITUACION
        if exp_base.get("situacion") != exp_nuevo.get("situacion"):
            cambios_situacion.append(CambioSituacion(
                numero=numero,
                caratula=exp_nuevo.get("caratula", ""),
                situacion_anterior=exp_base.get("situacion", ""),
                situacion_nueva=exp_nuevo.get("situacion", "")
            ))

        # Detectar cambio en ULTIMA_ACTUACION
        if exp_base.get("ultima_actuacion") != exp_nuevo.get("ultima_actuacion"):
            cambios_ultima_actuacion.append(CambioUltimaActuacion(
                numero=numero,
                caratula=exp_nuevo.get("caratula", ""),
                ultima_actuacion_anterior=exp_base.get("ultima_actuacion", ""),
                ultima_actuacion_nueva=exp_nuevo.get("ultima_actuacion", "")
            ))

        # Detectar cambio en DEPENDENCIA
        if exp_base.get("dependencia") != exp_nuevo.get("dependencia"):
            cambios_dependencia.append(CambioDependencia(
                numero=numero,
                caratula=exp_nuevo.get("caratula", ""),
                dependencia_anterior=exp_base.get("dependencia", ""),
                dependencia_nueva=exp_nuevo.get("dependencia", "")
            ))

    total_cambios = (
        len(nuevos) +
        len(eliminados) +
        len(cambios_situacion) +
        len(cambios_ultima_actuacion) +
        len(cambios_dependencia)
    )

    comparacion = ComparacionDetallada(
        nuevos=nuevos,
        eliminados=eliminados,
        cambios_situacion=cambios_situacion,
        cambios_ultima_actuacion=cambios_ultima_actuacion,
        cambios_dependencia=cambios_dependencia,
        total_cambios=total_cambios
    )

    print(f"✅ Comparación completada:")
    print(f"   📌 Nuevos: {len(nuevos)}")
    print(f"   📌 Eliminados: {len(eliminados)}")
    print(f"   📌 Cambios situación: {len(cambios_situacion)}")
    print(f"   📌 Cambios última actuación: {len(cambios_ultima_actuacion)}")
    print(f"   📌 Cambios dependencia: {len(cambios_dependencia)}")

    return comparacion
```

**Criterios de Testing:**
- [ ] Detecta expedientes nuevos correctamente
- [ ] Detecta expedientes eliminados correctamente
- [ ] Detecta cambios en situación
- [ ] Detecta cambios en última actuación
- [ ] Detecta cambios en dependencia
- [ ] Auto-busca `listado_base.json` si existe
- [ ] Fallback a segundo archivo más reciente si no existe BASE

---

### FASE 2: Backend - JSON BASE Permanente 📁

**Objetivo:** Implementar gestión de `listado_base.json` con estrategia de merge.

#### Archivo: `Sistema_v6/extraccion_masiva/extractor_masivo.py`

**Ubicación:** Agregar método después de `comparar_con_base()`

```python
def actualizar_base_permanente(
    self,
    listado_nuevo_path: str
) -> str:
    """
    Actualiza el JSON BASE permanente con los datos del listado nuevo.

    Estrategia de Merge:
    1. Si no existe listado_base.json → crearlo con el nuevo listado
    2. Si existe:
       - AGREGAR expedientes nuevos
       - ACTUALIZAR expedientes existentes (situación, última actuación, etc.)
       - NUNCA ELIMINAR expedientes

    Args:
        listado_nuevo_path: Ruta al listado recién extraído

    Returns:
        Ruta al listado_base.json actualizado
    """
    base_path = self.data_dir / "listado_base.json"

    # Cargar listado nuevo
    try:
        with open(listado_nuevo_path, 'r', encoding='utf-8') as f:
            nuevo_data = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando listado nuevo: {e}")
        raise

    # Si no existe BASE, crearlo
    if not base_path.exists():
        print(f"📝 Creando BASE permanente por primera vez...")
        with open(base_path, 'w', encoding='utf-8') as f:
            json.dump(nuevo_data, f, ensure_ascii=False, indent=2)
        print(f"✅ BASE creado: {base_path}")
        return str(base_path)

    # Cargar BASE existente
    try:
        with open(base_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
    except Exception as e:
        print(f"❌ Error cargando BASE existente: {e}")
        raise

    # Convertir a diccionarios indexados por número
    base_dict = {
        exp["numero"]: exp
        for exp in base_data.get("expedientes", [])
    }
    nuevo_dict = {
        exp["numero"]: exp
        for exp in nuevo_data.get("expedientes", [])
    }

    # Contadores
    agregados = 0
    actualizados = 0

    # MERGE: Agregar nuevos + Actualizar existentes
    for numero, exp_nuevo in nuevo_dict.items():
        if numero not in base_dict:
            # AGREGAR nuevo
            base_dict[numero] = exp_nuevo
            agregados += 1
        else:
            # ACTUALIZAR existente (solo si hay cambios)
            exp_base = base_dict[numero]
            cambio = False

            # Comparar cada campo y actualizar si cambió
            for campo in ["situacion", "ultima_actuacion", "dependencia", "caratula", "fecha_inicio"]:
                if exp_base.get(campo) != exp_nuevo.get(campo):
                    exp_base[campo] = exp_nuevo.get(campo)
                    cambio = True

            if cambio:
                actualizados += 1

    # Guardar BASE actualizado
    base_data["expedientes"] = list(base_dict.values())
    base_data["metadata"] = {
        "total": len(base_dict),
        "ultima_actualizacion": datetime.now().isoformat(),
        "total_agregados_ultima_vez": agregados,
        "total_actualizados_ultima_vez": actualizados
    }

    with open(base_path, 'w', encoding='utf-8') as f:
        json.dump(base_data, f, ensure_ascii=False, indent=2)

    print(f"✅ BASE actualizado:")
    print(f"   📌 Total en BASE: {len(base_dict)}")
    print(f"   📌 Agregados: {agregados}")
    print(f"   📌 Actualizados: {actualizados}")

    return str(base_path)
```

#### Archivo: `Sistema_v6/extraccion_masiva/extractor_masivo.py`

**Ubicación:** Modificar método `extraer_listado_completo()` (línea ~270)

**Cambio:** Agregar llamada a `actualizar_base_permanente()` después de guardar snapshot

```python
async def extraer_listado_completo(
    self,
    username: str,
    password: str,
    fecha_corte: Optional[str] = None,
    sesion: Optional[SesionExtraccion] = None,
    callback_progreso: Optional[Callable] = None,
) -> Tuple[str, int]:
    """Extrae listado completo de expedientes del PJN."""

    # ... código existente ...

    # Guardar snapshot timestamped (EXISTENTE)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"listado_{timestamp}.json"
    listado_path = self.data_dir / filename

    with open(listado_path, 'w', encoding='utf-8') as f:
        json.dump(listado_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Listado guardado: {listado_path}")

    # NUEVO: Actualizar BASE permanente
    try:
        base_path = self.actualizar_base_permanente(str(listado_path))
        print(f"✅ BASE permanente actualizado: {base_path}")
    except Exception as e:
        print(f"⚠️ Error actualizando BASE (no crítico): {e}")

    return str(listado_path), total_expedientes
```

**Criterios de Testing:**
- [ ] Primera extracción crea `listado_base.json`
- [ ] Extracciones subsiguientes agregan nuevos expedientes al BASE
- [ ] Extracciones subsiguientes actualizan expedientes existentes
- [ ] El BASE NUNCA elimina expedientes
- [ ] Metadata incluye timestamp y estadísticas de última actualización

---

### FASE 3: Frontend - Tipos TypeScript 📘

**Objetivo:** Agregar tipos completos para comparación detallada.

#### Archivo: `Sistema_v6/frontend/src/types/expediente.ts`

**Ubicación:** Reemplazar interface `Comparacion` existente (líneas 91-100)

```typescript
// ============================================================================
// COMPARACIÓN DETALLADA
// ============================================================================

export interface CambioSituacion {
  numero: string
  caratula: string
  situacion_anterior: string
  situacion_nueva: string
}

export interface CambioUltimaActuacion {
  numero: string
  caratula: string
  ultima_actuacion_anterior: string
  ultima_actuacion_nueva: string
}

export interface CambioDependencia {
  numero: string
  caratula: string
  dependencia_anterior: string
  dependencia_nueva: string
}

export interface ComparacionDetallada {
  nuevos: ExpedienteListado[]
  eliminados: ExpedienteListado[]
  cambios_situacion: CambioSituacion[]
  cambios_ultima_actuacion: CambioUltimaActuacion[]
  cambios_dependencia: CambioDependencia[]
  total_cambios: number
  total_nuevos: number
  total_eliminados: number
  total_modificados: number
}

// Mantener interface antigua para compatibilidad
export interface Comparacion {
  nuevos: number
  eliminados: number
  comunes: number
}
```

#### Archivo: `Sistema_v6/frontend/src/stores/expedientesStore.ts`

**Ubicación:** Modificar interface `ExtraccionMasivaState` (línea ~44)

```typescript
import type { ComparacionDetallada } from '@/types/expediente'

interface ExtraccionMasivaState {
  // ... campos existentes ...

  // CAMBIAR de Comparacion a ComparacionDetallada
  comparacion: ComparacionDetallada | null
}
```

**Ubicación:** Modificar método `obtenerProgreso()` (línea ~657)

```typescript
// Dentro del método obtenerProgreso, al mapear comparacion:
const comparacion = data.comparacion as ComparacionDetallada | null

set({
  extraccionMasiva: {
    ...state.extraccionMasiva,
    comparacion: comparacion,
  }
})
```

**Criterios de Testing:**
- [ ] TypeScript compila sin errores
- [ ] Tipos importados correctamente en store
- [ ] Tipos importados correctamente en componentes

---

### FASE 4: Frontend - Componente de Comparación Detallada 🎨

**Objetivo:** Crear componente visual para mostrar cambios detallados.

#### Archivo NUEVO: `Sistema_v6/frontend/src/components/expedientes/ComparacionDetalladaPanel.tsx`

```typescript
import React, { useState } from 'react'
import { ChevronDown, ChevronRight, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import type { ComparacionDetallada } from '@/types/expediente'

interface Props {
  comparacion: ComparacionDetallada
}

export const ComparacionDetalladaPanel: React.FC<Props> = ({ comparacion }) => {
  const [expandidoNuevos, setExpandidoNuevos] = useState(false)
  const [expandidoEliminados, setExpandidoEliminados] = useState(false)
  const [expandidoSituacion, setExpandidoSituacion] = useState(false)
  const [expandidoUltimaActuacion, setExpandidoUltimaActuacion] = useState(false)
  const [expandidoDependencia, setExpandidoDependencia] = useState(false)

  return (
    <div className="space-y-4">
      {/* RESUMEN */}
      <div className="grid grid-cols-3 gap-4">
        {/* Card Nuevos */}
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Nuevos</span>
            </div>
            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {comparacion.total_nuevos}
            </span>
          </div>
        </div>

        {/* Card Eliminados */}
        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <span className="text-sm font-medium text-red-900 dark:text-red-100">Eliminados</span>
            </div>
            <span className="text-2xl font-bold text-red-600 dark:text-red-400">
              {comparacion.total_eliminados}
            </span>
          </div>
        </div>

        {/* Card Modificados */}
        <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              <span className="text-sm font-medium text-amber-900 dark:text-amber-100">Modificados</span>
            </div>
            <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {comparacion.total_modificados}
            </span>
          </div>
        </div>
      </div>

      {/* DETALLES EXPANDIBLES */}
      <div className="space-y-2">
        {/* Nuevos */}
        {comparacion.total_nuevos > 0 && (
          <div className="border border-blue-200 dark:border-blue-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoNuevos(!expandidoNuevos)}
              className="w-full px-4 py-3 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-blue-900 dark:text-blue-100">
                Expedientes Nuevos ({comparacion.total_nuevos})
              </span>
              {expandidoNuevos ? (
                <ChevronDown className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              )}
            </button>
            {expandidoNuevos && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-2">
                  {comparacion.nuevos.map((exp) => (
                    <li key={exp.numero} className="text-sm border-l-2 border-blue-400 pl-3 py-1">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{exp.numero}</div>
                      <div className="text-gray-600 dark:text-gray-400">{exp.caratula}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-500">
                        {exp.dependencia} • {exp.situacion}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Eliminados */}
        {comparacion.total_eliminados > 0 && (
          <div className="border border-red-200 dark:border-red-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoEliminados(!expandidoEliminados)}
              className="w-full px-4 py-3 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-red-900 dark:text-red-100">
                Expedientes Eliminados ({comparacion.total_eliminados})
              </span>
              {expandidoEliminados ? (
                <ChevronDown className="h-5 w-5 text-red-600 dark:text-red-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
            </button>
            {expandidoEliminados && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-2">
                  {comparacion.eliminados.map((exp) => (
                    <li key={exp.numero} className="text-sm border-l-2 border-red-400 pl-3 py-1">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{exp.numero}</div>
                      <div className="text-gray-600 dark:text-gray-400">{exp.caratula}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Situación */}
        {comparacion.cambios_situacion.length > 0 && (
          <div className="border border-amber-200 dark:border-amber-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoSituacion(!expandidoSituacion)}
              className="w-full px-4 py-3 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-amber-900 dark:text-amber-100">
                Cambios de Situación ({comparacion.cambios_situacion.length})
              </span>
              {expandidoSituacion ? (
                <ChevronDown className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              )}
            </button>
            {expandidoSituacion && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_situacion.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-amber-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                          {cambio.situacion_anterior}
                        </span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/50 rounded font-medium">
                          {cambio.situacion_nueva}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Última Actuación */}
        {comparacion.cambios_ultima_actuacion.length > 0 && (
          <div className="border border-purple-200 dark:border-purple-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoUltimaActuacion(!expandidoUltimaActuacion)}
              className="w-full px-4 py-3 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-purple-900 dark:text-purple-100">
                Cambios de Última Actuación ({comparacion.cambios_ultima_actuacion.length})
              </span>
              {expandidoUltimaActuacion ? (
                <ChevronDown className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              )}
            </button>
            {expandidoUltimaActuacion && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_ultima_actuacion.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-purple-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="space-y-1">
                        <div className="text-xs">
                          <span className="text-gray-500">Anterior:</span>{' '}
                          <span className="text-gray-700 dark:text-gray-300">{cambio.ultima_actuacion_anterior}</span>
                        </div>
                        <div className="text-xs">
                          <span className="text-gray-500">Nueva:</span>{' '}
                          <span className="text-purple-700 dark:text-purple-300 font-medium">
                            {cambio.ultima_actuacion_nueva}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Dependencia */}
        {comparacion.cambios_dependencia.length > 0 && (
          <div className="border border-green-200 dark:border-green-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoDependencia(!expandidoDependencia)}
              className="w-full px-4 py-3 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-green-900 dark:text-green-100">
                Cambios de Dependencia ({comparacion.cambios_dependencia.length})
              </span>
              {expandidoDependencia ? (
                <ChevronDown className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-green-600 dark:text-green-400" />
              )}
            </button>
            {expandidoDependencia && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_dependencia.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-green-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                          {cambio.dependencia_anterior}
                        </span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 rounded font-medium">
                          {cambio.dependencia_nueva}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
```

#### Archivo: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`

**Ubicación:** Reemplazar sección de comparación (líneas 958-987)

```typescript
import { ComparacionDetalladaPanel } from './ComparacionDetalladaPanel'

// ... dentro del componente, reemplazar sección de comparación:

{/* Comparación con BASE (si existe) */}
{extraccionMasiva.comparacion && (
  <div className="border-t pt-4">
    <h3 className="text-lg font-semibold mb-4">Comparación con BASE</h3>
    <ComparacionDetalladaPanel comparacion={extraccionMasiva.comparacion} />
  </div>
)}
```

**Criterios de Testing:**
- [ ] Componente renderiza sin errores
- [ ] Cards de resumen muestran totales correctos
- [ ] Secciones expandibles funcionan correctamente
- [ ] Scroll funciona en listas largas (max-h-64)
- [ ] Dark mode funciona correctamente
- [ ] Muestra todos los tipos de cambios detectados

---

### FASE 5: Integración y Testing Final 🧪

**Objetivo:** Conectar todos los componentes y validar flujo completo.

#### Checklist de Integración

**Backend:**
- [ ] `comparar_con_base()` retorna `ComparacionDetallada` en lugar de dict básico
- [ ] `actualizar_base_permanente()` se ejecuta después de cada extracción
- [ ] Router mapea correctamente `comparacion` a `sesion.to_dict()`
- [ ] Endpoint `/sesion/{session_id}` incluye comparación detallada

**Frontend:**
- [ ] Store importa tipos correctos desde `@/types/expediente`
- [ ] Store mapea `comparacion` como `ComparacionDetallada | null`
- [ ] Componente `ExtraccionMasivaDialog` importa `ComparacionDetalladaPanel`
- [ ] Componente renderiza panel solo si `comparacion` existe

#### Escenarios de Testing

**Escenario 1: Primera Extracción (Sin BASE)**
```
GIVEN: No existe listado_base.json
WHEN: Se ejecuta extracción masiva
THEN:
  - Se crea listado_base.json con todos los expedientes
  - Se crea snapshot timestamped
  - comparacion es null (no hay BASE anterior)
  - Frontend NO muestra sección de comparación
```

**Escenario 2: Segunda Extracción (Con Nuevos)**
```
GIVEN: Existe listado_base.json con 100 expedientes
WHEN: Se ejecuta extracción masiva que encuentra 105 expedientes
THEN:
  - Se actualiza listado_base.json (105 total)
  - comparacion.total_nuevos = 5
  - comparacion.total_eliminados = 0
  - comparacion.total_modificados = 0
  - Frontend muestra 5 expedientes en sección "Nuevos"
```

**Escenario 3: Tercera Extracción (Con Cambios)**
```
GIVEN: Existe listado_base.json con 105 expedientes
WHEN: Se ejecuta extracción que detecta:
  - 2 expedientes cambiaron situación
  - 5 expedientes cambiaron última actuación
  - 1 expediente cambió dependencia
  - 3 expedientes nuevos
THEN:
  - comparacion.total_nuevos = 3
  - comparacion.total_modificados = 8 (2+5+1)
  - Frontend muestra todas las secciones expandibles
  - Cada sección tiene el número correcto de items
```

**Escenario 4: Procesamiento de Seleccionados**
```
GIVEN: Usuario selecciona 10 expedientes del listado
WHEN: Se ejecuta procesamiento con procesar_con_pdf=true
THEN:
  - NO se actualiza listado_base.json
  - NO se genera comparación (fase="procesamiento")
  - Frontend muestra archivos_descargados
  - Frontend NO muestra "Páginas Procesadas"
  - Frontend NO muestra sección de comparación
```

---

## Estructura de Archivos Final

```
Sistema_v6/
├── extraccion_masiva/
│   ├── models.py                    # ✅ MODIFICADO (Fase 1)
│   │   ├── CambioSituacion          # NUEVO
│   │   ├── CambioUltimaActuacion    # NUEVO
│   │   ├── CambioDependencia        # NUEVO
│   │   └── ComparacionDetallada     # NUEVO
│   │
│   ├── extractor_masivo.py          # ✅ MODIFICADO (Fases 1 y 2)
│   │   ├── comparar_con_base()      # REEMPLAZADO
│   │   ├── actualizar_base_permanente()  # NUEVO
│   │   └── extraer_listado_completo()    # MODIFICADO
│   │
│   └── gestor_batch.py              # ✅ SIN CAMBIOS
│
├── data/
│   └── extraccion_masiva/
│       ├── listado_base.json        # 📁 NUEVO - BASE permanente
│       ├── listado_2025-01-15_10-30-00.json  # Snapshots timestamped
│       ├── listado_2025-01-16_14-20-00.json
│       └── ...
│
└── frontend/
    ├── src/
    │   ├── types/
    │   │   └── expediente.ts        # ✅ MODIFICADO (Fase 3)
    │   │
    │   ├── stores/
    │   │   └── expedientesStore.ts  # ✅ MODIFICADO (Fase 3)
    │   │
    │   └── components/
    │       └── expedientes/
    │           ├── ExtraccionMasivaDialog.tsx  # ✅ MODIFICADO (Fase 4)
    │           └── ComparacionDetalladaPanel.tsx  # 📄 NUEVO (Fase 4)
    └── ...
```

---

## API Contracts

### GET `/api/extraccion-masiva/sesion/{session_id}`

**Response con comparación detallada:**

```json
{
  "session_id": "uuid-1234",
  "estado": "completado",
  "fase": "listado",
  "progreso_actual": 100,
  "progreso_total": 100,
  "mensaje": "Extracción completada",
  "listado_path": "/data/extraccion_masiva/listado_2025-01-15_10-30-00.json",
  "comparacion": {
    "nuevos": [
      {
        "numero": "FPA 001234/2024",
        "caratula": "NUEVO EXPEDIENTE vs. DEMANDADO",
        "dependencia": "Juzgado Federal Nro 1",
        "situacion": "En trámite",
        "fecha_inicio": "2024-01-15",
        "ultima_actuacion": "2024-01-15"
      }
    ],
    "eliminados": [],
    "cambios_situacion": [
      {
        "numero": "FPA 000999/2023",
        "caratula": "EXPEDIENTE ARCHIVADO vs. PARTE",
        "situacion_anterior": "En trámite",
        "situacion_nueva": "Archivado"
      }
    ],
    "cambios_ultima_actuacion": [
      {
        "numero": "FPA 001000/2024",
        "caratula": "EXPEDIENTE ACTIVO vs. PARTE",
        "ultima_actuacion_anterior": "2024-01-10",
        "ultima_actuacion_nueva": "2024-01-15"
      }
    ],
    "cambios_dependencia": [],
    "total_cambios": 3,
    "total_nuevos": 1,
    "total_eliminados": 0,
    "total_modificados": 2
  },
  "archivos_descargados": 0,
  "paginas_procesadas": 5
}
```

---

## Estrategia de Migración

### Para Usuarios con Datos Existentes

**Opción 1: Migración Automática (Recomendada)**

Al ejecutar la primera extracción después de la actualización:

1. Sistema detecta que NO existe `listado_base.json`
2. Busca el archivo timestamped más reciente (ej: `listado_2025-01-14_15-00-00.json`)
3. Lo copia como `listado_base.json`
4. Continúa con la extracción normal
5. Genera comparación entre BASE (recién creado) y nuevo listado

**Opción 2: Script de Migración Manual**

Crear script `Sistema_v6/scripts/migrar_a_base_permanente.py`:

```python
"""
Script de migración: Crea BASE permanente desde el listado más reciente.

Uso:
    python Sistema_v6/scripts/migrar_a_base_permanente.py
"""

import json
from pathlib import Path
from datetime import datetime

def migrar():
    data_dir = Path("./Sistema_v6/data/extraccion_masiva")

    # Buscar listado más reciente
    archivos = sorted(data_dir.glob("listado_*.json"), reverse=True)

    if not archivos:
        print("❌ No hay listados para migrar")
        return

    listado_reciente = archivos[0]
    print(f"📁 Listado más reciente: {listado_reciente.name}")

    # Crear BASE
    base_path = data_dir / "listado_base.json"

    if base_path.exists():
        print("⚠️ Ya existe listado_base.json - no se sobrescribirá")
        return

    # Copiar contenido
    with open(listado_reciente, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Agregar metadata
    data["metadata"] = {
        "total": len(data.get("expedientes", [])),
        "creado_desde": listado_reciente.name,
        "fecha_migracion": datetime.now().isoformat(),
    }

    # Guardar BASE
    with open(base_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ BASE creado: {base_path}")
    print(f"   Total expedientes: {data['metadata']['total']}")

if __name__ == "__main__":
    migrar()
```

---

## Monitoreo y Métricas

### Métricas a Trackear

**Backend (Logs):**
- Total de expedientes en BASE
- Expedientes agregados por extracción
- Expedientes actualizados por extracción
- Tipos de cambios detectados (situación, última actuación, dependencia)
- Tiempo de comparación

**Frontend (UI):**
- Total nuevos (badge azul)
- Total eliminados (badge rojo)
- Total modificados (badge ámbar)
- Desglose por tipo de cambio

### Logs de Ejemplo

```
✅ Extracción masiva completada
   📊 Resultados:
      - Expedientes extraídos: 105
      - Tiempo total: 45.2s

📝 Actualizando BASE permanente...
   📌 Antes: 100 expedientes
   📌 Agregados: 5
   📌 Actualizados: 8
   📌 Después: 105 expedientes
   ✅ BASE actualizado

📊 Comparación con BASE:
   📌 Nuevos: 5
   📌 Eliminados: 0
   📌 Cambios situación: 2
   📌 Cambios última actuación: 5
   📌 Cambios dependencia: 1
   📌 Total cambios: 13
```

---

## Dependencias entre Fases

```
FASE 1 (Backend Comparación)
   ↓
   Necesario para → FASE 3 (Frontend Tipos)
   ↓
FASE 2 (Backend BASE)
   ↓
   ↓
   ↓ ← Necesario para
   ↓
FASE 4 (Frontend Componente)
   ↓
FASE 5 (Integración)
```

**Puede ejecutarse en paralelo:**
- Fase 1 + Fase 2 (ambas backend, diferentes métodos)
- Fase 3 (frontend types) puede iniciar después de Fase 1

**Debe ejecutarse secuencialmente:**
- Fase 4 requiere Fase 3 completa
- Fase 5 requiere todas las anteriores

---

## Resumen de Cambios

| Archivo | Tipo | Cambios |
|---------|------|---------|
| `models.py` | MODIFICADO | +4 nuevos modelos (CambioSituacion, CambioUltimaActuacion, CambioDependencia, ComparacionDetallada) |
| `extractor_masivo.py` | MODIFICADO | Reemplazar `comparar_con_base()`, agregar `actualizar_base_permanente()`, modificar `extraer_listado_completo()` |
| `expediente.ts` | MODIFICADO | +4 nuevas interfaces (CambioSituacion, CambioUltimaActuacion, CambioDependencia, ComparacionDetallada) |
| `expedientesStore.ts` | MODIFICADO | Cambiar tipo de `comparacion` a `ComparacionDetallada | null` |
| `ComparacionDetalladaPanel.tsx` | NUEVO | Componente visual completo (300+ líneas) |
| `ExtraccionMasivaDialog.tsx` | MODIFICADO | Reemplazar sección de comparación (líneas 958-987) |
| `listado_base.json` | NUEVO | Archivo de datos permanente |

**Total:**
- 1 archivo nuevo (componente)
- 1 archivo de datos nuevo (BASE)
- 5 archivos modificados
- ~500 líneas de código agregadas

---

## Próximos Pasos

1. Revisar y aprobar este plan
2. Ejecutar Fase 1 (Backend Comparación)
3. Ejecutar Fase 2 (Backend BASE)
4. Testing backend con datos reales
5. Ejecutar Fase 3 (Frontend Tipos)
6. Ejecutar Fase 4 (Frontend Componente)
7. Testing frontend con mock data
8. Ejecutar Fase 5 (Integración completa)
9. Testing end-to-end
10. Migración de datos existentes (si aplica)

---

## Notas Finales

- **Compatibilidad:** Los snapshots timestamped se mantienen para histórico
- **Performance:** La comparación es O(n) donde n = total de expedientes
- **Escalabilidad:** Para >10,000 expedientes, considerar indexación o BD
- **Backup:** El BASE permanente debería respaldarse periódicamente
- **Rollback:** Si hay problemas, eliminar `listado_base.json` y sistema vuelve a comportamiento anterior

---

**Documento creado:** 2025-01-12
**Versión:** 1.0
**Autor:** AI Agent
**Estado:** Pendiente de Aprobación
