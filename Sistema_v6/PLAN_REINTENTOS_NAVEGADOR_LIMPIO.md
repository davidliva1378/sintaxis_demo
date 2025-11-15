# Plan: Mejorar Sistema de Reintentos en Extracción Masiva

## Objetivo
Solucionar el bloqueo del sistema cuando hay errores de navegador durante extracción masiva, implementando cierre/reapertura de contexto/página en cada reintento.

## Problema Actual
- Navegador Playwright se crea UNA vez y se reutiliza en todos los reintentos
- Cuando hay error, navegador queda en estado corrupto/bloqueado
- `_navegar_a_listado()` usa misma página corrupta → sistema se bloquea
- Requiere reinicio manual del servidor

## Solución: Opción C - Reiniciar Contexto/Página por Reintento

### Estrategia
- Mantener browser base durante todo el proceso (eficiencia)
- Crear contexto/página NUEVA en cada intento (estado limpio)
- Cerrar contexto/página al terminar cada intento (exitoso o fallido)
- Hacer login nuevo con cada contexto/página limpia

---

## Tareas de Implementación

### ✅ FASE 1: Análisis Completado
- [x] Investigar comportamiento actual de reintentos
- [x] Identificar dónde se crea el navegador (línea 118)
- [x] Analizar función `_navegar_a_listado()` (líneas 449-463)
- [x] Identificar causa de bloqueo (contexto/página corrupta)
- [x] Evaluar opciones de solución (A, B, C, D)

### ⏳ FASE 2: Reestructuración de Código
- [ ] **Tarea 2.1:** Extraer lógica de login a método helper
  - Archivo: `extraccion_masiva/extractor_masivo.py`
  - Crear: `async def _login_y_navegar(self, page: Page) -> None`
  - Encapsula: login + navegación a listado
  - Reutilizable en cada intento

- [ ] **Tarea 2.2:** Reestructurar loop de reintentos
  - Archivo: `extraccion_masiva/extractor_masivo.py`
  - Método: `extraer_listado_completo()` (líneas 118-428)
  - Cambios:
    - Crear browser UNA vez (fuera del loop)
    - Loop de reintentos crea contexto/página nueva
    - Cerrar contexto/página al final de cada iteración
    - Cerrar browser al final del método

- [ ] **Tarea 2.3:** Mejorar manejo de excepciones
  - Asegurar cierre de recursos en `finally` blocks
  - Capturar errores específicos de Playwright
  - Logging detallado de cierre/apertura de recursos

### ⏳ FASE 3: Mejoras de Logging
- [ ] **Tarea 3.1:** Agregar logs de ciclo de vida del navegador
  - "🌐 Creando navegador principal..."
  - "📄 Intento {N}: Creando contexto/página nueva..."
  - "🔒 Cerrando contexto/página del intento {N}..."
  - "🚪 Cerrando navegador principal..."

- [ ] **Tarea 3.2:** Mejorar logs de reintentos
  - Indicar CLARAMENTE cuándo se reintenta con recursos limpios
  - Diferenciar entre error transitorio vs bloqueo

### ⏳ FASE 4: Testing
- [ ] **Tarea 4.1:** Prueba básica sin errores
  - Verificar que extracción normal funciona
  - Confirmar que navegador se cierra correctamente

- [ ] **Tarea 4.2:** Prueba con error simulado
  - Provocar timeout intencional
  - Verificar que reintenta con contexto limpio
  - Confirmar que NO se bloquea el sistema

- [ ] **Tarea 4.3:** Prueba de estrés
  - Múltiples reintentos consecutivos
  - Verificar liberación de memoria
  - Confirmar estabilidad del servidor

---

## Estructura de Código Propuesta

```python
# extraccion_masiva/extractor_masivo.py

async def extraer_listado_completo(self, ...):
    """Extrae expedientes con reintentos usando contexto/página limpia."""

    sesion = SesionExtraccion(...)

    async with async_playwright() as p:
        # Crear browser UNA vez (reutilizable)
        browser = await p.chromium.launch(headless=self.config.headless)

        try:
            # LOOP DE REINTENTOS
            for intento in range(1, self.config.max_reintentos + 1):
                sesion.intentos_realizados = intento

                # Crear contexto/página NUEVA para este intento
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.config.timeout_pagina)

                try:
                    # Login y navegación con página limpia
                    await self._login_y_navegar(page)

                    # Extracción completa
                    expedientes, motivo, metadata = await extraer_expedientes_completos(
                        page, ...
                    )

                    # Verificar éxito
                    if motivo in MOTIVOS_EXITOSOS:
                        sesion.estado = "completado"
                        return expedientes, motivo, metadata

                except Exception as e:
                    # Manejar error
                    motivo = self._clasificar_error(e)

                    # Registrar en historial
                    sesion.historial_intentos.append({...})

                    # Si es error fatal, abortar
                    if motivo == "navegador_cerrado":
                        raise

                finally:
                    # CRUCIAL: Cerrar contexto/página SIEMPRE
                    await page.close()
                    await context.close()

                # Si no fue exitoso y quedan reintentos, esperar delay
                if intento < self.config.max_reintentos:
                    delay = self._calcular_delay(intento)
                    await asyncio.sleep(delay)

            # Agotar reintentos
            sesion.estado = "error_agotado"
            raise Exception("Reintentos agotados")

        finally:
            # Cerrar browser al final
            await browser.close()


async def _login_y_navegar(self, page: Page) -> None:
    """Helper: Login + navegación a listado con página limpia."""
    # Login
    await page.goto(self.config.login_url)
    # ... lógica de login ...

    # Navegar a listado
    await self._navegar_a_listado(page)
```

---

## Estimación de Tiempo

| Tarea | Tiempo Estimado |
|-------|----------------|
| Fase 2: Reestructuración | 30-45 min |
| Fase 3: Logging | 15 min |
| Fase 4: Testing | 30 min |
| **TOTAL** | **~1.5 horas** |

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|-----------|
| Leaks de memoria por no cerrar recursos | Media | Usar `finally` blocks para garantizar cierre |
| Lentitud por recrear contexto | Baja | Aceptable (~5s), mejor que bloqueo total |
| Errores durante login en reintento | Media | Capturar y loguear específicamente |
| Playwright lanza excepciones inesperadas | Baja | Try/except amplios con logging detallado |

---

## Criterios de Éxito

- [ ] Sistema NO se bloquea después de errores de navegador
- [ ] Reintentos funcionan correctamente con estado limpio
- [ ] NO requiere reinicio manual del servidor
- [ ] Logging claro indica cuándo se cierra/reabre recursos
- [ ] Memoria se libera correctamente (sin leaks)
- [ ] Tiempo de reintento aceptable (<10s por intento)

---

## Próximos Pasos Después de Implementación

1. **Monitorear** en producción por 1-2 semanas
2. **Recopilar métricas**: tasa de éxito de reintentos, tiempo promedio
3. **Evaluar** si necesita optimización adicional
4. **Considerar** implementar Opción D (híbrida) si se necesita más velocidad

---

## Notas de Implementación

- Mantener compatibilidad con configuración existente (`ConfigExtraccionMasiva`)
- No cambiar interfaz pública del `ExtractorMasivo`
- Preservar historial de intentos en `SesionExtraccion`
- Callbacks de progreso deben seguir funcionando

---

## Referencias

- Ver `PLAN_SOLUCION_BLOQUEO_REINTENTOS.md` para análisis detallado y código completo
- Ver `PLAN_MEJORAS_ORDENACION_Y_TIMEOUTS.md` para correcciones de timeouts relacionadas
