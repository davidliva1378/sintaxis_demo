# 📘 Guía: Extracción Inicial v2.0

## 🎯 Descripción General

El **sistema de extracción inicial v2.0** replantea el flujo de incorporación de expedientes al sistema, aprovechando el `MonitorPJN` existente y añadiendo capacidades avanzadas de filtrado y procesamiento por lotes.

### Ventajas sobre v1.0

✅ **Reutilización de código:** Usa `MonitorPJN.extraer_listado_inicial()` (no duplica lógica)
✅ **Filtros potentes:** 4 tipos de filtros combinables con GUI intuitiva
✅ **Manejo inteligente de errores:** Umbral configurable con opciones al usuario
✅ **Formato dual:** Exporta JSON + CSV automáticamente
✅ **Extensible:** Preparado para migración futura a SQLite
✅ **Testeable:** Componentes independientes con tests unitarios

---

## 🔄 Flujo Completo

```
┌─────────────────────────────────────────┐
│ 1. EXTRACCIÓN DEL LISTADO              │
│    MonitorPJN.extraer_listado_inicial() │
│    → JSON + CSV                          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 2. FILTRADO AVANZADO (GUI)              │
│    FiltrosAvanzadosForm                 │
│    • Últimos X días                     │
│    • Situación procesal                 │
│    • Dependencia/juzgado                │
│    • Rango de fechas                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 3. GENERACIÓN DE DIRECTORIOS            │
│    GestorDirectoriosExpedientes         │
│    → 000001_Exp_123_2024/               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 4. EXTRACCIÓN COMPLETA BATCH            │
│    ExtractorCompletoBatch               │
│    • Umbral de errores: 5 consecutivos  │
│    • Pregunta al usuario: continuar/    │
│      saltar/cancelar                    │
└─────────────────────────────────────────┘
```

---

## 🚀 Uso Rápido

### Comando Básico

**IMPORTANTE:** El script debe ejecutarse desde el directorio `Sistema_v5`

```bash
cd Sistema_v5
python ejecutar_extraccion_inicial_v2.py
```

### Opciones Avanzadas

```bash
# Modo headless (sin navegador visible)
python ejecutar_extraccion_inicial_v2.py --headless

# Configuración personalizada (ruta relativa a Sistema_v5)
python ejecutar_extraccion_inicial_v2.py --config ../config/desarrollo.json

# Sin filtros (procesar todos)
python ejecutar_extraccion_inicial_v2.py --no-filtros

# Sin descargar adjuntos
python ejecutar_extraccion_inicial_v2.py --no-adjuntos

# Umbral de errores personalizado
python ejecutar_extraccion_inicial_v2.py --umbral-errores 10
```

---

## 📦 Componentes Nuevos

### 1. `FiltradorExpedientes` (filtrador.py)

Clase para aplicar filtros combinables sobre expedientes.

```python
from Sistema_v5.extractor_inicial import FiltradorExpedientes

# Crear filtrador
filtrador = FiltradorExpedientes(expedientes)

# Aplicar filtros encadenados
resultado = (filtrador
    .filtrar_por_dias_atras(30)                      # Últimos 30 días
    .filtrar_por_situacion(["En trámite"])           # Solo activos
    .filtrar_por_dependencia("JUZ. CIV.", regex=False)  # Civiles
    .obtener_resultados())

# Ver estadísticas
stats = filtrador.obtener_estadisticas()
print(f"Retenido: {stats['porcentaje_retenido']:.1f}%")
```

#### Filtros Disponibles

| Filtro | Método | Descripción |
|--------|--------|-------------|
| **Actividad** | `filtrar_por_dias_atras(dias)` | Expedientes con movimientos en últimos N días |
| **Situación** | `filtrar_por_situacion(["En trámite", ...])` | Por estado procesal |
| **Dependencia** | `filtrar_por_dependencia("JUZ.*", regex=True)` | Por juzgado/fuero (soporta regex) |
| **Rango fechas** | `filtrar_por_rango_fechas("2024-01-01", "2024-12-31")` | Por período de inicio |
| **Personalizado** | `filtrar_personalizado(lambda exp: ...)` | Predicado custom |

---

### 2. `FiltrosAvanzadosForm` (filtros_avanzados_form.py)

GUI Tkinter con filtros interactivos y previsualización en tiempo real.

```python
from Sistema_v5.extractor_inicial import mostrar_filtros_avanzados

seleccion = mostrar_filtros_avanzados(expedientes)

if seleccion:
    print(f"Usuario seleccionó {len(seleccion)} expedientes")
```

#### Características de la GUI

- ✅ **4 filtros activables** con checkboxes independientes
- ✅ **Previsualización instantánea** tras cada cambio
- ✅ **Estadísticas en tiempo real** (total, retenido, porcentaje)
- ✅ **Exportación directa** a JSON/CSV/Excel desde la GUI
- ✅ **Treeview con scroll** para grandes volúmenes
- ✅ **Validación de regex** con mensajes de error claros

---

### 3. `MonitorPJN.extraer_listado_inicial()` (core.py)

Nuevo método del monitor para extracción inicial.

```python
from Sistema_v5.pjn.monitor import MonitorPJN, MonitorConfig

config = MonitorConfig.from_file("config/monitor.json")
monitor = MonitorPJN(config)

# Extraer listado completo
expedientes, json_path = await monitor.extraer_listado_inicial(
    exportar_csv=True,  # Genera CSV adicional
)

print(f"✅ {len(expedientes)} expedientes en {json_path}")
```

#### Formato JSON Generado (v2.0)

```json
{
  "metadata": {
    "version": "2.0",
    "timestamp": "2025-01-23T14:30:22",
    "total_expedientes": 100,
    "config_utilizada": {
      "fecha_desde": "2024-01-01",
      "extraccion_completa": true,
      "orden": "fecha"
    }
  },
  "expedientes": [
    {
      "numero": "123/2024",
      "dependencia": "JUZ. CIV. 1",
      "caratula": "TEST S/ PRUEBA",
      "situacion": "En trámite",
      "ultima_actuacion": "15/01/2025"
    }
  ]
}
```

---

### 4. `ExtractorCompletoBatch` (batch_processor.py)

Procesador batch con manejo inteligente de errores.

```python
from Sistema_v5.extractor_inicial.batch_processor import ExtractorCompletoBatch

batch = ExtractorCompletoBatch(
    umbral_errores_consecutivos=5,
    headless=True,
    descargar_adjuntos=True,
)

# Callbacks opcionales
batch.set_callback_progreso(lambda i, t, e: print(f"{i}/{t}: {e.numero}"))
batch.set_callback_error_umbral(lambda n, msgs: "continuar")  # Auto-continuar

# Procesar
resumen = await batch.procesar_lote(expedientes_seleccionados)

print(f"Éxito: {resumen.exitosos}/{resumen.total}")
print(f"Errores: {resumen.errores}")
print(f"Omitidos: {resumen.omitidos}")
```

#### Estrategia de Errores

```
Error #1-4: ✅ Continuar automáticamente
Error #5:   ⏸️  PAUSAR y preguntar al usuario:
            • SÍ → Reiniciar contador, continuar
            • NO → Saltar expedientes restantes
            • CANCELAR → Detener completamente
```

---

## 📊 Exportadores (exporters.py)

Funciones para exportar/importar listados en múltiples formatos.

### Exportación

```python
from Sistema_v5.extractor_inicial import exportar_json, exportar_csv, exportar_excel

# JSON con metadata
exportar_json(expedientes, Path("expedientes.json"), incluir_metadata=True)

# CSV simple
exportar_csv(expedientes, Path("expedientes.csv"))

# Excel con formato (requiere openpyxl)
exportar_excel(expedientes, Path("expedientes.xlsx"))
```

### Importación

```python
from Sistema_v5.extractor_inicial import cargar_json, cargar_csv

# Cargar JSON
expedientes, metadata = cargar_json(Path("expedientes.json"))
print(f"Timestamp: {metadata['timestamp']}")

# Cargar CSV
expedientes = cargar_csv(Path("expedientes.csv"))
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests del filtrador
pytest Sistema_v5/tests/test_filtrador_expedientes.py -v

# Con coverage
pytest Sistema_v5/tests/test_filtrador_expedientes.py --cov=extractor_inicial.filtrador
```

### Estructura de Tests

```
tests/
├── test_filtrador_expedientes.py     ✅ Implementado
├── test_batch_processor.py           🔜 Pendiente
└── test_exporters.py                 🔜 Pendiente
```

---

## 🔧 Configuración

### Añadir a `config/sistema.json`

```json
{
  "directorio_extraccion_inicial": "data/extraccion_inicial",
  "directorio_expedientes_base": "data/expedientes",
  "extraccion_expedientes_completa": true,
  "expedientes_orden": "fecha",
  "expedientes_detener_duplicados": false,
  "dias_atras_expedientes": null,
  "headless": true
}
```

---

## 📈 Roadmap Futuro

### Fase 1: Completar Testing (Sprint 4)
- [ ] Tests para `ExtractorCompletoBatch`
- [ ] Tests para exportadores
- [ ] Tests de integración end-to-end

### Fase 2: Migración a SQLite (Futuro)
```sql
CREATE TABLE expedientes (
    id INTEGER PRIMARY KEY,
    numero TEXT UNIQUE,
    dependencia TEXT,
    caratula TEXT,
    situacion TEXT,
    ultima_actuacion DATE,
    fecha_extraccion TIMESTAMP
);
CREATE INDEX idx_fecha_actuacion ON expedientes(ultima_actuacion);
CREATE INDEX idx_situacion ON expedientes(situacion);
```

### Fase 3: Mejoras UX (Futuro)
- [ ] Progress bar visual en GUI
- [ ] Gráficos de estadísticas (matplotlib)
- [ ] Auto-guardado de filtros favoritos
- [ ] Modo "dry-run" (simular sin crear directorios)

---

## ❓ Preguntas Frecuentes

### ¿Puedo usar el sistema antiguo?

Sí, `ejecutar_extraccion_inicial.py` (v1) sigue funcionando. El v2 es opcional y coexiste.

### ¿Se puede ejecutar sin GUI?

Sí, usa `--no-filtros` para omitir el paso de filtrado.

### ¿Cómo cambiar el umbral de errores?

Usa `--umbral-errores N` (por defecto N=5).

### ¿Qué pasa si cancelo a mitad de proceso?

Los expedientes procesados exitosamente antes de cancelar se mantienen. El reporte JSON muestra el estado de cada uno.

---

## 🐛 Troubleshooting

### Error: "No module named 'openpyxl'"

Solución: `pip install openpyxl` (solo si usas exportación a Excel)

### Error: "Patrón regex inválido"

Verifica la sintaxis del regex. Usa herramientas como [regex101.com](https://regex101.com/)

### La GUI no se actualiza en tiempo real

Asegúrate de activar el checkbox "Activar" para cada filtro antes de aplicarlo.

---

## 🔄 ¿Qué sigue después de la Extracción Inicial?

Una vez completada la extracción inicial exitosamente:

1. **Verificar resultados:**
   ```bash
   cd Sistema_v5
   python verificar_extraccion.py
   ```

2. **Configurar monitoreo continuo:**
   - Consultar: `docs/FLUJO_COMPLETO_SISTEMA.md`
   - Ejecutar monitor: `python ejecutar_monitor.py`

3. **Próximos pasos:**
   - El monitor verificará periódicamente nuevas actuaciones
   - No es necesario repetir la extracción inicial
   - Solo agregar nuevos expedientes cuando sea necesario

📖 **Guía completa del flujo:** `Sistema_v5/docs/FLUJO_COMPLETO_SISTEMA.md`

---

## 📞 Soporte

Para reportar problemas o sugerencias:
- GitHub Issues: https://github.com/tu-repo/issues
- Documentación completa: `Sistema_v5/docs/`

**Documentación relacionada:**
- `FLUJO_COMPLETO_SISTEMA.md` - Flujo de extracción inicial a monitoreo
- `RESUMEN_V2.0.md` - Resumen ejecutivo del sistema
- `ENTREGA_V2.0.md` - Documentación de entrega

---

**Versión:** 2.0.0
**Fecha:** Octubre 2025
**Autor:** Sistema_v5 Team
