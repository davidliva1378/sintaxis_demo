# Tabla de selectores del portal PJN

Este inventario recopila los selectores utilizados por los scripts Playwright del proyecto para automatizar el portal del Poder Judicial de la Nación (PJN). Se incluyen los archivos y funciones que los consumen, la finalidad prevista y observaciones relevantes para su mantenimiento ante cambios en la interfaz.

---

## ⚡ Sistema_v5 - Selectores Centralizados (RECOMENDADO)

**Módulo:** `Sistema_v5/pjn/selectores.py`
**Estado:** ✅ **Centralizado y en uso activo**
**Última actualización:** 15 de Octubre 2025
**Portal PJN:** Material UI (interfaz moderna)

### 🎯 Uso Recomendado

```python
from Sistema_v5.pjn.selectores import SEL_AUTH, SEL_ENTRADAS, SEL_EXPEDIENTES, SEL_ACTUACIONES

# En lugar de strings hardcodeados:
await page.fill("input[name='username']", usuario)  # ❌ Evitar

# Usar constantes centralizadas:
await page.fill(SEL_AUTH.USUARIO, usuario)  # ✅ Correcto
```

### 📋 Autenticación (Keycloak)

| Selector | Constante Python | Fragilidad | Notas |
|----------|------------------|------------|-------|
| `input[name='username']` | `SEL_AUTH.USUARIO` | 🟢 Baja | Atributo estándar HTML |
| `input[name='password']` | `SEL_AUTH.PASSWORD` | 🟢 Baja | Atributo estándar HTML |
| `#kc-login` | `SEL_AUTH.BOTON_LOGIN` | 🟢 Baja | ID de Keycloak estable |
| `text='Menú'` | `SEL_AUTH.CONFIRMACION_LOGIN` | 🟡 Media | Texto visible, sensible a idioma |

**Archivos que usan:** `scraping/base.py:217-240`

---

### 📨 Entradas/Notificaciones (Material UI)

| Selector | Constante Python | Fragilidad | Notas de Mantenimiento |
|----------|------------------|------------|------------------------|
| `div.MuiTableContainer-root tr` | `SEL_ENTRADAS.TABLA` | 🟡 Media | Clase MUI estándar pero puede cambiar en updates |
| `#LayoutScrollingContainer` | `SEL_ENTRADAS.CONTENEDOR_SCROLL` | 🟢 Baja | ID estable del layout |
| `p.MuiTypography-root...css-11dlpbt` | `SEL_ENTRADAS.EXPEDIENTE_NUMERO` | 🔴 Alta | **FRÁGIL:** Clase CSS generada, buscar alternativa con `data-testid` |
| `p.MuiTypography-root...css-4icvzy` | `SEL_ENTRADAS.EXPEDIENTE_CARATULA` | 🔴 Alta | **FRÁGIL:** Clase CSS generada |
| `[aria-label]` | `SEL_ENTRADAS.ELEMENTOS_CON_ARIA` | 🟢 Baja | Atributo de accesibilidad, robusto |
| `.MuiAvatar-root p` | `SEL_ENTRADAS.AVATAR_LETRA` | 🟡 Media | Estructura MUI, verificar en updates |

**Patrones regex** (para locators):
- `SEL_ENTRADAS.TEXTO_FIN_EVENTOS` = `"No hay m[aá]s eventos"`
- `SEL_ENTRADAS.TEXTO_CARGANDO` = `"Cargando m[aá]s eventos"`

**Archivos que usan:** `scraping/entradas.py:175-233`

---

### 📁 Expedientes (Bootstrap + JSF)

| Selector | Constante Python | Fragilidad | Notas de Mantenimiento |
|----------|------------------|------------|------------------------|
| `table.table-striped` | `SEL_EXPEDIENTES.TABLA_RESULTADOS` | 🟢 Baja | Clase Bootstrap estándar |
| `table.table-striped tbody tr` | `SEL_EXPEDIENTES.FILAS_RESULTADOS` | 🟢 Baja | Selectores semánticos |
| `td` | `SEL_EXPEDIENTES.COLUMNAS_FILA` | 🟢 Baja | HTML estándar |
| `a` | `SEL_EXPEDIENTES.ENLACE_EXPEDIENTE` | 🟡 Media | Genérico, usar dentro de contexto de fila |
| `span[style='color:#000000;']` | `SEL_EXPEDIENTES.NUMERO_DETALLE` | 🔴 Alta | **MUY FRÁGIL:** Estilo inline puede cambiar |
| `#expediente\:j_idt96\:detailCover` | `SEL_EXPEDIENTES.CARATULA_DETALLE` | 🔴 Alta | **FRÁGIL:** ID JSF generado (`j_idt96`) |
| `#expediente\:j_idt96\:detailDependencia` | `SEL_EXPEDIENTES.DEPENDENCIA_DETALLE` | 🔴 Alta | ID JSF puede cambiar en redespliegues |
| `#expediente\:j_idt96\:detailCamera` | `SEL_EXPEDIENTES.JURISDICCION_DETALLE` | 🔴 Alta | ID JSF generado |
| `#expediente\:j_idt96\:detailSituation` | `SEL_EXPEDIENTES.SITUACION_DETALLE` | 🔴 Alta | ID JSF generado |

**Archivos que usan:**
- `scraping/expedientes.py:518-522` (detalles)
- `scraping/expedientes.py:752-766` (tabla resultados)

---

### 📄 Actuaciones (PrimeFaces)

| Selector | Constante Python | Fragilidad | Notas de Mantenimiento |
|----------|------------------|------------|------------------------|
| `#expediente\:action-table` | `SEL_ACTUACIONES.TABLA_ACTUALES` | 🟡 Media | ID JSF escapado, relativamente estable |
| `#expediente\:action-historic-table` | `SEL_ACTUACIONES.TABLA_HISTORICAS` | 🟡 Media | ID JSF escapado |
| `i.fa-download` | `SEL_ACTUACIONES.ICONO_DESCARGA` | 🟢 Baja | FontAwesome 4.x, estable |
| `a:has(span[title='Siguiente']):not(.ui-state-disabled)` | `SEL_ACTUACIONES.BOTON_SIGUIENTE` | 🟡 Media | Depende de atributo `title` |
| `.ui-paginator-page.ui-state-active` | `SEL_ACTUACIONES.PAGINA_ACTIVA_PATTERN` | 🟡 Media | Clases PrimeFaces estándar |
| `div.alert.white-panel` | `SEL_ACTUACIONES.MENSAJE_SIN_HISTORICAS` | 🟡 Media | Verificar en cambios de diseño |

**IDs sin escape** (para funciones de escape):
- `SEL_ACTUACIONES.TABLA_ACTUALES_ID` = `"expediente:action-table"`
- `SEL_ACTUACIONES.TABLA_HISTORICAS_ID` = `"expediente:action-historic-table"`

**Archivos que usan:**
- `scraping/actuaciones.py:247-537`
- `parsers/actuaciones_parser.py:165`

---

### 🛠️ Funciones Auxiliares

```python
from Sistema_v5.pjn.selectores import escapar_id_jsf_para_css, escapar_id_jsf_para_js

# Escapar IDs JSF para usar con querySelector
id_escapado = escapar_id_jsf_para_css("expediente:action-table")
# Resultado: "expediente\\:action-table" (sin el #)

# Construir selector completo
selector = f"#{id_escapado}"
# Resultado: "#expediente\\:action-table"

# Escapar IDs JSF para usar en JavaScript/evaluate
selector_js = escapar_id_jsf_para_js("expediente:action-table")
# Resultado: "expediente\\\\:action-table"
```

---

### 🔍 Código de Fragilidad

- 🟢 **Baja:** Selector estable (IDs semánticos, atributos HTML estándar, clases Bootstrap/FontAwesome)
- 🟡 **Media:** Riesgo moderado (IDs JSF escapados, clases PrimeFaces/MUI, textos visibles)
- 🔴 **Alta:** Muy frágil (estilos inline, IDs JSF generados `j_idt*`, clases CSS con hash)

---

### ⚠️ Selectores de Alta Prioridad para Reemplazo

Estos selectores son **críticos** y deben reemplazarse cuando se actualice el portal:

1. **`span[style='color:#000000;']`** (número de expediente)
   - **Problema:** Estilo inline arbitrario
   - **Solución sugerida:** Solicitar al equipo PJN agregar `data-testid="expediente-numero"`

2. **`p.MuiTypography-root...css-11dlpbt`** (número en entradas)
   - **Problema:** Clase CSS generada por emotion/styled-components
   - **Solución sugerida:** Buscar por `aria-label` o solicitar `data-testid`

3. **`#expediente\:j_idt96\:detail*`** (detalles de expediente)
   - **Problema:** IDs JSF con componentes generados (`j_idt96`)
   - **Solución sugerida:** Usar selectores por texto de label + input adyacente

---

### 📊 Tests Automatizados

El módulo incluye tests comprehensivos en `tests/test_selectores.py`:

```bash
# Ejecutar tests de selectores
pytest tests/test_selectores.py -v

# Verificar que todos los selectores estén definidos
pytest tests/test_selectores.py::TestSelectoresBasicos -v
```

**Coverage:** 100% de las constantes de selectores validadas

---

### 📝 Migración desde Versiones Anteriores

**Sistema_v3/v4 → Sistema_v5:**

```python
# Antes (v3/v4) - Selectores dispersos
SELEC_TABLA = "div.MuiTableContainer-root tr"
filas = await page.query_selector_all(SELEC_TABLA)

# Después (v5) - Selectores centralizados
from Sistema_v5.pjn.selectores import SEL_ENTRADAS
filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
```

**Ventajas:**
- ✅ Un solo lugar para actualizar cuando cambie el sitio
- ✅ Autocomplete en IDEs
- ✅ Tests automáticos validan integridad
- ✅ Documentación viva (nombres descriptivos)

---

## Autenticación y navegación inicial

| Selector | Tipo | Archivos / funciones | Objetivo en el sitio PJN | Observaciones de mantenimiento |
| --- | --- | --- | --- | --- |
| `input[name='username']` | CSS | `abrir_autorizados.acceso_autorizados`, `abrir_consultas.abrir_consultas`, `abrir_deox.acceso_deox`, `abrir_escritos.acceso_escritos`, `abrir_iwecs.acceso_iwecs`, `abrir_notificaciones.acceso_notificaciones`, `gestion_expedientes/bk/probar_busqueda_y_apertura_v2.login_portal` | Completar el usuario en el formulario Keycloak de login. | Cambiaría si Keycloak modifica atributos `name`; considerar preferir `#username` cuando esté disponible. |
| `input[name='password']` | CSS | Misma lista que el selector de usuario | Completar la clave en el formulario Keycloak. | Ídem observación anterior; preferible apuntar a `#password`. |
| `#kc-login` | ID | Mismos archivos que los anteriores | Activar el botón “Acceder” del login. | Estable; depende del template Keycloak. |
| `#username` | ID | `gestion_expedientes/probar_buscar_expediente.login_portal`, `test_busqueda_y_descarga.login_portal`, `test_busqueda_y_descarga_historicas.login_portal`, `test_extraccion_completa.login_portal` | Alternativa para el campo de usuario (tests). | Mantener sincronizado con los scripts principales. |
| `#password` | ID | Idénticos a `#username` | Alternativa para la clave. | -- |
| `text='Menú'` | Texto | `abrir_*` helpers y `gestion_expedientes/bk/probar_busqueda_y_apertura_v2.login_portal` | Verificar que el portal aterrizó en la pantalla post-login. | Sensible a cambios de idioma o copy del portal. |
| `text=Consultas` | Texto | Scripts de prueba `test_*` y `probar_buscar_expediente.login_portal` | Confirmar que el menú de Consultas está disponible tras autenticarse. | Cambia si la etiqueta del menú se renombra. |

## Búsqueda de expedientes

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `a[href='#collapseOne']` | CSS | `gestion_expedientes/buscar_expediente_por_numero`, `gestion_expedientes/bk/buscar_expediente_por_numero_bk`, `bk/probar_busqueda_y_apertura_v2` | Desplegar el panel de búsqueda avanzada. | Depende del ID del acordeón; vigilar cambios en markup. |
| `#collapseOne.collapse.in` | CSS (estado) | Mismos archivos | Asegurar que el panel está expandido antes de completar campos. | Cambiará si Bootstrap actualiza clases (`show` en vez de `in`). |
| `#j_idt83\:consultaExpediente\:j_idt116\:numero` | CSS (ID con escapes) | `gestion_expedientes/buscar_expediente_por_numero`, `bk` equivalentes, `bk/probar_busqueda_y_apertura_v2` | Campo “Número de expediente”. | JSF suele regenerar IDs; incorporar estrategias más robustas (labels `for`). |
| `#j_idt83\:consultaExpediente\:j_idt118\:anio` | CSS | Idénticos | Campo “Año”. | Misma advertencia sobre IDs JSF. |
| `#j_idt83\:consultaExpediente\:consultaFiltroSearchButtonSAU` | CSS | Idénticos | Botón “Consultar”. | -- |
| `#j_idt150\:order_by_form\:camara` | CSS | `core/modulos_monitor/expedientes_modular/extraer_expedientes.extraer_expedientes` | Selector del desplegable de ordenamiento de expedientes. | ID generado por JSF; podría variar entre despliegues. |
| `a:has-text('Ordenar')` | CSS | `core/modulos_monitor/expedientes_modular/extraer_expedientes.extraer_expedientes` | Ejecuta el ordenamiento seleccionado. | Depende del texto visible; vigilar traducciones. |
| `text=No se han encontrado expedientes` | Texto | `gestion_expedientes/buscar_expediente_por_numero` y versión `bk` | Detectar mensaje de búsqueda vacía. | Sensible a copy exacto y acentos. |
| `table.table-striped` | CSS | `gestion_expedientes/busqueda_expediente.buscar_expedientes`, `bk` variantes, `mostrar_y_elegir_expediente`, `bk/buscar_y_abrir_expediente`, `bk/extraer_expedientes_bk` | Tabla de resultados de expedientes. | Si cambian clases Bootstrap, evaluar usar `role=grid` o similar. |
| `table.table-striped tbody tr` | CSS | `bk/extraer_expedientes_bk`, `bk/probar_busqueda_y_apertura_v2`, `bk/seleccionar_y_abrir_expediente`, `bk/extraer_expedientes_bk`, `gestion_expedientes/busqueda_expediente` | Iterar filas de resultados. | -- |
| `tbody tr td` | CSS | `mostrar_y_elegir_expediente`, `bk` variantes | Leer columnas de cada expediente. | Podría sustituirse por selectores `nth-child` con encabezados. |
| `a[id*=':j_idt285'][class]:not(.ui-state-disabled)` | CSS | `bk/extraer_expedientes_bk` | Botón “Siguiente” paginado (versión moderna). | Patron débil: depende del sufijo `j_idt285`; considerar localizar por texto `<span title='Siguiente'>`. |
| `a[id*='j_idt285']` | CSS | `bk/buscar_expediente_exacto` | Botón paginador genérico. | -- |
| `a:has(span[title='Siguiente'])` | CSS | `core/modulos_monitor/expedientes_modular/extraer_expedientes`, `core/modulos_monitor/expedientes_modular/bk/extraer_expedientes` | Botón de avance en la tabla (PrimeFaces moderno). | Depende del atributo `title` del ícono; revisar si cambia a `aria-label`. |
| `a` (dentro de fila) | Elemento | `abrir_expediente_desde_fila` y derivados | Abrir el enlace del expediente seleccionado. | Se asume un único `<a>` por fila. |

## Lectura de expediente abierto

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `span[style='color:#000000;']` | CSS | `gestion_expedientes/extraer_datos_expediente` | Extraer número de expediente (encabezado). | Selector frágil: depende de estilo inline. |
| `#expediente\:j_idt96\:detailCover` | CSS | Misma función | Carátula del expediente. | IDs JSF; usar `aria-label` si aparece. |
| `#expediente\:j_idt96\:detailDependencia` | CSS | Misma función | Dependencia. | -- |
| `#expediente\:j_idt96\:detailCamera` | CSS | Misma función | Jurisdicción / Cámara. | -- |
| `#expediente\:j_idt96\:detailSituation` | CSS | Misma función | Situación procesal. | -- |

## Actuaciones (actuales)

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `#expediente\:action-table tbody tr` | CSS | `gestion_actuaciones/extraccion_v2.extraer_actuaciones_pagina`, `bk/extraccion_bk` | Tabla de actuaciones actuales. | IDs JSF; comprobar tras despliegues. |
| `td` (dentro de filas) | Elemento | Misma función y dependientes | Obtener columnas (oficina, fecha, etc.). | -- |
| `i.fa-download` | CSS | `gestion_actuaciones/extraccion_v2`, `bk/extraccion_bk`, `bk/historicas` | Detectar icono de descarga de adjuntos. | Cambiaría si modifican librería de íconos. |
| `a:has(span[title='Siguiente']):not(.ui-state-disabled)` | CSS con pseudoclase | `gestion_actuaciones/extraccion_v2` | Navegar entre páginas de actuaciones actuales. | Depende de texto `title`; considerar fallback por `aria-label`. |
| `#expediente\:action-table` | CSS | `gestion_actuaciones/extraccion_v2` (comparación de HTML) | Verificar que la tabla se actualizó tras paginar. | -- |

## Actuaciones históricas

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `a:has-text('Ver históricas')` | CSS con pseudo | `gestion_actuaciones/bk/historicas.extraer_actuaciones_historicas` | Abrir panel de actuaciones históricas. | Cambia si el botón cambia de texto. |
| `#expediente\:action-historic-table tbody tr` | CSS | Misma función | Filas de actuaciones históricas. | -- |
| `div.alert.white-panel` | CSS | Misma función | Detectar mensaje “no posee actuaciones históricas”. | Atento a variaciones del mensaje/estilos. |
| `a[id^='expediente:j_idt']:not(.ui-state-disabled):has-text('Siguiente')` | CSS | Misma función | Botón “Siguiente” en históricas. | Prefijo `j_idt` puede rotar; combinar con texto. |
| `#expediente\:action-historic-table tbody tr td:nth-child(3)` | CSS | `gestion_actuaciones/bk/historicas` (espera JavaScript) | Confirmar cambio de página (columna fecha). | Fragilidad si cambia el orden de columnas. |

## Descarga de expedientes y adjuntos

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `a[id^='expediente:j_idt214:j_idt231']:not(.ui-state-disabled)` | CSS | `gestion_actuaciones/bk/extraccion_bk` | Botón “Siguiente” en tabla antigua de actuaciones. | Selector legado; solo para compatibilidad histórica. |

## Notificaciones PJN (Material UI)

| Selector | Tipo | Archivos / funciones | Objetivo | Observaciones |
| --- | --- | --- | --- | --- |
| `div.MuiTableContainer-root tr` | CSS | `notificaciones_v2/extractor_entradas.extraer_entradas_pjn`, `notificaciones_control_v4_async.actualizar_notificaciones_nuevas`, `notificaciones_control_v5_async.actualizar_notificaciones_nuevas` | Filas virtualizadas de la grilla de notificaciones. | Material UI puede alterar clases dinámicas (`css-xxxxx`); revisar tras actualizaciones. |
| `p.MuiTypography-root.MuiTypography-body1.w-full.css-11dlpbt` | CSS | Mismas funciones | Obtener el número de expediente en la ficha expandida. | Las clases `css-...` son generadas; crear fallback por `data-testid` si aparece. |
| `p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-4icvzy` | CSS | Mismas funciones | Carátula del expediente. | Ídem nota anterior. |
| `#LayoutScrollingContainer` | CSS (ID) | Mismas funciones | Contenedor scrollable principal de la bandeja. | Se usa para scroll programático y wheel; crítico para detectar fin de lista. |
| `[aria-label]` | CSS | `notificaciones_v2/extractor_entradas._detectar_indicador_evento`, `notificaciones_control_v5_async._detectar_indicador_evento` | Identificar íconos con aria-label “Evento Notificación/Despacho”. | Permite resiliencia accesible; mantener regex sincronizadas. |
| `.MuiAvatar-root p` | CSS | Idénticas funciones `_detectar_indicador_evento` | Fallback para letra “n/d” dentro del avatar. | Cambia si Material UI cambia estructura del avatar. |
| `cont.get_by_role("heading", name=re.compile(r"No hay m[aá]s eventos"))` | Locator por rol | `notificaciones_v2/extractor_entradas.extraer_entradas_pjn`, `notificaciones_control_v5_async.actualizar_notificaciones_nuevas` | Detectar mensaje final de lista. | Depende del texto accesible; robusto a HTML pero sensible al copy. |
| `cont.get_by_text(re.compile(r"Cargando m[aá]s eventos"))` | Locator por texto | Mismas funciones | Detectar indicador de carga para pausar scroll. | Mantener patrón regex actualizado. |

## Notas generales

* Varios scripts duplican selectores entre versiones “refactorizada” y copias en `bk/`. Mantenerlos sincronizados o consolidar helpers.
* Los IDs generados por JSF (`j_idt…`) y PrimeFaces cambian con frecuencia. Se recomienda encapsular los selectores en constantes reutilizables y contemplar alternativas basadas en etiquetas visibles o atributos `aria-label`.
* Los textos exactos (`text='Menú'`, `text=Consultas`) son sensibles a cambios menores de copy. Considere usar expresiones regulares (`has-text`) o normalización previa para reducir falsos negativos.
* La tabla solo cubre los selectores observados en scripts Playwright/Selenium actuales. Si se agregan nuevos módulos PJN, replicar el formato para mantener el inventario actualizado.
