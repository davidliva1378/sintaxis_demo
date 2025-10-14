# Tabla de selectores del portal PJN

Este inventario recopila los selectores utilizados por los scripts Playwright del proyecto para automatizar el portal del Poder Judicial de la Nación (PJN). Se incluyen los archivos y funciones que los consumen, la finalidad prevista y observaciones relevantes para su mantenimiento ante cambios en la interfaz.

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
