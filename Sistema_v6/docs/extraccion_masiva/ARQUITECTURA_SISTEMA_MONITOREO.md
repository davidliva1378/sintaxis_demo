# 🔄 ARQUITECTURA DEL SISTEMA DE MONITOREO

**Fecha:** 2025-11-10
**Versión:** 1.0
**Estado:** Documentación completa

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Arquitectura de 3 Capas JSON](#arquitectura-de-3-capas-json)
3. [Estrategia Dual de Extracción](#estrategia-dual-de-extracción)
4. [Algoritmos de Comparación](#algoritmos-de-comparación)
5. [Lógica de Actualización](#lógica-de-actualización)
6. [Gestión de Conflictos](#gestión-de-conflictos)
7. [Implementación Técnica](#implementación-técnica)
8. [Configuración de Usuario](#configuración-de-usuario)

---

## 🎯 VISIÓN GENERAL

### Propósito del Sistema de Monitoreo

El **Sistema de Monitoreo** es el componente encargado de mantener sincronizado el sistema local con el sitio del PJN (Poder Judicial de la Nación) mediante extracciones periódicas y comparaciones inteligentes.

### Objetivos Principales

1. **Detectar cambios** en expedientes ya procesados (situación, fechas, dependencia)
2. **Encontrar nuevos expedientes** que aparecen en el PJN
3. **Marcar expedientes faltantes** que desaparecen del sistema
4. **Evitar sobrecarga** del sitio PJN mediante estrategia dual
5. **Gestionar conflictos** cuando hay discrepancias

### Flujo General

```
┌─────────────────────────────────────────────────────────────┐
│  MONITOR (SERVICIO)                                         │
│                                                               │
│  Ejecuta extracciones programadas:                          │
│  ├─ Frecuentes: Parciales (últimos 30 días) - Cada 1h      │
│  └─ Periódicas: Totales (todos) - Semanal/Fin de día       │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  EXTRACCIÓN DE MONITOREO                                    │
│                                                               │
│  Obtiene: JSON_MONITOREO (expedientes actuales del PJN)    │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  COMPARADOR (SERVICIO)                                      │
│                                                               │
│  Realiza 3 comparaciones:                                    │
│  ├─ 1. JSON_MONITOREO vs JSON_SISTEMA → Cambios            │
│  ├─ 2. JSON_MONITOREO vs JSON_BASE → Nuevos                │
│  └─ 3. JSON_SISTEMA vs JSON_MONITOREO → Faltantes          │
└──────────────────┬────────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  ACTUALIZADOR (SERVICIO)                                    │
│                                                               │
│  Actualiza:                                                  │
│  ├─ JSON_BASE (agrega nuevos + actualiza existentes)       │
│  ├─ JSON_SISTEMA (actualiza existentes + marca faltantes)  │
│  ├─ JSON_PENDIENTES (nuevos expedientes)                    │
│  └─ JSON_CONFLICTOS (discrepancias detectadas)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ ARQUITECTURA DE 3 CAPAS JSON

### Capa 1: JSON BASE (Universo Completo)

**Archivo:** `data/extraccion_masiva/listados/listado_base.json`

**Propósito:** Mantener el universo completo de expedientes extraídos del PJN.

**Estructura:**
```json
{
  "metadata": {
    "fecha_creacion": "2025-11-07T10:00:00",
    "ultima_actualizacion": "2025-11-10T15:30:00",
    "total_expedientes": 2340,
    "fuente": "PJN - Poder Judicial Neuquén",
    "tipo_ultima_extraccion": "TOTAL"
  },
  "expedientes": [
    {
      "numero": "12345/2024",
      "caratula": "Juan Pérez c/ Pedro Gómez s/ Cobro de Pesos",
      "dependencia": "Juzgado Civil 1",
      "situacion": "EN DESPACHO",
      "fecha_inicio": "2024-03-15",
      "ultima_actuacion": "2025-11-05",
      "fecha_agregado": "2025-11-07T10:30:00",
      "ultima_actualizacion": "2025-11-10T15:30:00"
    }
  ]
}
```

**Características:**
- Se actualiza con CADA extracción de monitoreo
- Crece con nuevos expedientes
- Actualiza metadata de expedientes existentes
- NUNCA elimina expedientes (histórico completo)

---

### Capa 2: JSON SISTEMA (Expedientes Seleccionados)

**Archivo:** `data/sistema/expedientes_sistema.json`

**Propósito:** Contener SOLO los expedientes que el usuario seleccionó para procesar y tener en el sistema.

**Estructura:**
```json
{
  "metadata": {
    "fecha_creacion": "2025-11-07T12:00:00",
    "ultima_actualizacion": "2025-11-10T15:30:00",
    "total_expedientes": 45,
    "expedientes_activos": 42,
    "expedientes_no_encontrados": 3
  },
  "expedientes": [
    {
      "numero": "12345/2024",
      "caratula": "Juan Pérez c/ Pedro Gómez s/ Cobro de Pesos",
      "dependencia": "Juzgado Civil 1",
      "situacion": "EN DESPACHO",
      "fecha_inicio": "2024-03-15",
      "ultima_actuacion": "2025-11-05",
      "fecha_agregado_sistema": "2025-11-07T12:30:00",
      "ultima_actualizacion_sistema": "2025-11-10T15:30:00",
      "estado_sistema": "ACTIVO",  // ACTIVO | NO_ENCONTRADO | ERROR
      "origen_seleccion": "extraccion_masiva_20251107",

      // Datos completos del expediente (incluye actuaciones, etc.)
      "actuaciones": [
        {
          "fecha": "2025-11-05",
          "descripcion": "Se dicta sentencia",
          "tipo": "RESOLUCION"
        }
      ],
      "partes": [...],
      "adjuntos": [...]
    }
  ]
}
```

**Características:**
- Contiene datos COMPLETOS de cada expediente (no solo metadata)
- Se actualiza con extracciones de monitoreo
- Puede marcar expedientes como "NO_ENCONTRADO"
- Da origen al WORKSPACE (directorios de trabajo)

---

### Capa 3: WORKSPACE (Directorios de Trabajo)

**Ubicación:** `data/workspace/{numero_expediente}/`

**Propósito:** Crear un directorio por cada expediente en JSON_SISTEMA para almacenar archivos, PDFs, análisis, etc.

**Estructura de directorios:**
```
data/workspace/
├── 12345-2024/
│   ├── metadata.json         # Info del expediente
│   ├── actuaciones.json      # Lista de actuaciones
│   ├── pdfs/                 # PDFs descargados (futuro)
│   │   ├── 001_providencia.pdf
│   │   └── 002_sentencia.pdf
│   ├── analisis/             # Análisis generados
│   │   ├── clasificacion.json
│   │   └── vencimientos.json
│   └── notas.txt            # Notas del usuario
│
├── 12346-2024/
│   └── ...
```

**Características:**
- Se crea SOLO para expedientes en JSON_SISTEMA
- NO se elimina automáticamente (queda como histórico)
- Puede marcarse como "inactivo" si el expediente ya no está en JSON_SISTEMA

---

### Relación entre Capas

```
┌──────────────────────────────────────────────────────┐
│  JSON BASE (2,340 expedientes)                       │
│  - Universo completo                                  │
│  - Se agregan nuevos                                  │
│  - Se actualizan existentes                          │
│  - NUNCA se eliminan                                  │
└───────────────┬──────────────────────────────────────┘
                │
                │ Usuario selecciona 45 de 2,340
                │ (mediante filtrado y selección)
                ↓
┌──────────────────────────────────────────────────────┐
│  JSON SISTEMA (45 expedientes)                       │
│  - Subset seleccionado                                │
│  - Datos completos                                    │
│  - Se actualiza con monitoreo                        │
│  - Puede marcar como NO_ENCONTRADO                   │
└───────────────┬──────────────────────────────────────┘
                │
                │ Se crean directorios
                ↓
┌──────────────────────────────────────────────────────┐
│  WORKSPACE (45 directorios)                          │
│  - Un directorio por expediente                       │
│  - Contiene archivos de trabajo                      │
│  - NO se elimina automáticamente                     │
└──────────────────────────────────────────────────────┘
```

---

## 🔄 ESTRATEGIA DUAL DE EXTRACCIÓN

### Problema a Resolver

- **Extracción total frecuente:** Sobrecarga el sitio PJN y es ineficiente
- **Extracción parcial únicamente:** Puede perder cambios en expedientes antiguos

### Solución: Estrategia Dual

Combinar dos tipos de extracciones:

#### 1. Extracciones PARCIALES Frecuentes (Primaria)

**Frecuencia:** Configurable (recomendado: cada 1-2 horas)

**Criterio:** Últimos N días (recomendado: 30 días)

**Propósito:**
- Capturar cambios recientes
- Detectar nuevos expedientes
- Evitar sobrecarga del sitio

**Ejemplo:**
```json
{
  "tipo_extraccion": "PARCIAL",
  "criterio": "FECHA_ULTIMA_ACTUACION",
  "fecha_desde": "2025-10-11",  // Últimos 30 días
  "fecha_hasta": "2025-11-10",
  "total_extraido": 245
}
```

#### 2. Extracciones TOTALES Periódicas (Seguridad)

**Frecuencia:** Configurable (recomendado: semanal o fin de día)

**Criterio:** Todos los expedientes

**Propósito:**
- **Red de seguridad:** Capturar cambios perdidos
- Detectar expedientes desaparecidos
- Verificar integridad del sistema

**Ejemplo:**
```json
{
  "tipo_extraccion": "TOTAL",
  "criterio": "TODOS",
  "total_extraido": 2340
}
```

---

### Configuración Recomendada

| Tipo | Frecuencia | Criterio | Propósito |
|------|------------|----------|-----------|
| PARCIAL | Cada 1h | Últimos 30 días | Cambios recientes |
| PARCIAL | Cada 6h | Últimos 90 días | Cambios medios |
| TOTAL | Semanal (Domingo 3am) | Todos | Red de seguridad |
| TOTAL | Fin de día laboral | Todos | Sincronización diaria |

---

### Ventajas de la Estrategia Dual

✅ **Eficiencia:** Extracciones frecuentes son pequeñas (30 días)
✅ **Cobertura:** Extracción total captura todo
✅ **Baja carga:** PJN no se sobrecarga con consultas masivas frecuentes
✅ **Confiabilidad:** Red de seguridad para cambios perdidos
✅ **Flexibilidad:** Usuario configura frecuencias según necesidad

---

## 🔍 ALGORITMOS DE COMPARACIÓN

El sistema realiza **3 comparaciones** después de cada extracción de monitoreo:

### Comparación 1: Detectar CAMBIOS en Expedientes del Sistema

**Objetivo:** Encontrar expedientes que están en JSON_SISTEMA y tienen datos desactualizados.

**Comparación:** `JSON_MONITOREO vs JSON_SISTEMA`

**Algoritmo:**
```python
def detectar_cambios(monitoreo: List[Dict], sistema: List[Dict]) -> List[Cambio]:
    cambios = []

    # Indexar por número para búsqueda rápida
    sistema_dict = {exp["numero"]: exp for exp in sistema}

    for exp_mon in monitoreo:
        numero = exp_mon["numero"]

        # Si está en el sistema, comparar
        if numero in sistema_dict:
            exp_sis = sistema_dict[numero]

            # Comparar campos críticos
            cambios_encontrados = {}

            if exp_mon["situacion"] != exp_sis["situacion"]:
                cambios_encontrados["situacion"] = {
                    "anterior": exp_sis["situacion"],
                    "nuevo": exp_mon["situacion"]
                }

            if exp_mon["ultima_actuacion"] != exp_sis["ultima_actuacion"]:
                cambios_encontrados["ultima_actuacion"] = {
                    "anterior": exp_sis["ultima_actuacion"],
                    "nuevo": exp_mon["ultima_actuacion"]
                }

            if exp_mon["dependencia"] != exp_sis["dependencia"]:
                cambios_encontrados["dependencia"] = {
                    "anterior": exp_sis["dependencia"],
                    "nuevo": exp_mon["dependencia"]
                }

            if exp_mon["caratula"] != exp_sis["caratula"]:
                cambios_encontrados["caratula"] = {
                    "anterior": exp_sis["caratula"],
                    "nuevo": exp_mon["caratula"]
                }

            if cambios_encontrados:
                cambios.append({
                    "numero": numero,
                    "tipo": "ACTUALIZACION",
                    "cambios": cambios_encontrados,
                    "fecha_deteccion": datetime.now().isoformat()
                })

    return cambios
```

**Campos que se comparan:**
- `situacion` (EN DESPACHO, EN LETRA, etc.)
- `ultima_actuacion` (fecha)
- `dependencia` (juzgado)
- `caratula` (nombre del expediente)

**Acción:** Actualizar JSON_SISTEMA con nuevos valores

---

### Comparación 2: Detectar NUEVOS Expedientes

**Objetivo:** Encontrar expedientes que están en JSON_MONITOREO pero NO en JSON_BASE (expedientes completamente nuevos).

**Comparación:** `JSON_MONITOREO vs JSON_BASE`

**Algoritmo:**
```python
def detectar_nuevos(monitoreo: List[Dict], base: List[Dict]) -> List[Dict]:
    nuevos = []

    # Indexar números existentes en base
    numeros_base = {exp["numero"] for exp in base}

    for exp_mon in monitoreo:
        if exp_mon["numero"] not in numeros_base:
            nuevos.append({
                "expediente": exp_mon,
                "fecha_deteccion": datetime.now().isoformat(),
                "origen": "monitor_extraccion"
            })

    return nuevos
```

**Acción:**
1. Agregar a `JSON_BASE`
2. Agregar a `JSON_PENDIENTES_REVISION` para que el usuario decida si lo procesa

---

### Comparación 3: Detectar FALTANTES (Lógica Condicional)

**Objetivo:** Encontrar expedientes que están en JSON_SISTEMA pero NO en JSON_MONITOREO, pero solo marcarlos como "NO_ENCONTRADO" si deberían haber aparecido.

**Comparación:** `JSON_SISTEMA vs JSON_MONITOREO`

**Algoritmo (CRÍTICO - Lógica Condicional):**
```python
def detectar_faltantes(
    sistema: List[Dict],
    monitoreo: List[Dict],
    tipo_extraccion: str,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict]:
    """
    Detecta expedientes faltantes CON LÓGICA CONDICIONAL.

    NO marca como faltante si el expediente no debería estar en la extracción.
    """
    faltantes = []

    # Indexar números encontrados en monitoreo
    numeros_monitoreo = {exp["numero"] for exp in monitoreo}

    for exp_sis in sistema:
        numero = exp_sis["numero"]

        # Si NO está en monitoreo
        if numero not in numeros_monitoreo:

            # LÓGICA CONDICIONAL: Evaluar si DEBERÍA haber estado
            deberia_estar = evaluar_si_deberia_estar(
                exp_sis,
                tipo_extraccion,
                fecha_desde,
                fecha_hasta
            )

            if deberia_estar:
                faltantes.append({
                    "numero": numero,
                    "caratula": exp_sis["caratula"],
                    "tipo_extraccion": tipo_extraccion,
                    "fecha_deteccion": datetime.now().isoformat(),
                    "accion_sugerida": "MARCAR_NO_ENCONTRADO"
                })

    return faltantes


def evaluar_si_deberia_estar(
    expediente: Dict,
    tipo_extraccion: str,
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str]
) -> bool:
    """
    Evalúa si un expediente DEBERÍA haber aparecido en la extracción.

    Reglas:
    1. TOTAL: Siempre debería estar
    2. PARCIAL: Solo si está en el rango de fechas
    3. DIRIGIDA: Solo si fue específicamente buscado
    """

    # Caso 1: Extracción TOTAL
    if tipo_extraccion == "TOTAL":
        # SIEMPRE debería estar
        return True

    # Caso 2: Extracción PARCIAL por fechas
    if tipo_extraccion == "PARCIAL":
        if not fecha_desde or not fecha_hasta:
            # Sin rango definido, asumir que debería estar
            return True

        # Verificar si la última actuación está en el rango
        ultima_act = parse_date(expediente["ultima_actuacion"])
        desde = parse_date(fecha_desde)
        hasta = parse_date(fecha_hasta)

        if desde <= ultima_act <= hasta:
            # SÍ debería estar (está en el rango)
            return True
        else:
            # NO debería estar (fuera del rango)
            return False

    # Caso 3: Extracción DIRIGIDA
    if tipo_extraccion == "DIRIGIDA":
        # Requiere lista de números buscados (no implementado aún)
        # Por ahora, asumir que debería estar
        return True

    # Default: Asumir que debería estar
    return True
```

**Ejemplo de Uso:**

```python
# Extracción TOTAL
# Expediente 12345/2024 NO aparece
# → deberia_estar = True
# → MARCAR como NO_ENCONTRADO ✅

# Extracción PARCIAL (últimos 30 días)
# Expediente 99999/2020 (última actuación: 2020-05-15) NO aparece
# → última_actuacion FUERA del rango
# → deberia_estar = False
# → NO MARCAR (es normal que no aparezca) ✅

# Extracción PARCIAL (últimos 30 días)
# Expediente 12345/2024 (última actuación: 2025-11-05) NO aparece
# → última_actuacion DENTRO del rango
# → deberia_estar = True
# → MARCAR como NO_ENCONTRADO ✅
```

**Acción:**
- Si `deberia_estar = True`: Marcar como "NO_ENCONTRADO" en JSON_SISTEMA
- Si `deberia_estar = False`: NO hacer nada (mantener estado actual)

---

## 🔄 LÓGICA DE ACTUALIZACIÓN

Después de las comparaciones, se actualizan los JSONs correspondientes:

### Actualización de JSON_BASE

**Cuándo:** Después de TODA extracción de monitoreo

**Acciones:**
1. **Agregar nuevos expedientes** detectados en Comparación 2
2. **Actualizar expedientes existentes** con nuevos datos

```python
def actualizar_json_base(
    base: List[Dict],
    monitoreo: List[Dict],
    nuevos: List[Dict]
) -> List[Dict]:
    """Actualizar JSON_BASE con nuevos y actualizaciones."""

    # Indexar por número
    base_dict = {exp["numero"]: exp for exp in base}

    # 1. Actualizar existentes
    for exp_mon in monitoreo:
        numero = exp_mon["numero"]
        if numero in base_dict:
            # Actualizar datos
            base_dict[numero].update({
                "situacion": exp_mon["situacion"],
                "ultima_actuacion": exp_mon["ultima_actuacion"],
                "dependencia": exp_mon["dependencia"],
                "caratula": exp_mon["caratula"],
                "ultima_actualizacion": datetime.now().isoformat()
            })

    # 2. Agregar nuevos
    for nuevo in nuevos:
        exp = nuevo["expediente"]
        exp["fecha_agregado"] = datetime.now().isoformat()
        exp["ultima_actualizacion"] = datetime.now().isoformat()
        base_dict[exp["numero"]] = exp

    return list(base_dict.values())
```

---

### Actualización de JSON_SISTEMA

**Cuándo:** Después de extracciones que afectan expedientes del sistema

**Acciones:**
1. **Actualizar expedientes existentes** con nuevos datos (Comparación 1)
2. **Marcar como NO_ENCONTRADO** si corresponde (Comparación 3)

```python
def actualizar_json_sistema(
    sistema: List[Dict],
    cambios: List[Dict],
    faltantes: List[Dict]
) -> List[Dict]:
    """Actualizar JSON_SISTEMA con cambios y faltantes."""

    sistema_dict = {exp["numero"]: exp for exp in sistema}

    # 1. Aplicar cambios detectados
    for cambio in cambios:
        numero = cambio["numero"]
        if numero in sistema_dict:
            # Actualizar cada campo cambiado
            for campo, valores in cambio["cambios"].items():
                sistema_dict[numero][campo] = valores["nuevo"]

            sistema_dict[numero]["ultima_actualizacion_sistema"] = datetime.now().isoformat()

    # 2. Marcar faltantes
    for faltante in faltantes:
        numero = faltante["numero"]
        if numero in sistema_dict:
            sistema_dict[numero]["estado_sistema"] = "NO_ENCONTRADO"
            sistema_dict[numero]["fecha_no_encontrado"] = datetime.now().isoformat()

    return list(sistema_dict.values())
```

---

### Actualización de JSON_PENDIENTES

**Cuándo:** Cuando se detectan nuevos expedientes (Comparación 2)

**Archivo:** `data/sistema/pendientes_revision.json`

**Estructura:**
```json
{
  "metadata": {
    "total_pendientes": 5,
    "ultima_actualizacion": "2025-11-10T15:30:00"
  },
  "expedientes_nuevos": [
    {
      "numero": "99999/2024",
      "caratula": "Nuevo Expediente",
      "dependencia": "Juzgado Civil 2",
      "situacion": "EN DESPACHO",
      "fecha_deteccion": "2025-11-10T15:30:00",
      "origen": "monitor_extraccion_parcial_20251110"
    }
  ]
}
```

**Propósito:** Usuario puede revisar y decidir si agrega estos expedientes al sistema.

---

## ⚠️ GESTIÓN DE CONFLICTOS

### Tipos de Conflictos

#### 1. Conflicto de Datos Locales vs PJN

**Escenario:** Usuario modificó datos localmente, pero el PJN tiene otros valores.

**Ejemplo:**
- Sistema local: `situacion = "EN DESPACHO"`
- PJN (monitoreo): `situacion = "EN LETRA"`

**Acción:**
1. Notificar al usuario
2. Mostrar ambos valores
3. Usuario decide:
   - Aceptar del PJN (sobrescribir local)
   - Mantener local (ignorar PJN)
   - Revisar manualmente

**Archivo:** `data/sistema/conflictos.json`

```json
{
  "conflictos": [
    {
      "id": "conflict_001",
      "numero_expediente": "12345/2024",
      "campo": "situacion",
      "valor_local": "EN DESPACHO",
      "valor_pjn": "EN LETRA",
      "fecha_deteccion": "2025-11-10T15:30:00",
      "estado": "PENDIENTE",  // PENDIENTE | RESUELTO
      "accion_usuario": null
    }
  ]
}
```

---

#### 2. Conflicto de Expediente No Encontrado

**Escenario:** Expediente desapareció del PJN pero está en el sistema.

**Posibles Causas:**
- Expediente archivado en el PJN
- Error temporal del sitio
- Cambio de dependencia (movido a otro juzgado)

**Acción:**
1. Marcar como "NO_ENCONTRADO" en JSON_SISTEMA
2. NO eliminar del sistema
3. Notificar al usuario
4. Usuario decide:
   - Mantener como histórico
   - Investigar manualmente
   - Eliminar del sistema

---

### UI para Gestión de Conflictos

**Componente:** `ConflictosDialog.tsx`

```
┌──────────────────────────────────────────────────────┐
│  ⚠️ Conflictos Detectados (3)                        │
├──────────────────────────────────────────────────────┤
│                                                       │
│  📋 Expediente: 12345/2024                          │
│  Campo: Situación                                    │
│  ├─ Local: "EN DESPACHO"                            │
│  └─ PJN:   "EN LETRA" ✅                             │
│                                                       │
│  [Aceptar PJN] [Mantener Local] [Revisar Después]  │
│                                                       │
├──────────────────────────────────────────────────────┤
│  📋 Expediente: 99999/2020                          │
│  Estado: NO ENCONTRADO en PJN                        │
│  ├─ Última vez visto: 2025-11-01                    │
│  └─ Tipo extracción: TOTAL (debería estar)          │
│                                                       │
│  [Mantener Histórico] [Investigar] [Eliminar]      │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 💻 IMPLEMENTACIÓN TÉCNICA

### Servicios Necesarios

#### 1. ServicioMonitor

**Archivo:** `Sistema_v6/monitoring/servicio_monitor.py`

**Responsabilidades:**
- Programar extracciones (cron-like)
- Ejecutar extracciones según configuración
- Coordinar comparaciones y actualizaciones

```python
class ServicioMonitor:
    """Servicio principal de monitoreo."""

    def __init__(
        self,
        extractor: ExtractorMasivo,
        comparador: ComparadorExpedientes,
        actualizador: ActualizadorJSONs,
        gestor_conflictos: GestorConflictos,
        config: ConfigMonitor
    ):
        self.extractor = extractor
        self.comparador = comparador
        self.actualizador = actualizador
        self.gestor_conflictos = gestor_conflictos
        self.config = config

    async def ejecutar_monitoreo(self, tipo: str = "PARCIAL"):
        """Ejecutar ciclo completo de monitoreo."""

        logger.info(f"Iniciando monitoreo {tipo}")

        # 1. Extracción
        if tipo == "PARCIAL":
            criterio = self.config.criterio_parcial  # últimos 30 días
            monitoreo = await self.extractor.extraer_con_criterio(criterio)
        else:
            monitoreo = await self.extractor.extraer_listado_completo()

        # 2. Cargar JSONs existentes
        base = self._cargar_json_base()
        sistema = self._cargar_json_sistema()

        # 3. Comparaciones
        cambios = self.comparador.detectar_cambios(monitoreo, sistema)
        nuevos = self.comparador.detectar_nuevos(monitoreo, base)
        faltantes = self.comparador.detectar_faltantes(
            sistema,
            monitoreo,
            tipo_extraccion=tipo,
            fecha_desde=criterio.get("fecha_desde") if tipo == "PARCIAL" else None,
            fecha_hasta=criterio.get("fecha_hasta") if tipo == "PARCIAL" else None
        )

        # 4. Detectar conflictos
        conflictos = self.gestor_conflictos.detectar_conflictos(
            cambios, faltantes
        )

        if conflictos:
            # Notificar al usuario
            await self._notificar_conflictos(conflictos)
            # Esperar decisión del usuario
            return

        # 5. Actualizar JSONs
        base_actualizado = self.actualizador.actualizar_json_base(
            base, monitoreo, nuevos
        )
        sistema_actualizado = self.actualizador.actualizar_json_sistema(
            sistema, cambios, faltantes
        )

        # 6. Guardar
        self._guardar_json_base(base_actualizado)
        self._guardar_json_sistema(sistema_actualizado)

        if nuevos:
            self._guardar_json_pendientes(nuevos)

        logger.info(
            f"Monitoreo completado: "
            f"{len(cambios)} cambios, "
            f"{len(nuevos)} nuevos, "
            f"{len(faltantes)} faltantes"
        )
```

---

#### 2. ComparadorExpedientes

**Archivo:** `Sistema_v6/monitoring/comparador_expedientes.py`

**Responsabilidades:**
- Implementar las 3 comparaciones
- Optimizar búsquedas con índices

```python
class ComparadorExpedientes:
    """Comparador de expedientes entre JSONs."""

    def detectar_cambios(
        self,
        monitoreo: List[Dict],
        sistema: List[Dict]
    ) -> List[Cambio]:
        """Comparación 1: Detectar cambios."""
        # Implementación vista anteriormente
        ...

    def detectar_nuevos(
        self,
        monitoreo: List[Dict],
        base: List[Dict]
    ) -> List[Dict]:
        """Comparación 2: Detectar nuevos."""
        # Implementación vista anteriormente
        ...

    def detectar_faltantes(
        self,
        sistema: List[Dict],
        monitoreo: List[Dict],
        tipo_extraccion: str,
        fecha_desde: Optional[str],
        fecha_hasta: Optional[str]
    ) -> List[Dict]:
        """Comparación 3: Detectar faltantes CON LÓGICA CONDICIONAL."""
        # Implementación vista anteriormente
        ...
```

---

#### 3. ActualizadorJSONs

**Archivo:** `Sistema_v6/monitoring/actualizador_jsons.py`

**Responsabilidades:**
- Actualizar JSON_BASE
- Actualizar JSON_SISTEMA
- Actualizar JSON_PENDIENTES
- Mantener backup antes de actualizar

```python
class ActualizadorJSONs:
    """Actualizador de archivos JSON."""

    def actualizar_json_base(
        self,
        base: List[Dict],
        monitoreo: List[Dict],
        nuevos: List[Dict]
    ) -> List[Dict]:
        """Actualizar JSON_BASE."""
        # Implementación vista anteriormente
        ...

    def actualizar_json_sistema(
        self,
        sistema: List[Dict],
        cambios: List[Dict],
        faltantes: List[Dict]
    ) -> List[Dict]:
        """Actualizar JSON_SISTEMA."""
        # Implementación vista anteriormente
        ...

    def guardar_con_backup(
        self,
        archivo: str,
        datos: List[Dict]
    ):
        """Guardar con backup automático."""
        # Crear backup antes de sobrescribir
        if Path(archivo).exists():
            backup = f"{archivo}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy(archivo, backup)

        # Guardar nuevo
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
```

---

#### 4. GestorConflictos

**Archivo:** `Sistema_v6/monitoring/gestor_conflictos.py`

**Responsabilidades:**
- Detectar conflictos que requieren intervención del usuario
- Guardar conflictos en JSON
- Notificar al usuario

```python
class GestorConflictos:
    """Gestor de conflictos de datos."""

    def detectar_conflictos(
        self,
        cambios: List[Dict],
        faltantes: List[Dict]
    ) -> List[Conflicto]:
        """Detectar conflictos que requieren decisión del usuario."""

        conflictos = []

        # Conflictos tipo 1: Cambios críticos
        for cambio in cambios:
            # Si hay cambios en campos críticos, notificar
            if "situacion" in cambio["cambios"]:
                conflictos.append({
                    "tipo": "CAMBIO_SITUACION",
                    "expediente": cambio["numero"],
                    "datos": cambio["cambios"]["situacion"]
                })

        # Conflictos tipo 2: Expedientes no encontrados
        for faltante in faltantes:
            conflictos.append({
                "tipo": "NO_ENCONTRADO",
                "expediente": faltante["numero"],
                "datos": faltante
            })

        return conflictos

    async def notificar_usuario(self, conflictos: List[Conflicto]):
        """Notificar conflictos al usuario vía WebSocket."""
        # Enviar notificación al frontend
        ...
```

---

### Programación de Tareas (Scheduler)

**Librería recomendada:** `APScheduler`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Extracción parcial cada 1 hora
scheduler.add_job(
    monitor.ejecutar_monitoreo,
    'interval',
    hours=1,
    args=['PARCIAL'],
    id='monitoreo_parcial'
)

# Extracción total semanal (Domingos 3am)
scheduler.add_job(
    monitor.ejecutar_monitoreo,
    'cron',
    day_of_week='sun',
    hour=3,
    args=['TOTAL'],
    id='monitoreo_total_semanal'
)

scheduler.start()
```

---

### Endpoints REST para Monitoreo

```python
# routers/monitoring.py

@router.post("/monitoring/start")
async def iniciar_monitoreo(
    config: ConfigMonitor,
    monitor: ServicioMonitor = Depends(get_monitor)
):
    """Iniciar servicio de monitoreo."""
    await monitor.iniciar(config)
    return {"status": "iniciado"}

@router.post("/monitoring/trigger/{tipo}")
async def forzar_extraccion(
    tipo: str,  # PARCIAL | TOTAL
    monitor: ServicioMonitor = Depends(get_monitor)
):
    """Forzar extracción manual."""
    await monitor.ejecutar_monitoreo(tipo)
    return {"status": "completado"}

@router.get("/monitoring/status")
async def estado_monitoreo(
    monitor: ServicioMonitor = Depends(get_monitor)
):
    """Obtener estado del monitoreo."""
    return {
        "activo": monitor.is_running(),
        "ultima_extraccion": monitor.ultima_extraccion,
        "proxima_extraccion": monitor.proxima_extraccion
    }

@router.get("/monitoring/conflictos")
async def obtener_conflictos():
    """Obtener conflictos pendientes."""
    with open("data/sistema/conflictos.json") as f:
        return json.load(f)

@router.post("/monitoring/conflictos/{conflicto_id}/resolver")
async def resolver_conflicto(
    conflicto_id: str,
    accion: str,  # ACEPTAR_PJN | MANTENER_LOCAL | REVISAR_DESPUES
    gestor: GestorConflictos = Depends(get_gestor_conflictos)
):
    """Resolver conflicto."""
    await gestor.resolver_conflicto(conflicto_id, accion)
    return {"status": "resuelto"}
```

---

## ⚙️ CONFIGURACIÓN DE USUARIO

### Archivo de Configuración

**Ubicación:** `data/sistema/config_monitor.json`

```json
{
  "activado": true,

  "extracciones_parciales": {
    "habilitado": true,
    "frecuencia_horas": 1,
    "criterio": "FECHA_ULTIMA_ACTUACION",
    "dias_atras": 30
  },

  "extracciones_totales": {
    "habilitado": true,
    "frecuencia": "SEMANAL",
    "dia_semana": "DOMINGO",
    "hora": 3
  },

  "notificaciones": {
    "cambios_situacion": true,
    "nuevos_expedientes": true,
    "expedientes_faltantes": true,
    "conflictos": true,
    "email": "usuario@example.com",
    "webhook_url": null
  },

  "actualizacion_automatica": {
    "json_base": true,
    "json_sistema": true,
    "resolver_conflictos_automaticamente": false
  }
}
```

---

### UI de Configuración

**Componente:** `MonitorConfigDialog.tsx`

```
┌──────────────────────────────────────────────────────┐
│  ⚙️ Configuración de Monitoreo                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  🔄 EXTRACCIONES PARCIALES                           │
│  ├─ ☑ Habilitado                                     │
│  ├─ Frecuencia: [1▼] horas                          │
│  └─ Criterio: Últimos [30▼] días                    │
│                                                       │
│  🔄 EXTRACCIONES TOTALES                             │
│  ├─ ☑ Habilitado                                     │
│  ├─ Frecuencia: [Semanal▼]                          │
│  └─ Día: [Domingo▼] Hora: [03:00]                   │
│                                                       │
│  🔔 NOTIFICACIONES                                   │
│  ├─ ☑ Cambios de situación                          │
│  ├─ ☑ Nuevos expedientes                            │
│  ├─ ☑ Expedientes faltantes                         │
│  └─ ☑ Conflictos detectados                         │
│                                                       │
│  ⚡ ACTUALIZACIONES AUTOMÁTICAS                      │
│  ├─ ☑ JSON BASE                                      │
│  ├─ ☑ JSON SISTEMA                                   │
│  └─ ☐ Resolver conflictos automáticamente           │
│                                                       │
│  [Cancelar] [Guardar Configuración]                 │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 📊 MÉTRICAS Y LOGS

### Logs de Monitoreo

**Archivo:** `logs/monitoreo_YYYYMMDD.log`

```
2025-11-10 15:30:00 [INFO] Iniciando monitoreo PARCIAL
2025-11-10 15:30:05 [INFO] Extracción completada: 245 expedientes
2025-11-10 15:30:10 [INFO] Comparación 1: 12 cambios detectados
2025-11-10 15:30:12 [INFO] Comparación 2: 3 nuevos expedientes
2025-11-10 15:30:15 [INFO] Comparación 3: 0 faltantes
2025-11-10 15:30:18 [INFO] Actualizando JSON_BASE: +3 nuevos, ~12 actualizados
2025-11-10 15:30:20 [INFO] Actualizando JSON_SISTEMA: ~12 actualizados
2025-11-10 15:30:22 [INFO] Monitoreo completado exitosamente
```

---

### Dashboard de Monitoreo (Frontend)

```
┌──────────────────────────────────────────────────────┐
│  📊 Dashboard de Monitoreo                           │
├──────────────────────────────────────────────────────┤
│                                                       │
│  🟢 Estado: ACTIVO                                   │
│  Última extracción: Hace 15 minutos (PARCIAL)       │
│  Próxima extracción: En 45 minutos                  │
│                                                       │
│  📈 ESTADÍSTICAS ÚLTIMAS 24 HORAS                    │
│  ├─ Extracciones realizadas: 24 parciales, 1 total │
│  ├─ Cambios detectados: 34                          │
│  ├─ Nuevos expedientes: 7                           │
│  └─ Faltantes detectados: 2                         │
│                                                       │
│  ⚠️ CONFLICTOS PENDIENTES                            │
│  ├─ Cambios de situación: 3 [Ver]                  │
│  └─ Expedientes no encontrados: 2 [Ver]            │
│                                                       │
│  [Configurar] [Forzar Extracción] [Ver Logs]       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

---

## 🎯 RESUMEN EJECUTIVO

### Componentes Clave

1. **3 Capas de JSONs**
   - JSON BASE: Universo completo
   - JSON SISTEMA: Subset seleccionado
   - WORKSPACE: Directorios de trabajo

2. **Estrategia Dual**
   - Extracciones parciales frecuentes (eficiencia)
   - Extracciones totales periódicas (seguridad)

3. **3 Comparaciones**
   - Cambios en sistema
   - Nuevos expedientes
   - Faltantes (con lógica condicional)

4. **Gestión de Conflictos**
   - Detección automática
   - Notificación al usuario
   - Resolución manual

### Próximos Pasos para Implementación

1. Crear servicios de monitoreo (4 clases)
2. Implementar algoritmos de comparación
3. Crear endpoints REST
4. Crear UI de configuración
5. Implementar scheduler
6. Testing completo

**Tiempo estimado:** 12-16 horas

---

**FIN DE ARQUITECTURA DEL SISTEMA DE MONITOREO**

**Estado:** ✅ DOCUMENTACIÓN COMPLETA
**Fecha:** 2025-11-10
**Versión:** 1.0
