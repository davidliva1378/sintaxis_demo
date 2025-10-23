# 🔄 Flujo Completo del Sistema v5 - De Extracción Inicial a Monitoreo

## 📋 Índice

1. [Resumen del Flujo](#resumen-del-flujo)
2. [Fase 1: Extracción Inicial](#fase-1-extracción-inicial)
3. [Fase 2: Verificación Post-Extracción](#fase-2-verificación-post-extracción)
4. [Fase 3: Monitoreo Continuo](#fase-3-monitoreo-continuo)
5. [Fase 4: Mantenimiento](#fase-4-mantenimiento)
6. [Scripts Disponibles](#scripts-disponibles)

---

## 🎯 Resumen del Flujo

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: EXTRACCIÓN INICIAL (Una sola vez)                  │
├─────────────────────────────────────────────────────────────┤
│ ejecutar_extraccion_inicial_v2.py                           │
│ → Extrae listado completo del PJN                           │
│ → Filtra expedientes deseados                               │
│ → Crea directorios por expediente                           │
│ → Descarga todas las actuaciones                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: VERIFICACIÓN (Opcional pero recomendada)           │
├─────────────────────────────────────────────────────────────┤
│ • Revisar logs en: Sistema_v5/logs/                         │
│ • Verificar directorios creados en: data/expedientes/       │
│ • Revisar reporte en: Sistema_v5/data/reportes/            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: MONITOREO CONTINUO (Diario/periódico)              │
├─────────────────────────────────────────────────────────────┤
│ ejecutar_monitor.py o ejecutar_monitor_continuo.py          │
│ → Verifica nuevas actuaciones en expedientes existentes     │
│ → Descarga actuaciones nuevas                               │
│ → Genera notificaciones/reportes                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ FASE 4: MANTENIMIENTO (Según necesidad)                    │
├─────────────────────────────────────────────────────────────┤
│ • Agregar nuevos expedientes (repetir Fase 1)               │
│ • Revisar expedientes archivados                            │
│ • Limpiar directorios obsoletos                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Fase 1: Extracción Inicial

### ¿Cuándo ejecutarla?
- **Primera vez:** Al incorporar un cliente nuevo
- **Actualización masiva:** Cuando hay muchos expedientes nuevos
- **Migración:** Al cambiar de sistema

### Comando

```bash
cd Sistema_v5
python ejecutar_extraccion_inicial_v2.py --headless
```

### ¿Qué hace?

1. **Extrae listado completo del PJN** → `data/extraccion_inicial/expedientes_YYYYMMDD_HHMMSS.json`
2. **Abre GUI de filtros** → Seleccionas expedientes deseados
3. **Crea directorios** → `data/expedientes/000001_Exp_123_2024/`
4. **Descarga actuaciones completas** → JSON dentro de cada directorio
5. **Genera reporte** → `data/reportes/extraccion_YYYYMMDD_HHMMSS.json`

### Resultado esperado

```
data/
├── extraccion_inicial/
│   ├── expedientes_20251023_103045.json  # Listado completo
│   └── expedientes_20251023_103045.csv   # CSV para análisis
├── expedientes/
│   ├── 000001_Exp_123_2024/
│   │   ├── expediente.json               # Metadata
│   │   ├── actuaciones.json              # Todas las actuaciones
│   │   └── adjuntos/                     # Archivos descargados
│   ├── 000002_Exp_456_2024/
│   └── ...
└── reportes/
    └── extraccion_20251023_110530.json   # Resumen del proceso
```

### Logs generados

```
Sistema_v5/logs/extraccion_inicial_v2.log
```

---

## ✅ Fase 2: Verificación Post-Extracción

### 1. Revisar Logs

```bash
cd Sistema_v5
tail -f logs/extraccion_inicial_v2.log
```

**Buscar:**
- ✅ `EXTRACCIÓN INICIAL COMPLETADA CON ÉXITO`
- ⚠️ Errores: líneas con `❌` o `ERROR`
- 📊 Resumen final: exitosos/errores/omitidos

### 2. Verificar Directorios Creados

```bash
# Contar directorios creados
ls -1d data/expedientes/*/  | wc -l

# Ver estructura de un expediente
tree data/expedientes/000001_Exp_123_2024/
```

**Estructura esperada por expediente:**
```
000001_Exp_123_2024/
├── expediente.json          # Metadata básica
├── actuaciones.json         # Todas las actuaciones
├── adjuntos/                # Archivos descargados (si --no-adjuntos no usado)
│   ├── documento_1.pdf
│   └── documento_2.pdf
└── historico/               # Backups de actuaciones anteriores
```

### 3. Revisar Reporte de Extracción

```bash
# Ver último reporte
cat data/reportes/extraccion_*.json | jq '.'
```

**Información del reporte:**
```json
{
  "resumen": {
    "total": 50,
    "exitosos": 48,
    "errores": 2,
    "omitidos": 0,
    "tiempo_inicio": "2025-10-23T10:30:00",
    "duracion_segundos": 1250.5
  },
  "resultados": [
    {
      "numero": "123/2024",
      "estado": "success",
      "mensaje": "✓ 123/2024 — Act.: 15/20 — Descargas: Sí"
    },
    ...
  ]
}
```

### 4. Verificar JSON de Expedientes

```bash
# Ver un expediente de ejemplo
cat data/expedientes/000001_Exp_123_2024/expediente.json | jq '.'
```

**Contenido esperado:**
```json
{
  "numero_expediente": "123/2024",
  "metadata": {
    "dependencia": "JUZ. CIV. Y COM. FED. 1",
    "caratula": "GARCÍA S/ COBRO DE PESOS",
    "situacion": "En trámite",
    "ultima_actuacion": "23/10/2025"
  },
  "creado_en": "2025-10-23T10:35:12"
}
```

---

## 🔄 Fase 3: Monitoreo Continuo

Una vez completada la extracción inicial, el siguiente paso es **monitorear periódicamente** los expedientes para detectar nuevas actuaciones.

### Opciones de Monitoreo

#### Opción 1: Monitor Simple (Ejecución Manual)

```bash
cd Sistema_v5
python ejecutar_monitor.py
```

**Características:**
- Se ejecuta una vez y termina
- Verifica todos los expedientes configurados
- Descarga nuevas actuaciones
- Genera reporte

**Cuándo usar:**
- Revisiones manuales periódicas
- Testing
- Ejecuciones programadas con cron/Task Scheduler

#### Opción 2: Monitor Continuo (Ejecución Permanente)

```bash
cd Sistema_v5
python ejecutar_monitor_continuo.py
```

**Características:**
- Se ejecuta indefinidamente
- Verifica expedientes según intervalo configurado
- Genera notificaciones cuando hay nuevas actuaciones
- Se puede dejar corriendo en servidor

**Cuándo usar:**
- Servidores dedicados
- Necesidad de notificaciones inmediatas
- Monitoreo 24/7

**Configuración del intervalo:**
Editar `config/monitor.json`:
```json
{
  "intervalo_verificacion_minutos": 60,  // Cada hora
  "notificar_nuevas_actuaciones": true
}
```

#### Opción 3: Monitor con Sistema de Bandeja (GUI)

```bash
cd Sistema_v5
python ejecutar_monitor_tray.py
```

**Características:**
- Icono en bandeja del sistema
- Notificaciones visuales
- Control desde GUI (pausar/reanudar)
- Ideal para uso en escritorio

**Cuándo usar:**
- Computadoras de escritorio
- Usuarios que prefieren interfaz gráfica
- Necesidad de control visual

### Configuración del Monitor

Editar `config/monitor.json`:

```json
{
  "directorio_expedientes_base": "data/expedientes",
  "intervalo_verificacion_minutos": 60,
  "notificar_nuevas_actuaciones": true,
  "descargar_adjuntos": true,
  "headless": true,
  "max_reintentos": 3,
  "umbral_errores_consecutivos": 5
}
```

### ¿Qué hace el Monitor?

1. **Lee listado de expedientes** → Desde `data/expedientes/`
2. **Se conecta al PJN** → Con credenciales configuradas
3. **Verifica cada expediente** → Compara con última versión guardada
4. **Detecta cambios:**
   - Nuevas actuaciones
   - Actualizaciones en actuaciones existentes
   - Cambios en metadata (situación, etc.)
5. **Descarga novedades** → Actualiza `actuaciones.json`
6. **Genera notificaciones** → Según configuración
7. **Guarda logs** → En `Sistema_v5/logs/monitor_*.log`

### Logs del Monitor

```bash
# Ver actividad en tiempo real
tail -f Sistema_v5/logs/monitor.log

# Buscar novedades detectadas
grep "NUEVA ACTUACIÓN" Sistema_v5/logs/monitor.log
```

---

## 🛠️ Fase 4: Mantenimiento

### 1. Agregar Nuevos Expedientes

Si necesitas incorporar expedientes nuevos después de la extracción inicial:

**Opción A: Repetir extracción inicial completa**
```bash
cd Sistema_v5
python ejecutar_extraccion_inicial_v2.py --headless
# En GUI: filtrar solo los nuevos expedientes
```

**Opción B: Agregar manualmente (avanzado)**
```bash
# 1. Crear directorio
cd Sistema_v5
python gestor_directorios_expedientes.py --crear "789/2024"

# 2. El monitor lo detectará automáticamente en próxima ejecución
```

### 2. Gestión de Expedientes Archivados

**Identificar expedientes archivados:**
```bash
cd Sistema_v5
python -c "
import json
from pathlib import Path

expedientes_dir = Path('data/expedientes')
for exp_dir in expedientes_dir.iterdir():
    if exp_dir.is_dir():
        exp_json = exp_dir / 'expediente.json'
        if exp_json.exists():
            data = json.loads(exp_json.read_text())
            if data.get('metadata', {}).get('situacion') == 'Archivado':
                print(f'Archivado: {exp_dir.name}')
"
```

**Opciones:**
- Moverlos a directorio `data/expedientes_archivados/`
- Excluirlos del monitoreo (configurar filtros en monitor.json)
- Mantenerlos pero reducir frecuencia de verificación

### 3. Limpiar Directorios Obsoletos

```bash
# Backup antes de limpiar
tar -czf backup_expedientes_$(date +%Y%m%d).tar.gz data/expedientes/

# Eliminar expedientes específicos
rm -rf data/expedientes/000005_Exp_999_2023/
```

### 4. Revisar Uso de Espacio

```bash
# Tamaño total de expedientes
du -sh data/expedientes/

# Top 10 expedientes más pesados
du -sh data/expedientes/*/ | sort -hr | head -10

# Tamaño de adjuntos
du -sh data/expedientes/*/adjuntos/ | sort -hr | head -10
```

---

## 📚 Scripts Disponibles

### Scripts Principales

| Script | Descripción | Cuándo usar |
|--------|-------------|-------------|
| `ejecutar_extraccion_inicial_v2.py` | Extracción inicial con filtros | Primera vez o actualización masiva |
| `ejecutar_monitor.py` | Monitor simple (una ejecución) | Revisiones manuales periódicas |
| `ejecutar_monitor_continuo.py` | Monitor continuo (loop infinito) | Servidores, monitoreo 24/7 |
| `ejecutar_monitor_tray.py` | Monitor con GUI en bandeja | Computadoras de escritorio |
| `ejecutar_web.py` | Interfaz web del monitor | Acceso remoto vía navegador |

### Scripts de Utilidad

| Script | Descripción |
|--------|-------------|
| `gestor_directorios_expedientes.py` | Gestión manual de directorios |
| `inicializar_directorios.py` | Crear estructura de carpetas inicial |
| `mi_monitor_expedientes.py` | Monitor personalizado simple |

### Scripts de Debug/Testing

| Script | Descripción |
|--------|-------------|
| `test_monitor_simple.py` | Test básico del monitor |
| `debug_consultas.py` | Debug de consultas al PJN |
| `test_filtro_entradas.py` | Test de filtros |

---

## 🎯 Flujo Recomendado para Producción

### Setup Inicial (Una vez)

```bash
# 1. Navegar al directorio
cd Sistema_v5

# 2. Configurar credenciales (si no están configuradas)
# Editar config/sistema.json y config/monitor.json

# 3. Inicializar estructura de directorios
python inicializar_directorios.py

# 4. Ejecutar extracción inicial
python ejecutar_extraccion_inicial_v2.py --headless

# 5. Verificar resultados
cat data/reportes/extraccion_*.json | jq '.resumen'
```

### Operación Diaria (Automática)

**Opción A: Cron Job (Linux/Mac)**

```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar cada hora)
0 * * * * cd /ruta/a/sintaXis/Sistema_v5 && python ejecutar_monitor.py >> logs/cron.log 2>&1
```

**Opción B: Task Scheduler (Windows)**

```powershell
# Crear tarea programada
schtasks /create /tn "MonitorPJN" /tr "python C:\ruta\a\sintaXis\Sistema_v5\ejecutar_monitor.py" /sc hourly
```

**Opción C: Servicio Continuo (Servidor)**

```bash
# Usar screen o tmux para sesión persistente
screen -S monitor_pjn
cd Sistema_v5
python ejecutar_monitor_continuo.py

# Detach con Ctrl+A, D
# Reattach con: screen -r monitor_pjn
```

---

## ❓ Preguntas Frecuentes

### ¿Debo repetir la extracción inicial cada vez?

**No.** La extracción inicial se hace **una sola vez** o cuando:
- Incorporas un cliente nuevo
- Hay muchos expedientes nuevos (más de 10-20)
- Migraste de otro sistema

Para el día a día, usa el **monitor**.

### ¿Qué pasa si el monitor encuentra nuevas actuaciones?

El monitor:
1. Descarga la nueva actuación
2. Actualiza `actuaciones.json` del expediente
3. Guarda backup del anterior en `historico/`
4. Genera notificación (si está configurado)
5. Registra en el log

### ¿Puedo ejecutar monitor y extracción inicial al mismo tiempo?

**No es recomendable.** Pueden competir por:
- Sesión del PJN
- Escritura en los mismos archivos

Ejecuta la extracción inicial fuera del horario del monitor.

### ¿Cómo sé si hay errores?

**Revisar logs:**
```bash
# Errores en extracción inicial
grep "ERROR\|❌" Sistema_v5/logs/extraccion_inicial_v2.log

# Errores en monitor
grep "ERROR" Sistema_v5/logs/monitor.log
```

**Revisar reportes:**
```bash
# Ver resumen del último reporte
cat data/reportes/extraccion_*.json | jq '.resumen'
```

### ¿Qué hago si un expediente falla repetidamente?

1. **Revisar logs** para identificar el error específico
2. **Verificar manualmente** en el PJN si el expediente existe
3. **Excluir temporalmente** ese expediente del monitor
4. **Reportar** si es un bug del scraper

---

## 📞 Próximos Pasos

Después de completar la extracción inicial:

1. ✅ **Verificar logs y reportes** (Fase 2)
2. ✅ **Configurar monitor** según tus necesidades
3. ✅ **Ejecutar monitor** manualmente para probar
4. ✅ **Automatizar** con cron/task scheduler
5. ✅ **Configurar notificaciones** (opcional)

---

**Documentación relacionada:**
- `GUIA_EXTRACCION_INICIAL_V2.md` - Detalles de extracción inicial
- `config/monitor.json` - Configuración del monitor
- `config/sistema.json` - Configuración general

**Versión:** 1.0
**Fecha:** 23 de Octubre de 2025
