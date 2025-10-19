# Guía de Implementación: Sesión Persistente para Monitor PJN

> **Objetivo**: Mantener el navegador y la sesión de login abiertos entre verificaciones para mejorar el rendimiento del monitor.

---

## 📊 Beneficios Esperados

- **Velocidad**: 60-75% más rápido en verificaciones subsecuentes
- **Eficiencia**: Solo 1 login por día (vs. 96+ logins/día actualmente)
- **Carga del servidor**: Reducción drástica de requests de autenticación
- **Tiempo ahorrado**: ~48 minutos/día en un monitor con intervalos de 15 min

---

## 🎯 Arquitectura Propuesta

### Estado Actual
```
Verificación → Abrir navegador → Login → Extraer → Cerrar navegador
Verificación → Abrir navegador → Login → Extraer → Cerrar navegador
Verificación → Abrir navegador → Login → Extraer → Cerrar navegador
```

### Estado Objetivo
```
Verificación 1 → Abrir navegador → Login → Extraer → MANTENER ABIERTO
Verificación 2 → Verificar sesión → Extraer → MANTENER ABIERTO
Verificación 3 → Verificar sesión → Extraer → MANTENER ABIERTO
...
Al detener → Cerrar navegador
```

---

## 📋 Checklist de Tareas

### Fase 1: Preparación y Análisis (30-60 min)

- [ ] **1.1** Revisar código actual de autenticación
  - Archivo: `pjn/scraping/base.py`
  - Función: `obtener_pagina_autenticada()`
  - Entender flujo actual de login/logout

- [ ] **1.2** Revisar código del monitor
  - Archivo: `pjn/monitor/core.py`
  - Métodos: `_verificar_entradas_internal()` y `_verificar_expedientes_internal()`
  - Identificar puntos de integración

- [ ] **1.3** Diseñar estructura de clases
  - Crear diagrama de clases propuesto
  - Definir interfaces y métodos necesarios

- [ ] **1.4** Crear branch de desarrollo
  ```bash
  git checkout -b feature/sesion-persistente
  ```

---

### Fase 2: Implementación del Session Manager (2-3 horas)

- [ ] **2.1** Crear clase `SessionManager`
  - **Archivo**: `pjn/scraping/session_manager.py` (NUEVO)
  - **Responsabilidades**:
    - Mantener instancias de browser, context y page
    - Crear sesión inicial
    - Verificar validez de sesión
    - Renovar sesión expirada
    - Cerrar sesión limpiamente

- [ ] **2.2** Implementar método `create_session()`
  ```python
  async def create_session(self, headless: bool = True) -> tuple[Browser, BrowserContext, Page]:
      """Crea una nueva sesión de navegador."""
      # Inicializar Playwright
      # Crear browser
      # Crear context con cookies persistentes
      # Crear page
      # Hacer login
      # Retornar (browser, context, page)
  ```

- [ ] **2.3** Implementar método `is_session_valid()`
  ```python
  async def is_session_valid(self) -> bool:
      """Verifica si la sesión actual sigue válida."""
      # Verificar que page existe
      # Verificar que no hay error 401/403
      # Verificar que elementos de login no están presentes
      # Opcional: hacer request de prueba
  ```

- [ ] **2.4** Implementar método `ensure_session()`
  ```python
  async def ensure_session(self) -> Page:
      """Asegura que hay una sesión válida, creándola si es necesario."""
      # Si no hay sesión, crear una nueva
      # Si hay sesión, verificar validez
      # Si sesión inválida, renovar
      # Retornar page activa
  ```

- [ ] **2.5** Implementar método `close_session()`
  ```python
  async def close_session(self) -> None:
      """Cierra la sesión persistente limpiamente."""
      # Cerrar page
      # Cerrar context
      # Cerrar browser
      # Limpiar referencias
  ```

- [ ] **2.6** Implementar manejo de cookies
  ```python
  async def save_cookies(self, filepath: str) -> None:
      """Guarda cookies de la sesión."""

  async def load_cookies(self, filepath: str) -> None:
      """Carga cookies guardadas."""
  ```

---

### Fase 3: Integración con MonitorPJN (1-2 horas)

- [ ] **3.1** Modificar `__init__()` de MonitorPJN
  - **Archivo**: `pjn/monitor/core.py`
  ```python
  def __init__(self, config: MonitorConfig):
      self.config = config
      self.session_manager = SessionManager()  # ← NUEVO
      # ... resto del código existente
  ```

- [ ] **3.2** Modificar `_verificar_entradas_internal()`
  - **ANTES**:
    ```python
    async with obtener_pagina_autenticada(headless=...) as (page, _, _):
        # extracción
    ```
  - **DESPUÉS**:
    ```python
    page = await self.session_manager.ensure_session(headless=self.config.headless)
    # extracción (sin cerrar page)
    ```

- [ ] **3.3** Modificar `_verificar_expedientes_internal()`
  - Mismo cambio que entradas

- [ ] **3.4** Agregar método `stop()` al monitor
  ```python
  async def stop(self) -> None:
      """Detiene el monitor y cierra la sesión."""
      await self.session_manager.close_session()
  ```

- [ ] **3.5** Modificar scheduler para llamar `stop()` al salir
  - **Archivo**: `ejecutar_monitor_statusbar.py` (o similar)
  - Asegurar que llama `await monitor.stop()` al detener

---

### Fase 4: Configuración (30 min)

- [ ] **4.1** Agregar opción de configuración
  - **Archivo**: `configuracion/monitor/shared_config.py`
  ```python
  @dataclass
  class MonitorSharedConfig:
      # ... campos existentes ...
      sesion_persistente: bool = True  # ← NUEVO
      sesion_timeout_minutos: int = 60  # ← NUEVO
  ```

- [ ] **4.2** Agregar validación
  ```python
  def __post_init__(self):
      # ... validaciones existentes ...
      if self.sesion_timeout_minutos < 5 or self.sesion_timeout_minutos > 480:
          raise ValueError("sesion_timeout debe estar entre 5 y 480 minutos")
  ```

- [ ] **4.3** Actualizar archivos de configuración JSON
  - `config/monitor.json`
  - `scripts/config/sistema.json`
  ```json
  {
    "sesion_persistente": true,
    "sesion_timeout_minutos": 60
  }
  ```

- [ ] **4.4** Agregar widgets al GUI
  - **Archivo**: `configuracion/gui/config_form.py`
  - Agregar checkbox para "Sesión persistente"
  - Agregar spinbox para "Timeout de sesión (minutos)"

---

### Fase 5: Manejo de Errores (1-2 horas)

- [ ] **5.1** Implementar detección de sesión expirada
  ```python
  class SessionExpiredError(Exception):
      """Lanzada cuando la sesión ha expirado."""
      pass
  ```

- [ ] **5.2** Agregar retry logic con renovación de sesión
  ```python
  async def _verificar_entradas_internal(self):
      max_retries = 2
      for attempt in range(max_retries):
          try:
              page = await self.session_manager.ensure_session()
              # extracción
              break
          except SessionExpiredError:
              if attempt < max_retries - 1:
                  await self.session_manager.close_session()
                  continue
              raise
  ```

- [ ] **5.3** Agregar logging detallado
  ```python
  logger.info("🔄 Creando nueva sesión persistente...")
  logger.info("✅ Sesión válida, reutilizando...")
  logger.warning("⚠️ Sesión expirada, renovando...")
  logger.error("❌ Error al crear sesión: {error}")
  ```

- [ ] **5.4** Implementar timeout de sesión
  ```python
  # Si la sesión tiene más de X minutos, renovar automáticamente
  if (datetime.now() - self.session_created_at).total_seconds() > self.config.sesion_timeout_minutos * 60:
      await self.close_session()
      await self.create_session()
  ```

---

### Fase 6: Testing (1-2 horas)

- [ ] **6.1** Crear tests unitarios
  - **Archivo**: `tests/test_session_manager.py` (NUEVO)
  ```python
  async def test_create_session():
      """Test de creación de sesión."""

  async def test_session_validation():
      """Test de validación de sesión."""

  async def test_session_renewal():
      """Test de renovación de sesión."""

  async def test_close_session():
      """Test de cierre de sesión."""
  ```

- [ ] **6.2** Crear tests de integración
  - **Archivo**: `tests/test_monitor_persistent_session.py` (NUEVO)
  ```python
  async def test_monitor_with_persistent_session():
      """Test del monitor usando sesión persistente."""

  async def test_multiple_verifications():
      """Test de múltiples verificaciones con misma sesión."""

  async def test_session_expiration_handling():
      """Test del manejo de expiración de sesión."""
  ```

- [ ] **6.3** Testing manual
  - Ejecutar monitor con sesión persistente activada
  - Verificar logs: debe mostrar "reutilizando sesión"
  - Dejar correr por 1 hora, verificar que no recrea sesión
  - Forzar cierre de sesión, verificar que se recupera

- [ ] **6.4** Testing de rendimiento
  - Medir tiempo de verificación CON sesión persistente
  - Medir tiempo de verificación SIN sesión persistente
  - Comparar resultados
  - Documentar mejora de rendimiento

---

### Fase 7: Optimizaciones (1 hora)

- [ ] **7.1** Implementar pool de páginas
  ```python
  # Si se necesita paralelizar entradas y expedientes
  class SessionManager:
      async def get_page(self, page_id: str) -> Page:
          """Obtiene o crea una página del pool."""
  ```

- [ ] **7.2** Implementar persistencia de cookies en disco
  ```python
  # Guardar cookies al cerrar
  # Cargar cookies al iniciar
  # Permite sobrevivir reinicios del monitor
  ```

- [ ] **7.3** Agregar métricas de sesión
  ```python
  # Tiempo de vida de la sesión
  # Número de verificaciones exitosas con la misma sesión
  # Tasa de renovaciones de sesión
  ```

- [ ] **7.4** Implementar health check de sesión
  ```python
  async def health_check(self) -> dict:
      """Retorna estado de salud de la sesión."""
      return {
          "session_active": self.page is not None,
          "session_age_minutes": (datetime.now() - self.created_at).total_seconds() / 60,
          "last_verification": self.last_verification_time,
          "verifications_count": self.verifications_count
      }
  ```

---

### Fase 8: Documentación (30 min)

- [ ] **8.1** Actualizar README.md
  - Agregar sección sobre sesión persistente
  - Explicar configuración
  - Explicar ventajas

- [ ] **8.2** Crear documentación técnica
  - **Archivo**: `docs/SESSION_MANAGER.md` (NUEVO)
  - Arquitectura de la solución
  - Diagramas de flujo
  - API documentation

- [ ] **8.3** Actualizar comentarios en código
  - Documentar todos los métodos públicos
  - Agregar ejemplos de uso

- [ ] **8.4** Crear guía de troubleshooting
  - Problemas comunes y soluciones
  - Logs a revisar
  - Comandos de diagnóstico

---

### Fase 9: Migración y Rollout (30 min)

- [ ] **9.1** Crear feature flag
  ```python
  # Permitir activar/desactivar sesión persistente
  if self.config.sesion_persistente:
      page = await self.session_manager.ensure_session()
  else:
      async with obtener_pagina_autenticada(...) as (page, _, _):
          # código legacy
  ```

- [ ] **9.2** Testing en staging/desarrollo
  - Correr por 24 horas en ambiente de prueba
  - Verificar estabilidad
  - Recolectar métricas

- [ ] **9.3** Rollout gradual
  - Activar en 1 instancia de producción
  - Monitorear por 48 horas
  - Si todo OK, activar en todas las instancias

- [ ] **9.4** Documentar rollback plan
  ```python
  # Si algo falla, desactivar sesión persistente:
  "sesion_persistente": false
  ```

---

### Fase 10: Monitoreo Post-Implementación (Ongoing)

- [ ] **10.1** Configurar alertas
  - Alerta si la sesión se renueva más de X veces por hora
  - Alerta si falla la creación de sesión

- [ ] **10.2** Recolectar métricas
  - Tiempo promedio de verificación
  - Número de renovaciones de sesión por día
  - Uptime de sesiones

- [ ] **10.3** Revisar logs semanalmente
  - Buscar patrones de errores
  - Identificar oportunidades de mejora

- [ ] **10.4** Ajustar configuración según necesidad
  - Timeout de sesión
  - Intervalo de health checks

---

## 📁 Estructura de Archivos Nuevos/Modificados

### Archivos NUEVOS a Crear
```
pjn/scraping/session_manager.py          ← SessionManager class
tests/test_session_manager.py            ← Unit tests
tests/test_monitor_persistent_session.py ← Integration tests
docs/SESSION_MANAGER.md                  ← Technical documentation
```

### Archivos a MODIFICAR
```
pjn/monitor/core.py                      ← Integración con SessionManager
pjn/scraping/base.py                     ← Posibles helpers para sesión
configuracion/monitor/shared_config.py   ← Nuevos campos de config
configuracion/gui/config_form.py         ← Widgets de GUI
config/monitor.json                      ← Valores por defecto
scripts/config/sistema.json              ← Valores por defecto
ejecutar_monitor_statusbar.py            ← Cleanup al salir
```

---

## 🧪 Criterios de Aceptación

La implementación está completa cuando:

- [x] Se puede activar/desactivar sesión persistente desde configuración
- [x] El monitor reutiliza la misma sesión entre verificaciones
- [x] La sesión se renueva automáticamente al expirar
- [x] El navegador se cierra limpiamente al detener el monitor
- [x] Los logs muestran claramente cuándo se crea/reutiliza/renueva sesión
- [x] Las pruebas automatizadas pasan al 100%
- [x] El rendimiento mejora mediblemente (>50% más rápido)
- [x] No hay memory leaks (verificado con 24h de ejecución)
- [x] La documentación está completa y actualizada

---

## 🚨 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Memory leaks por navegador persistente | Media | Alto | Implementar timeout de sesión, monitoreo de memoria |
| Sesión expira sin detección | Media | Medio | Health checks frecuentes, retry logic robusto |
| Cambios en PJN rompen validación de sesión | Baja | Alto | Feature flag para rollback rápido |
| Complejidad añadida dificulta mantenimiento | Media | Medio | Documentación exhaustiva, tests completos |

---

## 📈 Métricas de Éxito

**Antes de la implementación:**
- Tiempo promedio de verificación: ~45 segundos
- Logins por día: ~96 (cada 15 min)
- Uso de CPU: Picos frecuentes por apertura/cierre de navegador

**Después de la implementación (objetivo):**
- Tiempo promedio de verificación: ~15 segundos (66% reducción)
- Logins por día: ~24 (cada hora, por timeout)
- Uso de CPU: Más estable, sin picos frecuentes

---

## 🔗 Referencias y Recursos

### Documentación de Playwright
- [Browser Contexts](https://playwright.dev/python/docs/browser-contexts)
- [Storage State (Cookies)](https://playwright.dev/python/docs/auth#basic-shared-account-in-all-tests)
- [Session Management](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-storage-state)

### Patrones de Diseño
- [Singleton Pattern](https://refactoring.guru/design-patterns/singleton) para SessionManager
- [Object Pool Pattern](https://refactoring.guru/design-patterns/object-pool) para pool de páginas

### Best Practices
- [Managing Browser State in Automation](https://martinfowler.com/articles/browser-automation.html)
- [Async Context Managers in Python](https://peps.python.org/pep-0492/)

---

## 💡 Notas Adicionales

### Alternativas Consideradas

**Opción 1: Cookies en disco (implementada)**
- Pros: Simple, rápida
- Contras: Cookies pueden expirar

**Opción 2: Token-based auth**
- Pros: Más control sobre expiración
- Contras: PJN puede no soportarlo

**Opción 3: Headful browser siempre visible**
- Pros: Debugging fácil
- Contras: Uso de recursos, distracción visual

### Decisiones de Diseño

1. **¿Por qué un SessionManager separado?**
   - Separación de responsabilidades
   - Reutilizable en otros contextos
   - Más fácil de testear

2. **¿Por qué no usar una librería externa?**
   - Playwright ya provee las primitivas necesarias
   - Más control sobre el comportamiento
   - Menos dependencias

3. **¿Por qué feature flag?**
   - Rollback rápido si hay problemas
   - Permite testing A/B
   - Migración gradual

---

## ✅ Checklist Final Pre-Merge

Antes de mergear a main:

- [ ] Todos los tests pasan
- [ ] Code review completo
- [ ] Documentación actualizada
- [ ] Changelog actualizado
- [ ] Testing manual en staging (24h mínimo)
- [ ] Métricas de rendimiento documentadas
- [ ] Rollback plan documentado
- [ ] Equipo informado del cambio

---

**Tiempo estimado total: 8-12 horas**

**Complejidad: Media-Alta**

**Valor esperado: Alto** (mejora sustancial de rendimiento)

---

*Última actualización: 2025-10-19*
