# Actuaciones v5 - Guía de Consumo Externo

La versión **v5** de las utilidades de actuaciones está orientada a integrarse en
aplicaciones externas que necesitan operar con los archivos JSON generados por el
scraper de `actuaciones_v4`. A diferencia del módulo original, `actuaciones_v5`
no depende de Playwright ni de rutinas de scraping: sólo provee una API amigable
para leer, inspeccionar, filtrar y persistir el contenido de un expediente.

## Objetivos principales

- **Compatibilidad garantizada** con las versiones de formato `1.0` y `1.1`
  definidas en `actuaciones_v4`.
- **Lectura tipada** de los archivos JSON mediante clases `ActuacionesExpediente`
  y `Actuacion`, simplificando el acceso a campos frecuentes como `Indice`,
  `Hash`, `TieneArchivo` o `Descargado`.
- **Actualización de métricas** de manera automática al guardar cambios, evitando
  inconsistencias entre el encabezado y la lista de actuaciones.
- **Herramientas de filtrado** para obtener subconjuntos útiles (por ejemplo,
  actuaciones con adjuntos pendientes de descarga).

## Contenido del módulo `actuaciones_v5`

### `cargar_expediente_actuaciones(ruta)`
Carga el JSON indicado y devuelve una instancia de `ActuacionesExpediente`. Esta
función valida que la estructura posea las llaves `Expediente` y `Actuaciones`, y
confirma que la versión del formato se encuentre dentro de las compatibles.

### `ActuacionesExpediente`
Encapsula el encabezado y la lista completa de actuaciones. Métodos destacados:

- `filtrar_actuaciones(...)`: devuelve una lista filtrada por si son históricas,
  si poseen archivo o si ya fueron descargadas.
- `iter_actuaciones(...)`: iterador perezoso basado en los mismos filtros.
- `marcar_descargado(...)`: actualiza el estado de descarga de una actuación
  identificándola por `hash` o `indice` y recalcula automáticamente los
  contadores del encabezado.
- `resumen_descargas()`: expone un diccionario con los totales de adjuntos,
  descargas realizadas y pendientes.
- `recalcular_metricas()`: sincroniza los campos `Cantidad de Actuaciones
  Obtenidas`, `total_actuales`, `total_historicas`, `Cantidad de Archivos
  Descargados`, `total_archivos_con_enlace` y `descargas_pendientes` con los
  datos actuales.
- `guardar(ruta=None)`: escribe el JSON en disco (usando la ruta original si no
  se especifica otra) aplicando `ensure_ascii=False` e identado en 2 espacios.

### `Actuacion`
Representa una actuación individual conservando todos los campos originales y
permitiendo acceso directo a atributos frecuentes (`indice`, `tiene_archivo`,
`descargado`, etc.). También incluye:

- `marcar_descargado(nombre_archivo=None, estado=True)`: helper para modificar la
  bandera de descarga y actualizar el nombre del archivo adjunto.
- Propiedad `es_actual`: atajo booleano que indica si la actuación pertenece a
  la pestaña actual (`True`) u a la histórica (`False`).
- Método `to_dict()`: retorna el diccionario listo para serializar, incluyendo
  los campos adicionales que el scraper haya anexado.

## Ejemplos de uso

```python
from Sistema_v4.actuaciones.actuaciones_v5 import cargar_expediente_actuaciones

expediente = cargar_expediente_actuaciones("ActuacionesCompletas/EXP123/actuaciones-EXP123.json")

# Obtener actuaciones con adjunto que aún no se descargaron
pendientes = expediente.filtrar_actuaciones(con_archivo=True, descargadas=False)

for actuacion in pendientes:
    print(actuacion.indice, actuacion.nombre_archivo)

# Marcar una actuación como descargada por hash y guardar los cambios
expediente.marcar_descargado(hash_valor="abc123", nombre_archivo="presentacion.pdf")
expediente.guardar()
```

## Buenas prácticas

- **No editar manualmente** los contadores del encabezado. Utilice
  `recalcular_metricas()` o los métodos `marcar_descargado`/`guardar` para
  mantener la consistencia automática.
- **Verificar la versión** antes de consumir archivos muy antiguos. Si la versión
  no figura dentro de `VERSIONES_COMPATIBLES`, considere convertir el archivo a
  la nueva estructura utilizando el scraper actualizado.
- **Conservar los campos adicionales** (`datos_adicionales`) al manipular
  actuaciones personalizadas, de modo que los procesos posteriores que dependan
  de ellos (por ejemplo, trazas de auditoría) los sigan recibiendo.

## Diferencias con `actuaciones_v4`

- No se incluyen funciones asincrónicas ni dependencias de Playwright.
- Las utilidades de descarga directa de adjuntos permanecen en `actuaciones_v4`;
  `actuaciones_v5` sólo se encarga del tratamiento del JSON resultante.
- Se añaden validaciones explícitas y errores claros para estructuras faltantes
  o versiones desconocidas.

Con estas herramientas, cualquier servicio externo puede simular, poblar o
transformar expedientes sin necesidad de replicar la lógica interna del scraper.
