# Referencia Sistema v5 - Código Funcional

Esta carpeta contiene código del Sistema_v5 que sirve como referencia para implementar el procesamiento real de expedientes en Sistema_v6.

## Archivos Clave

### Procesamiento:
- **procesamiento/integracion_procesador.py** - Filtro inteligente de actuaciones, clasificación por utilidad jurídica

### Extracción:
- **extraccion/scraping/** - Módulos de scraping del PJN con Playwright
- **extraccion/parsers/** - Parsers de HTML del portal judicial

## Uso

**NO ejecutar directamente.** Usar como referencia para:

1. Implementar `_procesar_expediente()` en `extraccion_masiva/gestor_batch.py`
2. Ver cómo buscar expediente por número en el PJN
3. Ver cómo extraer actuaciones completas
4. Ver cómo descargar documentos adjuntos
5. Ver cómo parsear el HTML del PJN

## Archivos a Revisar para Implementación

### Para buscar y navegar a expediente:
```python
# Ver: extraccion/scraping/base.py
# - Métodos de login
# - Navegación básica en el PJN

# Ver: extraccion/scraping/expedientes.py
# - Búsqueda de expedientes
# - Extracción de listados
```

### Para extraer datos de expediente:
```python
# Ver: extraccion/parsers/expedientes_parser.py
# - Parseo de carátula
# - Extracción de partes
# - Metadata del expediente
```

### Para extraer actuaciones:
```python
# Ver: extraccion/parsers/actuaciones_parser.py
# - Parseo de actuaciones
# - Extracción de documentos adjuntos
# - Fechas y metadata
```

### Para clasificación inteligente:
```python
# Ver: procesamiento/integracion_procesador.py
# - ClasificadorActuaciones
# - Análisis de utilidad jurídica
# - Detección de vencimientos
```

## Notas Importantes

- Sistema_v5 usa Tkinter para GUI (ignorar esas partes)
- Sistema_v6 usa React + FastAPI
- **Adaptar la LÓGICA**, no copiar literalmente
- Los selectores CSS pueden haber cambiado en el PJN
- Verificar y actualizar selectores si es necesario

## Estructura de Sistema_v5

```
Sistema_v5/
├── pjn/
│   ├── scraping/          ← Lógica de scraping
│   ├── parsers/           ← Parsers HTML
│   ├── models/            ← Modelos de datos
│   └── utils/             ← Utilidades
├── generador_documentos/
│   └── integracion_procesador.py  ← Clasificación inteligente
└── bin/
    └── ejecutar_extraccion.py     ← Flujo completo (referencia)
```

## Ejemplo de Adaptación

**Sistema_v5 (referencia):**
```python
# En scraping/expedientes.py
def buscar_expediente(page, numero):
    page.goto("https://pjn.gob.ar/busqueda")
    page.fill("#numero", numero)
    page.click("button[type=submit]")
    return extraer_datos(page)
```

**Sistema_v6 (adaptar a):**
```python
# En gestor_batch.py
async def _procesar_expediente(self, page, numero, ...):
    await page.goto(URL_BUSQUEDA)
    await page.fill("#numero", numero)
    await page.click("button[type=submit]")
    datos = await self._extraer_datos_expediente(page)
    await self.expediente_repository.guardar(datos)
```

---

**Creado:** 2025-11-10
**Propósito:** Referencia para implementar FASE 3 de Extracción Masiva
**No modificar:** Solo lectura - código de referencia
