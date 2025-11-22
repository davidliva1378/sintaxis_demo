# 🚀 HOJA DE RUTA V2 PARA AGENTES: Extracción Masiva con Filtrado

**Versión:** 2.0 (Con FASE 2 de Filtrado)
**Tarea:** Completar implementación de extracción masiva con filtrado y selección
**Estado actual:** 30% completado
**Objetivo:** 100% funcional
**Tiempo estimado:** 18-24 horas

---

## ⚡ INICIO RÁPIDO (5 minutos)

### 1. ¿Qué cambió desde V1?

Se descubrió una **FASE 2 CRÍTICA** que no existía:

```
V1: Extracción → Procesamiento de TODOS
V2: Extracción → FILTRADO Y SELECCIÓN → Procesamiento de SELECCIONADOS
                   ↑ NUEVA FASE CRÍTICA
```

### 2. ¿Qué debo hacer ahora?

Implementar 18 tareas en 3 fases:
1. **Backend Listado** (2-3h): Endpoints para obtener y procesar seleccionados
2. **Frontend Filtrado** (8-10h): UI completa de filtrado y selección ⭐ CRÍTICA
3. **Procesamiento Selectivo** (6-8h): Lógica real de procesamiento

### 3. ¿Cuál es la fase más importante?

**FASE 2: Frontend de Filtrado** (8-10 horas)

Sin esta fase, el usuario no puede elegir qué expedientes procesar, haciendo el sistema poco útil para volúmenes grandes (2000+ expedientes).

### 4. ¿Qué archivos tocaré?

**Backend (3 archivos):**
- ✏️ `presentation/api/rest/routers/extraccion_masiva.py` - 2 endpoints nuevos
- ✏️ `application/use_cases/extraccion_masiva_use_case.py` - 1 método nuevo
- ✏️ `extraccion_masiva/gestor_batch.py` - Implementar lógica real

**Frontend (4 archivos nuevos + 1 modificado):**
- 🆕 `components/expedientes/FiltradoExpedientesDialog.tsx` - Componente principal
- 🆕 `components/expedientes/TablaVirtualizada.tsx` - Tabla con virtualización
- 🆕 `hooks/useFiltrosExpedientes.ts` - Lógica de filtros
- 🆕 `hooks/useSeleccionMasiva.ts` - Lógica de selección
- ✏️ `components/expedientes/ExtraccionMasivaDialog.tsx` - Agregar etapa filtrado

---

## 📋 PLAN EN 3 NIVELES (Actualizado)

### NIVEL 1: MVP CON FILTRADO BÁSICO (10-13 horas) ⭐ RECOMENDADO

**Objetivo:** Sistema funcional con filtrado y selección

#### Tareas críticas:
1. **Tarea 1** - Endpoint `/listado` [2h]
2. **Tarea 2** - Endpoint `/procesar-seleccionados` [1h]
3. **Tarea 3** - Componente FiltradoExpedientesDialog [5-6h]
4. **Tarea 8** - Implementar `_procesar_expediente()` [2-3h]

**Al completar NIVEL 1:**
- ✅ Sistema extrae listado completo
- ✅ Usuario ve tabla con filtros básicos
- ✅ Usuario selecciona expedientes
- ✅ Sistema procesa SOLO seleccionados
- ✅ Expedientes guardados en sistema
- ⚠️ Sin filtros avanzados
- ⚠️ Sin virtualización optimizada

**Flujo:**
```
Extracción → Ver listado → Filtrar → Seleccionar → Procesar → Guardar
```

---

### NIVEL 2: FILTRADO COMPLETO (15-18 horas)

**Objetivo:** Sistema con todos los filtros y optimizaciones

#### Tareas adicionales:
5. **Tarea 4** - Hook de filtros (7 tipos) [2h]
6. **Tarea 5** - Selección masiva (5 funciones) [1h]
7. **Tarea 6** - Virtualización + paginación [2h]
8. **Tarea 7** - Integración completa [1h]
9. **Tarea 9-11** - Repository + Estados + DI [2-3h]

**Al completar NIVEL 2:**
- ✅ Todo lo del NIVEL 1
- ✅ 7 tipos de filtros funcionales
- ✅ 5 funciones de selección masiva
- ✅ Tabla virtualizada (sin lag con 2000+ filas)
- ✅ Paginación (50/100/200/500)
- ✅ Performance optimizada
- ⚠️ Sin tests

---

### NIVEL 3: PRODUCCIÓN (18-24 horas)

**Objetivo:** Sistema listo para producción

#### Tareas finales:
10. **Tarea 12-18** - Testing completo [2-3h]
11. Documentación actualizada

**Al completar NIVEL 3:**
- ✅ Todo lo del NIVEL 2
- ✅ Tests unitarios y de integración
- ✅ Documentación completa
- ✅ Listo para producción

---

## 🎯 RUTA RECOMENDADA

### OPCIÓN A: MVP Rápido (NIVEL 1)
**Tiempo:** 10-13 horas
**Para:** Demostración o validación del concepto

```
Tarea 1 → Tarea 2 → Tarea 3 → Tarea 8 → Prueba manual
```

### OPCIÓN B: Completo (NIVEL 2) ⭐ RECOMENDADA
**Tiempo:** 15-18 horas
**Para:** Despliegue en staging

```
Tarea 1 → Tarea 2 → Tarea 3 → Tarea 4 → Tarea 5 →
Tarea 6 → Tarea 7 → Tarea 8 → Tarea 9-11 → Prueba completa
```

### OPCIÓN C: Producción (NIVEL 3)
**Tiempo:** 18-24 horas
**Para:** Despliegue en producción

```
Todas las 18 tareas + Testing exhaustivo
```

---

## 📊 FLUJO DETALLADO CON EJEMPLOS

### FASE 1: Extracción (✅ Ya implementado)

```
Usuario: Configura extracción → Inicia
Sistema: Extrae 2,340 expedientes del PJN
Resultado: data/extraccion_masiva/listados/listado_20251107.json
```

### FASE 2: Filtrado (❌ A implementar)

```
Usuario: Ve tabla con 2,340 expedientes
       ↓
Usuario: Aplica filtros
       - Dependencia: "JUZGADO FEDERAL N°1"
       - Situación: "ACTIVO"
       - Fecha últimos 30 días
       ↓
Sistema: Filtra → Muestra 345 expedientes
       ↓
Usuario: Selecciona todos visibles (345)
       ↓
Usuario: Deselecciona manualmente 300
       ↓
Resultado: 45 expedientes seleccionados
       ↓
Usuario: Click "Procesar 45 seleccionados"
```

### FASE 3: Procesamiento Selectivo (❌ A implementar)

```
Sistema: Procesa SOLO 45 expedientes
       ↓
Para cada expediente (1/45 ... 45/45):
  - Navega al expediente en PJN
  - Extrae actuaciones (metadata)
  - Guarda en repository
  - Actualiza estado
  - Emite progreso por WebSocket
       ↓
Resultado: 45 expedientes en sistema
          2,295 NO procesados (quedan disponibles)
```

---

## 📦 CHECKLIST DE EJECUCIÓN ACTUALIZADA

### ANTES DE EMPEZAR:
- [ ] Leer `PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md` (30 min)
- [ ] Leer `RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md` (10 min)
- [ ] Entender el nuevo flujo de 3 fases
- [ ] Identificar nivel objetivo (1, 2, o 3)
- [ ] Verificar Node.js y npm instalados para frontend

### FASE 1: Backend Listado (2-3h)
- [ ] Tarea 1: Endpoint `/listado` funciona
- [ ] Tarea 2: Endpoint `/procesar-seleccionados` funciona
- [ ] Probar con curl ambos endpoints
- [ ] Commit: "feat: Agregar endpoints de listado y procesamiento selectivo"

### FASE 2: Frontend Filtrado (8-10h) ⭐
- [ ] Instalar dependencias: `@tanstack/react-virtual`
- [ ] Tarea 3: Componente FiltradoExpedientesDialog renderiza
- [ ] Tarea 4: Hook useFiltrosExpedientes funciona
- [ ] Tarea 5: Hook useSeleccionMasiva funciona
- [ ] Tarea 6: Tabla virtualizada sin lag
- [ ] Tarea 7: Integración con flujo principal
- [ ] Probar flujo completo desde frontend
- [ ] Commit: "feat: Implementar filtrado y selección de expedientes"

### FASE 3: Procesamiento (6-8h)
- [ ] Tarea 8: `_procesar_expediente()` implementado
- [ ] Tarea 9: Guardado en repository funciona
- [ ] Tarea 10: Estados actualizados
- [ ] Tarea 11: DI Container actualizado
- [ ] Probar procesamiento de 5-10 expedientes
- [ ] Commit: "feat: Implementar procesamiento selectivo de expedientes"

### TESTING (2-3h)
- [ ] Tests unitarios de filtros
- [ ] Tests de selección masiva
- [ ] Test end-to-end del flujo completo
- [ ] Verificar performance con 2000+ expedientes
- [ ] Commit: "test: Agregar tests de filtrado y procesamiento"

---

## 🔧 SNIPPETS ÚTILES ACTUALIZADOS

### Probar endpoint de listado:
```bash
# Obtener listado completo
SESSION_ID="ext_20251107_120530"
curl -s "http://localhost:8000/api/v1/expedientes/extraer/$SESSION_ID/listado" | jq '.total'
# Esperado: 2340

curl -s "http://localhost:8000/api/v1/expedientes/extraer/$SESSION_ID/listado" | jq '.metadata.dependencias | length'
# Esperado: número de dependencias únicas
```

### Probar endpoint de procesamiento selectivo:
```bash
# Procesar 3 expedientes seleccionados
curl -X POST "http://localhost:8000/api/v1/expedientes/extraer/$SESSION_ID/procesar-seleccionados" \
  -H "Content-Type: application/json" \
  -d '{
    "numeros_expedientes": ["12345/2024", "12346/2024", "12347/2024"]
  }' | jq

# Esperado: { "session_id": "...", "total_seleccionados": 3, "mensaje": "..." }
```

### Instalar dependencias frontend:
```bash
cd Sistema_v6/frontend
npm install @tanstack/react-virtual
npm install react-window react-window-infinite-loader
```

### Ver performance de filtrado:
```javascript
// En consola del navegador
console.time('filtrado');
aplicarFiltros(expedientes, filtros);
console.timeEnd('filtrado');
// Esperado: < 200ms
```

---

## 🎨 UI MOCKUP - FASE 2

### Vista del componente FiltradoExpedientesDialog:

```
┌────────────────────────────────────────────────────┐
│  📥 Extracción Masiva - Selección                  │
├────────────────────────────────────────────────────┤
│                                                     │
│  🔍 Filtros                                        │
│  ┌──────────────────────────────────────────┐    │
│  │ Fecha: [Desc▼] [__/__/____] [__/__/____] │    │
│  │ Dependencia: [Todas ▼]  Situación:[Todas▼]│    │
│  │ Buscar: [______________] 🔎              │    │
│  │ [Limpiar] [Aplicar]                       │    │
│  └──────────────────────────────────────────┘    │
│                                                     │
│  ☑️ Selección                                      │
│  ┌──────────────────────────────────────────┐    │
│  │ ☐ Todos visibles  ☐ Todos (2,340)        │    │
│  │ 📊 45 de 2,340 seleccionados              │    │
│  └──────────────────────────────────────────┘    │
│                                                     │
│  📋 Tabla - 100 por página                         │
│  ┌─────────────────────────────────────────────┐ │
│  │☐│ Número    │ Carátula      │ Depend.│ Sit.│ │
│  │☑│12345/2024│Juan v. Pedro  │Juz. 1 │Activo││ │
│  │☑│12346/2024│María v. José  │Juz. 2 │Activo││ │
│  │☐│12347/2024│Pedro v. Ana   │Juz. 1 │Arch. ││ │
│  │   ... (solo visible, virtualizado)          │ │
│  │ ◀ [1] 2 3 ... 23 ▶   Total: 2,340          │ │
│  └─────────────────────────────────────────────┘ │
│                                                     │
│  [Cancelar] [← Volver] [Procesar 45 →]           │
└────────────────────────────────────────────────────┘
```

---

## 🚨 ERRORES COMUNES Y SOLUCIONES (Actualizado)

### Error 1: Tabla se congela con 2000+ filas
**Síntoma:** Lag al scrollear, UI no responde
**Solución:** Implementar virtualización con @tanstack/react-virtual
```bash
npm install @tanstack/react-virtual
```

### Error 2: Filtros no aplican
**Síntoma:** Cambiar filtro no actualiza tabla
**Solución:** Verificar useMemo en hook de filtros
```typescript
const expedientesFiltrados = useMemo(() => {
  return aplicarFiltros(expedientes, filtros);
}, [expedientes, filtros]); // ← Dependencias correctas
```

### Error 3: Selección no persiste al cambiar página
**Síntoma:** Seleccionados desaparecen al paginar
**Solución:** Usar Set para mantener selección global
```typescript
const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set());
// Set mantiene selección a través de páginas
```

### Error 4: Endpoint no encuentra listado
**Síntoma:** 404 "Listado no encontrado"
**Solución:** Verificar que ExtractorMasivo guarda listado_path en sesión
```python
self._emit("fin_listado", {
    "listado_path": str(listado_path),  # ← Agregar esto
})
```

### Error 5: Procesa todos en vez de seleccionados
**Síntoma:** Se procesan 2000+ en vez de 45
**Solución:** Verificar filtrado en backend
```python
# Filtrar solo los seleccionados
expedientes_seleccionados = [
    exp for exp in listado_completo
    if exp.get("numero") in numeros_set
]
```

---

## 📊 SEGUIMIENTO DE PROGRESO

### Template de registro:

```markdown
## Sesión 1: [FECHA]
- Nivel objetivo: [1/2/3]
- Fase: [1/2/3]
- Tareas completadas: [1, 2]
- Tareas en progreso: [3]
- Tiempo invertido: [4 horas]
- Bloqueantes: [Ninguno]
- Próximos pasos: [Completar Tarea 3]
- Notas: [...]

### Pruebas realizadas:
- [✅] Endpoint /listado funciona
- [✅] Retorna 2,340 expedientes
- [⏳] Componente FiltradoExpedientesDialog 50% completo
```

---

## 🎯 PRÓXIMO PASO INMEDIATO

### SI EMPIEZAS AHORA:

1. **Leer documentación (30 min):**
   ```bash
   cat PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md | less
   cat RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md | less
   ```

2. **Entender el nuevo flujo (10 min):**
   - Ver diagrama de 3 fases
   - Entender por qué FASE 2 es crítica

3. **Decidir nivel (5 min):**
   - Nivel 1: MVP (10-13h)
   - Nivel 2: Completo (15-18h) ⭐
   - Nivel 3: Producción (18-24h)

4. **Empezar con Tarea 1 (2h):**
   ```bash
   # Abrir archivo
   nano Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py

   # Agregar endpoint GET /{session_id}/listado
   # Ver código en PLAN V2

   # Probar
   curl http://localhost:8000/api/v1/expedientes/extraer/ext_20251107_120530/listado
   ```

---

## ✅ CRITERIOS DE ÉXITO POR NIVEL

### NIVEL 1 COMPLETO cuando:
- [ ] Endpoint `/listado` retorna 2000+ expedientes
- [ ] Endpoint `/procesar-seleccionados` funciona
- [ ] FiltradoExpedientesDialog renderiza tabla
- [ ] Usuario puede seleccionar expedientes
- [ ] Solo seleccionados se procesan
- [ ] Expedientes guardados en repository

### NIVEL 2 COMPLETO cuando:
- [ ] Todo lo de NIVEL 1
- [ ] 7 filtros funcionan correctamente
- [ ] Selección masiva responsive
- [ ] Tabla virtualizada (sin lag con 2000+)
- [ ] Paginación fluida
- [ ] Contador actualiza en tiempo real

### NIVEL 3 COMPLETO cuando:
- [ ] Todo lo de NIVEL 2
- [ ] Tests unitarios > 80% coverage
- [ ] Tests de integración pasan
- [ ] Performance validada (<200ms filtros)
- [ ] Documentación actualizada

---

## 📚 RECURSOS ADICIONALES

### Documentación de librerías:
- [@tanstack/react-virtual](https://tanstack.com/virtual/v3) - Virtualización
- [Material-UI Autocomplete](https://mui.com/material-ui/react-autocomplete/) - Multi-select
- [date-fns](https://date-fns.org/) - Manejo de fechas

### Ejemplos de código:
```typescript
// Ejemplo de filtro por rango de fechas
const filtrarPorFechas = (expedientes: Expediente[], desde: Date, hasta: Date) => {
  return expedientes.filter(exp => {
    const fecha = parseDate(exp.fecha_inicio);
    return fecha >= desde && fecha <= hasta;
  });
};

// Ejemplo de selección masiva
const seleccionarPorCondicion = (
  expedientes: Expediente[],
  condicion: (exp: Expediente) => boolean
) => {
  return expedientes.filter(condicion).map(exp => exp.numero);
};
```

---

## 🏁 RESUMEN ULTRA-RÁPIDO

### ¿Qué cambió?
Se agregó FASE 2: Filtrado y selección (8-10h)

### ¿Qué hacer?
18 tareas en 3 fases (18-24h total)

### ¿Por dónde empezar?
Tarea 1: Endpoint `/listado` (2h)

### ¿Qué es más importante?
FASE 2: Frontend de filtrado (8-10h)

### ¿Cuánto tarda el MVP?
10-13 horas (Nivel 1)

---

**🚀 ¡TODO LISTO PARA IMPLEMENTAR!**

**Pregunta clave:** ¿Qué nivel quieres alcanzar?
- Rápido: NIVEL 1 (10-13h)
- Completo: NIVEL 2 (15-18h) ⭐ Recomendado
- Producción: NIVEL 3 (18-24h)

**Siguiente acción:** Empezar con Tarea 1 del PLAN V2.

---

**Fecha:** 2025-11-07
**Versión:** 2.0
**Estado:** ✅ LISTA PARA EJECUCIÓN
