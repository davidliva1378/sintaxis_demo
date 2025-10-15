# Inventario de funciones en `Sistema_v4`

Este documento resume las funciones y clases detectadas en cada módulo de la versión actual.

## Paquete `Sistema_v4/__init__.py`

### Módulo `Sistema_v4/__init__.py`
- (sin definiciones detectadas)


## Paquete `Sistema_v4/actuaciones`

### Módulo `Sistema_v4/actuaciones/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/actuaciones/actuaciones_utils.py`
- Función `limpiar_texto(texto)`
- Función `normalizar_fecha(texto)`
- Función `generar_hash_archivo(fecha, tipo, detalle, longitud)`

### Módulo `Sistema_v4/actuaciones/actuaciones_v4.py`
- Función `_calcular_metricas_descargas(actuaciones)`
- Función `actualizar_metricas_descargas_en_json(payload)`
- Función `normalizar_numero_expediente(valor, valor_por_defecto)`
- Función `construir_encabezado_actuaciones(expediente_datos, actuaciones_actuales, actuaciones_historicas, incluye_historicas, timestamp_generacion)`
- Función `obtener_extension_valida(valor)`
- Función `construir_nombre_archivo_normalizado(fecha, tipo, hash_val, archivo_url, nombre_descarga)`
- Función `_escape_selector_for_css(selector)`
- Función `_escape_selector_for_js(selector)`
- Función asíncrona `_obtener_paginador_activo(page, tabla_id)`
- Función asíncrona `_esperar_cambio_pagina(page, tabla_id, html_anterior, paginador_selector_js, pagina_anterior)`
- Función asíncrona `construir_actuacion_desde_fila(page_expediente, fila, indice, timestamp_extraccion, es_historica)`
- Función asíncrona `extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial)`
- Función asíncrona `extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial)`
- Función asíncrona `obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino)`
- Función asíncrona `actualizar_actuaciones_desde_json(page_expediente, expediente_datos, ruta_json_existente)`
- Función asíncrona `extraer_actuaciones_completas(page_expediente, expediente_datos, incluir_historicas, directorio_base)`
- Función asíncrona `aviso_si_tarda(idx, segundos)`
- Función asíncrona `descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- Función asíncrona `descargar_archivos_de_json(page, carpeta_destino)`

### Módulo `Sistema_v4/actuaciones/actuaciones_v5.py`
- Función `_asegurar_dict(datos, llave)`
- Función `_asegurar_lista_actuaciones(datos)`
- Función `_parsear_fecha(valor)`
- Función `_contar_adjuntos(actuaciones)`
- Clase `Actuacion`
  - Método `from_dict(cls, datos)`
  - Método `to_dict(self)`
  - Método `marcar_descargado(self, nombre_archivo, estado)`
  - Método `es_actual(self)`
- Clase `ActuacionesExpediente`
  - Método `from_dict(cls, datos)`
  - Método `cargar_desde_archivo(cls, ruta)`
  - Método `guardar(self, ruta, indent)`
  - Método `to_dict(self)`
  - Método `_validar_version(self)`
  - Método `obtener_fecha_extraccion(self)`
  - Método `filtrar_actuaciones(self, historicas, con_archivo, descargadas)`
  - Método `iter_actuaciones(self, **filtros)`
  - Método `obtener_por_hash(self, hash_valor)`
  - Método `obtener_por_indice(self, indice)`
  - Método `marcar_descargado(self, hash_valor, indice, nombre_archivo, estado)`
  - Método `resumen_descargas(self)`
  - Método `recalcular_metricas(self)`
  - Método `exportar_actuaciones(self)`
- Función `cargar_expediente_actuaciones(ruta)`


## Paquete `Sistema_v4/config`

### Módulo `Sistema_v4/config/__init__.py`
- (sin definiciones detectadas)


## Paquete `Sistema_v4/documentacion`

### Módulo `Sistema_v4/documentacion/__init__.py`
- (sin definiciones detectadas)


## Paquete `Sistema_v4/monitor`

### Módulo `Sistema_v4/monitor/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/monitor/comparacion_expedientes.py`
- Clase `RutasComparacion`
  - (sin métodos definidos)
- Clase `ResultadoComparacion`
  - Método `total_cambios(self)`
  - Método `mensajes_faltantes(self)`
- Función `obtener_rutas(base_dir, config)`
- Función `comparar_expedientes(base_dir, config)`
- Función `_resolver_config_general(config)`
- Función `_resolver_modo_comparacion(config)`
- Función `_resolver_base_monitoreo(base_dir, config)`
- Función `_resolver_fecha_corte(config)`
- Función `_filtrar_por_fecha(expedientes, fecha_corte)`
- Función `_parsear_fecha(valor)`

### Módulo `Sistema_v4/monitor/configuracion_modo.py`
- Función `_mezclar_dicts(base, override)`
- Función `_inyectar_defaults(config)`
- Función `cargar_config_monitor(path)`
- Función `guardar_config_monitor(config, path)`
- Función `actualizar_modo_monitor(nuevo_modo, path)`
- Función `es_modo_valido(modo)`
- Función `obtener_fecha_corte(config, path)`

### Módulo `Sistema_v4/monitor/icono_base64.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/monitor/monitor_entradas_expedientes_v4.py`
- Función `_normalizar_dia_semana(valor)`
- Clase `ResultadoExpedientes`
  - (sin métodos definidos)
- Clase `ResultadoEntradas`
  - (sin métodos definidos)
- Clase `ConfiguracionDialog`
  - Método `__init__(self, config, parent)`
  - Método `_crear_ui(self)`
  - Método `_crear_tab_general(self)`
  - Método `_crear_tab_intervalos(self)`
  - Método `_crear_tab_filtro(self)`
  - Método `_crear_tab_reintentos(self)`
  - Método `_crear_tab_respaldo(self)`
  - Método `_crear_tab_notificaciones(self)`
  - Método `_crear_contenedor_ruta(self, edit, boton)`
  - Método `_crear_label_descriptivo(self, texto)`
  - Método `_conectar_eventos(self)`
  - Método `_cargar_datos(self)`
  - Método `_set_time_edit(self, widget, valor)`
  - Método `_seleccionar_monitoreo(self)`
  - Método `_seleccionar_respaldo(self)`
  - Método `accept(self)`
  - Método `_asegurar_dict(self, destino, clave, default)`
  - Método `_recopilar_configuracion(self, validar)`
  - Método `obtener_configuracion(self)`
  - Método `_validar_configuracion(self, config)`
  - Método `_validar_ruta(self, edit, descripcion)`
  - Método `_actualizar_preview_fecha(self)`
  - Método `_restaurar_defaults(self)`
  - Método `_mostrar_estado(self, mensaje, tipo)`
- Clase `VerificadorExpedientesV4`
  - Método `__init__(self, carpeta_salida, nombre_archivo, guardar_json, fecha_corte, orden)`
  - Método `run(self)`
  - Método asíncrono `_verificar_async(self)`
  - Método `_guardar_resultados(self, expedientes)`
- Clase `VerificadorEntradasV4`
  - Método `__init__(self, destino)`
  - Método `run(self)`
  - Método asíncrono `_verificar_async(self)`
- Clase `MonitorExpedientesTray`
  - Método `__init__(self)`
  - Método `_crear_icono()`
  - Método `cargar_config(self)`
  - Método `_aplicar_configuracion(self, config)`
  - Método `_resolver_directorio_monitoreo(self, config)`
  - Método `_resolver_reintentos(self, config)`
  - Método `_resolver_notificaciones(self, config)`
  - Método `_obtener_config_reintentos(self, tipo)`
  - Método `_should_notify(self, clave, default)`
  - Método `_resolver_intervalo_config(self, bloque, tipo)`
  - Método `esta_en_horario_laboral(self)`
  - Método `obtener_intervalo(self, tipo)`
  - Método `iniciar_temporizador(self)`
  - Método `reiniciar_temporizadores(self)`
  - Método `actualizar_tooltip(self)`
  - Método `actualizar_modo_seleccionado(self)`
  - Método `_manejar_cambio_modo(self, modo, checked)`
  - Método `cambiar_modo(self, nuevo_modo)`
  - Método `verificar_expedientes(self)`
  - Método `_limpiar_hilo_expedientes(self)`
  - Método `verificar_entradas(self)`
  - Método `_limpiar_hilo_entradas(self)`
  - Método `procesar_resultado_expedientes(self, datos)`
  - Método `procesar_resultado_entradas(self, datos)`
  - Método `respaldar_resultados(self)`
  - Método `mostrar_estado_sesion(self)`
  - Método `forzar_login(self)`
  - Método `comparar_expedientes_manual(self)`
  - Método `_comparar_expedientes(self, origen, notificar, notificar_sin_cambios, notificar_faltantes)`
  - Método `salir(self)`
  - Método `abrir_configuracion(self)`

### Módulo `Sistema_v4/monitor/respaldo_historico.py`
- Clase `ResultadoRespaldo`
  - (sin métodos definidos)
- Función `_normalizar_archivos(archivos)`
- Función `generar_respaldo_monitoreo(origen, destino_base, archivos)`


## Paquete `Sistema_v4/operaciones`

### Módulo `Sistema_v4/operaciones/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/operaciones/entradas/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/operaciones/entradas/bk/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/operaciones/entradas/bk/entradas.py`
- Función asíncrona `actualizar_notificaciones_nuevas(page, destino)`
- Función `notificaciones_proximas_a_vencer(destino, horas)`

### Módulo `Sistema_v4/operaciones/entradas/extractor_entradas.py`
- Función `limpiar_texto(texto)`
- Función `normalizar_texto(t)`
- Función `_to_iso(fecha_str)`
- Función `_parse_fechas_exactas(fechas)`
- Función `_parse_fecha_limite(f)`
- Función asíncrona `_near_bottom(page, tol)`
- Función asíncrona `_scroll_step(page)`
- Función asíncrona `_wheel(page, cont_locator)`
- Función asíncrona `_detectar_indicador_evento(fila)`
- Función `_base_key(e)`
- Función `_event_key(e)`
- Función asíncrona `extraer_entradas_pjn(page, destino, duplicados, incluir_tipos, fechas, fecha_desde, fecha_hasta)`

### Módulo `Sistema_v4/operaciones/entradas/test_extractor_entradas.py`
- Función asíncrona `main()`

### Módulo `Sistema_v4/operaciones/entradas/utils.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/operaciones/expedientes/__init__.py`
- (sin definiciones detectadas)

### Módulo `Sistema_v4/operaciones/expedientes/expedientes_v4.py`
- Función `_resolver_valor_orden(orden)`
- Función `_norm_fecha(s)`
- Función `_build_fingerprint(html, max_len)`
- Función asíncrona `_is_locator_enabled(locator)`
- Función asíncrona `_tbody_fingerprint(tbody)`
- Función asíncrona `_extraer_total_esperado(page)`
- Función asíncrona `extraer_expedientes_completos(page, sel_tabla, sel_tbody, sel_siguiente, max_paginas, omitir_duplicados, detener_en_duplicado, fecha_corte, tiempo_maximo_segundos, orden)`
- Función asíncrona `extraer_datos_expediente(page)`
- Función asíncrona `abrir_expediente_desde_fila(fila, page)`
- Función `_seleccionar_primera_opcion(opciones)`
- Función asíncrona `mostrar_y_elegir_expediente(page, filas, estrategia_seleccion, descripcion_estrategia)`
- Función asíncrona `buscar_expediente_por_numero(page, numero, anio, timeout)`
- Función asíncrona `buscar_expedientes_por_caratula(page, caratula)`
- Función asíncrona `buscar_expedientes(page, numero, anio, caratula)`

### Módulo `Sistema_v4/operaciones/rf_test_actualizacion_actuaciones.py`
- Función `seleccionar_por_consola(opciones)`
- Función `_mostrar_credenciales_vacias()`
- Función asíncrona `login_portal(page)`
- Función `_resolver_ruta_json(ruta)`
- Función `_cargar_json_existente(ruta)`
- Función `_sugerir_anio(numero_expediente)`
- Función asíncrona `main()`

### Módulo `Sistema_v4/operaciones/rf_test_extraccion_completa.py`
- Función `seleccionar_por_consola(opciones)`
- Función `_mostrar_credenciales_vacias()`
- Función asíncrona `login_portal(page)`
- Función asíncrona `main()`


## Paquete `Sistema_v4/utils`

### Módulo `Sistema_v4/utils/__init__.py`
- (sin definiciones detectadas)


## Paquete `Sistema_v4/web`

### Módulo `Sistema_v4/web/__init__.py`
- (sin definiciones detectadas)

## Observaciones generales

- Documentar dependencias externas: varios módulos importan componentes de `Sistema_v3` o `core`, lo que indica acoplamiento que conviene revisar para `Sistema_v5`.
- Hay scripts interactivos (`rf_test_*.py`) con credenciales por defecto embebidas; se debe extraer esta información sensible y centralizar la configuración en variables de entorno obligatorias.
- `operaciones/entradas/utils.py` intenta importar `..expedientes.utils`, módulo inexistente en `Sistema_v4`, lo que rompe el paquete. Es necesario redefinir o eliminar estos helpers.
- `operaciones/entradas/bk/entradas.py` depende de utilidades de `Sistema_v3` y parece mantenerse como copia de seguridad; conviene decidir si se migra al nuevo stack o se retira para evitar confusiones.
- El monitor Qt (`monitor_entradas_expedientes_v4.py`) concentra UI, control de tareas y lógica de negocio en una sola clase de más de 40 métodos; para `Sistema_v5` sería recomendable dividir responsabilidades (configuración, ejecución de verificaciones, UI) y aislar la interacción con Playwright en componentes reutilizables.
