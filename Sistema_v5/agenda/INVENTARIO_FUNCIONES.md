# Inventario funcional del módulo `Sistema_v5.agenda`

Este inventario documenta las clases, métodos públicos y funciones auxiliares
expuestas por el módulo de agenda. Debe mantenerse actualizado junto con las
modificaciones del código y el archivo `CONSIDERACIONES.md`.

## Clases de dominio

### `AgendaItem`
- **Ubicación:** `agenda.py`
- **Descripción:** Dataclass inmutable que representa un registro de agenda con
  identificador único, categoría, título, fechas relevantes, etiquetas y
  metadatos opcionales.
- **Métodos relevantes:**
  - `dias_restantes(referencia: date | None = None) -> int`: retorna los días
    corridos restantes hasta `fecha_vencimiento`.
  - `esta_vencido(referencia: date | None = None) -> bool`: indica si el ítem
    está vencido en relación con la fecha de referencia.

### `AgendaQuery`
- **Descripción:** Dataclass mutable utilizada como filtro de búsqueda en el
  repositorio. Permite filtrar por tipos, rango de fechas, etiquetas y texto.

## Repositorios

### `AgendaRepository`
- **Propósito:** Implementación en memoria que gestiona una colección de
  `AgendaItem` con operaciones básicas (`add`, `update`, `get`, `remove`,
  `all`, `filter`).
- **Consideraciones:** Valida la unicidad de IDs y permite iterar por los
  elementos almacenados.

### `JSONAgendaRepository`
- **Propósito:** Extiende `AgendaRepository` para proporcionar persistencia en
  disco a través de un archivo JSON con escritura atómica opcional (`auto_flush`).
- **Operaciones sobrescritas:** `add`, `update`, `remove` (persisten cambios) y
  `flush()` para guardar manualmente. Carga inicial mediante `_cargar_desde_disco()`.
- **Uso recomendado:** Simulación de base de datos ligera o pruebas integrales
  que requieren durabilidad entre ejecuciones.

## Servicio principal

### `AgendaService`
Servicio de alto nivel que encapsula las operaciones sobre la agenda y las
utilidades de cómputo de plazos.

- **Inicialización:** `AgendaService(repository=None, *, feriados=None, categorias=None)`.
  Acepta repositorios personalizados, define feriados y permite registrar
  categorías adicionales.
- **Gestión de categorías:**
  - `agregar_categoria(categoria)`.
  - `categorias_disponibles()`.
  - `eliminar_categoria(categoria)`.
- **Gestión de feriados:**
  - `sincronizar_feriados(feriados)`.
  - `agregar_feriados(feriados)`.
  - `agregar_feriado(feriado)`.
  - `quitar_feriado(feriado)`.
  - `listar_feriados()`.
- **Gestión de ítems:**
  - `registrar_item(...)`: valida datos generales y crea un `AgendaItem`.
  - Atajos especializados: `registrar_vencimiento`, `registrar_audiencia`,
    `registrar_tarea`, `registrar_nota`, `registrar_recordatorio`.
  - Consultas y mantenimiento: `obtener`, `listar`, `buscar`, `eliminar` y
    `actualizar_item` (preserva validaciones y metadatos).
- **Utilidades de fechas expuestas:**
  - `contar_dias_habiles(inicio, fin)`.
  - `contar_dias_corridos(inicio, fin)`.
  - `calcular_fecha_plazo(fecha_inicio, dias, tipo_plazo="habiles")`.

## Funciones auxiliares de plazos

- `calcular_fecha_plazo(fecha_inicio, dias, tipo_plazo="habiles", *, feriados=None)`:
  calcula la fecha de vencimiento considerando días hábiles o corridos.
- `dias_habiles_entre(inicio, fin, *, feriados=None)`.
- `dias_corridos_entre(inicio, fin)`.
- `contar_dias_habiles(inicio, fin, *, feriados=None)`.
- `contar_dias_corridos(inicio, fin)`.
- `es_dia_habil(dia, feriados)` (función interna expuesta para consultas).

## Gestión global compartida

- `crear_agenda_default(*, feriados=None, repository=None, categorias=None)`:
  factoría para instanciar `AgendaService` con configuración personalizada.
- `obtener_agenda_global()` y los atajos `registrar_vencimiento`, `registrar_tarea`,
  `registrar_audiencia`, `registrar_nota`, `registrar_recordatorio` que operan
  sobre la instancia única compartida.

## Identificadores y normalización (internos)

- `_normalizar_etiquetas(etiquetas)`.
- `_resolver_identificador(identificador, fecha, titulo, tipo)`.
- `_generar_identificador(fecha, titulo, tipo)`.
- `_item_to_dict(item)` / `_item_from_dict(data)` para serialización JSON.
- `_json_default(value)`.

Estas funciones internas respaldan la funcionalidad pública y deben revisarse
si se modifica el modelo de datos o el esquema de persistencia.
