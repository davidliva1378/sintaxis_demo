# Extracción de expedientes v4

Este documento describe el uso de la corrutina `Sistema_v4.operaciones.expedientes.expedientes_v4.extraer_expedientes_completos`, el corazón del scraper que recorre la bandeja de expedientes del PJN.

## Firma general

```python
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    sel_tabla=SEL_TABLA,
    sel_tbody=SEL_TBODY,
    sel_siguiente=SEL_SIGUIENTE,
    max_paginas=200,
    omitir_duplicados=True,
    detener_en_duplicado=True,
    *,
    fecha_corte=None,
    tiempo_maximo_segundos=None,
    orden=None,
)
```

La función devuelve una tupla `(expedientes, motivo, metadata)`:

* `expedientes` es una lista de diccionarios con las claves `numero`, `dependencia`, `caratula`, `situacion` y `ultima_actuacion` (fecha normalizada a `YYYY-MM-DD` cuando es posible).
* `motivo` es una cadena que indica por qué se detuvo la extracción.
* `metadata` es un diccionario con información complementaria. Desde esta versión incluye la clave opcional `"total_esperado"` cuando el portal anuncia la cantidad total de expedientes que deberían listarse.

## Parámetros posicionales

| Parámetro | Tipo | Descripción |
| --- | --- | --- |
| `page` | `Page` | Página de Playwright ya autenticada y posicionada sobre el listado paginado de expedientes. |
| `sel_tabla` | `str` | Selector del elemento `<table>` que contiene el listado. Acepta cualquier sintaxis soportada por Playwright (CSS, `text=`, `xpath=`, etc.). |
| `sel_tbody` | `str` | Selector que apunta al contenedor de filas. Se emplea internamente para construir `f"{sel_tbody} tr"`. Si el HTML no usa `<tbody>`, reemplazá el valor por el nodo que agrupa las filas. |
| `sel_siguiente` | `str` | Selector —o lista de selectores separados por comas— que localiza el control "Siguiente". |
| `max_paginas` | `int` | Límite superior de páginas a procesar antes de frenar con el motivo `"limite_paginas"`. |
| `omitir_duplicados` | `bool` | Indica si las filas repetidas (según `numero`, `caratula` y `dependencia`) se descartan silenciosamente. |
| `detener_en_duplicado` | `bool` | Si es `True`, el primer duplicado encontrado detiene el scraper con el motivo `"duplicado_encontrado"`. |

## Parámetros con nombre

| Parámetro | Tipo | Descripción |
| --- | --- | --- |
| `fecha_corte` | `str \| None` | Fecha mínima permitida. Puede pasarse como `YYYY-MM-DD` o `DD/MM/AAAA`. Cuando `ultima_actuacion` cae por debajo de este umbral se devuelve el motivo `"limite_fecha"`. |
| `tiempo_maximo_segundos` | `int \| None` | Tiempo máximo de ejecución. Si se supera se retorna `"limite_tiempo"` con los datos recopilados hasta el momento. |
| `orden` | `str \| None` | Ordenamiento inicial de la tabla antes de empezar a iterar. Admite `"fecha"`, `"caratula"`, `"oficina"` y `"situacion"`. Valores no reconocidos se ignoran conservando el orden actual. |

## Selectores por defecto y personalización

| Constante | Valor por defecto | Propósito |
| --- | --- | --- |
| `SEL_TABLA` | ``"table.table-striped"`` | Identifica la tabla principal del listado. |
| `SEL_TBODY` | ``f"{SEL_TABLA} tbody"`` | Selecciona el cuerpo de filas dentro de la tabla. |
| `SEL_SIGUIENTE` | `a[aria-label='Siguiente']`<br>`button[aria-label='Siguiente']`<br>`a:has(span[title='Siguiente'])`<br>`button:has(span[title='Siguiente'])`<br>`.pagination li.next:not(.disabled) a`<br>`.pagination a:has-text('Siguiente')`<br>`.rf-ds-btn-next` | Ubica el control que avanza el paginado. |

Los portales que utilicen otros selectores pueden ajustar el comportamiento de dos formas:

1. **Sobrescribir los parámetros** al invocar la función, por ejemplo `await extraer_expedientes_completos(page, sel_tabla="table#resultados", sel_siguiente="a.next")`.
2. **Modificar las constantes** antes de llamar a la corrutina si se desea establecer defaults distintos para toda la aplicación.

## Motivos de finalización

El segundo elemento de la tupla indica la causa exacta de salida:

* `"fin_listado"`: se llegó al final natural del paginado (no hubo cambios de página tras hacer clic en "Siguiente").
* `"limite_paginas"`: se superó `max_paginas`.
* `"limite_fecha"`: se alcanzó una fila cuya `ultima_actuacion` es anterior a `fecha_corte`.
* `"limite_tiempo"`: el tiempo de ejecución excedió `tiempo_maximo_segundos`.
* `"sin_siguiente"`: no se encontró ningún control para avanzar de página.
* `"sin_siguiente_habilitado"`: existen controles, pero ninguno habilitado/visible.
* `"siguiente_timeout"`: el botón "Siguiente" no apareció en pantalla dentro del tiempo esperado.
* `"siguiente_deshabilitado"`: el control estaba deshabilitado al momento del clic.
* `"error_click"`: Playwright no pudo hacer clic en "Siguiente".
* `"duplicado_encontrado"`: se detectó un expediente repetido y `detener_en_duplicado=True`.

La función siempre retorna los datos acumulados hasta el instante del evento que produjo el motivo.

## Ejemplos de uso

### Extracción básica

```python
expedientes, motivo, metadata = await extraer_expedientes_completos(page)
```

### Ordenamiento inicial

```python
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    orden="fecha",  # también acepta "caratula", "oficina" y "situacion"
)
```

### Corte por fecha y tiempo máximo

```python
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    fecha_corte="2024-01-01",
    tiempo_maximo_segundos=90,
)
```

## Integración con el monitor

El hilo `VerificadorExpedientesV4` definido en `Sistema_v4.monitor.monitor_entradas_expedientes_v4` consume directamente esta función para poblar el monitor de bandeja. Allí se normaliza el `motivo` y se persisten los resultados en JSON cuando corresponde.

> ℹ️ Desde la versión 4, el monitor invoca a `extraer_expedientes_completos` con `detener_en_duplicado=False`. De esta manera, si aparece un expediente repetido (por ejemplo, **FPA 001425/2013**), se omite del resultado pero la paginación continúa hasta completar el recorrido o alcanzar otro límite configurado. El motivo `"duplicado_encontrado"` solo se emite cuando algún consumidor redefine el parámetro a `True`.
