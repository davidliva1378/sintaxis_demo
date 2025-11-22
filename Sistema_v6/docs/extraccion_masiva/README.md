# Documentación de Extracción Masiva - Sistema v6

Esta carpeta contiene toda la documentación y planes de implementación para la funcionalidad de **Extracción Masiva** del proyecto Sistema_v6.

## 📂 Estructura de Documentos

### 1️⃣ PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md (PRINCIPAL)
**📖 64KB - Plan Maestro Completo**

Este es el **documento principal** y más completo. Contiene:
- ✅ Plan V2.1 completo con 22 tareas detalladas
- ✅ MVP dividido en 3 fases (Fases 1-3 implementables)
- ✅ Fase 4 de Monitoreo (documentada pero NO implementar aún)
- ✅ Arquitectura técnica completa
- ✅ Estimaciones de tiempo por tarea
- ✅ Orden de implementación recomendado

**USO:** Este es tu documento de referencia principal para implementar la extracción masiva.

---

### 2️⃣ RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md
**📖 14KB - Resumen Ejecutivo**

Resumen conciso del plan principal:
- Diagnóstico del estado actual
- Visión general de las 4 fases
- Decisiones arquitectónicas clave
- Roadmap de implementación

**USO:** Lee esto primero para entender el contexto general antes de entrar en detalles.

---

### 3️⃣ ARQUITECTURA_SISTEMA_MONITOREO.md
**📖 40KB - Arquitectura Detallada FASE 4**

Documentación técnica completa del sistema de monitoreo automático:
- Arquitectura de componentes
- Flujos de datos
- Modelos de dominio
- Integraciones con Sistema v6

**⚠️ IMPORTANTE:** Esta es la FASE 4 que **NO se implementa en el MVP**. Solo consultar para entender el diseño futuro.

---

### 4️⃣ IMPLEMENTACION_EXTRACCION_MASIVA_UNIFICADA.md
**📖 17KB - Guía de Unificación**

Documenta cómo unificar la extracción masiva con el sistema existente:
- Integración con arquitectura DDD actual
- Adaptadores necesarios
- Patrón de repositorios
- Inyección de dependencias

**USO:** Consultar al integrar la extracción con el proyecto Sistema_v6 existente.

---

### 5️⃣ PLAN_UNIFICACION_EXTRACCION_MASIVA.md
**📖 31KB - Plan Alternativo de Unificación**

Plan detallado para unificar múltiples enfoques de extracción:
- Comparación de enfoques v4, v5 y v6
- Estrategia de migración
- Checklist de implementación

**USO:** Referencia secundaria para entender decisiones de diseño.

---

### 6️⃣ INDICE_DOCUMENTACION_EXTRACCION_MASIVA.md
**📖 9KB - Índice de Documentación**

Índice completo de toda la documentación relacionada con extracción masiva en el proyecto.

**USO:** Buscar rápidamente otros documentos relacionados.

---

## 🎯 Flujo de Implementación Recomendado

### Paso 1: Lectura Inicial
1. Lee `RESUMEN_DIAGNOSTICO_Y_PLAN_V2.md` (contexto general)
2. Lee `PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md` (plan detallado)

### Paso 2: Implementación MVP (Fases 1-3)
Sigue el `PLAN_COMPLETAR_EXTRACCION_MASIVA_V2.md` en orden:

#### **FASE 1: Backend (3-4 horas)**
- Tarea 1: Endpoint GET `/listado` ✅ **COMPLETADO**
- Tarea 1B: Comparación automática con BASE ✅ **COMPLETADO**
- Tarea 2: Endpoint POST `/procesar-seleccionados` ✅ **COMPLETADO**

#### **FASE 2: Frontend Filtrado (8-10 horas)** ⭐ CRÍTICA
- Tarea 3: Componente FiltradoExpedientesDialog ✅ **COMPLETADO**
- Tarea 4: Hook useFiltrosExpedientes (7 filtros) ✅ **COMPLETADO**
- Tarea 5: Hook useSeleccionMasiva (5 funciones) ✅ **COMPLETADO**
- Tarea 6: TablaVirtualizada con @tanstack/react-virtual ✅ **COMPLETADO**
- Tarea 7: Integración con ExtraccionMasivaDialog ⏳ **PENDIENTE**

#### **FASE 3: Procesamiento Selectivo (6-8 horas)**
- Tarea 8: Implementar lógica real en `GestorBatch._procesar_expediente()` ⏳ **PENDIENTE**
- Tarea 9: Integrar guardado con IExpedienteRepository ⏳ **PENDIENTE**
- Tarea 10: Actualizar estados con GestorEstados ⏳ **PENDIENTE**
- Tarea 11: Actualizar DI Container ⏳ **PENDIENTE**

### Paso 3: Integración (Consultar otros documentos)
- Usa `IMPLEMENTACION_EXTRACCION_MASIVA_UNIFICADA.md` para integrar con Sistema_v6
- Ajusta según la arquitectura existente

### Paso 4: FUTURO - Fase 4 (NO implementar ahora)
- Consultar `ARQUITECTURA_SISTEMA_MONITOREO.md` cuando se decida implementar
- Esta fase es para monitoreo automático y notificaciones

---

## 📁 Ubicación del Proyecto

**Directorio del proyecto:** `Sistema_v6/`

Todos los demás directorios en la raíz son referencias y serán eliminados posteriormente.

---

## 🚀 Estado Actual de Implementación

### ✅ Completado (Backend + Frontend Core - ~65%)
- ExtractorMasivo con comparación BASE
- GestorBatch (estructura, falta lógica real)
- API REST endpoints funcionales
- Hooks de filtrado y selección (7 filtros + 5 funciones)
- Componentes React (TablaVirtualizada, FiltradoExpedientesDialog)
- Types y API client

### ⏳ Pendiente (~35%)
- Integración con flujo completo de extracción
- Lógica real de procesamiento individual
- Guardado en repositorio y actualización de estados
- Configuración del DI Container
- Testing end-to-end

### 📅 Fase 4 - Monitoreo (Futuro - Documentado)
- Sistema de monitoreo automático
- Detección de cambios
- Notificaciones
- Panel de administración

---

## 📝 Notas Importantes

1. **Proyecto principal:** Todo el código va en `Sistema_v6/`
2. **MVP First:** Implementar solo Fases 1-3 inicialmente
3. **Fase 4:** Está completamente diseñada pero NO implementar aún
4. **Rendimiento:** Sistema diseñado para manejar 2000+ expedientes
5. **Arquitectura:** Sigue principios DDD del proyecto Sistema_v6

---

**Última actualización:** 2025-11-10
**Branch:** sintaxis_parcial3
**Estado:** En desarrollo - MVP en progreso
