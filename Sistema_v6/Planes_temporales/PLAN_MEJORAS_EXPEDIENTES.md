# Plan de Mejoras: Frontend de Expedientes

Este plan detalla las mejoras de UI/UX y técnicas sugeridas en el reporte de revisión.

## 1. Mejoras en Visualización de Texto (`TextoActuacionPanel`)
- [ ] **Mejorar Mensaje de Error:** Reemplazar "No hay texto extraido disponible" con opciones de acción (ej: "Ver PDF Original").
- [ ] **Formato de Texto:** Mejorar la tipografía y espaciado del texto extraído (clase `prose` de Tailwind o estilos personalizados para lectura jurídica).

## 2. Mejoras en Lista de Actuaciones (`ActuacionesList`)
- [ ] **Filtros:** Implementar filtrado por tipo de actuación (Sentencia, Decreto, etc.) y rango de fechas.
- [ ] **Virtualización/Paginación:** Si la lista es muy larga, usar virtualización o paginación para mejorar el rendimiento.

## 3. Feedback de Procesamiento (`ExpedienteDetallePage`)
- [ ] **Indicador de Estado Persistente:** Mostrar si un expediente se está procesando en segundo plano, incluso si se recarga la página (usando datos del backend o WebSockets).

## 4. Persistencia de Estado de UI
- [ ] **Recordar Estado:** Mantener filtros y actuaciones expandidas al navegar (usando `zustand` con persistencia o `localStorage`).

## 5. Consistencia Técnica
- [ ] **Verificación de IDs:** Asegurar que el frontend use consistentemente el `indice` como `id` para todas las operaciones.
