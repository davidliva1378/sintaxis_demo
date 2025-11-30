# Plan de Refactorización de Frontend

## Objetivo
Mejorar la mantenibilidad y calidad del código del frontend abordando los "God Objects" identificados y centralizando lógica repetida.

## Estrategia
Se procederá de manera incremental, comenzando por cambios de bajo riesgo (utilidades) hasta llegar a la refactorización mayor de componentes y estado.

## Fases de Implementación

### Fase 1: Fundamentos y Limpieza
**Objetivo**: Eliminar duplicación y valores hardcodeados.

1.  **Centralizar Utilidades (`src/lib/utils.ts`)**:
    -   Implementar `normalizeExpedienteUrl(numero: string): string`.
    -   Implementar `formatDate(date: string): string`.
    -   Reemplazar usos en `ExpedientesPage.tsx` y `ExtraccionMasivaDialog.tsx`.

2.  **Corregir API Clients**:
    -   Revisar `src/api/expedientesApi.ts` y otros.
    -   Eliminar fallbacks a `http://localhost:8000` y asegurar uso de `import.meta.env.VITE_API_URL`.

### Fase 2: Soporte Backend (Nueva Funcionalidad)
**Objetivo**: Permitir reutilizar el listado base de extracciones anteriores.

1.  **Nuevo Endpoint en `extraccion.py`**:
    -   Implementar `GET /api/extraccion/masiva/base`.
    -   Debe leer `listado_base.json` usando `ExtractorMasivo.cargar_listado`.
    -   Retornar lista de expedientes para visualización offline.

### Fase 3: Refactorización de Estado (Store)
**Objetivo**: Dividir `expedientesStore.ts` para separar responsabilidades.

1.  **Crear `src/stores/extraccionStore.ts`**:
    -   Mover interfaces `ExtraccionMasivaState`, `ProgresoExtraccion`, etc.
    -   Mover acciones: `iniciarExtraccionMasivaAvanzada`, `conectarWebSocket`, `obtenerProgreso`, etc.
    -   **Nuevo**: Agregar acción `cargarListadoBase` para consumir el nuevo endpoint.

2.  **Limpiar `expedientesStore.ts`**:
    -   Mantener solo lógica CRUD de expedientes (`listar`, `obtener`, `filtros`).
    -   Eliminar código muerto relacionado con extracción.

3.  **Actualizar Componentes**:
    -   Modificar `ExtraccionMasivaDialog` para consumir `useExtraccionStore`.
    -   Modificar `ExpedientesPage` si es necesario.

### Fase 3: Modularización de Componentes
**Objetivo**: Descomponer `ExtraccionMasivaDialog.tsx` (>1700 líneas) en componentes manejables.

1.  **Crear estructura de directorios**:
    -   `src/components/expedientes/extraccion/`

2.  **Extraer Sub-componentes**:
    -   `ConfigPanel.tsx`: Formulario de configuración (headless, timeouts, etc.).
    -   `ProgressPanel.tsx`: Barras de progreso y logs.
    -   `FiltersPanel.tsx`: Filtros de resultados (texto, dependencias, fechas).
    -   `ResultsTable.tsx`: Tabla de expedientes extraídos con selección.

3.  **Refactorizar `ExtraccionMasivaDialog.tsx`**:
    -   Componer el diálogo usando los nuevos sub-componentes.
    -   Mantener la lógica de orquestación (handlers principales) en el componente padre por ahora, pasando props a los hijos.

### Fase 4: Mejoras de UX (Solicitadas por Usuario)
**Objetivo**: Mejorar la experiencia durante y después de la extracción.

1.  **Feedback en Tiempo Real (`ProgressPanel.tsx`)**:
    -   Mostrar métricas detalladas: Página actual, Velocidad (exp/min), Tiempo transcurrido/estimado.
    -   Mostrar log de últimos eventos (ej: "Extrayendo página 5...", "Encontrado exp. 123/2024").
    -   Implementar visualización de estado de conexión WebSocket.

2.  **Botón Cancelar Funcional**:
    -   Implementar llamada real al endpoint de cancelación en `extraccionStore`.
    -   Asegurar que el backend procese la señal de cancelación inmediatamente.
    -   Feedback visual inmediato al pulsar (estado "Cancelando...").

3.  **Persistencia del Reporte**:
    -   Eliminar el temporizador de auto-cierre del reporte final.
    -   Agregar botón explícito "Continuar" o "Cerrar Reporte".
    -   Permitir descargar el reporte desde la vista de resumen.

## Verificación
-   **Build**: El proyecto debe compilar sin errores (`npm run build`).
-   **Lint**: Sin warnings de ESLint (`npm run lint`).
-   **Funcional**:
    -   La extracción masiva debe funcionar igual que antes.
    -   Los filtros de expedientes deben funcionar correctamente.
    -   La navegación a detalles de expediente debe funcionar.
    -   **UX**: Verificar feedback en tiempo real, cancelación y persistencia del reporte.
