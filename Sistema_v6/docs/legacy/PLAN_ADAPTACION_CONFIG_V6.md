# 🚀 PLAN DE ADAPTACIÓN: Configuración v5.1.1 → Sistema_v6

**Rama objetivo:** `claude/v6-testing-011CUquXfHQF1jAeAMXMPexk`
**Fecha inicio:** 2025-11-06
**Estado:** 🟡 Pendiente de inicio
**Basado en:** ANALISIS_CONFIGURACION_V5.1.1.md (Sección 7.1)

---

## ⚠️ ADVERTENCIA IMPORTANTE

Antes de iniciar, revisar **ANALISIS_IMPACTO_CONFIGURACION_V6.md** que indica:

> **Sistema_v6 ya tiene su propio sistema de configuración moderno (Pydantic Settings + .env)**
>
> Este plan debe usarse SOLO para:
> - Verificar que v6 tiene equivalencias funcionales
> - Identificar valores específicos a ajustar en `.env`
> - NO para copiar código/estructura directamente de v5

---

## 📊 Resumen Ejecutivo

### Objetivo

Adaptar configuración de Sistema_v6 basándose en análisis de v5.1.1, pero **respetando la arquitectura Clean Architecture** ya existente en v6.

### Alcance

- ✅ **En alcance:** Valores de configuración, variables de entorno, estructura de directorios de datos
- ❌ **Fuera de alcance:** Copiar módulos completos, reemplazar sistema Pydantic Settings, cambiar arquitectura

### Estrategia

**Adaptación selectiva** en lugar de copia directa:
1. Verificar qué existe en v6
2. Identificar gaps funcionales (no arquitectónicos)
3. Adaptar solo lo necesario al sistema de v6

---

## 📋 CHECKLIST DE ADAPTACIÓN

### Fase 0: Verificación Inicial (PRE-REQUISITO)

**ANTES de cualquier cambio, verificar estado actual de Sistema_v6:**

- [ ] **TAREA 0.1:** Verificar que Sistema_v6 existe en la rama
  - Comando: `ls -la Sistema_v6/`
  - Esperado: Estructura Clean Architecture presente

- [ ] **TAREA 0.2:** Verificar sistema de configuración actual
  - Archivo: `Sistema_v6/infrastructure/config/settings.py`
  - Archivo: `Sistema_v6/.env.example`
  - Esperado: Sistema Pydantic Settings funcional

- [ ] **TAREA 0.3:** Revisar documentación de v6 existente
  - Archivo: `PLAN_ADAPTACION_V6_REFORMULADA.md`
  - Archivo: `REPORTE_COMPARACION_V6_VS_V5.1.1.md`
  - Objetivo: Entender estado actual (completado 100%)

- [ ] **TAREA 0.4:** Verificar que NO hay código de v5 en Sistema_v6
  - Buscar: `Sistema_v6/pjn/config.py` (no debe existir)
  - Buscar: `Sistema_v6/config/sistema.json` (no debe existir)
  - Esperado: Solo estructura de v6

---

### Fase 1: Estructura de Directorios de Datos

**Objetivo:** Crear directorios de workspace según estructura de v5.1.1

- [ ] **TAREA 1.1:** Verificar estructura actual de Sistema_v6
  ```bash
  find Sistema_v6 -maxdepth 2 -type d | sort
  ```

- [ ] **TAREA 1.2:** Identificar directorios faltantes comparando con v5.1.1
  - v5.1.1 tiene: `var/cache`, `var/log`, `var/monitor`
  - v5.1.1 tiene: `workspace/inicial`, `workspace/expedientes`, etc.
  - v6 tiene: Verificar equivalentes

- [ ] **TAREA 1.3:** Crear directorios de datos necesarios (si faltan)
  ```bash
  cd Sistema_v6
  mkdir -p data/cache data/logs data/monitor
  mkdir -p data/expedientes data/downloads data/reportes
  ```
  **NOTA:** v6 usa `data/` en lugar de `var/` y `workspace/`

- [ ] **TAREA 1.4:** Documentar estructura creada
  - Actualizar README de v6 con estructura de directorios
  - Explicar equivalencias con v5.1.1

**Resultado esperado:** Directorios de datos creados y documentados, respetando convenciones de v6.

---

### Fase 2: Variables de Entorno

**Objetivo:** Asegurar que `.env` de v6 tiene todas las variables equivalentes a v5.1.1

- [ ] **TAREA 2.1:** Analizar variables de v5.1.1
  - Revisar: ANALISIS_CONFIGURACION_V5.1.1.md sección 4
  - Listar: SISTEMA_*, MCP_*, PJN_*
  - Total: ~40 variables documentadas

- [ ] **TAREA 2.2:** Revisar `.env.example` actual de v6
  ```bash
  cat Sistema_v6/.env.example
  ```

- [ ] **TAREA 2.3:** Identificar variables faltantes en v6
  - Comparar con listado de v5.1.1
  - Priorizar: Variables críticas vs opcionales

- [ ] **TAREA 2.4:** Agregar variables faltantes a `.env.example` de v6
  - **Solo si son funcionalmente necesarias**
  - Adaptar nombres al estilo de v6 (sin prefijo SISTEMA_)
  - Documentar cada variable agregada

- [ ] **TAREA 2.5:** Extender `Settings` class si es necesario
  ```python
  # En Sistema_v6/infrastructure/config/settings.py
  # Agregar campos Pydantic para nuevas variables
  ```

**Resultado esperado:** `.env.example` actualizado con variables equivalentes, adaptadas a v6.

---

### Fase 3: Configuración de Monitoreo

**Objetivo:** Adaptar configuración de intervalos y horarios de monitoreo de v5.1.1

- [ ] **TAREA 3.1:** Revisar config de monitor en v5.1.1
  - `intervalos_laboral_expedientes`: 10 min
  - `intervalos_laboral_entradas`: 15 min
  - `dias_laborales`: ["lunes", "martes", "jueves", "viernes"]
  - `hora_inicio`: "08:00", `hora_fin`: "18:00"

- [ ] **TAREA 3.2:** Verificar equivalente actual en v6
  ```bash
  grep -i "monitor" Sistema_v6/.env.example
  ```

- [ ] **TAREA 3.3:** Decidir estrategia de adaptación
  - ✅ Opción A: Usar `MONITOR_INTERVAL` simple de v6 (ya existe)
  - ⚠️ Opción B: Agregar horarios laborales complejos de v5.1.1

- [ ] **TAREA 3.4:** Si se elige Opción B, implementar en Settings
  ```python
  class Settings(BaseSettings):
      # Monitor - Horarios laborales (de v5.1.1)
      dias_laborales: list[str] = ["lunes", "martes", "miercoles", "jueves", "viernes"]
      hora_inicio: str = "08:00"
      hora_fin: str = "18:00"
      intervalos_laboral: int = 10
      intervalos_no_laboral: int = 60
  ```

- [ ] **TAREA 3.5:** Actualizar lógica de monitoreo para usar nuevas variables
  - Ubicación probable: `Sistema_v6/application/services/`
  - Adaptar scheduler para respetar horarios

**Resultado esperado:** Configuración de monitoreo de v6 equivalente a v5.1.1 en funcionalidad.

---

### Fase 4: Configuración de MCP Server

**Objetivo:** Verificar y ajustar configuración del servidor MCP

- [ ] **TAREA 4.1:** Verificar que MCP server existe en v6
  ```bash
  find Sistema_v6 -name "*mcp*" -type f
  ```

- [ ] **TAREA 4.2:** Comparar config de MCP v5.1.1 vs v6
  - v5.1.1: `mcp_server/config.py` con `MCPConfig` class
  - v6: Verificar equivalente

- [ ] **TAREA 4.3:** Revisar variables MCP en v5.1.1
  ```bash
  # De ANALISIS_CONFIGURACION_V5.1.1.md:
  MCP_WORKSPACE_PATH
  MCP_SERVER_PORT=8000
  MCP_ENABLE_PDF_EXTRACTION=true
  MCP_AUTH_TOKENS
  ```

- [ ] **TAREA 4.4:** Asegurar que `.env` de v6 tiene equivalentes
  - Agregar si faltan
  - Documentar uso

- [ ] **TAREA 4.5:** Verificar que código MCP en v6 lee estas variables
  - Si no existe, es un gap funcional real
  - Considerar si se necesita (v6 puede no usar MCP)

**Resultado esperado:** Configuración MCP documentada, agregada solo si v6 usa MCP.

---

### Fase 5: Dependencias Python

**Objetivo:** Verificar compatibilidad de dependencias

- [ ] **TAREA 5.1:** Comparar `requirements.txt` de v5.1.1 vs v6
  ```bash
  diff Sistema_v5/requirements.txt Sistema_v6/requirements.txt
  ```

- [ ] **TAREA 5.2:** Identificar dependencias críticas de v5.1.1
  - playwright==1.50.0 ✅ (debe estar en v6)
  - APScheduler==3.11.0 ✅
  - mcp>=1.0.0 ⚠️ (verificar si v6 usa MCP)
  - pdfplumber>=0.11.0 ✅

- [ ] **TAREA 5.3:** Verificar que v6 tiene dependencias equivalentes
  - v6 usa `pyproject.toml` además de `requirements.txt`
  - Revisar ambos archivos

- [ ] **TAREA 5.4:** Documentar diferencias justificadas
  - v6 tiene: SQLAlchemy, FastAPI (arquitectura diferente)
  - v5.1.1 tiene: Flask (opcional, no core)
  - Diferencias son por diseño, no gaps

- [ ] **TAREA 5.5:** Solo agregar dependencias si hay gap funcional real
  - NO agregar Flask a v6 (usa FastAPI)
  - NO agregar dependencias legacy

**Resultado esperado:** Dependencias de v6 verificadas, documentar que son equivalentes.

---

### Fase 6: Constantes del Sistema

**Objetivo:** Verificar que v6 tiene constantes equivalentes a v5.1.1

- [ ] **TAREA 6.1:** Revisar `Sistema_v5/pjn/constants.py`
  - URL_CONSULTAS del PJN
  - Motivos de finalización
  - Campos de expedientes
  - Timeouts y límites

- [ ] **TAREA 6.2:** Buscar equivalente en v6
  ```bash
  find Sistema_v6 -name "*constants*" -o -name "*config*" | xargs grep -l "URL_CONSULTAS"
  ```

- [ ] **TAREA 6.3:** Si no existe, verificar dónde están definidas en v6
  - Pueden estar en Settings
  - Pueden estar en módulos de dominio
  - v6 puede usar enfoque diferente

- [ ] **TAREA 6.4:** Documentar ubicación de constantes en v6
  - Crear mapping: Constante v5.1.1 → Ubicación en v6
  - Agregar a documentación

- [ ] **TAREA 6.5:** Solo crear archivo de constantes si no existe alternativa
  - Si v6 usa Settings para todo, no crear constants.py
  - Respetar arquitectura de v6

**Resultado esperado:** Constantes localizadas en v6 o agregadas según arquitectura de v6.

---

### Fase 7: Testing y Validación

**Objetivo:** Verificar que adaptación no rompió funcionalidad existente

- [ ] **TAREA 7.1:** Revisar tests existentes en Sistema_v6
  ```bash
  ls -la Sistema_v6/tests/
  pytest Sistema_v6/tests/ --collect-only
  ```

- [ ] **TAREA 7.2:** Ejecutar suite de tests actual
  ```bash
  cd Sistema_v6
  pytest tests/ -v
  ```
  - Documentar estado: ¿Pasaban antes? ¿Pasan ahora?

- [ ] **TAREA 7.3:** Verificar que nueva configuración carga correctamente
  ```python
  from Sistema_v6.infrastructure.config import Settings
  settings = Settings()  # Debe cargar sin errores
  print(settings.model_dump())  # Ver valores cargados
  ```

- [ ] **TAREA 7.4:** Probar creación de directorios
  ```python
  # Si se implementó método similar a v5.1.1:
  # settings.crear_directorios()
  # O manualmente: mkdir según lo definido
  ```

- [ ] **TAREA 7.5:** Smoke test de funcionalidad principal
  - Autenticación funciona
  - Scraping básico funciona
  - Monitoreo puede configurarse

**Resultado esperado:** Tests pasan, configuración carga, funcionalidad básica verificada.

---

### Fase 8: Documentación

**Objetivo:** Documentar todos los cambios realizados

- [ ] **TAREA 8.1:** Actualizar README de Sistema_v6
  - Agregar sección de configuración
  - Documentar variables de entorno
  - Explicar estructura de directorios

- [ ] **TAREA 8.2:** Crear guía de migración desde v5.1.1
  - Documento: `Sistema_v6/docs/MIGRACION_DESDE_V5.md`
  - Tabla de equivalencias: v5.1.1 → v6
  - Diferencias arquitectónicas explicadas

- [ ] **TAREA 8.3:** Documentar decisiones de diseño
  - Por qué no se copió X de v5.1.1
  - Qué se adaptó y por qué
  - Qué se decidió no incluir y justificación

- [ ] **TAREA 8.4:** Crear changelog de adaptación
  - Listar todos los cambios realizados
  - Versión antes/después
  - Impacto en funcionalidad

- [ ] **TAREA 8.5:** Actualizar `.env.example` con comentarios
  - Cada variable debe tener comentario explicativo
  - Indicar cuáles son equivalentes a v5.1.1

**Resultado esperado:** Documentación completa y clara para futuros desarrolladores.

---

## 🎯 Priorización de Tareas

### Alta Prioridad (Crítico)

1. **Fase 0:** Verificación inicial - DEBE completarse primero
2. **Fase 2:** Variables de entorno - Core de la configuración
3. **Fase 7:** Testing - Validar que nada se rompió

### Media Prioridad (Importante)

4. **Fase 1:** Directorios - Necesarios para operación
5. **Fase 3:** Monitoreo - Feature principal del sistema
6. **Fase 6:** Constantes - Necesarias para scraping

### Baja Prioridad (Opcional)

7. **Fase 4:** MCP Server - Solo si v6 lo usa
8. **Fase 5:** Dependencias - Ya deben estar correctas
9. **Fase 8:** Documentación - Importante pero no bloquea funcionalidad

---

## ⚠️ Precauciones y Checkpoints

### Antes de Cada Fase

- [ ] **Checkpoint:** Crear commit de estado actual
- [ ] **Checkpoint:** Verificar que tests pasan (si existen)
- [ ] **Checkpoint:** Backup de archivos que se modificarán

### Durante Cada Fase

- [ ] **Precaución:** NO copiar archivos completos de v5 a v6
- [ ] **Precaución:** NO reemplazar sistema Pydantic Settings
- [ ] **Precaución:** Consultar ANALISIS_IMPACTO antes de cambios grandes

### Después de Cada Fase

- [ ] **Verificación:** Tests siguen pasando
- [ ] **Verificación:** Configuración sigue cargando
- [ ] **Verificación:** Commit de cambios con mensaje descriptivo

---

## 📈 Métricas de Éxito

### Criterios de Completitud

- ✅ **Funcional:** Sistema_v6 tiene configuración equivalente a v5.1.1
- ✅ **No regresión:** Tests de v6 siguen pasando
- ✅ **Documentado:** Cambios están documentados
- ✅ **Mantenible:** Respeta arquitectura de v6

### Criterios de NO Éxito (Evitar)

- ❌ Sistema v6 se parece a v5.1.1 en estructura (debe mantener Clean Architecture)
- ❌ Hay código duplicado entre v5 y v6
- ❌ Tests de v6 fallan después de adaptación
- ❌ Sistema Pydantic Settings fue reemplazado por JSON configs

---

## 🔄 Plan de Rollback

Si algo sale mal en cualquier fase:

1. **Revertir commit:** `git reset --hard <commit-anterior>`
2. **Revisar logs:** Identificar qué causó el problema
3. **Consultar documentación:** ANALISIS_IMPACTO_CONFIGURACION_V6.md
4. **Replantear enfoque:** Quizás la adaptación no es necesaria
5. **Pedir ayuda:** Revisar con equipo o documentación adicional

---

## 📝 Log de Ejecución

### Sesión 1: [FECHA]

**Agente:** [Nombre/ID]
**Fase completada:** [Número]
**Tareas completadas:** [Lista]
**Bloqueadores encontrados:** [Descripción]
**Decisiones tomadas:** [Lista]
**Próximos pasos:** [Plan]

---

## 🎓 Notas para Agentes

### Antes de Iniciar

1. **LEER OBLIGATORIO:**
   - ANALISIS_CONFIGURACION_V5.1.1.md (completo)
   - ANALISIS_IMPACTO_CONFIGURACION_V6.md (sección "Lo que NO hacer")
   - Este plan (completo)

2. **VERIFICAR:**
   - Que estás en la rama correcta: `claude/v6-testing-011CUquXfHQF1jAeAMXMPexk`
   - Que Sistema_v6 existe y está completo
   - Que entiendes arquitectura Clean de v6

3. **RECORDAR:**
   - NO copiar código directamente
   - ADAPTAR, no replicar
   - RESPETAR arquitectura de v6
   - DOCUMENTAR decisiones

### Durante la Ejecución

- Usar **TodoWrite** para trackear progreso de cada tarea
- Hacer **commits frecuentes** con mensajes descriptivos
- **Consultar** análisis de impacto ante dudas
- **Preguntar** antes de hacer cambios grandes

### Después de Completar

- Actualizar este documento con resultados
- Crear resumen ejecutivo de cambios
- Documentar lecciones aprendidas
- Preparar handoff para siguiente agente (si aplica)

---

**Última actualización:** 2025-11-06
**Estado del plan:** ✅ Listo para iniciar
**Próximo paso:** Ejecutar Fase 0 (Verificación Inicial)
