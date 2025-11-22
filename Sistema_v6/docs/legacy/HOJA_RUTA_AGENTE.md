# 🚀 HOJA DE RUTA PARA AGENTES: Completar Extracción Masiva

**Tarea:** Completar implementación de extracción masiva de expedientes
**Estado actual:** 45% completado
**Objetivo:** 100% funcional
**Tiempo estimado:** 14-20 horas

---

## ⚡ INICIO RÁPIDO (5 minutos)

### 1. ¿Qué debo hacer?
Completar la implementación de la **lógica de procesamiento de expedientes** que actualmente solo simula con `sleep()`.

### 2. ¿Dónde está el problema?
```
Archivo: Sistema_v6/extraccion_masiva/gestor_batch.py
Línea: 252
Función: _procesar_expediente()
Problema: Solo simula con sleep(), no procesa nada real
```

### 3. ¿Cuál es el impacto?
- ❌ El sistema extrae el listado de expedientes
- ❌ Pero NO procesa las actuaciones
- ❌ NO clasifica ni detecta vencimientos
- ❌ NO guarda los expedientes en el sistema
- ❌ NO actualiza los estados

### 4. ¿Qué archivos tocaré?
**Principales:**
- ✏️ `Sistema_v6/extraccion_masiva/gestor_batch.py` (CRÍTICO)
- ✏️ `Sistema_v6/infrastructure/di_container.py`
- ✏️ `Sistema_v6/application/use_cases/extraccion_masiva_use_case.py`
- 🆕 `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py` (NUEVO)
- 🆕 `Sistema_v6/presentation/api/rest/websocket/extraccion_ws.py` (NUEVO)
- ✏️ `Sistema_v6/presentation/api/rest/main.py` (descomentar)

---

## 📋 PLAN EN 3 NIVELES

### NIVEL 1: MÍNIMO VIABLE (6-8 horas) ⭐ PRIORIDAD ALTA

**Objetivo:** Que el sistema procese y guarde expedientes

#### Tareas críticas:
1. **Tarea 2** - Implementar `_procesar_expediente()` [3-4h]
   - Extraer actuaciones del expediente
   - Retornar datos reales

2. **Tarea 4** - Integrar guardado en repository [1-2h]
   - Guardar expedientes procesados
   - Manejar errores de guardado

3. **Tarea 9** - Actualizar DI Container [0.5-1h]
   - Inyectar dependencias necesarias

**Al completar NIVEL 1:**
✅ Sistema extrae listado
✅ Sistema procesa expedientes
✅ Sistema guarda en repository
⚠️ Pero sin clasificación ni API REST

---

### NIVEL 2: FUNCIONALIDAD COMPLETA (10-12 horas)

**Objetivo:** Sistema completo con clasificación y API

#### Tareas adicionales:
4. **Tarea 3** - Integrar clasificación [2h]
   - Clasificar actuaciones
   - Detectar vencimientos

5. **Tarea 5** - Actualizar estados [1h]
   - Actualizar estados de expedientes

6. **Tarea 6** - Crear router REST [2-3h]
   - 8 endpoints funcionales

7. **Tarea 7** - Crear WebSocket handler [1h]
   - Progreso en tiempo real

8. **Tarea 8** - Habilitar router [0.5h]
   - Descomentar en main.py

**Al completar NIVEL 2:**
✅ Todo lo del NIVEL 1
✅ Clasificación de actuaciones
✅ Detección de vencimientos
✅ API REST completa
✅ WebSocket funcional
⚠️ Pero sin tests

---

### NIVEL 3: PRODUCCIÓN (14-20 horas)

**Objetivo:** Sistema listo para producción con tests

#### Tareas finales:
9. **Tarea 1** - Análisis de dependencias [1-2h]
10. **Tarea 10-14** - Testing completo [3-5h]
11. **Tarea 15** - Documentación [1h]

**Al completar NIVEL 3:**
✅ Todo lo del NIVEL 2
✅ Tests unitarios
✅ Tests de integración
✅ Documentación actualizada
✅ Listo para producción

---

## 🎯 RUTA RECOMENDADA

### OPCIÓN A: Máxima velocidad (NIVEL 1 solo)
**Tiempo:** 6-8 horas
**Para:** Demostración rápida o MVP
```
Tarea 2 → Tarea 4 → Tarea 9 → Prueba manual
```

### OPCIÓN B: Balance velocidad/calidad (NIVEL 2) ⭐ RECOMENDADA
**Tiempo:** 10-12 horas
**Para:** Despliegue en staging
```
Tarea 1 → Tarea 2 → Tarea 3 → Tarea 4 → Tarea 5 →
Tarea 9 → Tarea 6 → Tarea 7 → Tarea 8 → Prueba completa
```

### OPCIÓN C: Producción completa (NIVEL 3)
**Tiempo:** 14-20 horas
**Para:** Despliegue en producción
```
Todas las 15 tareas en orden + Testing exhaustivo
```

---

## 📦 CHECKLIST DE EJECUCIÓN

### ANTES DE EMPEZAR:
- [ ] Leer `RESUMEN_DIAGNOSTICO_Y_PLAN.md` (10 min)
- [ ] Leer secciones relevantes de `PLAN_COMPLETAR_EXTRACCION_MASIVA.md`
- [ ] Checkout a rama correcta: `sintaxis_parcial2`
- [ ] Verificar que el servidor backend funciona: `uvicorn presentation.api.rest.main:app --reload`
- [ ] Identificar nivel objetivo (1, 2, o 3)

### DURANTE LA IMPLEMENTACIÓN:
- [ ] Seguir orden de tareas recomendado
- [ ] Probar cada función antes de continuar
- [ ] Hacer commits frecuentes con mensajes descriptivos
- [ ] Actualizar TODOs en el plan
- [ ] Loggear errores para debugging

### AL FINALIZAR CADA TAREA:
- [ ] Verificar criterios de éxito de la tarea
- [ ] Ejecutar prueba manual básica
- [ ] Commit con mensaje claro
- [ ] Marcar tarea como completada en TODO list

### AL FINALIZAR EL NIVEL:
- [ ] Ejecutar prueba end-to-end del flujo
- [ ] Verificar logs del backend
- [ ] Verificar archivos generados
- [ ] Actualizar documentación de estado
- [ ] Commit final del nivel

---

## 🔧 SNIPPETS ÚTILES

### Verificar código actual:
```bash
# Ver la función problemática
sed -n '234,275p' Sistema_v6/extraccion_masiva/gestor_batch.py

# Ver TODOs en el código
grep -n "TODO" Sistema_v6/extraccion_masiva/gestor_batch.py
```

### Probar imports:
```bash
cd Sistema_v6
python -c "from extraccion_masiva.gestor_batch import GestorBatch; print('✅ OK')"
python -c "from extractor_inicial.procesamiento_expedientes import ProcesadorExpedientesInicial; print('✅ OK')"
```

### Iniciar servidor de desarrollo:
```bash
cd Sistema_v6
uvicorn presentation.api.rest.main:app --reload --port 8000 --log-level debug
```

### Ver endpoints disponibles:
```bash
curl http://localhost:8000/docs
```

### Probar extracción básica (después de implementar):
```bash
curl -X POST http://localhost:8000/api/v1/expedientes/extraer/masivo \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "umbral_errores": 10, "exportar_formatos": ["json"]}'
```

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error 1: ImportError de módulos
**Síntoma:** `ImportError: cannot import name 'ProcesadorExpedientesInicial'`
**Solución:** Verificar que el módulo existe y está en PYTHONPATH
```bash
export PYTHONPATH=/home/user/sintaXis:$PYTHONPATH
```

### Error 2: Router comentado
**Síntoma:** Endpoints no aparecen en /docs
**Solución:** Descomentar líneas en `main.py` y `routers/__init__.py`

### Error 3: TypeError al crear GestorBatch
**Síntoma:** `TypeError: __init__() got unexpected keyword argument`
**Solución:** Verificar que agregaste los nuevos parámetros al `__init__`

### Error 4: NoneType error en procesamiento
**Síntoma:** `'NoneType' object has no attribute 'guardar'`
**Solución:** Verificar que las dependencias se inyectan correctamente en DI Container

### Error 5: WebSocket no conecta
**Síntoma:** `WebSocket connection failed`
**Solución:**
1. Verificar que el router está habilitado
2. Verificar que el handler está importado correctamente
3. Verificar la URL: `ws://localhost:8000/api/v1/expedientes/extraer/{id}/ws`

---

## 📊 SEGUIMIENTO DE PROGRESO

### Actualizar después de cada sesión:

```markdown
## Registro de Progreso

### Sesión 1: [FECHA]
- Nivel objetivo: [1/2/3]
- Tareas completadas: [2, 4]
- Tareas en progreso: [3]
- Tiempo invertido: [4 horas]
- Bloqueantes: [Ninguno/Descripción]
- Próximos pasos: [Completar Tarea 3]

### Sesión 2: [FECHA]
...
```

### Métricas clave:
- **Completitud:** XX% (actualizar después de cada tarea)
- **Tests pasando:** XX/XX
- **Endpoints funcionales:** XX/8
- **Tiempo invertido:** XX horas de YY estimadas

---

## 🎓 REFERENCIAS RÁPIDAS

### Documentos principales:
1. **RESUMEN_DIAGNOSTICO_Y_PLAN.md** - Visión general
2. **PLAN_COMPLETAR_EXTRACCION_MASIVA.md** - Plan detallado
3. **INDICE_DOCUMENTACION_EXTRACCION_MASIVA.md** - Índice completo

### Código de referencia:
- `extractor_inicial/procesamiento_expedientes.py` - Ejemplo de procesamiento
- `pjn/scraping/actuaciones.py` - Extracción de actuaciones
- `configuracion/estados.py` - Gestión de estados
- `application/ports/repositories.py` - Interfaces

### Arquitectura:
```
Frontend React → API REST → Use Case → GestorBatch → ExtractorMasivo
                                ↓
                          Repository
                          Procesador
                          Estados
```

---

## ✅ CRITERIOS DE ÉXITO POR NIVEL

### NIVEL 1 COMPLETO cuando:
- [ ] `_procesar_expediente()` extrae actuaciones reales
- [ ] Expedientes se guardan en el repository
- [ ] No hay errores en logs durante extracción
- [ ] Archivos JSON se generan en `data/extraccion_masiva/`

### NIVEL 2 COMPLETO cuando:
- [ ] Todo lo de NIVEL 1
- [ ] Actuaciones clasificadas correctamente
- [ ] Vencimientos detectados
- [ ] 8 endpoints REST responden
- [ ] WebSocket envía progreso en tiempo real
- [ ] Frontend puede controlar la extracción

### NIVEL 3 COMPLETO cuando:
- [ ] Todo lo de NIVEL 2
- [ ] Tests unitarios > 80% coverage
- [ ] Tests de integración pasan
- [ ] Documentación actualizada
- [ ] Sin TODOs críticos en el código

---

## 🏁 PRÓXIMO PASO INMEDIATO

### SI NIVEL 1:
```bash
1. Leer PLAN_COMPLETAR_EXTRACCION_MASIVA.md → Tarea 2
2. Abrir: Sistema_v6/extraccion_masiva/gestor_batch.py
3. Ir a línea 234
4. Implementar lógica según pseudocódigo del plan
5. Probar con un expediente
```

### SI NIVEL 2:
```bash
1. Completar NIVEL 1 primero
2. Leer PLAN_COMPLETAR_EXTRACCION_MASIVA.md → Tareas 3-8
3. Seguir secuencialmente
```

### SI NIVEL 3:
```bash
1. Completar NIVEL 2 primero
2. Ejecutar testing exhaustivo
3. Actualizar documentación
```

---

**🚀 ¡ADELANTE! Todo está documentado y listo para implementar.**

**Pregunta clave:** ¿Qué nivel quieres alcanzar?
- **Rápido (6-8h):** NIVEL 1
- **Completo (10-12h):** NIVEL 2 ⭐ Recomendado
- **Producción (14-20h):** NIVEL 3

**Siguiente acción:** Leer `RESUMEN_DIAGNOSTICO_Y_PLAN.md` y empezar con Tarea 2.

---

**Fecha:** 2025-11-07
**Versión:** 1.0
**Estado:** ✅ LISTA PARA EJECUCIÓN
