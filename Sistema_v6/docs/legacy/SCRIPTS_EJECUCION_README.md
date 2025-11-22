# Scripts de Ejecución - Integración procesador_pdf

**Tarea 5: Automatización del flujo con scripts CLI**
**Fecha**: 2025-11-03
**Estado**: ✅ COMPLETADO

---

## 📋 Resumen Ejecutivo

Esta integración proporciona scripts de línea de comandos (CLI) para ejecutar las funcionalidades principales del sistema sintaXis con soporte completo para `procesador_pdf`.

**Beneficios clave**:
- **CLI unificado** para todas las operaciones
- **Argumentos flexibles** para personalizar comportamiento
- **Ejecución automatizada** con procesamiento opcional
- **Fácil integración** en workflows y cron jobs

---

## 📁 Scripts Creados

### Scripts Principales

| Script | Propósito | Ubicación |
|--------|-----------|-----------|
| `sintaxis` | **CLI unificado** - Acceso a todos los comandos | Raíz del proyecto |
| `ejecutar_extraccion.py` | Extracción incremental de expedientes | Raíz del proyecto |
| `ejecutar_procesamiento_json.py` | Procesar JSONs existentes | Raíz del proyecto |

### Scripts Modificados

| Script | Cambios | Ubicación |
|--------|---------|-----------|
| `core/flujo_inicial/main_extraccion.py` | Agregados argumentos CLI | `core/flujo_inicial/` |
| `core/flujo_inicial/procesar_actuaciones_json.py` | Ya creado en Tarea 4 | `core/flujo_inicial/` |

---

## 🚀 Uso

### 1. CLI Unificado `sintaxis`

El script `sintaxis` proporciona acceso unificado a todas las funcionalidades.

#### Ver comandos disponibles

```bash
python sintaxis --help
```

Output:
```
SintaXis - Sistema Jurídico Automatizado
Script de línea de comandos unificado

Comandos disponibles:
    extraer         Extrae expedientes del PJN
    procesar        Procesa archivos JSON de actuaciones
    clasificar      Clasifica una actuación específica
    help            Muestra ayuda detallada
```

#### Comando: extraer

```bash
# Extracción básica (sin procesamiento)
python sintaxis extraer

# Extracción CON procesamiento
python sintaxis extraer --procesar

# Procesamiento con umbral personalizado
python sintaxis extraer --procesar --dias-urgentes 3

# Explícitamente SIN procesamiento
python sintaxis extraer --no-procesar
```

#### Comando: procesar

```bash
# Procesar un archivo JSON
python sintaxis procesar datos_extraidos/expediente_123.json

# Procesar carpeta completa
python sintaxis procesar datos_extraidos/monitoreo/ --recursivo

# Con umbral de urgencia personalizado
python sintaxis procesar datos.json --dias-urgentes 5

# Sin análisis de vencimientos (solo clasificación)
python sintaxis procesar datos.json --no-vencimientos
```

#### Comando: clasificar

```bash
# Clasificar una actuación específica
python sintaxis clasificar \
    --tipo "CEDULA_ELECTRONICA" \
    --detalle "Notificación de sentencia definitiva"

# Con archivo adjunto
python sintaxis clasificar \
    --tipo "CEDULA" \
    --detalle "Se notifica..." \
    --con-archivo
```

Output:
```
======================================================================
CLASIFICACIÓN DE ACTUACIÓN
======================================================================

Actuación:
  Tipo: CEDULA_ELECTRONICA
  Detalle: Notificación de sentencia definitiva
  Con archivo: SÍ

Resultado:
  Utilidad: ALTA
  Confianza: 95.5%
  Motivo: Cédula de notificación con plazo procesal
  Tiene plazo probable: SÍ
  Keywords: cedula, notificacion, sentencia, definitiva
```

#### Comando: help

```bash
# Ayuda general
python sintaxis help

# Ayuda de comando específico
python sintaxis help extraer
python sintaxis help procesar
python sintaxis help clasificar
```

---

### 2. Scripts Individuales

#### `ejecutar_extraccion.py`

Script dedicado para extracción de expedientes.

```bash
# Uso básico
python ejecutar_extraccion.py

# Con procesamiento
python ejecutar_extraccion.py --procesar

# Ver todas las opciones
python ejecutar_extraccion.py --help
```

**Opciones disponibles**:
- `--procesar`: Activar procesamiento con procesador_pdf
- `--no-procesar`: Desactivar procesamiento explícitamente
- `--dias-urgentes N`: Umbral de días para vencimientos urgentes (default: 7)

**Output de ejemplo**:

```
======================================================================
EXTRACCIÓN INCREMENTAL DE EXPEDIENTES
======================================================================

Configuración:
  Procesar expedientes: ✅ SÍ
  Días para urgencia: 7
  procesador_pdf disponible: ✅ SÍ

🔁 Intento 1 de extracción...
📄 Página 1...
📊 Expedientes extraídos en página 1: 50
📄 Página 2...
...
📁 Expedientes guardados en datos_extraidos/monitoreo/historico/expedientes_20251103.json

======================================================================
🔄 INICIANDO PROCESAMIENTO DE EXPEDIENTES
======================================================================

📊 RESUMEN DE PROCESAMIENTO:
  Total expedientes: 150
  Procesados: 150

⚠️  VENCIMIENTOS URGENTES DETECTADOS: 3

======================================================================

🏁 Extracción finalizada.
```

#### `ejecutar_procesamiento_json.py`

Script dedicado para procesar archivos JSON existentes.

```bash
# Procesar archivo individual
python ejecutar_procesamiento_json.py datos.json

# Procesar carpeta con recursión
python ejecutar_procesamiento_json.py carpeta/ --recursivo

# Ver opciones
python ejecutar_procesamiento_json.py --help
```

**Opciones**:
- `--recursivo, -r`: Buscar en subcarpetas
- `--dias-urgentes N`: Umbral de urgencia (default: 7)
- `--no-vencimientos`: No analizar vencimientos

---

### 3. Scripts en Contexto

#### `core/flujo_inicial/main_extraccion.py`

Script principal (mejorado con argumentos CLI).

```bash
# Desde el directorio core/flujo_inicial/
cd core/flujo_inicial
python main_extraccion.py --procesar

# Desde raíz del proyecto
python core/flujo_inicial/main_extraccion.py --procesar
```

---

## 🔧 Casos de Uso

### Caso 1: Extracción Diaria Automatizada

Crear un cron job para extraer y procesar expedientes diariamente.

```bash
# Editar crontab
crontab -e

# Agregar tarea diaria a las 8 AM
0 8 * * * cd /home/user/sintaXis && python ejecutar_extraccion.py --procesar >> logs/extraccion.log 2>&1
```

**Beneficio**: Expedientes clasificados y analizados automáticamente cada día.

### Caso 2: Procesamiento de Datos Históricos

Procesar todos los archivos JSON existentes de forma masiva.

```bash
# Procesar todo el histórico
python sintaxis procesar datos_extraidos/monitoreo/historico/ --recursivo

# Con umbral de urgencia de 3 días
python sintaxis procesar datos_extraidos/ --recursivo --dias-urgentes 3
```

**Beneficio**: Clasificar y analizar rápidamente miles de actuaciones acumuladas.

### Caso 3: Clasificación Rápida para Análisis

Clasificar actuaciones específicas para entender su relevancia.

```bash
# Clasificar múltiples actuaciones
python sintaxis clasificar --tipo "CEDULA" --detalle "Notificación de fallo"
python sintaxis clasificar --tipo "AUTO" --detalle "Se da por presentado"
python sintaxis clasificar --tipo "PROVEIDO" --detalle "Agréguese"
```

**Beneficio**: Entender qué tipos de actuaciones son relevantes sin procesar archivos completos.

### Caso 4: Pipeline Completo en Bash Script

Crear un workflow automatizado completo.

```bash
#!/bin/bash
# pipeline_completo.sh

echo "🔄 Iniciando pipeline completo..."

# 1. Extraer expedientes CON procesamiento
python sintaxis extraer --procesar --dias-urgentes 5

# 2. Procesar datos históricos adicionales
python sintaxis procesar datos_extraidos/backup/ --recursivo

# 3. Generar reporte consolidado
python scripts/generar_reporte_consolidado.py

echo "✅ Pipeline completado"
```

### Caso 5: Integración con Sistemas Externos

Usar los scripts desde otros programas.

```python
import subprocess
import json

# Ejecutar extracción
resultado = subprocess.run(
    ["python", "ejecutar_extraccion.py", "--procesar"],
    capture_output=True,
    text=True
)

if resultado.returncode == 0:
    print("✅ Extracción exitosa")

    # Procesar resultados
    with open("datos_extraidos/monitoreo/historico/reportes/estadisticas_*.json") as f:
        stats = json.load(f)

    print(f"Actuaciones de utilidad ALTA: {stats['utilidad_alta']}")
else:
    print(f"❌ Error: {resultado.stderr}")
```

---

## 📊 Comparación: Antes vs Después

### Flujo Anterior (Sin Scripts CLI)

```bash
# Usuario debe:
1. Abrir Python interactivo
2. Importar módulos manualmente
3. Configurar parámetros en código
4. Ejecutar funciones
5. Procesar resultados manualmente

# Ejemplo:
$ python
>>> from core.flujo_inicial import extraccion_incremental_async
>>> import asyncio
>>> asyncio.run(extraccion_incremental_async())
```

**Problemas**:
- ❌ No automatizable fácilmente
- ❌ Requiere conocimiento de Python
- ❌ No se puede usar en cron jobs
- ❌ Difícil de documentar
- ❌ No se puede combinar con otras herramientas

### Flujo Actual (Con Scripts CLI)

```bash
# Usuario ejecuta directamente:
python sintaxis extraer --procesar

# O en cron job:
0 8 * * * cd /path/sintaXis && python sintaxis extraer --procesar

# O en pipeline bash:
./pipeline_completo.sh
```

**Ventajas**:
- ✅ Totalmente automatizable
- ✅ No requiere conocimiento de Python
- ✅ Compatible con cron, systemd, etc.
- ✅ Fácil de documentar y compartir
- ✅ Se integra con cualquier herramienta

---

## 🎯 Argumentos y Opciones

### Argumentos Comunes

| Argumento | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `--procesar` | Flag | False | Activar procesamiento con procesador_pdf |
| `--no-procesar` | Flag | False | Desactivar procesamiento explícitamente |
| `--dias-urgentes` | Int | 7 | Días para considerar vencimiento urgente |
| `--recursivo, -r` | Flag | False | Buscar archivos recursivamente |
| `--no-vencimientos` | Flag | False | No analizar vencimientos |
| `--help, -h` | Flag | - | Mostrar ayuda |

### Argumentos Específicos

#### `sintaxis clasificar`

| Argumento | Tipo | Descripción |
|-----------|------|-------------|
| `--tipo` | String | Tipo de actuación |
| `--detalle` | String | Detalle de actuación |
| `--con-archivo` | Flag | La actuación tiene archivo adjunto |

---

## 🔄 Flujo de Ejecución

### Diagrama de Flujo: `python sintaxis extraer --procesar`

```
Usuario ejecuta comando
       │
       ▼
┌──────────────────────────────────────────┐
│ sintaxis (script CLI principal)         │
│ ├─ Parsea argumentos                    │
│ ├─ Valida opciones                      │
│ └─ Llama a comando_extraer(args)        │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ comando_extraer()                        │
│ ├─ Verifica PROCESADOR_DISPONIBLE       │
│ ├─ Muestra configuración                │
│ └─ Llama a extraccion_incremental_async │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ extraccion_incremental_async()           │
│ ├─ Extrae expedientes del PJN           │
│ ├─ Guarda JSON de expedientes           │
│ └─ Si procesar_expedientes=True:        │
│     ├─ Inicializa ProcesadorExpedientes │
│     ├─ Clasifica actuaciones            │
│     ├─ Analiza vencimientos             │
│     └─ Genera reportes                  │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ Reportes generados:                      │
│ ├─ expedientes_FECHA.json               │
│ ├─ estadisticas_TIMESTAMP.json          │
│ ├─ vencimientos_urgentes_TIMESTAMP.json │
│ └─ errores_TIMESTAMP.json (si aplica)   │
└──────────────────────────────────────────┘
```

---

## 💡 Tips y Mejores Prácticas

### 1. Usar Variables de Entorno

```bash
# Definir configuración en variables
export SINTAXIS_DIAS_URGENTES=5
export SINTAXIS_PROCESAR=true

# Crear wrapper script
python sintaxis extraer --procesar --dias-urgentes ${SINTAXIS_DIAS_URGENTES}
```

### 2. Logging de Ejecuciones

```bash
# Redirigir output a archivo de log
python sintaxis extraer --procesar > logs/extraccion_$(date +%Y%m%d).log 2>&1

# Con timestamp en cada línea
python sintaxis extraer --procesar 2>&1 | ts '[%Y-%m-%d %H:%M:%S]' > logs/extraccion.log
```

### 3. Notificaciones por Email

```bash
#!/bin/bash
# extraccion_con_notificacion.sh

# Ejecutar extracción
python sintaxis extraer --procesar > /tmp/resultado.txt 2>&1

# Si hay vencimientos urgentes, enviar email
if grep -q "VENCIMIENTOS URGENTES" /tmp/resultado.txt; then
    cat /tmp/resultado.txt | mail -s "⚠️ Vencimientos Urgentes Detectados" admin@example.com
fi
```

### 4. Verificación de Salud

```bash
#!/bin/bash
# verificar_procesador.sh

# Verificar que procesador_pdf está disponible
python -c "from Sistema_v5.procesador_pdf import ClasificadorActuaciones; print('OK')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ procesador_pdf disponible"
    python sintaxis extraer --procesar
else
    echo "⚠️ procesador_pdf no disponible, ejecutando solo extracción"
    python sintaxis extraer --no-procesar
fi
```

### 5. Procesamiento en Paralelo

```bash
#!/bin/bash
# procesar_paralelo.sh

# Procesar múltiples carpetas en paralelo con GNU parallel
find datos_extraidos -type d -name "20*" | \
    parallel -j 4 python sintaxis procesar {} --recursivo
```

---

## 🛡️ Manejo de Errores

### Errores Comunes

#### Error 1: "ModuleNotFoundError"

**Problema**: No se encuentra el módulo

```bash
$ python sintaxis extraer --procesar
ModuleNotFoundError: No module named 'core.flujo_inicial'
```

**Solución**:
```bash
# Ejecutar desde la raíz del proyecto
cd /home/user/sintaXis
python sintaxis extraer --procesar

# O agregar al PYTHONPATH
export PYTHONPATH=/home/user/sintaXis:$PYTHONPATH
```

#### Error 2: "procesador_pdf no disponible"

**Problema**: Procesamiento solicitado pero módulo no instalado

```bash
$ python sintaxis extraer --procesar
⚠️ procesador_pdf no disponible, se ejecutará solo extracción
```

**Solución**:
```bash
# Instalar dependencias
cd Sistema_v5/procesador_pdf
pip install -r requirements.txt

# Verificar instalación
python -c "from Sistema_v5.procesador_pdf import ClasificadorActuaciones; print('OK')"
```

#### Error 3: "Permission denied"

**Problema**: Script no es ejecutable

```bash
$ ./sintaxis extraer
bash: ./sintaxis: Permission denied
```

**Solución**:
```bash
# Hacer script ejecutable
chmod +x sintaxis

# O ejecutar con python explícitamente
python sintaxis extraer
```

#### Error 4: Timeout en extracción

**Problema**: Extracción se detiene por timeout

**Solución**:
```bash
# Aumentar timeout en configuración
# O ejecutar en horarios de menos carga
python sintaxis extraer --procesar
# Si falla, reintentar automáticamente
while [ $? -ne 0 ]; do
    echo "Reintentando..."
    sleep 60
    python sintaxis extraer --procesar
done
```

---

## 📚 API de Scripts

### Valores de Retorno

Todos los scripts siguen la convención Unix de códigos de salida:

| Código | Significado | Cuándo ocurre |
|--------|-------------|---------------|
| `0` | Éxito | Operación completada sin errores |
| `1` | Error | Error durante ejecución |
| `2` | Error de argumentos | Argumentos CLI inválidos |
| `130` | Cancelado (Ctrl+C) | Usuario interrumpió ejecución |

**Uso en scripts**:

```bash
python sintaxis extraer --procesar

if [ $? -eq 0 ]; then
    echo "✅ Éxito"
else
    echo "❌ Error"
    exit 1
fi
```

---

## 🎓 Ejemplos Avanzados

### Ejemplo 1: Pipeline Completo con Validación

```bash
#!/bin/bash
# pipeline_validado.sh

set -e  # Detener en primer error

echo "🔄 Iniciando pipeline..."

# 1. Verificar prerequisites
echo "1️⃣ Verificando prerequisites..."
python -c "from Sistema_v5.procesador_pdf import ClasificadorActuaciones" || {
    echo "❌ procesador_pdf no disponible"
    exit 1
}

# 2. Extracción
echo "2️⃣ Extrayendo expedientes..."
python sintaxis extraer --procesar --dias-urgentes 5

# 3. Verificar que se generaron archivos
echo "3️⃣ Verificando archivos generados..."
if [ ! -f "datos_extraidos/monitoreo/historico/expedientes_"*.json ]; then
    echo "❌ No se generaron archivos"
    exit 1
fi

# 4. Procesar históricos adicionales
echo "4️⃣ Procesando históricos..."
python sintaxis procesar datos_extraidos/backup/ --recursivo

# 5. Consolidar reportes
echo "5️⃣ Consolidando reportes..."
python -c "
import json
from pathlib import Path

vencimientos_urgentes = []
for reporte in Path('datos_extraidos').rglob('vencimientos_urgentes_*.json'):
    with open(reporte) as f:
        vencimientos_urgentes.extend(json.load(f))

print(f'📊 Total vencimientos urgentes: {len(vencimientos_urgentes)}')

if vencimientos_urgentes:
    print('⚠️ ATENCIÓN REQUERIDA:')
    for v in vencimientos_urgentes[:5]:
        print(f\"  • {v['expediente']}: {v['tipo']} - Vence en {v['dias_restantes']} días\")
"

echo "✅ Pipeline completado"
```

### Ejemplo 2: Monitoreo Continuo

```bash
#!/bin/bash
# monitoreo_continuo.sh

# Monitorear vencimientos cada 6 horas

while true; do
    echo "[$(date)] Iniciando verificación..."

    # Extraer y procesar
    python sintaxis extraer --procesar --dias-urgentes 3 > /tmp/resultado.txt 2>&1

    # Verificar vencimientos urgentes
    if grep -q "VENCIMIENTOS URGENTES" /tmp/resultado.txt; then
        urgentes=$(grep -oP '(?<=VENCIMIENTOS URGENTES DETECTADOS: )\d+' /tmp/resultado.txt)

        echo "⚠️ $urgentes vencimientos urgentes detectados!"

        # Enviar notificación (Telegram, email, etc.)
        curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d chat_id="$CHAT_ID" \
            -d text="⚠️ $urgentes vencimientos urgentes detectados en sintaXis"
    else
        echo "✅ No hay vencimientos urgentes"
    fi

    echo "Esperando 6 horas..."
    sleep 21600  # 6 horas
done
```

### Ejemplo 3: Clasificación Masiva

```bash
#!/bin/bash
# clasificar_tipos_comunes.sh

# Clasificar los tipos de actuaciones más comunes para entender su relevancia

tipos_comunes=(
    "CEDULA_ELECTRONICA"
    "AUTO"
    "PROVEIDO"
    "OFICIO"
    "SENTENCIA"
    "RESOLUCION"
)

echo "📊 Clasificando tipos comunes de actuaciones..."
echo ""

for tipo in "${tipos_comunes[@]}"; do
    echo "Tipo: $tipo"
    python sintaxis clasificar --tipo "$tipo" --detalle "Ejemplo genérico" | grep "Utilidad:"
    echo ""
done
```

Output:
```
📊 Clasificando tipos comunes de actuaciones...

Tipo: CEDULA_ELECTRONICA
  Utilidad: ALTA

Tipo: AUTO
  Utilidad: MEDIA

Tipo: PROVEIDO
  Utilidad: BAJA

Tipo: OFICIO
  Utilidad: MEDIA

Tipo: SENTENCIA
  Utilidad: ALTA

Tipo: RESOLUCION
  Utilidad: ALTA
```

---

## ✅ Checklist de Integración

- [x] Script CLI unificado `sintaxis` creado
- [x] Script `ejecutar_extraccion.py` creado
- [x] Script `ejecutar_procesamiento_json.py` creado
- [x] `main_extraccion.py` actualizado con argumentos CLI
- [x] Todos los scripts son ejecutables
- [x] Manejo de errores implementado
- [x] Códigos de salida Unix implementados
- [x] Ayuda (`--help`) en todos los comandos
- [x] Documentación completa
- [x] Ejemplos de uso incluidos
- [x] Casos de uso documentados

---

## 🎯 Conclusión

La integración de scripts CLI proporciona:

1. **Acceso unificado** a todas las funcionalidades vía `sintaxis`
2. **Scripts especializados** para casos de uso específicos
3. **Automatización completa** con cron jobs y pipelines
4. **Flexibilidad total** con argumentos CLI configurables
5. **Integración fácil** con sistemas externos

**Resultado**: El sistema sintaXis ahora es completamente automatizable desde la línea de comandos, permitiendo workflows sofisticados, integración con herramientas externas, y despliegues en producción sin intervención manual.

---

**Integración completada el**: 2025-11-03
**Tarea**: 5 de 7 (Fase B - Prioridad MEDIA)
**Estado**: ✅ COMPLETADO
**Próximas tareas opcionales**: Tarea 6 (Generador Documentos), Tarea 7 (Web App/API)
