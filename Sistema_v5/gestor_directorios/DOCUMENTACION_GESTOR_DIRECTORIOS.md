# Gestor de directorios de expedientes

Este documento amplía la descripción del paquete ``Sistema_v5.gestor_directorios``. El módulo
provee utilidades para crear y mantener la estructura de archivos de expedientes que utilizan
los distintos componentes de **Sistema_v5**, desde los scrapers de PJN hasta los orquestadores
de flujos y la interfaz de usuario. Su objetivo principal es asegurar que todos los servicios
trabajen sobre una convención de carpetas y manifiestos consistente, incluyendo la asignación
de identificadores numéricos únicos.

## Resumen general

* ``GestorDirectoriosExpedientes`` encapsula la lógica para generar árboles de directorios,
  escribir manifiestos JSON y sincronizar metadatos.
* El módulo se integra con ``SystemConfig`` para respetar rutas definidas en la configuración
  centralizada del sistema.
* Las estructuras creadas se apoyan en ``ESTRUCTURA_POR_DEFECTO``, un diccionario anidado que
  define el árbol mínimo que cada expediente debe tener.
* ``inicializar_directorio_base`` es la puerta de entrada recomendada para preparar la carpeta
  raíz de expedientes tras una instalación o despliegue.

## Responsabilidades principales

1. **Creación de estructuras**: materializa en disco las carpetas base y las personalizaciones
   opcionales para cada expediente.
2. **Escritura de manifiestos**: persiste ``manifest.json`` en cada expediente con el detalle de
   directorios generados y metadata asociada.
3. **Normalización y registro**: utiliza ``normalizar_numero_expediente`` para estandarizar
   nombres y mantiene un índice numérico incremental por expediente.
4. **Operaciones masivas**: permite crear expedientes desde definiciones JSON y actualizar
   estructuras existentes sin perder compatibilidad con versiones previas.

## API pública

### Constantes y funciones de módulo

- ``ESTRUCTURA_POR_DEFECTO``: árbol de carpetas mínimo generado por defecto.
- ``inicializar_directorio_base(config: SystemConfig | None = None, **kwargs)``: crea el árbol
  base utilizando la configuración del sistema. Propaga parámetros como ``base_dir`` o
  ``config_path`` hacia ``GestorDirectoriosExpedientes.desde_config``.

### Clase ``GestorDirectoriosExpedientes``

#### Constructor y configuración

- ``raiz``: ``Path`` base donde se crean los expedientes.
- ``estructura``: estructura inicial (se copia profundamente del valor por defecto para evitar
  efectos colaterales).
- ``manifest_filename`` y ``index_filename``: nombres de los archivos de manifiesto e índice.

Métodos principales:

- ``desde_config(config=None, *, base_dir=None, config_path="config/sistema.json")``
  Resuelve la ruta raíz leyendo ``SystemConfig``. Gestiona rutas relativas mediante
  ``_resolver_ruta``.
- ``generar_arbol(destino=None, *, metadata=None, estructura=None, fusionar_estructura=True)``
  Crea la estructura solicitada, registra cada directorio en la lista ``directories`` y escribe
  el manifiesto mediante ``_persistir_manifest``. Si se proporciona metadata se copia para evitar
  mutaciones externas. La estructura efectiva se calcula con ``_obtener_estructura_efectiva``.
- ``crear_para_expediente(numero_expediente)``
  Normaliza el número, obtiene un identificador único a través del índice, construye la ruta
  (``_obtener_ruta_expediente``) y delega en ``generar_arbol`` para crear el árbol completo. La
  metadata incluye ``numero_expediente``, ``numero_normalizado`` e ``id``.
- ``crear_desde_json(expedientes)``
  Itera un iterable de diccionarios, valida campos obligatorios/opcionales, normaliza los números
  y crea cada expediente. Acumula errores descriptivos y sólo los reporta al final, permitiendo
  revisar un resumen de problemas de importación.
- ``actualizar_expediente(numero_expediente, metadata_nueva, estructura=None)``
  Localiza la carpeta adecuada (respetando versiones antiguas que usaban sólo el nombre
  normalizado), fusiona directorios existentes con la nueva estructura y actualiza la metadata en
  el manifiesto. Garantiza que el ``id`` del expediente se preserve y se escriba con la metadata
  final.
- ``actualizar_estructura(estructura_personalizada, *, reemplazar=False)``
  Permite modificar la estructura interna del gestor para futuras creaciones. Con ``reemplazar``
  en ``True`` se sustituye por completo; de lo contrario, se usa ``_fusionar_estructuras`` para
  combinar ramas específicas.

#### Helpers relevantes

- ``_fusionar_estructuras(base, extra)``
  Mezcla dos árboles de carpetas recursivamente. Se usa tanto en la actualización global de la
  estructura como en la generación puntual por expediente.
- ``_resolver_ruta(ruta, base_dir, config_path)``
  Resuelve rutas relativas o con variables de entorno partiendo de la configuración del sistema.
- ``_crear_estructura(base, estructura, manifest, raiz_manifest)``
  Recorre recursivamente el diccionario de estructura, valida que no se utilicen rutas absolutas
  ni ``..`` y crea cada carpeta. Cada directorio relativo al raíz se registra en el manifiesto.
- ``_obtener_estructura_efectiva(estructura_personalizada, fusionar)``
  Decide si utilizar la estructura interna, la personalizada o una combinación de ambas.
- ``_persistir_manifest(manifest_path, manifest)`` y ``_persistir_json_atomico(destino, contenido)``
  Escriben JSON con reemplazo atómico usando archivos temporales, minimizando corrupciones ante
  fallos.
- ``_indice_path()``, ``_cargar_indice()``, ``_guardar_indice()`` y
  ``_obtener_o_registrar_identificador(numero_normalizado)``
  Gestionan el índice de IDs incrementales por expediente. El índice se almacena en
  ``expedientes_index.json`` y se actualiza de manera atómica.
- ``_obtener_ruta_expediente(numero_normalizado, identificador)``
  Genera nombres del estilo ``000123_EXP_123_2024`` para facilitar ordenamiento y búsqueda.

## Flujos típicos

1. **Inicialización del entorno**
   1. Ejecutar ``inicializar_directorio_base()`` tras configurar el sistema. Esto crea el árbol
      base en la ruta definida por ``SystemConfig`` y genera ``manifest.json`` con la estructura
      inicial.
   2. Opcionalmente ajustar la estructura global con ``GestorDirectoriosExpedientes.actualizar_estructura``
      antes de comenzar a crear expedientes reales.

2. **Creación manual de un expediente**
   1. Instanciar el gestor (directamente o mediante ``desde_config``).
   2. Llamar a ``crear_para_expediente(numero_expediente)``. Se devuelve la ruta creada y el
      manifiesto asociado.
   3. Consumir el manifiesto para integrarse con otros módulos (por ejemplo, interfaces gráficas
      o servicios que necesiten saber dónde guardar documentos).

3. **Creación masiva desde JSON**
   1. Preparar un iterable de diccionarios con la clave ``numero_expediente`` y, opcionalmente,
      ``metadata``, ``estructura`` y ``fusionar_estructura``.
   2. Invocar ``crear_desde_json``. El método crea cada expediente válido y acumula errores por
      entrada. Si ocurre al menos un error se lanza ``ValueError`` con un resumen.
   3. Revisar el detalle para corregir entradas fallidas antes de reintentar.

4. **Actualización de metadatos/estructura**
   1. Usar ``actualizar_expediente`` para incorporar nuevos campos en el manifiesto, forzar la
      creación de carpetas adicionales o sincronizar expedientes migrados.
   2. El gestor combina directorios previos con los nuevos, evitando borrar información existente
      y asegurando que la metadata previa persista salvo los campos sobrescritos.

5. **Gestión del índice de IDs**
   1. Cada vez que se crea o actualiza un expediente se consulta ``expedientes_index.json``.
   2. Si el expediente no tenía ID, se asigna el siguiente correlativo y se persiste el índice con
      ``_guardar_indice``.
   3. El índice permite generar rutas estables y detectar duplicados en operaciones masivas.

## Ejemplos de uso

```python
from pathlib import Path
from Sistema_v5.gestor_directorios import GestorDirectoriosExpedientes

base = Path("data/expedientes")
gestor = GestorDirectoriosExpedientes(base)

# Crear un expediente manualmente
ruta, manifest = gestor.crear_para_expediente("Exp 123/2024")
print(ruta)
print(manifest["metadata"]["id"])

# Ajustar la estructura antes de crear otro expediente
gestor.actualizar_estructura({"documentos_usuario": {"firmados": None}})

# Generar un árbol personalizado sin afectar el gestor
manifest_personalizado = gestor.generar_arbol(
    destino=base / "experimental",
    estructura={"tmp": None},
    fusionar_estructura=False,
)

# Importación masiva desde JSON
lote = [
    {
        "numero_expediente": "Exp 999/2024",
        "metadata": {"origen": "Migración"},
    },
    {
        "numero_expediente": "Exp 1000/2024",
        "estructura": {"audiencias": {"audio": None}},
        "fusionar_estructura": True,
    },
]
creados = gestor.crear_desde_json(lote)
```

### Consideraciones de validación y escritura atómica

- Todas las rutas proporcionadas en las estructuras se validan para evitar rutas absolutas o el
  uso de ``..`` que podrían escapar del árbol del expediente.
- Los manifiestos e índices se escriben usando ``NamedTemporaryFile`` y ``os.replace`` para
  garantizar operaciones atómicas en sistemas compatibles (incluidos POSIX y Windows), reduciendo
  la probabilidad de corrupciones.
- Durante la importación masiva, cualquier error de validación se acumula y se reporta al final.
  Es posible que se hayan creado expedientes válidos antes del error; es responsabilidad del flujo
  de alto nivel decidir si revertir esos cambios.

## Futuras extensiones

- **Creación masiva basada en streams**: incorporar un método que procese iterables perezosos o
  generadores, escribiendo resultados parciales en un registro para permitir reanudaciones.
- **Actualización incremental del índice**: abstraer la persistencia del índice detrás de una
  interfaz para soportar almacenamiento distribuido (por ejemplo, bases de datos clave-valor o
  servicios REST).
- **Índice numérico compartido**: exponer hooks para sincronizar el identificador correlativo con
  otros sistemas que también asignan IDs, evitando duplicados al trabajar en múltiples nodos.

## Recursos adicionales

- ``README.md`` en este mismo directorio ofrece una guía rápida de uso.
- ``Sistema_v5/configuracion/core/system_config.py`` describe cómo se obtienen las rutas base.
- ``Sistema_v5/gestor_directorios_expedientes.py`` y ``Sistema_v5/mi_monitor_expedientes.py``
  muestran integraciones de alto nivel con el gestor.
