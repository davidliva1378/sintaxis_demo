# Plan de Implementación: Solución al Bloqueo en Extracción Masiva

**Fecha de creación:** 2025-11-15
**Sistema:** sintaXis v6 - Extracción Masiva PJN
**Rama actual:** sintaxis_parcial3
**Commit base:** cb684af

---

## Resumen Ejecutivo

### Problemas a Resolver

**CRÍTICO #1: Bloqueo Infinito del Sistema**
- **Ubicación:** `pjn/scraping/expedientes.py` líneas 246, 638
- **Causa:** `_tbody_fingerprint()` llama `tbody.inner_html()` SIN timeout
- **Efecto:** Cuando navegador está corrupto, operación NUNCA retorna → task asyncio se congela
- **Impacto:** Usuario debe reiniciar servidor manualmente

**CRÍTICO #2: Navegador Zombie en Reintentos**
- **Ubicación:** `extraccion_masiva/extractor_masivo.py` líneas 118-332
- **Causa:** Navegador se crea UNA vez, se reutiliza en todos los reintentos
- **Efecto:** Después de error, navegador queda corrupto pero "vivo" → reintentos fallan con mismo navegador
- **Impacto:** Sistema no puede recuperarse de errores de navegador

### Solución Propuesta

**Estrategia de 3 Capas de Protección:**

1. **Capa 1 - Prevención de Bloqueo:**
   Agregar `asyncio.wait_for()` con timeout a operaciones críticas

2. **Capa 2 - Estado Limpio:**
   Recrear contexto/página entre reintentos (no reutilizar navegador corrupto)

3. **Capa 3 - Circuit Breaker:**
   Timeout global en task completa (opcional)

---

## Cambios Detallados

### CAMBIO 1: Timeout en `_tbody_fingerprint()`
**Prioridad:** 🔴 CRÍTICA
**Archivos afectados:**
- `pjn/scraping/expedientes.py` (~líneas 244-250)
- `Sistema_v4/operaciones/expedientes/expedientes_v4.py` (~líneas 120-127)

#### Código Actual (PROBLEMÁTICO)

```python
async def _tbody_fingerprint(tbody: Locator | ElementHandle) -> str:
    """Toma un snapshot del tbody para detectar cambios."""
    if isinstance(tbody, Locator):
        html = await tbody.inner_html()  # ❌ SIN TIMEOUT - PUEDE BLOQUEARSE
    else:
        html = await tbody.inner_html()  # ❌ SIN TIMEOUT - PUEDE BLOQUEARSE
    return _build_fingerprint(html)
```

#### Código Nuevo (CON TIMEOUT)

```python
async def _tbody_fingerprint(
    tbody: Locator | ElementHandle,
    timeout_ms: int = 5000
) -> str:
    """Toma un snapshot del tbody para detectar cambios.

    Args:
        tbody: Locator o ElementHandle del tbody
        timeout_ms: Timeout en milisegundos para prevenir bloqueos

    Raises:
        TimeoutError: Si la operación excede el timeout (navegador posiblemente corrupto)
    """
    try:
        if isinstance(tbody, Locator):
            html = await asyncio.wait_for(
                tbody.inner_html(),
                timeout=timeout_ms / 1000
            )
        else:
            html = await asyncio.wait_for(
                tbody.inner_html(),
                timeout=timeout_ms / 1000
            )
        return _build_fingerprint(html)
    except asyncio.TimeoutError:
        logger.error(
            "⏱️ Timeout obteniendo tbody fingerprint después de %dms - navegador posiblemente corrupto",
            timeout_ms
        )
        raise TimeoutError(
            f"Timeout obteniendo tbody fingerprint después de {timeout_ms}ms"
        )
```

#### Cambios en Llamadas a `_tbody_fingerprint()`

**Ubicaciones a actualizar:**
1. `expedientes.py` línea ~246 (dentro del loop de polling)
2. `expedientes.py` línea ~638 (después de clic en "Siguiente")
3. `expedientes_v4.py` línea ~448 (dentro del loop de polling)

**Ejemplo de actualización:**
```python
# ANTES
fingerprint_actual = await _tbody_fingerprint(tbody_locator)

# DESPUÉS
fingerprint_actual = await _tbody_fingerprint(tbody_locator, timeout_ms=5000)
```

---

### CAMBIO 2: Reestructurar Reintentos con Contexto/Página Nueva
**Prioridad:** 🔴 CRÍTICA
**Archivo:** `extraccion_masiva/extractor_masivo.py` (líneas 118-428)

#### Estructura Actual (PROBLEMÁTICA)

```python
async def extraer_listado_completo(self, ...):
    async with async_playwright() as p:
        # ❌ Browser/context/page creados UNA VEZ
        browser = await p.chromium.launch(headless=self.config.headless)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await self._hacer_login(page)

        # LOOP DE REINTENTOS
        while sesion.intentos_realizados < sesion.intentos_maximos:
            try:
                # ❌ USA MISMO PAGE CORRUPTO EN REINTENTOS
                expedientes = await extraer_expedientes_completos(page, ...)
                break
            except Exception as e:
                # ❌ Solo navega de vuelta, NO recrea navegador
                await self._navegar_a_listado(page)
```

#### Estructura Nueva (CON ESTADO LIMPIO)

```python
async def extraer_listado_completo(self, ...):
    """Extrae expedientes con reintentos usando contexto/página limpia en cada intento."""

    sesion = SesionExtraccion(...)
    expedientes_resultado = None
    motivo_resultado = None
    metadata_resultado = None

    async with async_playwright() as p:
        # ✅ Browser base (se reutiliza, pero contexts/pages se recrean)
        browser = await p.chromium.launch(
            headless=self.config.headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        try:
            # LOOP DE REINTENTOS
            for intento in range(1, self.config.max_reintentos + 1):
                sesion.intentos_realizados = intento
                context = None
                page = None

                try:
                    logger.info(f"📄 Intento {intento}/{self.config.max_reintentos}: Creando contexto/página nueva...")

                    # ✅ CONTEXTO/PÁGINA NUEVA para cada intento
                    context = await browser.new_context()
                    page = await context.new_page()
                    page.set_default_timeout(self.config.timeout_pagina)

                    # ✅ Login + navegación con página limpia
                    await self._login_y_navegar(page)

                    # ✅ Extracción con página limpia
                    expedientes_raw, motivo, metadata = await extraer_expedientes_completos(
                        page,
                        fecha_corte=fecha_corte,
                        tiempo_maximo_segundos=self.config.tiempo_maximo_segundos,
                        orden="fecha",
                        detener_en_duplicado=self.config.detener_en_duplicado,
                        omitir_duplicados=self.config.omitir_duplicados,
                        max_paginas=self.config.max_paginas,
                    )

                    # Registrar en historial
                    sesion.historial_intentos.append({
                        "intento": intento,
                        "timestamp": datetime.now().isoformat(),
                        "motivo": motivo,
                        "total_expedientes": len(expedientes_raw) if expedientes_raw else 0,
                        "metadata": metadata
                    })

                    # Verificar si fue exitoso
                    if motivo in MOTIVOS_EXITOSOS:
                        logger.info(f"✅ Intento {intento} exitoso: {motivo}")
                        expedientes_resultado = expedientes_raw
                        motivo_resultado = motivo
                        metadata_resultado = metadata
                        sesion.estado = "completado"
                        break  # Salir del loop de reintentos
                    else:
                        logger.warning(f"⚠️ Intento {intento} no exitoso: {motivo}")

                except Exception as e_intento:
                    # Clasificar error
                    error_str = str(e_intento).lower()
                    error_type = type(e_intento).__name__

                    if any(kw in error_str for kw in ['target closed', 'browser', 'context closed']):
                        motivo = "navegador_cerrado"
                        logger.error(f"❌ Intento {intento}: Navegador cerrado inesperadamente")
                    elif error_type == 'TimeoutError' or 'timeout' in error_str:
                        motivo = "timeout_conexion"
                        logger.error(f"❌ Intento {intento}: Timeout de conexión")
                    else:
                        motivo = "error_desconocido"
                        logger.error(f"❌ Intento {intento}: Error tipo {error_type}: {e_intento}")

                    # Registrar en historial
                    sesion.historial_intentos.append({
                        "intento": intento,
                        "timestamp": datetime.now().isoformat(),
                        "motivo": motivo,
                        "error": str(e_intento),
                        "total_expedientes": 0
                    })

                    # Si navegador cerrado, no tiene sentido reintentar
                    if motivo == "navegador_cerrado":
                        logger.error("🚫 Navegador cerrado - abortando reintentos")
                        sesion.estado = "error_agotado"
                        raise

                finally:
                    # ✅ CRUCIAL: Cerrar contexto/página SIEMPRE
                    if page:
                        try:
                            await page.close()
                            logger.debug(f"🔒 Página del intento {intento} cerrada")
                        except Exception as e:
                            logger.warning(f"⚠️ Error cerrando página: {e}")

                    if context:
                        try:
                            await context.close()
                            logger.debug(f"🔒 Contexto del intento {intento} cerrado")
                        except Exception as e:
                            logger.warning(f"⚠️ Error cerrando contexto: {e}")

                # Si fue exitoso, ya salimos con break
                # Si no, esperar delay antes de siguiente intento
                if intento < self.config.max_reintentos:
                    delay = self._calcular_delay_reintento(intento)
                    logger.info(f"⏱️ Esperando {delay}s antes del siguiente intento...")
                    await asyncio.sleep(delay)

            # Si llegamos aquí, agotamos reintentos sin éxito
            if not expedientes_resultado:
                logger.error("🚫 Reintentos agotados sin éxito")
                sesion.estado = "error_agotado"
                sesion.mensaje = f"Agotados {self.config.max_reintentos} reintentos"
                raise Exception(f"Extracción falló después de {self.config.max_reintentos} intentos")

            # Retornar resultado exitoso
            return expedientes_resultado, motivo_resultado, metadata_resultado

        finally:
            # ✅ Cerrar browser al final
            try:
                await browser.close()
                logger.info("🚪 Navegador principal cerrado")
            except Exception as e:
                logger.warning(f"⚠️ Error cerrando navegador: {e}")


def _calcular_delay_reintento(self, intento: int) -> int:
    """Calcula delay progresivo para reintentos."""
    DELAYS = [5, 10, 20]  # segundos
    idx = intento - 1
    return DELAYS[min(idx, len(DELAYS) - 1)]
```

---

### CAMBIO 3: Extraer Login a Método Helper
**Prioridad:** 🟡 ALTA
**Archivo:** `extraccion_masiva/extractor_masivo.py`

#### Nuevo Método

```python
async def _login_y_navegar(self, page: Page) -> None:
    """Realiza login al PJN y navega al listado de expedientes.

    Este método encapsula todo el flujo de autenticación y navegación inicial,
    permitiendo reutilizarlo en cada intento con una página limpia.

    Args:
        page: Página de Playwright limpia (nuevo contexto)

    Raises:
        Exception: Si falla el login o la navegación
    """
    # Login al portal PJN
    logger.info("🔐 Iniciando login al Portal Judicial Nacional...")

    try:
        await page.goto("https://portalpjn.pjn.gov.ar/inicio")
        await page.wait_for_load_state("networkidle")

        # Hacer clic en "Ingresá con tu DNI"
        await page.click("text=Ingresá con tu DNI")
        await page.wait_for_load_state("networkidle")

        # Ingresar credenciales
        await page.fill('input[name="username"]', self.username)
        await page.fill('input[name="password"]', self.password)

        # Submit
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # Verificar login exitoso
        if "inicio" not in page.url.lower():
            raise Exception("Login falló - URL inesperada después de submit")

        logger.info("✅ Login exitoso")

    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        raise

    # Navegar al listado de expedientes
    logger.info("🧭 Navegando a listado de expedientes...")
    await self._navegar_a_listado(page)
    logger.info("✅ Navegación completada")
```

---

### CAMBIO 4: Timeout Global en Background Task (OPCIONAL)
**Prioridad:** 🟢 MEDIA
**Archivo:** `presentation/api/rest/routers/extraccion_masiva.py` (~línea 250)

#### Código Actual

```python
async def _ejecutar_extraccion_background(...):
    try:
        # Ejecutar extracción
        resultado = await extractor.extraer_listado_completo(...)
```

#### Código Nuevo (CON CIRCUIT BREAKER)

```python
async def _ejecutar_extraccion_background(...):
    try:
        # Ejecutar extracción con timeout global (circuit breaker)
        resultado = await asyncio.wait_for(
            extractor.extraer_listado_completo(...),
            timeout=600  # 10 minutos máximo
        )

    except asyncio.TimeoutError:
        logger.error("⏱️ Extracción excedió timeout global de 10 minutos")
        sesion = sesiones_activas.get(session_id)
        if sesion:
            sesion.estado = "error_agotado"
            sesion.mensaje = "Timeout global - extracción demasiado lenta o bloqueada"
            sesion.motivo_finalizacion = "timeout_global"
        raise
```

---

### CAMBIO 5: Mejorar Logging
**Prioridad:** 🟡 ALTA
**Archivos múltiples**

#### Nuevos Mensajes de Log

**En creación/cierre de navegador:**
```python
logger.info("🌐 Creando navegador principal...")
logger.info(f"📄 Intento {intento}: Creando contexto/página nueva...")
logger.debug(f"🔒 Página del intento {intento} cerrada")
logger.debug(f"🔒 Contexto del intento {intento} cerrado")
logger.info("🚪 Navegador principal cerrado")
```

**En timeout de fingerprint:**
```python
logger.error(
    "⏱️ Timeout obteniendo tbody fingerprint después de %dms - navegador posiblemente corrupto",
    timeout_ms
)
```

**En reintentos:**
```python
logger.info(f"⏱️ Esperando {delay}s antes del siguiente intento...")
logger.warning(f"⚠️ Intento {intento} no exitoso: {motivo}")
logger.info(f"✅ Intento {intento} exitoso: {motivo}")
```

---

## Orden de Implementación

### FASE 1: Prevención de Bloqueo (30 min)
1. ✅ Modificar `_tbody_fingerprint()` en `pjn/scraping/expedientes.py`
2. ✅ Modificar `_tbody_fingerprint()` en `Sistema_v4/operaciones/expedientes/expedientes_v4.py`
3. ✅ Actualizar todas las llamadas a `_tbody_fingerprint()` para pasar timeout
4. ✅ Agregar import de `asyncio` si no existe

### FASE 2: Reestructuración de Reintentos (45 min)
5. ✅ Crear método `_login_y_navegar()` (CAMBIO 3)
6. ✅ Crear método `_calcular_delay_reintento()`
7. ✅ Reestructurar `extraer_listado_completo()` (CAMBIO 2)
8. ✅ Agregar logging detallado (CAMBIO 5)

### FASE 3: Testing (30 min)
9. ✅ Prueba básica: extracción sin errores
10. ✅ Prueba con timeout: provocar timeout y verificar recuperación
11. ✅ Prueba de reintentos: verificar múltiples reintentos funcionan
12. ✅ Prueba de recursos: verificar liberación de memoria

### FASE 4: Opcional (15 min)
13. ⚠️ Agregar timeout global (CAMBIO 4) - solo si fases 1-3 no son suficientes

---

## Plan de Testing

### Test 1: Verificar Prevención de Bloqueo
**Objetivo:** Confirmar que `_tbody_fingerprint()` con timeout previene bloqueo infinito

**Pasos:**
1. Modificar temporalmente timeout a 2000ms (2s)
2. Provocar condición de navegador lento (throttling de red)
3. Iniciar extracción masiva
4. **Resultado esperado:**
   - Sistema lanza TimeoutError después de 2s
   - NO se bloquea infinitamente
   - Logs muestran "⏱️ Timeout obteniendo tbody fingerprint..."

### Test 2: Verificar Reintentos con Estado Limpio
**Objetivo:** Confirmar que reintentos crean contexto/página nueva

**Pasos:**
1. Agregar logging en `_login_y_navegar()` para contar llamadas
2. Provocar error en primer intento (ej: timeout)
3. Verificar que segundo intento hace login nuevamente
4. **Resultado esperado:**
   - Logs muestran "📄 Intento 2: Creando contexto/página nueva..."
   - Logs muestran "🔐 Iniciando login..." por segunda vez
   - Segundo intento funciona correctamente

### Test 3: Verificar Liberación de Recursos
**Objetivo:** Confirmar que navegadores se cierran correctamente

**Pasos:**
1. Ejecutar extracción masiva con 3 reintentos forzados
2. Monitorear procesos Chromium durante ejecución
3. Al finalizar, verificar que todos los procesos Chromium se cerraron
4. **Resultado esperado:**
   - Durante: máximo 1 proceso Chromium activo
   - Al finalizar: 0 procesos Chromium

**Comando para verificar:**
```bash
# Durante extracción
ps aux | grep -i chromium | wc -l

# Al finalizar (debe ser 0)
ps aux | grep -i chromium
```

### Test 4: Extracción Normal Sin Errores
**Objetivo:** Confirmar que cambios no rompieron funcionalidad básica

**Pasos:**
1. Ejecutar extracción masiva normal (sin provocar errores)
2. Verificar que extrae expedientes correctamente
3. Verificar tiempos de respuesta razonables
4. **Resultado esperado:**
   - Extracción exitosa
   - Tiempo similar a versión anterior (+/- 10%)
   - Todos los expedientes extraídos

---

## Checklist Pre-Implementación

Antes de empezar, verificar:

- [ ] Commit actual guardado (`cb684af`)
- [ ] Crear nueva rama: `git checkout -b fix/bloqueo-reintentos`
- [ ] Backup de archivos a modificar (opcional)
- [ ] Servidor de desarrollo corriendo
- [ ] Credenciales PJN de prueba disponibles

---

## Checklist Post-Implementación

Después de implementar:

- [ ] Tests 1-4 ejecutados y pasados
- [ ] Logs revisados (sin errores inesperados)
- [ ] Procesos Chromium verificados (todos cerrados)
- [ ] Memoria del servidor verificada (sin leaks)
- [ ] Código revisado (no hay `print()` debug olvidados)
- [ ] Commit creado con mensaje descriptivo
- [ ] Push a rama remota

---

## Estimación de Tiempo Total

| Actividad | Tiempo |
|-----------|--------|
| Fase 1: Prevención de Bloqueo | 30 min |
| Fase 2: Reestructuración | 45 min |
| Fase 3: Testing | 30 min |
| Fase 4: Opcional | 15 min (si necesario) |
| **TOTAL ESTIMADO** | **~2 horas** |

---

## Rollback Plan (Si Algo Sale Mal)

Si después de implementar hay problemas:

```bash
# Opción 1: Revertir cambios
git restore pjn/scraping/expedientes.py
git restore extraccion_masiva/extractor_masivo.py

# Opción 2: Volver al commit anterior
git reset --hard cb684af

# Reiniciar servidor
pkill -9 -f uvicorn && pkill -9 -f vite
python3 scripts/iniciar_servidores.py
```

---

## Próximos Pasos Después de Implementación

1. **Monitorear** en uso real por 24-48 horas
2. **Recopilar métricas:**
   - Tasa de éxito de reintentos
   - Tiempo promedio de extracción
   - Frecuencia de timeouts
3. **Optimizar** si es necesario:
   - Ajustar timeouts según métricas
   - Implementar timeout global si se necesita
4. **Documentar** casos de uso y patrones observados

---

## Referencias

**Archivos principales:**
- `pjn/scraping/expedientes.py` - Función de extracción v6
- `Sistema_v4/operaciones/expedientes/expedientes_v4.py` - Función de extracción v4
- `extraccion_masiva/extractor_masivo.py` - Orquestador de extracción masiva
- `presentation/api/rest/routers/extraccion_masiva.py` - API REST

**Documentación relacionada:**
- `PLAN_MEJORAS_ORDENACION_Y_TIMEOUTS.md` - Plan anterior de mejoras
- Playwright docs: https://playwright.dev/python/docs/api/class-page

---

**FIN DEL PLAN**
