# Plan: Soporte para Expedientes Incidentales

## Resumen del Problema

Los expedientes incidentales (formato: `FPA XXXX/YYYY/N`) se tratan incorrectamente en el sistema v6:
- **Problema actual**: El sufijo del incidente (`/1`, `/I`, `/CA1`) se **elimina** durante la normalización por `_remover_incidentes()`
- **Comportamiento deseado**: Principal (`FPA XXXX/YYYY`) e incidental (`FPA XXXX/YYYY/1`) son expedientes **separados** con sus propias actuaciones
- **Solución existente**: `detector_cambios.py` ya tiene `_normalizar_numero()` que PRESERVA incidentes

---

## CONTEXTO CRÍTICO: Cómo Funciona la Búsqueda en el PJN

### Limitación del Portal PJN

El formulario de búsqueda del PJN **solo acepta dos campos**:
- **Número**: `004379` (solo dígitos)
- **Año**: `2021`

**NO hay campo para incidentes**. El incidente NO se puede buscar directamente.

### Flujo Actual (Problemático)

```
Usuario solicita: "FRE 004379/2021/1" (incidente)
           ↓
descomponer_numero_expediente() + _remover_incidentes()
           ↓
Se extrae: numero="004379", anio="2021" (se PIERDE "/1")
           ↓
Formulario PJN: búsqueda con numero + año
           ↓
PJN retorna: TODAS las coincidencias para 004379/2021
  - Fila 1: 004379/2021 (principal)
  - Fila 2: 004379/2021/1 (incidente 1)
  - Fila 3: 004379/2021/CA1 (incidente CA1)
           ↓
gestor_batch.py: toma filas[0] (SIEMPRE el primero)
           ↓
Resultado: posiblemente el expediente INCORRECTO
```

### Flujo Correcto (A Implementar)

```
Usuario solicita: "FRE 004379/2021/1"
           ↓
Preservar número completo: numero_completo = "FRE-004379-2021-1"
Extraer para búsqueda: numero="004379", anio="2021"
           ↓
Buscar en PJN con numero/año
           ↓
PJN retorna múltiples filas
           ↓
Para cada fila, extraer número de la primera columna
           ↓
Comparar: normalizar_numero_completo(fila_numero) == numero_completo_buscado
           ↓
Seleccionar la fila que coincida exactamente con el incidente solicitado
```

**Conclusión clave**: El incidente NO se busca, se **SELECCIONA** de entre los resultados.

---

## DIAGNÓSTICO: Estado Actual del Código

### Dualidad Inconsistente

**Enfoque INCORRECTO (elimina incidentes):**
- `pjn/scraping/base.py::_remover_incidentes()` - función local que elimina sufijos
- `pjn/scraping/base.py::descomponer_numero_expediente()` - llama a `_remover_incidentes()`
- Resultado: `FPA 21002641/2010/I` → `21002641/2010` (pierde `/I`)

**Enfoque CORRECTO (preserva incidentes):**
- `application/services/detector_cambios.py::_normalizar_numero()` (líneas 16-41)
- Resultado: `FPA 21002641/2010/I` → `FPA-21002641-2010-I` (preserva `-I`)

### Punto Crítico: gestor_batch.py

En `extraccion_masiva/gestor_batch.py` líneas ~296-300:
```python
if len(filas) > 1:
    print(f"⚠️ Múltiples expedientes encontrados ({len(filas)})...")
enlace_expediente = await filas[0].query_selector("a")  # SIEMPRE TOMA EL PRIMERO
```

Este es el **punto exacto** donde se pierde el incidente correcto.

### Referencia: producción_v5.1.1 (que funcionaba mejor)

En v5.1.1 existía `mostrar_y_elegir_expediente()` con sistema de estrategia:
```python
estrategia = estrategia_seleccion or _seleccionar_primera_opcion
indice = estrategia(opciones_datos)  # Podía elegir según datos
```

Este sistema de selección flexible fue simplificado/eliminado en v6.

### Implementación de Referencia (detector_cambios.py)

```python
def _normalizar_numero(numero: str) -> str:
    """Normaliza preservando sufijos de incidentes:
    - 'FRE 004379/2021/1' → 'FRE-004379-2021-1'
    - 'FRE 004379/2021/I' → 'FRE-004379-2021-I'
    """
    if not numero:
        return ""
    match = re.match(r'([A-Z]+)[\s\-_]?(\d+)[\-/_](\d{4})(?:[\s\-/_](.+))?', numero.strip().upper())
    if match:
        prefijo, num, anio, sufijo = match.groups()
        base = f"{prefijo}-{num}-{anio}"
        return f"{base}-{sufijo}" if sufijo else base
    return numero.strip().upper()
```

---

## PLAN DE IMPLEMENTACIÓN

### Fase 1: Unificar Normalización (Propagar `_normalizar_numero`)

#### 1.1 Crear función centralizada en `text.py`

**Archivo**: `Sistema_v6/core/domain/utils/text.py`

Agregar nueva función que preserve incidentes:

```python
def normalizar_numero_completo(numero: str) -> str:
    """Normaliza número de expediente PRESERVANDO sufijos de incidentes.

    Args:
        numero: Número en cualquier formato

    Returns:
        Formato normalizado: 'XXX-NNNNNN-YYYY' o 'XXX-NNNNNN-YYYY-SUFIJO'

    Examples:
        >>> normalizar_numero_completo('FRE 004379/2021')
        'FRE-004379-2021'
        >>> normalizar_numero_completo('FRE 004379/2021/1')
        'FRE-004379-2021-1'
        >>> normalizar_numero_completo('FRE 004379/2021/CA1')
        'FRE-004379-2021-CA1'
    """
    if not numero:
        return ""
    match = re.match(
        r'([A-Z]+)[\s\-_]?(\d+)[\-/_](\d{4})(?:[\s\-/_](.+))?',
        numero.strip().upper()
    )
    if match:
        prefijo, num, anio, sufijo = match.groups()
        base = f"{prefijo}-{num}-{anio}"
        return f"{base}-{sufijo}" if sufijo else base
    return numero.strip().upper()
```

#### 1.2 Deprecar `_remover_incidentes`

**Archivo**: `Sistema_v6/core/domain/utils/text.py`

NO eliminar la función (podría romper código), pero marcarla como deprecated:

```python
import warnings

def _remover_incidentes(cadena: str) -> str:
    """DEPRECATED: Esta función elimina información de incidentes.

    Usar normalizar_numero_completo() para preservar incidentes.
    """
    warnings.warn(
        "_remover_incidentes está deprecated. Usar normalizar_numero_completo()",
        DeprecationWarning,
        stacklevel=2
    )
    # ... código existente ...
```

#### 1.3 Actualizar `descomponer_numero_expediente`

**Archivo**: `Sistema_v6/core/domain/utils/text.py`

Modificar para retornar incidente como cuarto valor:

```python
def descomponer_numero_expediente(
    valor: str | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Obtiene jurisdicción, número, año e incidente desde una cadena.

    IMPORTANTE: Ya NO remueve incidentes. Los preserva como cuarto valor.

    Args:
        valor: Número de expediente completo

    Returns:
        Tupla (jurisdiccion, numero, anio, incidente)

    Examples:
        >>> descomponer_numero_expediente("FPA 21002641/2010")
        (None, '21002641', '2010', None)
        >>> descomponer_numero_expediente("FPA 21002641/2010/I")
        (None, '21002641', '2010', 'I')
        >>> descomponer_numero_expediente("FPA 21002641/2010/CA1")
        (None, '21002641', '2010', 'CA1')
    """
    if not valor:
        return None, None, None, None

    texto = limpiar_texto(str(valor))
    if not texto:
        return None, None, None, None

    # Extraer incidente ANTES de procesar
    incidente = _extraer_incidente(texto)

    # Si hay incidente, removerlo temporalmente para extraer numero/año
    if incidente:
        texto = re.sub(r'[/\-_]' + re.escape(incidente) + r'$', '', texto)

    # ... resto del código existente para extraer jurisdiccion, numero, anio ...

    return jurisdiccion, numero, anio, incidente


def _extraer_incidente(cadena: str) -> str | None:
    """Extrae el sufijo de incidente de un número de expediente.

    Returns:
        Sufijo del incidente o None si no hay

    Examples:
        >>> _extraer_incidente("FPA 21002641/2010/I")
        'I'
        >>> _extraer_incidente("FPA 21002641/2010/CA1")
        'CA1'
        >>> _extraer_incidente("FPA 21002641/2010")
        None
    """
    # Patrón: número/año/SUFIJO donde SUFIJO es letras o números
    match = re.search(r'/(\d{4})[/\-_]([A-Za-z0-9]+)$', cadena)
    if match:
        return match.group(2).upper()
    return None
```

### Fase 2: Actualizar Llamadores

#### 2.1 Importar función en detector_cambios.py

**Archivo**: `Sistema_v6/application/services/detector_cambios.py`

Reemplazar función local por la centralizada:

```python
# ANTES (líneas 16-41):
def _normalizar_numero(numero: str) -> str:
    # ... implementación local ...

# DESPUÉS:
from core.domain.utils.text import normalizar_numero_completo as _normalizar_numero
```

#### 2.2 Actualizar gestor_batch.py

**Archivo**: `Sistema_v6/extraccion_masiva/gestor_batch.py`

```python
from core.domain.utils.text import normalizar_numero_completo

# En la comparación de expedientes (líneas ~274-284):
# ANTES:
def _buscar_expediente_en_resultados(self, numero_buscado, resultados):
    # usaba normalización que perdía incidentes

# DESPUÉS:
def _buscar_expediente_en_resultados(self, numero_buscado, resultados):
    num_normalizado = normalizar_numero_completo(numero_buscado)
    for exp in resultados:
        if normalizar_numero_completo(exp.numero) == num_normalizado:
            return exp
    return None
```

#### 2.3 Actualizar pjn/scraping/base.py

**Archivo**: `Sistema_v6/pjn/scraping/base.py`

Si existe `_remover_incidentes` duplicado, reemplazar por import:

```python
from core.domain.utils.text import normalizar_numero_completo
# Usar normalizar_numero_completo en lugar de _remover_incidentes
```

### Fase 3: Base de Datos (Opcional pero Recomendado)

#### 3.1 Nueva migración para campo incidente

**Archivo nuevo**: `Sistema_v6/infrastructure/persistence/migrations/013_agregar_numero_incidente.sql`

```sql
-- Agregar campo para sufijo de incidente
ALTER TABLE expedientes ADD COLUMN numero_incidente VARCHAR(20) NULL AFTER numero_original;

-- Crear índice único compuesto para evitar duplicados
ALTER TABLE expedientes DROP INDEX uk_numero_normalizado;
ALTER TABLE expedientes ADD UNIQUE INDEX uk_expediente_completo (numero_normalizado, numero_incidente);

-- Comentario explicativo
-- numero_normalizado: 'FPA-21002641-2010' (sin incidente)
-- numero_incidente: 'I', 'CA1', '1', etc. (o NULL para expediente principal)
```

**Rollback**: `013_agregar_numero_incidente_rollback.sql`

```sql
ALTER TABLE expedientes DROP INDEX uk_expediente_completo;
ALTER TABLE expedientes DROP COLUMN numero_incidente;
ALTER TABLE expedientes ADD UNIQUE INDEX uk_numero_normalizado (numero_normalizado);
```

---

## ARCHIVOS A MODIFICAR

| Archivo | Cambio | Prioridad |
|---------|--------|-----------|
| `core/domain/utils/text.py` | Nueva función `normalizar_numero_completo`, deprecar `_remover_incidentes`, actualizar `descomponer_numero_expediente` | Alta |
| `application/services/detector_cambios.py` | Importar función centralizada | Alta |
| `extraccion_masiva/gestor_batch.py` | Usar `normalizar_numero_completo` para seleccionar fila correcta | Alta |
| `pjn/scraping/base.py` | Actualizar normalización | Media |
| `infrastructure/persistence/migrations/` | Nueva migración para `numero_incidente` | Baja |

---

## VERIFICACIÓN

### Tests a ejecutar:

```python
# test_normalizar_numero.py
def test_preserva_incidente_numero():
    assert normalizar_numero_completo("FRE 004379/2021/1") == "FRE-004379-2021-1"

def test_preserva_incidente_letra():
    assert normalizar_numero_completo("FRE 004379/2021/I") == "FRE-004379-2021-I"

def test_preserva_incidente_compuesto():
    assert normalizar_numero_completo("FRE 004379/2021/CA1") == "FRE-004379-2021-CA1"

def test_sin_incidente():
    assert normalizar_numero_completo("FRE 004379/2021") == "FRE-004379-2021"

def test_principal_e_incidental_son_diferentes():
    principal = normalizar_numero_completo("FRE 004379/2021")
    incidental = normalizar_numero_completo("FRE 004379/2021/1")
    assert principal != incidental
```

### Métricas de éxito:

- [ ] `FRE 004379/2021` y `FRE 004379/2021/1` se almacenan como expedientes separados
- [ ] Las actuaciones del incidental no se mezclan con las del principal
- [ ] El detector de cambios distingue correctamente entre principal e incidental
- [ ] No hay regresión en expedientes existentes sin incidente

---

## NOTA IMPORTANTE

**La búsqueda en el PJN** sigue usando número/año sin incidente (el formulario del PJN no soporta incidentes directamente). El incidente se extrae de los **resultados** del PJN, no de la búsqueda.

Esto significa:
1. Buscar `21002641/2010` en PJN
2. El PJN puede retornar múltiples resultados: principal, incidente 1, incidente CA1, etc.
3. Cada resultado se almacena como expediente separado con su incidente correspondiente
