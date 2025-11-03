# Procesamiento Inteligente de Actuaciones
**Integración con procesador_pdf v2.1**

## 📋 Descripción

Este módulo integra el **procesador_pdf** con el sistema de extracción de actuaciones del Portal PJN, proporcionando análisis automático de:

- ✅ **Clasificación por utilidad jurídica** (NULA, BAJA, MEDIA, ALTA)
- ✅ **Detección de duplicados** (exactos y cédulas repetidas)
- ✅ **Análisis de vencimientos** y plazos procesales
- ✅ **Extracción de texto** de PDFs (opcional)

---

## 🚀 Uso Básico

### Extracción con Procesamiento Automático (Recomendado)

```python
from panel_pjn.acciones_pjn.gestion_actuaciones import extraer_actuaciones_completas

# Durante la extracción de un expediente
actuales, historicas, error, estadisticas = await extraer_actuaciones_completas(
    page_expediente=page,
    expediente_datos=expediente_info,
    incluir_historicas=True,
    procesar_actuaciones=True  # ← PROCESAMIENTO AUTOMÁTICO HABILITADO
)

if estadisticas:
    print(f"Utilidad ALTA: {estadisticas['UtilidadAlta']}")
    print(f"Vencimientos urgentes: {estadisticas['VencimientosUrgentes']}")
    print(f"Duplicados: {estadisticas['Duplicados']}")
```

**Resultado:** El JSON de actuaciones se guardará con campos adicionales de procesamiento.

---

### Procesamiento Manual de JSON Existente

Si ya tienes archivos JSON de actuaciones extraídos previamente:

```python
from panel_pjn.acciones_pjn.gestion_actuaciones import procesar_actuaciones_extraidas

# Procesar archivo JSON
resultado = procesar_actuaciones_extraidas("actuaciones-1234_2023.json")

# Ver estadísticas
print(resultado["Procesamiento"]["Estadisticas"])

# Ver vencimientos urgentes
for venc in resultado["Procesamiento"]["VencimientosUrgentes"]:
    print(f"Actuación {venc['indice_actuacion']}: vence en {venc['vencimiento']['dias_restantes']} días")
```

---

### Procesamiento en Lote (Múltiples Expedientes)

```python
from panel_pjn.acciones_pjn.gestion_actuaciones.procesamiento import ProcesadorActuacionesExtraccion

procesador = ProcesadorActuacionesExtraccion()

# Procesar todos los JSONs en un directorio
resultados = procesador.procesar_directorio(
    directorio="ActuacionesCompletas",
    patron="actuaciones-*.json"
)

# Ver resumen
for res in resultados:
    if res["exito"]:
        print(f"{res['archivo']}: {res['estadisticas']['Total']} actuaciones procesadas")
```

---

## 📊 Estructura del JSON Procesado

### Antes del Procesamiento

```json
{
  "Expediente": {...},
  "Actuaciones": [
    {
      "Indice": 1,
      "Tipo": "CEDULA_ELECTRONICA",
      "Detalle": "Notificación del traslado de demanda...",
      "Fecha": "2023-05-15",
      "TieneArchivo": true
    }
  ]
}
```

### Después del Procesamiento

```json
{
  "Expediente": {...},
  "Actuaciones": [
    {
      "Indice": 1,
      "Tipo": "CEDULA_ELECTRONICA",
      "Detalle": "Notificación del traslado de demanda...",
      "Fecha": "2023-05-15",
      "TieneArchivo": true,

      "Clasificacion": {
        "utilidad": "ALTA",
        "score": 95,
        "motivo": "Cédula electrónica con plazo procesal relevante",
        "tiene_plazo_probable": true,
        "keywords_detectados": ["cedula", "traslado", "demanda"]
      },
      "UtilidadJuridica": "ALTA",
      "TienePlazo": true,

      "Vencimientos": [
        {
          "tipo": "TRASLADO",
          "fecha_notificacion": "2023-05-15",
          "fecha_vencimiento": "2023-06-05",
          "dias_restantes": 21,
          "es_urgente": false,
          "descripcion": "Traslado de demanda"
        }
      ],
      "TieneVencimientos": true,
      "VencimientosUrgentes": false,

      "EsDuplicado": false
    }
  ],

  "Procesamiento": {
    "Timestamp": "2025-11-03T14:30:00",
    "Version": "1.0.0",
    "Estadisticas": {
      "Total": 25,
      "UtilidadNula": 8,
      "UtilidadBaja": 5,
      "UtilidadMedia": 7,
      "UtilidadAlta": 5,
      "ConVencimientos": 6,
      "VencimientosUrgentes": 2,
      "Duplicados": 3,
      "PorcentajeReduccion": 52.0
    },
    "Duplicados": [
      {
        "tipo": "EXACTO",
        "actuacion_original": 3,
        "actuacion_duplicada": 7,
        "motivo": "Contenido idéntico",
        "similitud": 100.0
      }
    ],
    "VencimientosUrgentes": [
      {
        "indice_actuacion": 12,
        "tipo_actuacion": "CEDULA_ELECTRONICA",
        "vencimiento": {
          "tipo": "CEDULA_ELECTRONICA",
          "dias_restantes": 3,
          "es_urgente": true
        }
      }
    ]
  }
}
```

---

## ⚙️ Configuración Avanzada

### Personalizar Procesamiento

```python
from panel_pjn.acciones_pjn.gestion_actuaciones.procesamiento import ProcesadorActuacionesExtraccion

config = {
    "clasificar": True,              # Clasificar por utilidad
    "detectar_duplicados": True,     # Detectar duplicados
    "analizar_vencimientos": True,   # Analizar plazos
    "extraer_texto_pdfs": False,     # Extraer texto de PDFs (lento)
    "dias_urgente": 5                # Días para considerar urgente
}

procesador = ProcesadorActuacionesExtraccion(config=config)
resultado = procesador.procesar_archivo_json("actuaciones.json")
```

---

## 🔧 Deshabilitar Procesamiento

Si deseas extraer sin procesar (modo legacy):

```python
actuales, historicas, error, estadisticas = await extraer_actuaciones_completas(
    page_expediente=page,
    expediente_datos=expediente_info,
    procesar_actuaciones=False  # ← PROCESAMIENTO DESHABILITADO
)

# estadisticas será None
```

---

## 📈 Beneficios del Procesamiento

| Funcionalidad | Beneficio | Ejemplo |
|--------------|-----------|---------|
| **Clasificación automática** | Identifica actuaciones relevantes vs. ruido | Filtrar 30-40% de actuaciones NULAS/BAJAS |
| **Detección de duplicados** | Evita revisar contenido repetido | Cédulas notificadas 2+ veces |
| **Análisis de vencimientos** | Alertas tempranas de plazos | Detectar vencimiento en 3 días |
| **Estadísticas** | Toma de decisiones informada | "52% de actuaciones son prescindibles" |

---

## 🐛 Troubleshooting

### Error: "módulo procesador_pdf no encontrado"

**Causa:** El módulo `Sistema_v5/procesador_pdf` no está disponible.

**Solución:**
1. Verificar que existe el directorio `Sistema_v5/procesador_pdf`
2. Asegurarse de que está en la rama `procesador_pdf2.1`
3. Verificar que `Sistema_v5` está en el PYTHONPATH

```bash
# Verificar instalación
python -c "from Sistema_v5.procesador_pdf import ClasificadorActuaciones"
```

### Procesamiento lento

**Causa:** Procesamiento de muchas actuaciones o extracción de texto de PDFs habilitada.

**Solución:**
- Deshabilitar `extraer_texto_pdfs` en configuración (está deshabilitado por defecto)
- El procesamiento de 100 actuaciones debería tomar < 10 segundos sin PDFs

### Clasificaciones incorrectas

**Causa:** El clasificador heurístico puede fallar en casos ambiguos.

**Solución:**
- Reportar casos problemáticos para mejorar las reglas
- Considerar usar el clasificador híbrido con LLM (futuro)

---

## 🔗 Módulos Relacionados

- **procesador_pdf** (`Sistema_v5/procesador_pdf/`): Módulo core de procesamiento
- **ia_local** (`Sistema_v5/ia_local/`): Clasificador híbrido con LLM
- **tests** (`Sistema_v5/tests/test_procesador_pdf.py`): Tests unitarios

---

## 📝 Changelog

### v1.0.0 (2025-11-03)
- ✅ Integración inicial con procesador_pdf
- ✅ Clasificación automática por utilidad jurídica
- ✅ Detección de duplicados exactos y cédulas
- ✅ Análisis de vencimientos con días hábiles
- ✅ Procesamiento en lote de directorios
- ✅ Estadísticas completas por expediente

---

## 👨‍💻 Autor

**Sistema sintaXis**
Integración realizada el 2025-11-03
Rama: `claude/review-pdf-processor-status-011CUkK2WHNDvGkPZTXySM6R`

---

## 📄 Licencia

Ver licencia principal del proyecto sintaXis.
