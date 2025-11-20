# Procesador PDF - Módulo de Análisis Inteligente de Actuaciones

Sistema inteligente para procesamiento, clasificación y análisis de actuaciones judiciales en formato PDF.

## 📋 Características

### ✅ Implementado (v1.0 - MVP)

- **Clasificador de Utilidad Jurídica**: Clasifica actuaciones por relevancia (nula, baja, media, alta) usando reglas heurísticas
- **Detector de Duplicados Exactos**: Identifica cédulas y actuaciones duplicadas por contenido normalizado
- **Extractor de Texto**: Extrae texto de PDFs (embebido + OCR opcional)
- **Analizador de Vencimientos**: Detecta plazos y calcula fechas de vencimiento con días hábiles
- **API Unificada**: Funciones helper para procesamiento completo

### 🚧 Planificado (Fases 2-3)

- Detector de duplicados semánticos (SimHash/MinHash)
- Generador de texto jurídico con IA (apelaciones, expresión de agravios)
- Sistema de alertas multinivel
- RAG jurídico optimizado

## 🚀 Instalación

```bash
# Clonar el repositorio
cd sintaXis/Sistema_v5

# Instalar dependencias
pip install -r requirements.txt

# Para OCR (opcional):
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang

# Windows
# Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```

## 📖 Uso Básico

### 1. Clasificar actuaciones

```python
from Sistema_v5.procesador_pdf import ClasificadorActuaciones

clasificador = ClasificadorActuaciones()

# Clasificar una actuación
clasificacion = clasificador.clasificar(
    tipo="SENTENCIA",
    detalle="Sentencia definitiva resolviendo el fondo del asunto",
    tiene_archivo=True
)

print(clasificacion.utilidad)  # UtilidadJuridica.ALTA
print(clasificacion.score)     # 85
print(clasificacion.motivo)    # "Tipo de alta prioridad: SENTENCIA"

# Clasificar lote de actuaciones
actuaciones = [
    {"id": 1, "tipo": "PROVIDENCIA", "detalle": "Agréguese", "tiene_archivo": False},
    {"id": 2, "tipo": "SENTENCIA", "detalle": "Sentencia definitiva...", "tiene_archivo": True},
    {"id": 3, "tipo": "CEDULA_ELECTRONICA", "detalle": "Notificado el 15/03/2024", "tiene_archivo": True},
]

clasificaciones = clasificador.clasificar_lote(actuaciones)

# Obtener estadísticas
stats = clasificador.estadisticas_clasificacion(clasificaciones)
print(f"Reducción estimada: {stats['reduccion_estimada']}%")
```

### 2. Detectar duplicados

```python
from Sistema_v5.procesador_pdf import DetectorDuplicados

detector = DetectorDuplicados()

# Detectar duplicados exactos
actuaciones = [
    {"id": 1, "Detalle": "Cédula notificada a Juan Pérez el 15/03/2024"},
    {"id": 2, "Detalle": "Cédula notificada a María López el 15/03/2024"},
    {"id": 3, "Detalle": "Cédula notificada a Carlos Gómez el 15/03/2024"},
]

duplicados = detector.detectar_duplicados_exactos(actuaciones, campo_texto="Detalle")

for dup in duplicados:
    print(f"Actuación {dup.actuacion_id_duplicada} es duplicado de {dup.actuacion_id_original}")
    print(f"Similitud: {dup.similitud * 100}%")

# Detectar cédulas duplicadas (caso especial)
duplicados_cedulas = detector.detectar_cedulas_duplicadas(actuaciones)
```

### 3. Extraer texto de PDFs

```python
from Sistema_v5.procesador_pdf import ExtractorTexto

extractor = ExtractorTexto(usar_ocr=True, idioma_ocr="spa")

# Extraer texto completo
texto = extractor.extraer("ruta/al/archivo.pdf")

print(f"Páginas: {texto.num_paginas}")
print(f"Método: {texto.metodo_extraccion}")
print(f"Palabras: {texto.longitud_palabras}")
print(f"Está vacío: {texto.esta_vacio}")

# Extraer solo primeros 500 caracteres (para clasificación rápida)
preview = extractor.extraer_primeros_n_caracteres("ruta/al/archivo.pdf", n=500)

# Detectar estructura formal
if extractor.detectar_estructura_formal(preview):
    print("Es un documento formal (sentencia, resolución, etc.)")
```

### 4. Analizar vencimientos

```python
from Sistema_v5.procesador_pdf import AnalizadorVencimientos

analizador = AnalizadorVencimientos(considerar_feria=True)

# Analizar texto
texto_cedula = """
Cédula de notificación electrónica.
Notificado el 15/03/2024 a las 10:30hs.
Plazo: 5 días hábiles para contestar.
"""

vencimientos = analizador.analizar_texto(texto_cedula)

for venc in vencimientos:
    print(f"Tipo: {venc.tipo.value}")
    print(f"Notificación: {venc.fecha_notificacion}")
    print(f"Vencimiento: {venc.fecha_vencimiento}")
    print(f"Días restantes: {venc.dias_restantes}")
    print(f"¿Urgente?: {venc.es_urgente}")
    print(f"¿Vencido?: {venc.esta_vencido}")

# Filtrar vencimientos urgentes
urgentes = analizador.filtrar_vencimientos_urgentes(vencimientos, dias_umbral=5)
```

### 5. Procesamiento completo (API unificada)

```python
from Sistema_v5.procesador_pdf import procesar_actuacion, procesar_expediente

# Procesar una actuación
actuacion = {
    "id": 1,
    "tipo": "CEDULA_ELECTRONICA",
    "detalle": "Notificación del 15/03/2024...",
    "tiene_archivo": True
}

resultado = procesar_actuacion(
    actuacion,
    ruta_pdf="/path/to/cedula.pdf",
    analizar_vencimientos=True,
    detectar_duplicados=False
)

print(f"Utilidad: {resultado.clasificacion.utilidad.value}")
print(f"Vencimientos: {len(resultado.vencimientos)}")
print(f"Requiere atención: {resultado.requiere_atencion}")

# Procesar expediente completo
actuaciones_expediente = [...]  # Lista de actuaciones
rutas_pdf = {1: "path1.pdf", 2: "path2.pdf"}

resultado_expediente = procesar_expediente(
    actuaciones_expediente,
    rutas_pdf=rutas_pdf,
    analizar_vencimientos=True,
    detectar_duplicados=True
)

print(f"Total actuaciones: {resultado_expediente['total_actuaciones']}")
print(f"Vencimientos urgentes: {len(resultado_expediente['vencimientos_urgentes'])}")
print(f"Duplicados detectados: {len(resultado_expediente['duplicados_detectados'])}")
print(f"Estadísticas: {resultado_expediente['estadisticas']}")
```

## 📂 Estructura del Módulo

```
procesador_pdf/
├── __init__.py                      # API pública
├── models.py                        # Modelos de datos (dataclasses)
├── clasificador.py                  # Clasificador de utilidad jurídica
├── detector_duplicados.py           # Detector de duplicados
├── extractor_texto.py               # Extractor de texto de PDFs
├── analizador_vencimientos.py       # Analizador de plazos
├── Plan_Procesamiento_Actuaciones_Hibrido.md  # Plan original
├── MEJORAS_PROPUESTAS.md            # Mejoras implementadas
└── README.md                        # Esta documentación
```

## 🎯 Casos de Uso

### Filtrar actuaciones sin valor

```python
clasificador = ClasificadorActuaciones()

# Clasificar todas las actuaciones
clasificaciones = clasificador.clasificar_lote(todas_las_actuaciones)

# Filtrar solo las relevantes
relevantes = [
    act for act_id, act in enumerate(todas_las_actuaciones)
    if clasificaciones[act_id].utilidad in [UtilidadJuridica.ALTA, UtilidadJuridica.MEDIA]
]

print(f"Reducción: {len(todas_las_actuaciones) - len(relevantes)} actuaciones filtradas")
```

### Eliminar cédulas duplicadas

```python
detector = DetectorDuplicados()

# Detectar cédulas duplicadas
duplicados = detector.detectar_cedulas_duplicadas(cedulas)

# Obtener IDs de duplicados a eliminar
ids_a_eliminar = {dup.actuacion_id_duplicada for dup in duplicados}

# Filtrar actuaciones
cedulas_unicas = [c for c in cedulas if c["id"] not in ids_a_eliminar]

print(f"Eliminadas {len(ids_a_eliminar)} cédulas duplicadas")
```

### Monitorear vencimientos

```python
analizador = AnalizadorVencimientos()

# Analizar todas las actuaciones del expediente
todos_vencimientos = []
for actuacion in actuaciones:
    vencimientos = analizador.analizar_actuacion(actuacion)
    todos_vencimientos.extend(vencimientos)

# Filtrar urgentes (próximos 3 días)
urgentes = analizador.filtrar_vencimientos_urgentes(todos_vencimientos, dias_umbral=3)

# Enviar alertas
for venc in urgentes:
    if venc.dias_restantes == 0:
        enviar_alerta_urgente(venc)
    elif venc.dias_restantes <= 3:
        enviar_alerta_preventiva(venc)
```

## 🔧 Configuración Avanzada

### Personalizar clasificador

```python
# Modificar patrones y keywords
clasificador = ClasificadorActuaciones()

# Agregar patrones personalizados
clasificador.PATRONES_NULA.append(r"^sin\s+efecto")
clasificador.KEYWORDS_ALTA.append("medida.*cautelar")

# Re-compilar patrones
clasificador._compilar_patrones()
```

### Personalizar feriados

```python
from datetime import date

analizador = AnalizadorVencimientos()

# Agregar feriados personalizados (ej: provinciales)
analizador.FERIADOS_2024.extend([
    date(2024, 11, 8),  # Feriado provincial ejemplo
])
```

## 📊 Métricas y KPIs

```python
# Después de procesar un expediente
resultado = procesar_expediente(actuaciones, rutas_pdf)

print("\n=== ESTADÍSTICAS ===")
print(f"Total actuaciones: {resultado['estadisticas']['total_actuaciones']}")
print(f"Utilidad NULA: {resultado['estadisticas']['nula']['count']} ({resultado['estadisticas']['nula']['porcentaje']}%)")
print(f"Utilidad BAJA: {resultado['estadisticas']['baja']['count']} ({resultado['estadisticas']['baja']['porcentaje']}%)")
print(f"Utilidad MEDIA: {resultado['estadisticas']['media']['count']} ({resultado['estadisticas']['media']['porcentaje']}%)")
print(f"Utilidad ALTA: {resultado['estadisticas']['alta']['count']} ({resultado['estadisticas']['alta']['porcentaje']}%)")
print(f"Reducción estimada: {resultado['estadisticas']['reduccion_estimada']}%")
print(f"Duplicados detectados: {len(resultado['duplicados_detectados'])}")
print(f"Vencimientos totales: {resultado['vencimientos_totales']}")
print(f"Vencimientos urgentes: {len(resultado['vencimientos_urgentes'])}")
```

## 🧪 Testing

```bash
# Ejecutar tests (cuando estén implementados)
cd Sistema_v5
pytest procesador_pdf/tests/ -v

# Con cobertura
pytest procesador_pdf/tests/ --cov=procesador_pdf --cov-report=html
```

## 🛣️ Roadmap

### Fase 1 (Completada) ✅
- [x] Clasificador por reglas heurísticas
- [x] Detector de duplicados exactos
- [x] Extractor de texto (PyPDF2 + pdfplumber)
- [x] Analizador de vencimientos básico
- [x] API unificada

### Fase 2 (Próxima)
- [ ] Detector de duplicados semánticos (SimHash)
- [ ] Sistema de alertas multinivel
- [ ] Dashboard de monitoreo
- [ ] Integración con base de datos MySQL

### Fase 3 (Futuro)
- [ ] Generador de texto jurídico con IA
- [ ] RAG jurídico optimizado
- [ ] Auto-evaluación de calidad
- [ ] Feedback loop para mejora continua

## 📝 Notas Importantes

### Sobre OCR

El OCR (pytesseract) es **opcional** y solo se usa cuando el PDF no tiene texto embebido. Para habilitarlo:

1. Instalar Tesseract en el sistema (ver Instalación)
2. Crear extractor con `usar_ocr=True`

```python
extractor = ExtractorTexto(usar_ocr=True, idioma_ocr="spa")
```

### Sobre Días Hábiles

El cálculo de días hábiles considera:
- Sábados y domingos (no hábiles)
- Feriados nacionales (hardcodeados 2024-2025)
- Feria judicial (enero-febrero, configurable)

Para años futuros o feriados provinciales, personalizar manualmente.

### Sobre Performance

- **Clasificación**: ~1000 actuaciones/segundo (solo metadatos)
- **Detección duplicados**: ~500 actuaciones/segundo
- **Extracción texto**: ~2-5 PDFs/segundo (sin OCR)
- **OCR**: ~1 página/segundo (depende de resolución y CPU)

## 🐛 Troubleshooting

### Error: "PyPDF2 no está instalado"

```bash
pip install PyPDF2
```

### Error: "pytesseract not found"

Asegurarse de tener Tesseract instalado en el sistema (no solo el paquete Python).

### Vencimientos no detectados

Verificar que el texto contenga patrones reconocibles:
- Fechas en formato DD/MM/YYYY o DD-MM-YYYY
- Palabras clave: "notificado", "plazo", "días"

### Duplicados no detectados

Los duplicados se detectan por contenido normalizado. Si las cédulas tienen texto muy diferente, no se detectarán como duplicadas.

## 📄 Licencia

Parte del sistema jurídico sintaXis.

## 👥 Contribuciones

Para contribuir o reportar bugs, ver el repositorio principal de sintaXis.

---

**Versión**: 1.0.0 (MVP - Fase 1)
**Última actualización**: 2025-10-31
