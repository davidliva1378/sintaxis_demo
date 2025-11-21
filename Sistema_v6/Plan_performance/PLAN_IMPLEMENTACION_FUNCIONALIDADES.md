# Plan de Implementación - Sistema SintaXis v6

## Estado del Proyecto

**Última actualización:** 2025-11-21
**Fases completadas:** 1, 2, 3, 4, 5, 6, 7
**Próxima fase:** 8

---

## Resumen de Fases

| Fase | Nombre | Estado | Prioridad |
|------|--------|--------|-----------|
| 1 | Correcciones Críticas | ✅ Completada | Alta |
| 2 | Visor PDF Modal | ✅ Completada | Alta |
| 3 | Mi Análisis | ✅ Completada | Alta |
| 4 | Debug PDF Buttons | ✅ Completada | Alta |
| 5 | Módulo Agenda | ✅ Completada | Media |
| 6 | Sistema de Escritos | ✅ Completada | Media |
| 7 | Mejoras Mi Análisis | ✅ Completada | Baja |
| 8 | Integración IA | ⏳ Pendiente | Baja |

---

## Fase 4: Debug PDF Buttons

### Objetivo
Diagnosticar y corregir por qué los botones "Ver PDF" y "Descargar" no aparecen en las actuaciones.

### Tareas

- [ ] **4.1 Investigar estructura de datos**
  - Archivo: `Sistema_v6/frontend/src/types/expediente.ts`
  - Verificar campos: `tiene_archivo`, `nombre_archivo`, `ruta_pdf`
  - Criterio: Documentar estructura actual

- [ ] **4.2 Verificar endpoint backend**
  - Archivo: `Sistema_v6/presentation/api/rest/routers/expedientes.py`
  - Endpoint: `GET /{numero}/actuaciones/{indice}/pdf`
  - Criterio: Confirmar que devuelve FileResponse correctamente

- [ ] **4.3 Verificar datos en workspace**
  - Directorio: `Sistema_v6/workspaces/`
  - Criterio: Confirmar existencia de PDFs descargados

- [ ] **4.4 Revisar lógica de renderizado**
  - Archivo: `Sistema_v6/frontend/src/components/expedientes/ActuacionesList.tsx`
  - Líneas: 172-194
  - Condición: `actuacion.tiene_archivo && actuacion.nombre_archivo`
  - Criterio: Los botones aparecen cuando hay PDFs

- [ ] **4.5 Agregar logging de debug**
  - Agregar console.log para verificar valores de `tiene_archivo` y `nombre_archivo`
  - Criterio: Identificar por qué la condición falla

### Criterios de Aceptación
- Los botones Ver PDF y Descargar aparecen para actuaciones con archivos
- El visor PDF modal funciona correctamente
- La descarga de PDF funciona correctamente

---

## Fase 5: Módulo Agenda

### Objetivo
Crear vista centralizada que unifique vencimientos, tareas y recordatorios con vista de calendario.

### Tareas

#### 5.1 Backend - Modelo de Datos
- [ ] **5.1.1 Crear migración SQL**
  - Archivo: `Sistema_v6/infrastructure/persistence/migrations/003_crear_tabla_agenda.sql`
  - Tablas: `agenda_eventos`, `agenda_tareas`
  - Campos evento: `id`, `user_id`, `titulo`, `descripcion`, `fecha_inicio`, `fecha_fin`, `tipo`, `expediente_numero`, `actuacion_indice`, `completado`, `prioridad`, `recordatorio`

- [ ] **5.1.2 Crear router agenda**
  - Archivo: `Sistema_v6/presentation/api/rest/routers/agenda.py`
  - Endpoints:
    - `GET /agenda/eventos` - Listar eventos por rango de fechas
    - `POST /agenda/eventos` - Crear evento
    - `PUT /agenda/eventos/{id}` - Actualizar evento
    - `DELETE /agenda/eventos/{id}` - Eliminar evento
    - `GET /agenda/resumen` - Resumen de próximos eventos
    - `POST /agenda/importar-vencimientos` - Importar vencimientos como eventos

- [ ] **5.1.3 Registrar router**
  - Archivo: `Sistema_v6/presentation/api/rest/main.py`

#### 5.2 Frontend - API Client
- [ ] **5.2.1 Crear agendaApi.ts**
  - Archivo: `Sistema_v6/frontend/src/api/agendaApi.ts`
  - Funciones: `obtenerEventos`, `crearEvento`, `actualizarEvento`, `eliminarEvento`, `importarVencimientos`

#### 5.3 Frontend - Componentes
- [ ] **5.3.1 Crear página AgendaPage**
  - Archivo: `Sistema_v6/frontend/src/pages/agenda/AgendaPage.tsx`
  - Features: Vista calendario mensual/semanal, lista de próximos eventos

- [ ] **5.3.2 Crear componente CalendarioAgenda**
  - Archivo: `Sistema_v6/frontend/src/components/agenda/CalendarioAgenda.tsx`
  - Usar librería: react-big-calendar o similar

- [ ] **5.3.3 Crear componente EventoForm**
  - Archivo: `Sistema_v6/frontend/src/components/agenda/EventoForm.tsx`
  - Modal para crear/editar eventos

- [ ] **5.3.4 Crear componente ListaEventos**
  - Archivo: `Sistema_v6/frontend/src/components/agenda/ListaEventos.tsx`
  - Lista filtrable de eventos

#### 5.4 Integración
- [ ] **5.4.1 Agregar ruta en router**
  - Archivo: `Sistema_v6/frontend/src/App.tsx`
  - Ruta: `/agenda`

- [ ] **5.4.2 Agregar al sidebar/navegación**
  - Agregar enlace a Agenda en el menú principal

### Criterios de Aceptación
- Vista de calendario funcional con eventos
- Crear/editar/eliminar eventos
- Importar vencimientos detectados automáticamente
- Filtrar por tipo de evento
- Vista de próximos eventos en dashboard

---

## Fase 6: Sistema de Escritos

### Objetivo
Gestión de escritos judiciales con plantillas, borradores y seguimiento de presentación.

### Tareas

#### 6.1 Backend - Modelo de Datos
- [ ] **6.1.1 Crear migración SQL**
  - Archivo: `Sistema_v6/infrastructure/persistence/migrations/004_crear_tablas_escritos.sql`
  - Tablas: `escritos`, `plantillas_escritos`, `escritos_adjuntos`
  - Campos escrito: `id`, `user_id`, `expediente_numero`, `titulo`, `contenido`, `plantilla_id`, `estado` (borrador/presentado/confirmado), `fecha_presentacion`, `numero_escrito`

- [ ] **6.1.2 Crear router escritos**
  - Archivo: `Sistema_v6/presentation/api/rest/routers/escritos.py`
  - Endpoints CRUD para escritos y plantillas

#### 6.2 Frontend - Componentes
- [ ] **6.2.1 Crear página EscritosPage**
  - Archivo: `Sistema_v6/frontend/src/pages/escritos/EscritosPage.tsx`

- [ ] **6.2.2 Crear editor de escritos**
  - Archivo: `Sistema_v6/frontend/src/components/escritos/EditorEscrito.tsx`
  - Editor rich text con variables de plantilla

- [ ] **6.2.3 Crear gestión de plantillas**
  - Archivo: `Sistema_v6/frontend/src/components/escritos/PlantillasManager.tsx`

### Criterios de Aceptación
- Crear escritos desde plantillas
- Editor con formato básico
- Guardar borradores
- Marcar como presentado
- Adjuntar archivos
- Historial de escritos por expediente

---

## Fase 7: Mejoras Mi Análisis

### Objetivo
Expandir funcionalidades del módulo Mi Análisis.

### Tareas

- [ ] **7.1 Búsqueda por tags**
  - Archivo: `Sistema_v6/frontend/src/components/expedientes/MiAnalisisList.tsx`
  - Agregar filtro de búsqueda por tags

- [ ] **7.2 Exportar notas**
  - Endpoint: `GET /analisis/expediente/{numero}/exportar`
  - Formatos: JSON, CSV, PDF

- [ ] **7.3 Colores personalizados**
  - Selector de color para cada nota
  - Visualización con fondo de color

- [ ] **7.4 Vista global de destacados**
  - Nueva página con todos los destacados del usuario
  - Agrupados por expediente

- [ ] **7.5 Compartir notas entre usuarios**
  - Sistema de permisos para compartir análisis

### Criterios de Aceptación
- Búsqueda funcional por tags
- Exportación en al menos 2 formatos
- Colores aplicados visualmente
- Vista consolidada de destacados

---

## Fase 8: Integración IA

### Objetivo
Análisis automático de actuaciones usando LLM.

### Tareas

#### 8.1 Backend - Servicio IA
- [ ] **8.1.1 Configurar cliente LLM**
  - Archivo: `Sistema_v6/infrastructure/ai/llm_client.py`
  - Soporte: OpenAI, Anthropic, local (Ollama)

- [ ] **8.1.2 Crear servicio de análisis**
  - Archivo: `Sistema_v6/application/services/ai_analysis_service.py`
  - Funciones: analizar_actuacion, resumir_expediente, detectar_vencimientos, sugerir_acciones

- [ ] **8.1.3 Crear router IA**
  - Archivo: `Sistema_v6/presentation/api/rest/routers/ia.py`
  - Endpoints:
    - `POST /ia/analizar-actuacion`
    - `POST /ia/resumir-expediente`
    - `POST /ia/sugerir-acciones`

#### 8.2 Frontend - Componentes
- [ ] **8.2.1 Botón analizar con IA**
  - Agregar a ActuacionesList y MiAnalisisList
  - Mostrar resultado en modal

- [ ] **8.2.2 Panel de sugerencias**
  - Archivo: `Sistema_v6/frontend/src/components/ia/SugerenciasPanel.tsx`
  - Mostrar sugerencias generadas por IA

- [ ] **8.2.3 Resumen automático**
  - Generar resumen del expediente completo

### Criterios de Aceptación
- Análisis de actuación individual funcional
- Resumen de expediente generado
- Sugerencias de acciones relevantes
- Tiempo de respuesta < 10 segundos
- Manejo de errores de API

---

## Notas Técnicas

### Estructura de Archivos

```
Sistema_v6/
├── presentation/api/rest/routers/
│   ├── analisis.py ✅
│   ├── agenda.py ✅
│   ├── escritos.py (pendiente)
│   └── ia.py (pendiente)
├── frontend/src/
│   ├── api/
│   │   ├── analisisApi.ts ✅
│   │   ├── agendaApi.ts ✅
│   │   └── escritosApi.ts (pendiente)
│   ├── pages/
│   │   ├── agenda/AgendaPage.tsx ✅
│   │   └── escritos/ (pendiente)
│   └── components/
│       ├── expedientes/
│       │   ├── MiAnalisisList.tsx ✅
│       │   └── PDFViewer.tsx ✅
│       ├── agenda/ (pendiente - componentes adicionales)
│       └── escritos/ (pendiente)
└── infrastructure/persistence/migrations/
    ├── 002_crear_tabla_notas_usuario.sql ✅
    ├── 003_crear_tablas_agenda.sql ✅
    └── 004_crear_tablas_escritos.sql (pendiente)
```

### Dependencias a Agregar

**Frontend:**
- `react-big-calendar` - Para vista de calendario
- `@tiptap/react` - Para editor rich text
- `date-fns` - Ya instalado

**Backend:**
- `openai` o `anthropic` - Para integración IA
- `weasyprint` - Para exportar a PDF

### Variables de Entorno Requeridas

```env
# Para Fase 8 - IA
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LLM_PROVIDER=openai  # o anthropic, ollama
```

---

## Instrucciones para Agente IA

### Cómo usar este plan

1. **Verificar estado**: Revisar qué tareas están completadas (✅) y cuáles pendientes ([ ])
2. **Seleccionar fase**: Comenzar por la fase con menor número pendiente
3. **Ejecutar tareas**: Completar cada tarea en orden dentro de la fase
4. **Marcar progreso**: Actualizar checkbox cuando se complete cada tarea
5. **Verificar criterios**: Confirmar que se cumplen los criterios de aceptación antes de pasar a la siguiente fase

### Comandos útiles

```bash
# Ejecutar migración
/usr/local/mysql/bin/mysql -u root -pSulaco01 sintaxis < Sistema_v6/infrastructure/persistence/migrations/XXX.sql

# Iniciar backend
cd Sistema_v6 && PYTHONPATH=/path/to/sintaXis:/path/to/sintaXis/Sistema_v6:$PYTHONPATH MYSQL_PASSWORD=Sulaco01 uvicorn presentation.api.rest.main:app --reload --host 127.0.0.1 --port 8000

# Iniciar frontend
cd Sistema_v6/frontend && npm run dev
```

### Prioridades

- **Alta**: Fases 4-5 (funcionalidad core)
- **Media**: Fase 6 (productividad)
- **Baja**: Fases 7-8 (mejoras y avanzadas)

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-11-21 | Creación del plan inicial |
| 2025-11-21 | Fases 1, 2, 3 completadas |
| 2025-11-21 | Fase 4 completada - Botones PDF funcionando |
| 2025-11-21 | Fase 5 completada - Módulo Agenda implementado |
| 2025-11-21 | Fase 6 completada - Sistema de Escritos implementado |
| 2025-11-21 | Fase 7 completada - Mejoras Mi Análisis (colores, búsqueda, destacados globales, exportación) |
