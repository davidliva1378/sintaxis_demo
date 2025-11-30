# 🖥️ Reporte de Revisión de Frontend

**Fecha**: 2025-11-29
**Versión**: 6.0.0
**Estado General**: 🟢 BUENO (Con áreas de mejora arquitectónica)

---

## 📋 Resumen Ejecutivo

El frontend está construido sobre un stack moderno y robusto (**React + Vite + TypeScript + Tailwind + Zustand**). La arquitectura general es sólida, con una clara separación entre UI, Estado y API. Sin embargo, se han identificado componentes y stores que han crecido desproporcionadamente ("God Objects"), lo que dificultará el mantenimiento futuro.

---

## 🏗️ Arquitectura y Estructura

| Componente | Estado | Observaciones |
|------------|--------|---------------|
| **Routing** | ✅ Excelente | `App.tsx` maneja rutas protegidas y públicas correctamente. |
| **API Layer** | ✅ Excelente | `api/` bien tipado y separado por dominios. `lib/api.ts` centraliza Axios. |
| **State Management** | 🟡 Mejorable | `expedientesStore.ts` es demasiado grande (>800 líneas). Mezcla lógica de negocio, UI y Sockets. |
| **UI Components** | 🟡 Mejorable | `ExtraccionMasivaDialog.tsx` es monolítico (>1700 líneas). Necesita refactorización urgente. |
| **Estilos** | ✅ Excelente | Uso consistente de Tailwind CSS y Shadcn UI. |

---

## 🔍 Hallazgos Detallados

### 1. "God Store": `expedientesStore.ts`
- **Problema**: Maneja listado, detalles, extracción individual, extracción masiva, WebSockets, polling y filtros.
- **Riesgo**: Dificultad para testear y mantener. Race conditions potenciales.
- **Recomendación**: Dividir en slices:
    - `useExpedientesDataStore` (CRUD básico)
    - `useExtraccionStore` (Lógica compleja de extracción masiva)
    - `useExpedientesUIStore` (Filtros, paginación, modales)

### 2. Componente Monolítico: `ExtraccionMasivaDialog.tsx`
- **Problema**: Archivo de >1700 líneas que maneja configuración, visualización de progreso, filtrado de resultados y lógica de negocio.
- **Riesgo**: Muy difícil de leer y modificar.
- **Recomendación**: Modularizar en sub-componentes:
    - `ExtractionConfigPanel.tsx`
    - `ExtractionProgress.tsx`
    - `ResultsFilter.tsx`
    - `ResultsTable.tsx`

### 3. Normalización de URLs
- **Problema**: En `ExpedientesPage.tsx`, la normalización de URLs se hace manualmente: `.replace(/\s+/g, '-').replace(/\//g, '-')`.
- **Riesgo**: Inconsistencias si el backend o otros componentes usan lógica diferente.
- **Recomendación**: Crear una utilidad centralizada `normalizeExpedienteUrl(numero)` en `src/lib/utils.ts`.

### 4. Hardcoded Values
- **Problema**: `API_BASE_URL` en `expedientesApi.ts` tiene fallback a `http://localhost:8000`.
- **Recomendación**: Asegurar que siempre se use la variable de entorno o rutas relativas si se usa proxy.

---

## 🚀 Plan de Mejoras Propuesto

### Prioridad Alta (Mantenibilidad)
1. **Refactorizar `ExtraccionMasivaDialog`**: Dividir en componentes más pequeños.
2. **Dividir `expedientesStore`**: Separar la lógica de extracción masiva a su propio store.

### Prioridad Media (Calidad de Código)
3. **Centralizar Utilidades**: Mover lógica de formateo de fechas y URLs a `src/lib/utils.ts`.
4. **Completar TODOs**: Implementar endpoints faltantes en `expedientesStore` (pausar, cancelar).

### Prioridad Baja (UX)
5. **Optimizar Re-renders**: Revisar selectores de Zustand para evitar renderizados innecesarios en componentes grandes.

---

**Generado por**: Antigravity Agent
