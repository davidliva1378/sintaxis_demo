# Plan Integral de Procesamiento de Actuaciones con IA (Enfoque Híbrido)

> **Objetivo:** establecer un plan **conceptual y detallado** (sin código) para procesar actuaciones judiciales a partir de un **JSON** de metadatos y **PDFs** por expediente, guardando **archivos en disco por hash**, **metadatos + texto** en **MySQL**, y **embeddings** en un **vector store** externo (FAISS/Chroma) con **punteros** desde la base.

---

## 0) Alcance, supuestos y principios

- **Entrada por expediente**  
  - `actuaciones.json` con metadatos mínimos (índice, fecha, tipo, detalle, tiene archivo, hash/ruta si aplica).  
  - Carpeta con **PDFs** (y anexos si los hubiera).
- **Salida del proceso**  
  - PDFs **canonizados por SHA-256** en repositorio de objetos.  
  - **Metadatos** en MySQL.  
  - **Texto limpio y segmentado** (por bloques) en MySQL (LONGTEXT) con **FULLTEXT**.  
  - **Embeddings** en FAISS/Chroma (disco), con **punteros** en MySQL.  
  - Reportes/Timelines/Agenda.
- **Principios rectores**  
  1) **Inmutabilidad por hash** (nunca se sobreescribe un archivo, se versiona por contenido).  
  2) **Idempotencia** (reprocesos no duplican; deduplicación por hash).  
  3) **Trazabilidad** (toda salida “IA” debe poder rastrearse al PDF original y al bloque de texto fuente).  
  4) **Seguridad y cumplimiento** (rutas relativas, permisos, logs, opciones de cifrado).  
  5) **Escalabilidad** (se separan DB transaccional, FS de objetos y vector store).

---

## 1) Layout de carpetas (disco)

```
sintaXis/
├─ datos_extraidos/
│  ├─ actuaciones/
│  │  └─ {EXPTE}/
│  │     ├─ pdf/            # copia (opcional) para consulta humana
│  │     ├─ texto/          # .txt opcionales de auditoría/QA (opcional)
│  │     └─ json/           # JSON enriquecidos por actuación (opcional)
│  ├─ objetos/              # REPOSITORIO CANÓNICO por HASH (inmutable)
│  │  └─ {sha256[:2]}/
│  │     └─ {sha256}.pdf
│  ├─ ocr/                  # temporales de OCR (si se usa batch)
│  └─ informes/             # reportes CSV/MD/PDF (timelines, resúmenes)
│
├─ vector_store/
│  └─ {modelo}/
│     └─ {yyyy_mm}/
│        ├─ faiss.index
│        └─ meta.json       # mapeo clave→id_texto, dimensión, versión
│
├─ backups/
│  ├─ {timestamp}/database.sql.gz
│  ├─ {timestamp}/manifest.json  # checksums + rutas (vector_store/objetos)
│  └─ {timestamp}/...            # fotos/archivos del FS si aplica
│
├─ logs/
│  ├─ descarga.log
│  ├─ ingesta.log
│  ├─ ocr.log
│  └─ rag_index.log
│
└─ tmp/                         # descargas temporales antes de canonizar
```

**Reglas:**  
- El **PDF canónico** vive en `objetos/{sha256[:2]}/{sha256}.pdf`.  
- Copias por expediente en `actuaciones/{EXPTE}/pdf/` son **opcionales** (comodidad de usuario).  
- **Nunca sobreescribir**: si el archivo cambia, cambia el **hash** (nuevo objeto).

---

## 2) Modelo de datos (MySQL) — campos (sin SQL)

### `expedientes`
- `id` (PK)  
- `numero`  
- `caratula`  
- `jurisdiccion`  
- `dependencia`  
- `situacion`  
- `fecha_inicio` (nullable)  
- `creado_en`, `actualizado_en`

### `actuaciones`
- `id` (PK)  
- `expediente_id` (FK)  
- `indice`                  # orden interno del portal  
- `fecha`  
- `tipo`                    # MOVIMIENTO, SENTENCIA, DEO, etc.  
- `detalle`                 # descripción breve  
- `oficina`  
- `foja` (nullable)  
- `tiene_archivo` (bool)  
- `hash_doc`                # hash del documento (para join con documentos)  
- `uso`                     # rag | agenda | auditoria | revisar  
- `utilidad`                # alta | media | baja | nula  
- `score`                   # 0-100 (heurístico/clasificador)  
- `extraida_en`             # timestamp extracción  
- `creado_en`, `actualizado_en`

### `documentos`
- `id` (PK)  
- `actuacion_id` (FK)       # 1 documento “principal” por actuación (si aplica)  
- `sha256` (UNIQUE)         # deduplicación canónica  
- `mime`                    # application/pdf  
- `bytes_size`  
- `ruta_relativa`           # "datos_extraidos/objetos/ab/abcdef....pdf"  
- `version`                 # entero (si hubiera reemplazos/anexos)  
- `creado_en`

> *Si una actuación puede tener varios anexos, agregar `actuacion_documento` (relación 1:N).*

### `textos`
- `id` (PK)  
- `actuacion_id` (FK)  
- `bloque_idx`              # 0..N  
- `plain_text` (LONGTEXT)  
- `tokens`                  # aproximado  
- `hash_text`               # hash del bloque (idempotencia)  
- `creado_en`  

> *Se recomienda **FULLTEXT** sobre `plain_text`.*

### `indices_vectores` (punteros a FAISS/Chroma)
- `id` (PK)  
- `texto_id` (FK)  
- `modelo`                  # "bge-m3", "all-MiniLM-L6-v2", etc.  
- `faiss_key`               # clave/colección/shard donde quedó indexado  
- `creado_en`

### (Opcional) `notificaciones_agenda`
- `id` (PK)  
- `actuacion_id` (FK)  
- `tipo_notificacion`       # CEDULA_ELECTRONICA_*  
- `fecha_notificacion`  
- `plazo_dias`              # si se detecta  
- `vence_el`                # si se calcula  
- `estado`                  # pendiente | atendida | vencida  
- `creado_en`, `actualizado_en`

---

## 3) Flujos de trabajo (pipeline conceptual)

### 3.1 Ingesta (desde JSON de actuaciones)
1. **Leer JSON** del expediente.  
2. **Upsert** en `expedientes` (número, carátula, etc.).  
3. **Upsert** en `actuaciones` por `(expediente_id, indice)` o por el `Hash` del PJN.  
4. Si `tiene_archivo`:
   - Registrar/actualizar stub en `documentos` (con `sha256` si viene dado; sino placeholder).  
5. Log en `ingesta.log` con conteos y timestamps.

**Resultado:** DB poblada con metadatos; archivos aún no descargados o por canonizar.

---

### 3.2 Preproceso (filtro de utilidad jurídica)
- Decidir **uso** y **prioridad** sin abrir el PDF, a partir de `tipo/detalle`:  
  - `RAG`: resoluciones, sentencias, escritos con sustancia, informes.  
  - `Agenda`: cédulas/notificaciones (plazos).  
  - `Auditoría`: constancias, carátulas, movimientos administrativos.  
  - `Revisar`: casos limítrofes/ambivalentes.  
- Grabar en `actuaciones`: `uso`, `utilidad`, `score`, `motivo`.  
- Generar **reporte** (CSV/MD) en `datos_extraidos/informes/`.

**Resultado:** cola priorizada para **descarga** y **extracción de texto**.

---

### 3.3 Descarga (plan por lotes y on-demand)

**Cuándo:**  
- **On-demand** (usuario abre/consulta).  
- **Batch programado** (nocturno/horario no laboral) por prioridad.

**Flujo:**  
1. Seleccionar **lote** de actuaciones (`uso ∈ {rag,agenda}`, `score` alto, recientes).  
2. Autenticación portal.  
3. Por actuación con `tiene_archivo=True`:  
   - **Descargar** a `tmp/` (nombre temporal).  
   - Validar **MIME** y tamaño.  
   - Calcular **SHA-256**.  
   - Mover a **canónico**: `objetos/{sha256[:2]}/{sha256}.pdf`.  
   - (Opcional) Copiar/symlink a `actuaciones/{EXPTE}/pdf/`.  
   - **Upsert** en `documentos` (`sha256`, `mime`, `bytes_size`, `ruta_relativa`).  
   - Actualizar `actuaciones.hash_doc` y `tiene_archivo=true`.  
   - Log en `descarga.log`.

**Reintentos/estados:**  
- `pendiente_descarga → descargando → descargado → verificado → listo_texto`  
- `fallido` (+ `motivo_error`, `reintentos`, backoff).

**Integridad:**  
- `sha256` **UNIQUE** en `documentos` (deduplicación).

---

### 3.4 Extracción de texto y normalización
- Sobre **RAG** y **Agenda**:  
  - Intentar **texto embebido**; si vacío → **OCR** (spa).  
  - **Normalizar**: quitar encabezados/pies repetidos, corregir espacios, unificar saltos de línea.  
  - Opcional: guardar `.txt` y/o `.json` enriquecidos en `actuaciones/{EXPTE}/texto/` y `json/`.

**Resultado:** texto limpio por actuación, listo para segmentar.

---

### 3.5 Segmentación (bloques)
- Dividir en **bloques** de ~200–400 palabras (óptimo para RAG).  
- Asignar `bloque_idx`, calcular `hash_text` y `tokens`.  
- Guardar **una fila por bloque** en `textos` (LONGTEXT + FULLTEXT).  

**Resultado:** MySQL listo para **búsqueda** por FULLTEXT y para **embeddings**.

---

### 3.6 Indexación textual + vectorial
- **MySQL FULLTEXT** (`textos.plain_text`) para búsquedas inmediatas.  
- **Vector store** (FAISS/Chroma) **fuera de MySQL**:  
  - Embeddings por bloque, organizados por `{modelo}/{yyyy_mm}` (shards).  
  - Guardar **punteros** en `indices_vectores` (`texto_id`, `modelo`, `faiss_key`).  
  - Mantener `meta.json` con versión/dimensión/modelo.

**Resultado:** consultas híbridas (keyword + semántica) y RAG eficaz.

---

### 3.7 Agenda y vencimientos (notificaciones)
- Identificar cédulas/notificaciones con plazos.  
- Normalizar `fecha_notificacion`, detectar `plazo_dias`, calcular `vence_el`.  
- Persistir en `notificaciones_agenda`.  
- Integrar con **UI/alertas** y **monitor** de vencimientos.

---

### 3.8 Resúmenes y reporting
- **Timeline** del expediente (fecha → tipo → síntesis corta).  
- **Reportes** CSV/MD diarios: nuevas descargas, OCR pendientes, RAG indexado, vencimientos.

---

## 4) Controles de calidad y validaciones

- **Idempotencia**:  
  - `UNIQUE(actuaciones: expediente_id+indice)` o clave estable del portal.  
  - `UNIQUE(documentos: sha256)` y `hash_text` para bloques.
- **Muestreo**: revisar 1–3% de lo marcado como “no RAG” para detectar falsos negativos.  
- **Detección de duplicados**: por `sha256`; near-duplicates futuros (SimHash/MinHash) si hiciera falta.  
- **KPIs**:
  - % actuaciones con texto embebido vs OCR,  
  - tiempo medio por descarga/extracción,  
  - tasa de error/timeout,  
  - tamaño medio PDFs,  
  - % cédulas con plazo detectado.

---

## 5) Seguridad y cumplimiento

- **Rutas relativas** en DB (no absolutas).  
- **Permisos** mínimos por rol (lectura/escritura; acceso a PDFs con datos sensibles).  
- **Cifrado** de volúmenes (FS y backups) si aplica.  
- **Logs de acceso** a documentos/descargas.  
- **Antimalware/AV** en `tmp/` (opcional).  
- **Política de retención** (definir cuánto conservar y cómo anonimizar si es requerido).

---

## 6) Backups, restauración y consistencia

- **Backups coordinados**:  
  - Dump **MySQL** (lógico o snapshot físico).  
  - Snapshot/copia de `datos_extraidos/` y `vector_store/`.  
  - `manifest.json` con:  
    - timestamps/commits,  
    - checksums de `objetos/`,  
    - versión/ubicación de cada índice vectorial,  
    - conteos por tabla.
- **Restauración**:  
  - Restaurar DB → restaurar `objetos/` → `vector_store/` → correr **reconciliación** (verificar que todo `hash_doc` exista en FS y todo `sha256` referenciado tenga fila en `documentos`).

---

## 7) Operación y monitoreo

- **Métricas**:  
  - Disponibilidad de portal,  
  - Tiempos y errores de descarga,  
  - OCR en cola,  
  - Espacio en disco (objetos / vector_store),  
  - Tiempos de búsqueda (FULLTEXT y vectorial).
- **Alertas**:  
  - % alto de fallos de descarga,  
  - espacio bajo,  
  - caída de índice FAISS,  
  - tareas solapadas (evitar ejecuciones concurrentes del mismo trabajo).
- **Logs**: `descarga.log`, `ingesta.log`, `ocr.log`, `rag_index.log`.

---

## 8) Naming, versiones y convenciones

- **PDF canónico**: `{sha256}.pdf` (2 niveles de prefijo por carpeta).  
- **Bloques de texto**: `actuacion_id + bloque_idx` como clave lógica.  
- **Modelos embeddings**: carpeta por modelo y shard temporal (`{yyyy_mm}`).  
- **Versionado de documentos**: si una actuación se re-sube, **nuevo hash** → **nuevo documento**; relacionar por `actuacion_id` + `version`.  
- **Horarios**: preferir **UTC** en DB, o registrar `timezone` explícito si la UI usa hora local.

---

## 9) Checklist por etapa (criterios de “DONE”)

**Ingesta**  
- [ ] JSON parseado y validado.  
- [ ] Expediente upsert.  
- [ ] Actuaciones upsert (sin duplicados).  
- [ ] Documentos stub si corresponde.  
- [ ] Reporte de ingesta generado.

**Preproceso**  
- [ ] Actuaciones etiquetadas con `uso/utilidad/score`.  
- [ ] Lote priorizado para descarga.  
- [ ] Resumen de clasificación (CSV/MD).

**Descarga**  
- [ ] Autenticación OK.  
- [ ] Archivos a `tmp/` y validados (MIME/tamaño).  
- [ ] Hash calculado y movimiento a `objetos/`.  
- [ ] `documentos` y `actuaciones.hash_doc` actualizados.  
- [ ] Reintentos aplicados si falló.

**Texto**  
- [ ] Extracción embebido u OCR cuando sea necesario.  
- [ ] Normalización y control de calidad básico.  
- [ ] Segmentación en bloques; `textos` poblada con FULLTEXT.

**Vectorial**  
- [ ] Embeddings generados por bloque (RAG).  
- [ ] `faiss.index` actualizado; `indices_vectores` con punteros.  
- [ ] `meta.json` actualizado (modelo/dim/shard/version).

**Agenda**  
- [ ] Cédulas detectadas; plazos normalizados (si posible).  
- [ ] Eventos creados/actualizados en `notificaciones_agenda`.  
- [ ] UI/alertas operativas.

**Backups/Observabilidad**  
- [ ] Dump DB + snapshot FS + manifest.  
- [ ] Métricas publicadas; alertas configuradas.  
- [ ] Logs revisados sin errores críticos.

---

## 10) Migración desde entorno simulado (JSON → MySQL)

- **Fase 1:** cargar expedientes/actuaciones/documentos (stubs) desde JSON.  
- **Fase 2:** descarga y canonización por hash (lotes priorizados).  
- **Fase 3:** extracción de texto, segmentación y FULLTEXT.  
- **Fase 4:** embeddings y punteros en `indices_vectores`.  
- **Fase 5:** reconciliación final (DB ↔ FS ↔ vector_store), KPIs y reporte.

---

## 11) Roadmap de mejoras futuras

- **Clasificador liviano** (aporta/no aporta) para robustecer `uso/utilidad/score`.  
- **Extractores específicos** (resuelve/considerando, montos, normas, plazos).  
- **Near-duplicates** de texto (SimHash/MinHash) para eliminar ruido.  
- **Caché de respuestas** en preguntas frecuentes por expediente.  
- **UI de auditoría** (comparar PDF ↔ texto segmentado ↔ contexto RAG con citas).

---

### Resultado esperado

- PDFs y anexos **deduplicados e inmutables** por hash.  
- **Metadatos** y **texto segmentado** en **MySQL** con **FULLTEXT**.  
- **Embeddings** en **vector store** externo, con punteros en DB.  
- **Consultas híbridas** (keyword + vectorial) para RAG jurídico de alta calidad.  
- **Trazabilidad completa** y **operación robusta** (backup/restauración, seguridad, monitoreo).
