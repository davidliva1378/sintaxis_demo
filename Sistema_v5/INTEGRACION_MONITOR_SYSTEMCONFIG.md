# 🔗 Integración del Monitor con SystemConfig

Este documento describe la integración completa entre `SystemConfig` y el sistema de monitoreo.

## 📋 Resumen

La integración permite usar **SystemConfig** (configuración unificada) o **MonitorConfig** (legacy) de forma intercambiable en todo el sistema de monitoreo, manteniendo **100% de retrocompatibilidad**.

---

## ✨ Características

- ✅ **Doble compatibilidad**: MonitorPJN acepta SystemConfig o MonitorConfig
- ✅ **Conversión automática**: SystemConfig se convierte automáticamente a MonitorConfig internamente
- ✅ **Sin breaking changes**: Todo el código existente sigue funcionando
- ✅ **Migración automática**: Script para migrar monitor.json → sistema.json
- ✅ **Tests completos**: 13 tests de integración (100% passing)
- ✅ **Scripts actualizados**: Todos los scripts de ejecución soportan ambos formatos

---

## 🏗️ Arquitectura

### Flujo de Conversión

```
SystemConfig
     ↓
     ├─→ MonitorConfig.from_system_config()  [Adaptador]
     ↓
MonitorConfig
     ↓
     └─→ MonitorPJN(config)  [Auto-detección y conversión]
```

### Componentes Modificados

#### 1. `pjn/monitor/config.py`

**Agregado**: Método adaptador `from_system_config()`

```python
@classmethod
def from_system_config(cls, system_config) -> "MonitorConfig":
    """Crea MonitorConfig desde SystemConfig.

    Este método permite usar SystemConfig con código que espera MonitorConfig,
    manteniendo retrocompatibilidad.
    """
    return cls(
        modo=system_config.modo_monitor,
        headless=system_config.headless,
        directorio_datos=system_config.directorio_monitor_datos,
        # ... mapea todos los campos relevantes
    )
```

**Campos mapeados** (20 total):
- `modo_monitor` → `modo`
- `headless` → `headless`
- `directorio_monitor_datos` → `directorio_datos`
- `intervalos_laboral_expedientes` → `intervalos_laboral_expedientes`
- `intervalos_laboral_entradas` → `intervalos_laboral_entradas`
- `intervalos_no_laboral_expedientes` → `intervalos_no_laboral_expedientes`
- `intervalos_no_laboral_entradas` → `intervalos_no_laboral_entradas`
- `dias_laborales` → `dias_laborales`
- `hora_inicio` → `hora_inicio`
- `hora_fin` → `hora_fin`
- `max_reintentos_expedientes` → `max_reintentos_expedientes`
- `espera_reintentos_expedientes` → `espera_reintentos_expedientes`
- `max_reintentos_entradas` → `max_reintentos_entradas`
- `espera_reintentos_entradas` → `espera_reintentos_entradas`
- `notificar_nuevas_entradas` → `notificar_nuevas_entradas`
- `notificar_cambios_expedientes` → `notificar_cambios_expedientes`
- `notificar_errores` → `notificar_errores`
- `verificar_entradas` → `verificar_entradas`
- `verificar_expedientes` → `verificar_expedientes`
- `comparacion_automatica` → `comparacion_automatica`
- `fecha_corte_expedientes` → `fecha_corte_expedientes`
- `fecha_desde_entradas` → `fecha_desde_entradas`
- `fecha_hasta_entradas` → `fecha_hasta_entradas`
- `fecha_desde_expedientes` → `fecha_desde_expedientes`
- `fecha_hasta_expedientes` → `fecha_hasta_expedientes`

#### 2. `pjn/monitor/core.py`

**Modificado**: Constructor de `MonitorPJN` con auto-detección

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..system_config import SystemConfig

class MonitorPJN:
    def __init__(self, config: "MonitorConfig | SystemConfig"):
        """Inicializa el monitor.

        Acepta tanto MonitorConfig como SystemConfig para máxima flexibilidad.
        """
        # Si recibimos SystemConfig, convertir a MonitorConfig
        if type(config).__name__ == "SystemConfig":
            logger.info("SystemConfig detectado, convirtiendo a MonitorConfig")
            config = MonitorConfig.from_system_config(config)

        self.config = config
        # ... resto de inicialización
```

**Técnica**: Uso de `TYPE_CHECKING` para evitar imports circulares.

#### 3. Scripts de Ejecución

**Actualizados** (3 scripts):

##### `ejecutar_monitor_sistema.py` (NUEVO - Recomendado)

Script específico para usar SystemConfig:

```python
# Cargar configuración unificada
config = SystemConfig.from_file(args.config)

# Crear monitor (auto-conversión interna)
monitor = MonitorPJN(config)

# Modo de verificación inmediata
if args.verificar_ahora:
    if config.verificar_entradas:
        nuevas_entradas = await monitor.verificar_entradas()
    if config.verificar_expedientes:
        expedientes_cambios = await monitor.verificar_expedientes()
else:
    # Modo continuo con scheduler
    scheduler = SchedulerMonitor(monitor)
    await scheduler.ejecutar()
```

**Uso**:
```bash
# Usar config/sistema.json (default)
python ejecutar_monitor_sistema.py

# Usar archivo específico
python ejecutar_monitor_sistema.py --config mi_sistema.json

# Verificación inmediata
python ejecutar_monitor_sistema.py --verificar-ahora
```

##### `ejecutar_monitor.py` (ACTUALIZADO)

Ahora soporta ambos formatos con auto-detección:

```python
# Cargar configuracion - priorizar sistema.json si existe
sistema_path = Path("config/sistema.json")
monitor_path = Path("config/monitor.json")

if sistema_path.exists():
    logger.info("Cargando configuración desde sistema.json")
    config = SystemConfig.from_file(sistema_path)
    modo = config.modo_monitor
elif monitor_path.exists():
    logger.info("Cargando configuración desde monitor.json (legacy)")
    config = MonitorConfig.from_file(monitor_path)
    modo = config.modo
else:
    logger.error("No se encontró archivo de configuración")
    return 1
```

**Comportamiento**:
1. Si existe `config/sistema.json` → lo usa
2. Si no, busca `config/monitor.json` (legacy)
3. Si ninguno existe → error

##### `ejecutar_monitor_continuo.py` (ACTUALIZADO)

Mismo comportamiento de auto-detección para modo continuo.

---

## 🧪 Tests de Integración

### Cobertura: 13 tests (100% passing)

#### 1. **TestSystemConfigToMonitorConfig**
- ✅ `test_from_system_config_preserva_todos_los_valores`: Verifica que la conversión preserva los 20+ campos
- ✅ `test_from_system_config_con_valores_default`: Verifica conversión con defaults

#### 2. **TestMonitorPJNWithSystemConfig**
- ✅ `test_monitor_acepta_system_config`: MonitorPJN acepta SystemConfig
- ✅ `test_monitor_acepta_monitor_config`: MonitorPJN aún acepta MonitorConfig (legacy)
- ✅ `test_monitor_convierte_system_config_internamente`: Verifica conversión automática

#### 3. **TestConfigFilesCompatibility**
- ✅ `test_monitor_carga_desde_sistema_json`: Carga sistema.json y crea monitor
- ✅ `test_monitor_carga_desde_monitor_json`: Carga monitor.json (legacy)
- ✅ `test_migracion_de_monitor_a_sistema`: Migración completa funciona

#### 4. **TestBackwardCompatibility**
- ✅ `test_codigo_legacy_con_monitor_config_sigue_funcionando`: Código antiguo funciona
- ✅ `test_nuevo_codigo_con_system_config_funciona`: Código nuevo funciona
- ✅ `test_mezcla_de_configs_no_causa_problemas`: Ambos configs coexisten

#### 5. **TestEdgeCases**
- ✅ `test_system_config_con_todos_los_campos_opcionales_none`: Maneja None correctamente
- ✅ `test_system_config_con_valores_extremos`: Maneja valores límite

**Ejecutar tests**:
```bash
python -m pytest tests/test_monitor_system_config_integration.py -v
```

---

## 📝 Guías de Uso

### Uso Recomendado (SystemConfig)

```python
from pjn import SystemConfig
from pjn.monitor import MonitorPJN, SchedulerMonitor

# Cargar configuración unificada
config = SystemConfig.from_file("config/sistema.json")

# Crear monitor (conversión automática)
monitor = MonitorPJN(config)

# Usar monitor
await monitor.verificar_entradas()
await monitor.verificar_expedientes()
```

### Uso Legacy (MonitorConfig)

```python
from pjn.monitor import MonitorConfig, MonitorPJN

# Cargar configuración legacy
config = MonitorConfig.from_file("config/monitor.json")

# Crear monitor (sin conversión)
monitor = MonitorPJN(config)

# Usar monitor (misma API)
await monitor.verificar_entradas()
await monitor.verificar_expedientes()
```

### Migración de monitor.json → sistema.json

#### Opción 1: Script de Migración

```bash
python scripts/migrar_configuraciones.py
```

El script:
1. ✅ Lee `config/monitor.json`
2. ✅ Crea backup en `backups/monitor_TIMESTAMP.json`
3. ✅ Convierte a `SystemConfig`
4. ✅ Crea estructura de directorios
5. ✅ Guarda en `config/sistema.json`

#### Opción 2: Programática

```python
from pjn import SystemConfig

# Migrar desde monitor.json
config = SystemConfig.from_monitor_config("config/monitor.json")

# Guardar como sistema.json
config.to_file("config/sistema.json")
```

---

## 🔄 Retrocompatibilidad

### ✅ Garantías

1. **Código existente**: Todo el código que usa `MonitorConfig` sigue funcionando sin cambios
2. **Archivos existentes**: `monitor.json` sigue siendo válido
3. **API pública**: Ningún cambio en la API de `MonitorPJN`
4. **Funcionalidad**: Todas las características existentes preservadas

### 📊 Matriz de Compatibilidad

| Código                    | monitor.json | sistema.json | Resultado |
|---------------------------|--------------|--------------|-----------|
| `MonitorConfig + MonitorPJN` | ✅           | ❌           | ✅ Funciona |
| `SystemConfig + MonitorPJN`  | ❌           | ✅           | ✅ Funciona |
| `ejecutar_monitor.py`     | ✅           | ✅           | ✅ Auto-detecta |
| `ejecutar_monitor_sistema.py` | ❌      | ✅           | ✅ Funciona |

---

## 🚀 Migración Recomendada

### Para Nuevos Proyectos

```bash
# 1. Crear/editar sistema.json con el asistente
python -m Sistema_v5.cli.configuracion wizard

# 2. Usar script nuevo
python ejecutar_monitor_sistema.py
```

### Para Proyectos Existentes

#### Opción A: Migración Completa (Recomendada)

```bash
# 1. Migrar monitor.json → sistema.json
python scripts/migrar_configuraciones.py

# 2. Verificar que funciona
python ejecutar_monitor_sistema.py --verificar-ahora

# 3. Usar nuevo script
python ejecutar_monitor_sistema.py
```

#### Opción B: Convivencia (Transición Gradual)

Mantener ambos archivos durante transición:

```bash
# Scripts legacy siguen funcionando
python ejecutar_monitor.py  # Usa monitor.json

# Nuevos scripts usan sistema.json
python ejecutar_monitor_sistema.py  # Usa sistema.json
```

---

## 🐛 Troubleshooting

### Error: "No se encontró archivo de configuración"

**Causa**: No existe `sistema.json` ni `monitor.json`

**Solución**:
```bash
# Opción 1: Crear sistema.json con el asistente CLI
python -m Sistema_v5.cli.configuracion wizard

# Opción 2: Crear por defecto
python -c "from pjn import SystemConfig; SystemConfig().to_file('config/sistema.json')"
```

### Error: "SystemConfig detectado, convirtiendo a MonitorConfig"

**Causa**: Mensaje informativo (no es error)

**Explicación**: MonitorPJN está convirtiendo automáticamente SystemConfig a MonitorConfig. Esto es comportamiento normal y esperado.

### Diferencias entre monitor.json y sistema.json

**Causa**: Campos adicionales en `sistema.json` no presentes en `monitor.json`

**Solución**: Los campos adicionales tienen valores por defecto. Para personalizar:
```bash
python -m Sistema_v5.cli.configuracion wizard
```

---

## 📚 Referencias

### Archivos Relacionados

- `pjn/system_config.py` - Configuración unificada (50+ opciones)
- `pjn/monitor/config.py` - Configuración del monitor (20 opciones)
- `pjn/monitor/core.py` - Motor del monitor
- `ejecutar_monitor_sistema.py` - Script para SystemConfig (nuevo)
- `ejecutar_monitor.py` - Script con auto-detección (actualizado)
- `tests/test_monitor_system_config_integration.py` - Tests de integración

### Documentación

- `CONFIGURADOR.md` - Guía completa del configurador
- `README.md` - Documentación principal
- `docs/DOCUMENTACION_COMPLETA.md` - API Reference

---

## ✅ Checklist de Integración

- ✅ Adaptador `MonitorConfig.from_system_config()` implementado
- ✅ `MonitorPJN.__init__()` acepta ambos tipos de config
- ✅ Auto-detección y conversión automática
- ✅ Scripts actualizados con soporte dual
- ✅ 13 tests de integración (100% passing)
- ✅ Retrocompatibilidad verificada
- ✅ Documentación completa
- ✅ Migración automática funcional

---

## 🎉 Resumen

La integración entre **SystemConfig** y el **Monitor** está **completa y funcional**:

1. ✅ **Sin breaking changes**: Todo el código existente sigue funcionando
2. ✅ **Flexibilidad máxima**: Usa SystemConfig o MonitorConfig según preferencia
3. ✅ **Migración simple**: Script automático o manual
4. ✅ **Tests completos**: 13 tests verifican toda la integración
5. ✅ **Documentación clara**: Guías para todos los escenarios

**Recomendación**: Para nuevos proyectos, usar **SystemConfig** + **ejecutar_monitor_sistema.py**. Para proyectos existentes, migrar gradualmente o mantener ambos configs durante transición.
