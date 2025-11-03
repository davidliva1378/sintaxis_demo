# Integración del Monitor PJN con Procesador PDF
**Versión:** 1.0.0
**Fecha:** 2025-11-03
**Tarea:** Integración PJN Monitor - Tarea 2

---

## 📋 Descripción

Esta integración enriquece el sistema de monitoreo de expedientes del PJN con análisis inteligente proporcionado por el `procesador_pdf`:

- ✅ **Clasificación automática** de actuaciones por utilidad jurídica
- ✅ **Detección de vencimientos urgentes** en expedientes nuevos/modificados
- ✅ **Análisis detallado de duplicados** con reportes estructurados
- ✅ **Reportes enriquecidos** con estadísticas de procesamiento

---

## 🎯 Funcionalidades Implementadas

### 1. Clasificación Automática de Actuaciones

**¿Qué hace?**
Después de cada extracción exitosa de expedientes, clasifica automáticamente todas las actuaciones en cuatro categorías de utilidad jurídica:
- **ALTA**: Actuaciones críticas (sentencias, resoluciones importantes)
- **MEDIA**: Actuaciones relevantes (providencias con contenido sustancial)
- **BAJA**: Actuaciones de trámite menor
- **NULA**: Actuaciones sin valor jurídico (mero trámite, notificaciones simples)

**Configuración:**
```json
{
  "procesador_pdf": {
    "clasificacion_automatica": true,
    "confianza_minima": 0.75
  }
}
```

**Salida:**
- Archivo: `datos_extraidos/monitoreo/clasificaciones/clasificaciones_YYYYMMDD-HHMMSS.json`
- Contenido: Lista completa de actuaciones clasificadas con scores y motivos

---

### 2. Alertas de Vencimientos Urgentes

**¿Qué hace?**
Durante la comparación de expedientes, detecta vencimientos procesales urgentes en expedientes nuevos o modificados, considerando:
- Plazos de cédulas electrónicas y físicas
- Traslados y alegatos
- Presentaciones con fecha límite
- Días hábiles procesales

**Configuración:**
```json
{
  "procesador_pdf": {
    "vencimientos_automaticos": true,
    "dias_urgentes": 7
  }
}
```

**Salida:**
- Archivo: `datos_extraidos/monitoreo/alertas/vencimientos_urgentes_YYYYMMDD-HHMMSS.json`
- Notificación en bandeja del sistema cuando hay vencimientos urgentes
- Avisos en el resultado de comparación

**Ejemplo de Alerta:**
```json
{
  "expediente": "2024-123456",
  "actuacion_tipo": "CEDULA_ELECTRONICA",
  "dias_restantes": 3,
  "fecha_vencimiento": "2025-11-06",
  "urgente": true
}
```

---

### 3. Análisis Detallado de Duplicados

**¿Qué hace?**
Analiza duplicados detectados durante la extracción, identificando:
- Duplicados exactos (contenido 100% idéntico)
- Cédulas repetidas (misma notificación múltiples veces)
- Patrones de duplicación

**Configuración:**
```json
{
  "procesador_pdf": {
    "duplicados_analisis": true
  }
}
```

**Salida:**
- Archivo: `datos_extraidos/monitoreo/duplicados/duplicados_YYYYMMDD-HHMMSS.json`
- Estadísticas en log del monitor

---

## 🔧 Configuración

### Estructura Completa en `config_monitor.json`

```json
{
  "modo": "automatico",
  "horario_laboral": { ... },
  "filtro_expedientes": { ... },
  "comparacion": { ... },

  "procesador_pdf": {
    "habilitado": true,
    "clasificacion_automatica": true,
    "confianza_minima": 0.75,
    "vencimientos_automaticos": true,
    "dias_urgentes": 7,
    "duplicados_analisis": true,
    "timeout_clasificacion": 300,
    "guardar_reportes": true,
    "carpeta_reportes": "datos_extraidos/monitoreo/reportes_pdf"
  }
}
```

### Parámetros Explicados

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `habilitado` | bool | `true` | Habilita/deshabilita todo el procesamiento |
| `clasificacion_automatica` | bool | `true` | Clasificar actuaciones después de extracción |
| `confianza_minima` | float | `0.75` | Confianza mínima para clasificación (0.0-1.0) |
| `vencimientos_automaticos` | bool | `true` | Detectar vencimientos en comparaciones |
| `dias_urgentes` | int | `7` | Días restantes para marcar como urgente |
| `duplicados_analisis` | bool | `true` | Análisis detallado de duplicados |
| `timeout_clasificacion` | int | `300` | Timeout en segundos para clasificación |
| `guardar_reportes` | bool | `true` | Guardar reportes en disco |
| `carpeta_reportes` | string | `...` | Carpeta para reportes PDF |

---

## 📊 Archivos Generados

### Estructura de Directorios

```
datos_extraidos/monitoreo/
├── expedientes_monitor.json              # Expedientes actuales
├── expedientes_monitor - base.json       # Histórico para comparación
├── historial_notificaciones.json        # Notificaciones/Despachos
├── historial_notificaciones.csv
│
├── reportes/                             # Reportes de comparación (existente)
│   └── comparacion_YYYYMMDD-HHMMSS.json
│
├── clasificaciones/                      # NUEVO: Clasificaciones de actuaciones
│   └── clasificaciones_YYYYMMDD-HHMMSS.json
│
├── alertas/                              # NUEVO: Alertas de vencimientos
│   └── vencimientos_urgentes_YYYYMMDD-HHMMSS.json
│
├── duplicados/                           # NUEVO: Análisis de duplicados
│   └── duplicados_YYYYMMDD-HHMMSS.json
│
└── historico/                            # Respaldos históricos
    └── YYYYMMDD-HHMMSS/
        ├── expedientes_monitor.json
        └── ...
```

---

## 🚀 Uso

### Modo Automático (Recomendado)

La integración funciona automáticamente sin cambios en el flujo de trabajo:

1. **El monitor extrae expedientes** (cada X minutos según configuración)
2. **procesador_pdf clasifica automáticamente** (si `clasificacion_automatica=true`)
3. **El monitor compara con histórico** (si `comparacion.auto=true`)
4. **procesador_pdf detecta vencimientos urgentes** (si `vencimientos_automaticos=true`)
5. **Se generan alertas en bandeja del sistema**

**No requiere intervención manual.**

---

### Modo Manual

#### Clasificar Actuaciones Manualmente

```python
from Sistema_v4.monitor.integracion_procesador_pdf import clasificar_actuaciones_expedientes

stats = clasificar_actuaciones_expedientes(
    ruta_expedientes="datos_extraidos/monitoreo/expedientes_monitor.json",
    destino_clasificaciones="datos_extraidos/monitoreo/clasificaciones"
)

print(f"Utilidad alta: {stats['utilidad_alta']}")
print(f"Reducción estimada: {stats['porcentaje_reduccion']}%")
```

#### Detectar Vencimientos Manualmente

```python
from Sistema_v4.monitor.integracion_procesador_pdf import detectar_vencimientos_urgentes

urgentes, total = detectar_vencimientos_urgentes(
    ruta_expedientes="datos_extraidos/monitoreo/expedientes_monitor.json",
    destino_alertas="datos_extraidos/monitoreo/alertas",
    dias_urgentes=5
)

print(f"{len(urgentes)} vencimientos urgentes de {total} totales")
```

#### Análisis Completo (Todo en Uno)

```python
from Sistema_v4.monitor.integracion_procesador_pdf import procesar_expedientes_monitor
from Sistema_v4.monitor.configuracion_modo import cargar_config_monitor

config = cargar_config_monitor()

resumen = procesar_expedientes_monitor(
    ruta_expedientes="datos_extraidos/monitoreo/expedientes_monitor.json",
    directorio_base="datos_extraidos/monitoreo",
    config=config.get("procesador_pdf", {})
)

print(resumen)
```

---

## 📈 Ejemplo de Salida

### Log del Monitor con Procesamiento

```
[2025-11-03 14:30:52] ⏰ Iniciando verificación de expedientes...
[2025-11-03 14:31:15] ✅ Expedientes actualizados: 245 de 250 esperados
[2025-11-03 14:31:15] 📁 Guardado en: datos_extraidos/monitoreo/expedientes_monitor.json
[2025-11-03 14:31:15] 🔄 Iniciando procesamiento inteligente...

============================================================
📊 RESUMEN DE PROCESAMIENTO INTELIGENTE
============================================================
📋 Clasificación:
   • Utilidad ALTA:  35
   • Utilidad MEDIA: 78
   • Utilidad BAJA:  62
   • Utilidad NULA:  70
   • Reducción estimada: 53.88%
⏰ Vencimientos:
   • Urgentes (≤7 días): 3
   • Total detectados: 12
🔍 Duplicados:
   • Exactos: 5
   • Cédulas: 8
   • Total: 13
============================================================

[2025-11-03 14:31:25] 🧪 Iniciando comparación automática...
[2025-11-03 14:31:26] ℹ️ Cambios detectados: 15 nuevos, 8 modificados, 2 eliminados
[2025-11-03 14:31:26] ⚠️ 3 vencimientos urgentes detectados (≤7 días)
```

### Notificación en Bandeja del Sistema

```
[Monitor PJN]
✅ Expedientes actualizados: 245

📊 Procesamiento completado:
- 35 actuaciones de alta utilidad
- 3 vencimientos urgentes
- 13 duplicados detectados
```

---

## 🛠️ API del Módulo `integracion_procesador_pdf.py`

### Funciones Principales

```python
# Clasificación
clasificar_actuaciones_expedientes(
    ruta_expedientes: str | Path,
    destino_clasificaciones: str | Path,
    config: Optional[Dict] = None
) -> Optional[Dict]

# Vencimientos
detectar_vencimientos_urgentes(
    ruta_expedientes: str | Path,
    destino_alertas: str | Path,
    dias_urgentes: int = 7,
    config: Optional[Dict] = None
) -> Optional[Tuple[List[Dict], int]]

# Duplicados
analizar_duplicados_detallado(
    ruta_expedientes: str | Path,
    destino_analisis: str | Path,
    config: Optional[Dict] = None
) -> Optional[Dict]

# Procesamiento completo
procesar_expedientes_monitor(
    ruta_expedientes: str | Path,
    directorio_base: str | Path,
    config: Dict
) -> Dict

# Utilidad para logging
registrar_resultado_procesamiento(
    resumen: Dict,
    log_function=None
)
```

---

## ⚙️ Deshabilitar Procesamiento

### Deshabilitar Todo el Procesamiento

```json
{
  "procesador_pdf": {
    "habilitado": false
  }
}
```

### Deshabilitar Funciones Específicas

```json
{
  "procesador_pdf": {
    "habilitado": true,
    "clasificacion_automatica": false,      // Solo clasificación OFF
    "vencimientos_automaticos": true,
    "duplicados_analisis": true
  }
}
```

---

## 🐛 Troubleshooting

### Error: "procesador_pdf no disponible"

**Causa:** El módulo `Sistema_v5/procesador_pdf` no está instalado o no se puede importar.

**Solución:**
1. Verificar instalación del procesador_pdf
2. Asegurarse de estar en la rama `procesador_pdf2.1`
3. Verificar que `Sistema_v5` está en PYTHONPATH

```bash
# Verificar instalación
python -c "from Sistema_v5.procesador_pdf import ClasificadorActuaciones"
```

### Procesamiento lento

**Causa:** Clasificación de muchas actuaciones.

**Solución:**
- El procesamiento de 250 expedientes (≈1000 actuaciones) toma 5-10 segundos
- Si es más lento, verificar CPU/memoria disponible
- Ajustar `timeout_clasificacion` si es necesario

### No se generan reportes

**Causa:** `guardar_reportes=false` o permisos de escritura.

**Solución:**
- Verificar `config_monitor.json` → `procesador_pdf.guardar_reportes`
- Verificar permisos de escritura en `datos_extraidos/monitoreo/`

### No aparecen alertas de vencimientos

**Causa:** Configuración deshabilitada o no hay vencimientos urgentes.

**Solución:**
- Verificar `vencimientos_automaticos=true`
- Verificar `dias_urgentes` (si es muy bajo, puede no haber urgentes)
- Revisar archivos en `datos_extraidos/monitoreo/alertas/`

---

## 📝 Changelog

### v1.0.0 (2025-11-03) - Inicial

**Archivos Nuevos:**
- ✅ `integracion_procesador_pdf.py` - Módulo completo de integración
- ✅ `README_INTEGRACION_MONITOR.md` - Documentación

**Archivos Modificados:**
- ✅ `configuracion_modo.py` - Agregada sección `procesador_pdf` en `DEFAULT_CONFIG`
- ✅ `comparacion_expedientes.py` - Integrada detección de vencimientos urgentes

**Funcionalidades:**
- ✅ Clasificación automática de actuaciones post-extracción
- ✅ Detección de vencimientos urgentes en comparaciones
- ✅ Análisis detallado de duplicados
- ✅ Reportes estructurados en JSON
- ✅ Integración opcional (no rompe funcionalidad existente)

---

## 🔗 Relacionado

- **Tarea 1:** [Integración con PJN Scraping](../../panel_pjn/acciones_pjn/gestion_actuaciones/README_PROCESAMIENTO.md)
- **Módulo Core:** `Sistema_v5/procesador_pdf/`
- **Tests:** `Sistema_v5/tests/test_procesador_pdf.py`
- **Estado General:** `ESTADO_PROCESADOR_PDF2.1.md` (raíz del proyecto)

---

## 👨‍💻 Autor

**Sistema sintaXis**
Integración realizada: 2025-11-03
Rama: `claude/review-pdf-processor-status-011CUkK2WHNDvGkPZTXySM6R`
Tarea: 2 de 3 (Fase A - Integraciones Críticas)

---

## 📄 Licencia

Ver licencia principal del proyecto sintaXis.
