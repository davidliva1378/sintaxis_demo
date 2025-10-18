# Consideraciones para la agenda de `Sistema_v5`

Este documento resume problemas detectados, oportunidades de mejora y puntos a tener en cuenta al integrar o ampliar la agenda jurídica incluida en `Sistema_v5`.

## Limitaciones actuales
- **Persistencia en memoria:** El `AgendaRepository` mantiene los elementos únicamente en memoria, por lo que se pierden ante un reinicio del proceso y no hay concurrencia segura para múltiples trabajadores o hilos. Conviene evaluar un backend persistente (base de datos o almacenamiento en disco) y mecanismos de locking o transacciones.【F:Sistema_v5/agenda/agenda.py†L56-L86】
- **Identificadores deterministas:** Los identificadores se generan con `_generar_identificador` a partir de la fecha, tipo y título. Si se registran eventos con datos repetidos, se sobrescriben en el repositorio. Sería más seguro incorporar un sufijo aleatorio o un contador incremental.【F:Sistema_v5/agenda/agenda.py†L160-L189】【F:Sistema_v5/agenda/agenda.py†L232-L236】
- **Ausencia de actualización:** El servicio permite crear y eliminar ítems, pero no modificarlos. Falta una operación `actualizar_item` o similar que respete validaciones y mantenga historial.【F:Sistema_v5/agenda/agenda.py†L102-L151】【F:Sistema_v5/agenda/agenda.py†L214-L222】
- **Metadatos sin esquema:** El campo `metadata` acepta cualquier mapping sin validación. Para integraciones complejas se recomienda definir contratos claros o dataclasses específicas según cada categoría.【F:Sistema_v5/agenda/agenda.py†L32-L150】
- **Feriados estáticos:** Los feriados se reciben como lista en el constructor y no existe una API para actualizarlos dinámicamente; tampoco se contemplan calendarios por jurisdicción. Se sugiere exponer métodos para sincronizar feriados y soportar múltiples calendarios.【F:Sistema_v5/agenda/agenda.py†L67-L123】【F:Sistema_v5/agenda/agenda.py†L236-L277】

## Riesgos funcionales
- **Validaciones mínimas:** Solo se valida que la fecha de vencimiento no sea anterior a la de inicio y que la categoría sea conocida. No hay chequeos sobre superposición de audiencias, duplicados por expediente o conflictos de recursos (salas, profesionales).【F:Sistema_v5/agenda/agenda.py†L120-L184】
- **Sin manejo de zonas horarias:** El módulo trabaja con `date` sin hora. Para audiencias o reuniones reales es probable que se requiera controlar horarios, zonas horarias y duración, así como recordatorios previos.【F:Sistema_v5/agenda/agenda.py†L32-L206】
- **Agenda global mutable:** La agenda global es un singleton en módulo. En contextos de pruebas o aplicaciones multicliente podría provocar fugas de estado o datos cruzados. Evaluar factoría por sesión o inyección explícita de dependencias.【F:Sistema_v5/agenda/agenda.py†L309-L350】

## Oportunidades de ampliación
- **Integración con notificaciones:** Aprovechar `registrar_recordatorio` para disparar eventos hacia módulos de notificaciones (email, SMS, panel) y permitir recordatorios periódicos.【F:Sistema_v5/agenda/agenda.py†L200-L277】
- **Reportes y dashboards:** Agregar consultas agregadas (próximos vencimientos, carga por profesional, KPIs) que faciliten la visualización en paneles de control.
- **Soporte para adjuntos:** Permitir vincular archivos (escritos, oficios) a cada ítem mediante referencias al gestor documental del sistema.
- **APIs de integración:** Publicar endpoints REST/gRPC o servicios internos que permitan a otros módulos registrar y consultar eventos sin depender de la instancia global.
- **Automatización de plazos:** Incorporar reglas configurables para calcular plazos según tipo de trámite, feriados oficiales y prórrogas, reduciendo la carga manual.【F:Sistema_v5/agenda/agenda.py†L236-L308】

## Buenas prácticas para el uso
- Inicializar la agenda con las categorías propias del organismo y feriados actualizados antes de registrar eventos.【F:Sistema_v5/agenda/agenda.py†L67-L108】
- Evitar depender de la agenda global en escenarios multiusuario; inyectar `AgendaService` en cada contexto de trabajo o solicitud.【F:Sistema_v5/agenda/agenda.py†L309-L342】
- Serializar o exportar periódicamente la información de la agenda hasta contar con una capa de persistencia robusta.

## Próximos pasos sugeridos
1. Diseñar una capa de persistencia que permita CRUD completo, versionado de cambios y auditoría.
2. Definir contratos de datos por tipo de evento (audiencia, vencimiento, etc.) para documentar metadatos y facilitar validaciones cruzadas.
3. Integrar las utilidades de plazos con módulos que gestionan expedientes, proponiendo plazos automáticos y alertas ante vencimientos críticos.【F:Sistema_v5/agenda/agenda.py†L236-L308】
4. Implementar pruebas de integración que cubran flujo completo desde otros módulos del sistema y casos de concurrencia.
