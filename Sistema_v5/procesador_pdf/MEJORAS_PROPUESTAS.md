# Mejoras Propuestas al Plan de Procesamiento de Actuaciones

> **Fecha:** 2025-10-31
> **Objetivo:** Complementar el plan híbrido existente con funcionalidades específicas para análisis jurídico, clasificación inteligente y generación de texto.

---

## 1. Clasificador Inteligente de Utilidad Jurídica

### Problema actual
El plan base clasifica por `tipo/detalle`, pero no detecta eficientemente:
- Providencias simples ("autos de mero trámite": "agréguese", "téngase presente", etc.)
- Actuaciones duplicadas con distinto hash (mismo contenido, distintos metadatos de fecha/hora)
- Cédulas de notificación múltiples del mismo acto para distintos actores

### Mejoras propuestas

#### 1.1 Clasificador por Reglas + ML Híbrido
**Fase 1: Reglas heurísticas (sin necesidad de abrir PDF)**
```
Utilidad NULA (score = 0-10):
- detalle contiene: "agréguese", "téngase presente", "en los términos solicitados"
- tipo = "PROVIDENCIA" AND longitud(detalle) < 50 caracteres
- tipo = "DESPACHO" AND detalle ~= /^(agreg|teng|en.*términ)/i

Utilidad BAJA (score = 11-40):
- tipo = "CEDULA_NOTIF" (pero analizar para agenda)
- tipo = "CARGO" (sólo interesa para trazabilidad)
- tipo = "CONSTANCIA_*"

Utilidad MEDIA (score = 41-70):
- tipo = "PRESENTACION" AND !contiene(["demanda", "contestación", "apelación"])
- tipo = "INFORME_*"
- tipo = "CEDULA_NOTIF" con plazo detectado → reclasificar a ALTA

Utilidad ALTA (score = 71-100):
- tipo = "SENTENCIA", "RESOLUCION", "AUTO_FUNDADO"
- tipo = "PRESENTACION" con keywords jurídicos clave
- tipo = "CEDULA_NOTIF" con plazo/vencimiento
- tipo = "ALEGATO", "EXPRESION_AGRAVIOS"
```

**Fase 2: Análisis de contenido PDF (solo para casos limítrofes)**
- Extraer primeros 500 caracteres del PDF
- Buscar patrones: "Visto", "Considerando", "Resuelve", "Fallo", etc.
- Si contiene estructura formal → score += 20
- Si solo dice "Agréguese" o "Téngase presente" → score = 5

#### 1.2 Atributos nuevos en tabla `actuaciones`
```sql
- utilidad: enum('nula','baja','media','alta')
- score: int (0-100)
- motivo_clasificacion: text -- explicación del score
- revisado_manualmente: bool
- fecha_clasificacion: datetime
```

---

## 2. Detector de Duplicados Semánticos

### Problema
Cédulas de notificación idénticas para distintos actores en el mismo expediente:
- Hash diferente (porque fecha/hora/destinatario cambia)
- Contenido sustancial idéntico

### Mejoras propuestas

#### 2.1 Normalización de contenido
```python
def normalizar_para_comparacion(texto):
    # Eliminar:
    - Fechas y horas
    - Nombres de destinatarios/domicilios
    - Números de folio/cargo
    - Firmas electrónicas y hashes PJN

    # Conservar:
    - Texto del acto notificado
    - Tipo de resolución
    - Identificación del expediente

    return texto_normalizado
```

#### 2.2 Detección de duplicados
**Estrategia 1: SimHash para near-duplicates**
```
1. Calcular simhash del texto normalizado
2. Comparar hamming distance con otros docs del mismo expediente
3. Si distance < umbral (ej: 3 bits) → marcar como duplicado
4. Conservar solo 1 copia "canónica" + referencias a los duplicados
```

**Estrategia 2: MinHash + LSH para escalabilidad**
```
- Útil cuando hay miles de actuaciones
- Agrupar en buckets por similitud
- Procesar solo los candidatos probables
```

#### 2.3 Nueva tabla `duplicados_detectados`
```sql
CREATE TABLE duplicados_detectados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actuacion_original_id INT,  -- actuación que se conserva
    actuacion_duplicada_id INT, -- actuación que se marca como dup
    similitud FLOAT,             -- 0.0-1.0
    tipo_duplicado ENUM('exacto','semantico','parcial'),
    hash_normalizado VARCHAR(64),
    creado_en DATETIME
);
```

---

## 3. Generador de Texto Jurídico con IA

### Objetivo
Generar borradores de escritos jurídicos basados en el análisis del expediente:
- Apelaciones
- Expresión de agravios
- Contestaciones
- Informes

### Arquitectura propuesta

#### 3.1 Pipeline de generación
```
1. Contexto RAG → recuperar actuaciones relevantes
2. Análisis de sentencia/resolución → extraer puntos clave
3. Prompt engineering → plantillas jurídicas por tipo de escrito
4. Generación LLM → Claude/GPT-4 con contexto jurídico
5. Post-procesamiento → formato, citas legales, estructura formal
6. Output → documento .docx/.pdf con formato profesional
```

#### 3.2 Plantillas jurídicas
```python
PLANTILLAS = {
    "apelacion": {
        "estructura": [
            "Encabezado (carátula, partes)",
            "Objeto del recurso",
            "Antecedentes del caso",
            "Fundamentos del agravio",
            "Derecho aplicable",
            "Petitorio"
        ],
        "prompt_base": "..."
    },
    "expresion_agravios": {
        "estructura": [...],
        "max_agravios": 5,
        "prompt_base": "..."
    },
    "contestacion_demanda": {...}
}
```

#### 3.3 Nueva tabla `generaciones_ia`
```sql
CREATE TABLE generaciones_ia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expediente_id INT,
    tipo_documento ENUM('apelacion','agravios','contestacion','informe','otro'),
    actuaciones_base TEXT,      -- IDs de actuaciones usadas como contexto
    prompt_usado TEXT,
    contenido_generado LONGTEXT,
    modelo_usado VARCHAR(50),
    tokens_usados INT,
    calidad_estimada FLOAT,     -- auto-evaluación
    revisado_por_usuario BOOL,
    aprobado BOOL,
    feedback_usuario TEXT,
    creado_en DATETIME
);
```

---

## 4. Sistema de Agenda y Vencimientos Mejorado

### Mejoras sobre el plan base

#### 4.1 Detección inteligente de plazos
```python
PATRONES_PLAZO = {
    "cedula_electronica": {
        "regex": r"notific[oó] el (\d{2}/\d{2}/\d{4})",
        "plazo_dias": 5,  # Art. 135 CPCCN
        "tipo": "cedula_electronica"
    },
    "cedula_fisica": {
        "plazo_dias": 3,
        "tipo": "cedula_fisica"
    },
    "traslado": {
        "regex": r"traslado.*(\d+)\s*d[íi]as?",
        "plazo_variable": True
    },
    "alegato": {
        "regex": r"alegato.*(\d+)\s*d[íi]as?",
        "plazo_variable": True
    }
}
```

#### 4.2 Cálculo de días hábiles
```python
def calcular_vencimiento(fecha_notificacion, plazo_dias, jurisdiccion):
    """
    Considera:
    - Feriados nacionales
    - Feriados provinciales/locales por jurisdicción
    - Feria judicial (enero/febrero)
    - Días inhábiles (art. 152 CPCCN)
    """
    return fecha_vencimiento
```

#### 4.3 Sistema de alertas multinivel
```sql
CREATE TABLE alertas_vencimiento (
    id INT PRIMARY KEY AUTO_INCREMENT,
    notificacion_id INT,
    dias_antes INT,              -- 10, 5, 3, 1, 0 (vencido)
    estado ENUM('pendiente','enviada','atendida','vencida'),
    canal ENUM('email','push','sms','web'),
    destinatario VARCHAR(255),
    enviada_en DATETIME,
    atendida_en DATETIME
);
```

---

## 5. Sistema de Avisos y Notificaciones

### Funcionalidades

#### 5.1 Tipos de avisos
```python
TIPOS_AVISO = {
    "vencimiento_proximo": {
        "prioridad": "alta",
        "dias_antes": [10, 5, 3, 1],
        "color": "amarillo"
    },
    "vencimiento_hoy": {
        "prioridad": "urgente",
        "color": "rojo"
    },
    "nueva_actuacion": {
        "prioridad": "media",
        "filtrar_por": "utilidad >= 'media'"
    },
    "sentencia_publicada": {
        "prioridad": "alta",
        "requiere_accion": True
    },
    "duplicado_detectado": {
        "prioridad": "baja",
        "destinatario": "sistema"
    }
}
```

#### 5.2 Canales de notificación
- **Email**: resumen diario + alertas urgentes
- **Push**: notificaciones en tiempo real (si hay app móvil)
- **Web**: panel de dashboard con badges/contadores
- **SMS**: solo para vencimientos críticos (opcional)

---

## 6. Integración con Sistema Existente

### Compatibilidad con actuaciones_v4/v5

```python
# Usar cargador existente
from Sistema_v4.actuaciones.actuaciones_v5 import cargar_expediente_actuaciones

# Extender con funcionalidad de clasificación
expediente = cargar_expediente_actuaciones("ruta/actuaciones.json")
for actuacion in expediente.iter_actuaciones():
    # Clasificar
    clasificacion = clasificador.clasificar(actuacion)

    # Detectar duplicados
    if clasificacion.utilidad != 'nula':
        duplicados = detector.buscar_duplicados(actuacion, expediente)

    # Analizar vencimientos
    if actuacion.tiene_archivo and clasificacion.puede_tener_plazo:
        vencimientos = analizador.extraer_vencimientos(actuacion)
```

---

## 7. Priorización de Implementación

### Fase 1 (MVP - 2 semanas)
✅ Clasificador por reglas heurísticas
✅ Detector de duplicados exactos (hash)
✅ Extractor básico de vencimientos (regex)
✅ Integración con actuaciones_v5

### Fase 2 (Features avanzadas - 3 semanas)
- Detector de duplicados semánticos (SimHash)
- Analizador de vencimientos con días hábiles
- Sistema de alertas multinivel
- Dashboard de monitoreo

### Fase 3 (IA Generativa - 4 semanas)
- Generador de texto jurídico (apelaciones)
- RAG jurídico optimizado
- Auto-evaluación de calidad
- Feedback loop para mejora continua

---

## 8. Métricas de Éxito

```python
KPIS = {
    "precision_clasificador": {
        "target": "> 95%",
        "metrica": "actuaciones correctamente clasificadas / total"
    },
    "recall_duplicados": {
        "target": "> 90%",
        "metrica": "duplicados detectados / duplicados reales"
    },
    "deteccion_vencimientos": {
        "target": "> 98%",
        "metrica": "vencimientos detectados / total con plazo"
    },
    "calidad_texto_generado": {
        "target": "> 80% aprobación",
        "metrica": "documentos aprobados / total generados"
    },
    "reduccion_volumen": {
        "target": "30-40%",
        "metrica": "actuaciones filtradas por baja utilidad"
    }
}
```

---

## 9. Consideraciones de Seguridad

### 9.1 Generación de texto jurídico
- **Disclaimer obligatorio**: "Documento generado con asistencia de IA - requiere revisión profesional"
- **Trazabilidad**: guardar prompt + contexto usado
- **Versionado**: permitir regeneración con distintos parámetros
- **Auditoría**: log de todos los documentos generados

### 9.2 Acceso a documentos sensibles
- Control de acceso por rol (abogado, secretario, cliente)
- Registro de quién accedió a cada PDF
- Opciones de anonimización para análisis/entrenamiento

---

## 10. Stack Tecnológico Recomendado

```python
# Procesamiento de PDFs
pypdf2==3.0.1          # extracción de texto
pdfplumber==0.10.3     # tablas y estructura
pytesseract==0.3.10    # OCR para PDFs escaneados

# Análisis de texto
spacy==3.7.2           # NLP, tokenización, NER
es_core_news_md        # modelo español

# Detección de duplicados
datasketch==1.6.4      # MinHash, LSH
simhash==2.1.2         # SimHash

# Embeddings y RAG
sentence-transformers==2.3.1
faiss-cpu==1.7.4       # o faiss-gpu
chromadb==0.4.22       # alternativa a FAISS

# LLM (generación de texto)
anthropic==0.18.1      # Claude API
openai==1.12.0         # GPT-4 (alternativa)

# Utilidades
python-dateutil==2.8.2
holidays==0.42         # feriados argentinos
```

---

## 11. Roadmap de Implementación

```
Semana 1-2: Clasificador + Detector duplicados exactos
├── Implementar reglas heurísticas
├── Tests con actuaciones reales
├── Integración con actuaciones_v5
└── Documentación API

Semana 3-4: Extractor de vencimientos + Agenda
├── Patrones regex por tipo de actuación
├── Cálculo de días hábiles
├── Sistema de alertas básico
└── UI para gestión de agenda

Semana 5-7: Duplicados semánticos + Optimizaciones
├── Implementar SimHash/MinHash
├── Pipeline de normalización
├── Dashboard de duplicados
└── Métricas de performance

Semana 8-11: Generador de texto jurídico (IA)
├── Plantillas por tipo de escrito
├── Integración con Claude/GPT-4
├── Sistema de revisión y feedback
├── Evaluación de calidad
└── Generación de .docx formateados
```

---

## Conclusión

Estas mejoras transforman el plan base (enfocado en infraestructura) en un **sistema jurídico inteligente** que:

1. ✅ **Filtra automáticamente** actuaciones irrelevantes (30-40% de reducción)
2. ✅ **Detecta duplicados** semánticos (cédulas repetidas)
3. ✅ **Extrae vencimientos** con precisión >98%
4. ✅ **Genera borradores** de escritos jurídicos con IA
5. ✅ **Alerta proactivamente** sobre plazos y eventos críticos

**Próximo paso:** Implementar Fase 1 (MVP) en `Sistema_v5/procesador_pdf/`
