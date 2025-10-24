# ⚡ Guía Rápida - Sistema v5

## 🚀 Inicio Rápido (Primera Vez)

```bash
# 1. Navegar a Sistema_v5
cd Sistema_v5

# 2. Ejecutar extracción inicial
python ejecutar_extraccion_inicial_v2.py --headless

# 3. Seleccionar expedientes en la GUI que aparece

# 4. Esperar a que termine (puede tardar varios minutos)

# 5. Verificar resultados
python verificar_extraccion.py
```

---

## 📋 Comandos Principales

### Extracción Inicial (Una sola vez)

```bash
cd Sistema_v5

# Básico
python ejecutar_extraccion_inicial_v2.py --headless

# Sin filtros (todos los expedientes)
python ejecutar_extraccion_inicial_v2.py --headless --no-filtros

# Umbral de errores mayor
python ejecutar_extraccion_inicial_v2.py --headless --umbral-errores 10
```

### Verificación Post-Extracción

```bash
cd Sistema_v5
python verificar_extraccion.py
```

### Monitoreo (Uso diario)

```bash
cd Sistema_v5

# Monitor simple (una ejecución)
python ejecutar_monitor.py

# Monitor continuo (loop infinito)
python ejecutar_monitor_continuo.py

# Monitor con GUI en bandeja
python ejecutar_monitor_tray.py
```

---

## 📁 Estructura de Archivos

```
Sistema_v5/
├── data/
│   ├── extraccion_inicial/
│   │   ├── expedientes_YYYYMMDD_HHMMSS.json  # Listado extraído
│   │   └── expedientes_YYYYMMDD_HHMMSS.csv   # CSV
│   ├── expedientes/
│   │   ├── 000001_Exp_123_2024/              # Directorio por expediente
│   │   │   ├── expediente.json               # Metadata
│   │   │   ├── actuaciones.json              # Actuaciones
│   │   │   └── adjuntos/                     # Archivos
│   │   └── ...
│   └── reportes/
│       └── extraccion_YYYYMMDD_HHMMSS.json   # Reporte del proceso
└── logs/
    ├── extraccion_inicial_v2.log             # Log de extracción
    └── monitor.log                            # Log del monitor
```

---

## 🔍 Verificación Rápida

```bash
# Ver últimas líneas del log
tail -20 Sistema_v5/logs/extraccion_inicial_v2.log

# Contar expedientes procesados
ls -1d Sistema_v5/data/expedientes/*/ | wc -l

# Ver último reporte
cat Sistema_v5/data/reportes/extraccion_*.json | tail -1 | jq '.resumen'

# Ver expedientes con errores
grep "ERROR" Sistema_v5/logs/extraccion_inicial_v2.log
```

---

## ⚙️ Configuración

### Archivos principales

- `../config/sistema.json` - Configuración general
- `../config/monitor.json` - Configuración del monitor

### Cambios comunes

**Intervalo del monitor:**
```json
// En config/monitor.json
{
  "intervalo_verificacion_minutos": 60  // Cada hora
}
```

**Headless por defecto:**
```json
// En config/sistema.json
{
  "headless": true  // Sin navegador visible
}
```

---

## 🆘 Solución de Problemas

### Error: "No se encontró el archivo de configuración"

```bash
# Verificar que existe
ls -la ../config/sistema.json

# Si no existe, copiar de plantilla
cp ../config/sistema.json.example ../config/sistema.json
```

### Error: "ModuleNotFoundError: No module named 'Sistema_v5'"

```bash
# Asegurarse de estar en Sistema_v5
pwd  # Debe mostrar: .../sintaXis/Sistema_v5

# Si no, navegar al directorio correcto
cd /ruta/a/sintaXis/Sistema_v5
```

### Expedientes no se descargaron completamente

```bash
# Ver resumen del reporte
python verificar_extraccion.py

# Buscar errores específicos
grep "❌" Sistema_v5/logs/extraccion_inicial_v2.log
```

### El monitor no detecta cambios

```bash
# Verificar que hay expedientes
ls Sistema_v5/data/expedientes/

# Revisar log del monitor
tail -f Sistema_v5/logs/monitor.log

# Ejecutar monitor en modo verbose
python ejecutar_monitor.py --verbose
```

---

## 📊 Estadísticas Rápidas

```bash
# Total de expedientes
ls -1d Sistema_v5/data/expedientes/*/ | wc -l

# Expedientes con adjuntos
find Sistema_v5/data/expedientes/*/adjuntos -type d 2>/dev/null | wc -l

# Tamaño total
du -sh Sistema_v5/data/expedientes/

# Top 5 más pesados
du -sh Sistema_v5/data/expedientes/*/ | sort -hr | head -5
```

---

## 🔄 Flujo Completo

```
1. EXTRACCIÓN INICIAL (una vez)
   ↓
2. VERIFICACIÓN
   ↓
3. MONITOREO CONTINUO (diario)
   ↓
4. MANTENIMIENTO (según necesidad)
```

---

## 📖 Documentación Completa

- **Extracción Inicial:** `docs/GUIA_EXTRACCION_INICIAL_V2.md`
- **Flujo Completo:** `docs/FLUJO_COMPLETO_SISTEMA.md`
- **Resumen Técnico:** `docs/RESUMEN_V2.0.md`
- **Entrega:** `docs/ENTREGA_V2.0.md`

---

## ⏱️ Tiempos Estimados

| Operación | Tiempo estimado |
|-----------|-----------------|
| Extracción inicial (50 exp) | 15-30 min |
| Extracción inicial (100 exp) | 30-60 min |
| Verificación | 1-2 min |
| Monitor (una ejecución) | 5-15 min |

*Tiempos aproximados, varían según conexión y carga del PJN*

---

## 💡 Tips Útiles

- ✅ Ejecutar extracción inicial fuera del horario pico del PJN
- ✅ Usar `--headless` para mejor rendimiento
- ✅ Revisar logs periódicamente
- ✅ Hacer backup de `data/` antes de cambios importantes
- ✅ Automatizar el monitor con cron/task scheduler

---

**Versión:** 1.0
**Última actualización:** Octubre 2025
