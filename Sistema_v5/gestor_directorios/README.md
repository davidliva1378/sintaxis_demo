# Gestor de directorios de expedientes

Este paquete concentra utilidades compartidas para crear y mantener la estructura de archivos
de expedientes que utilizan los módulos de **Sistema_v5**. Actualmente expone el gestor
``GestorDirectoriosExpedientes`` y el diccionario ``ESTRUCTURA_POR_DEFECTO`` que describe el
árbol mínimo que se crea para cada expediente.

## Estructura generada

Al invocar ``generar_arbol`` o ``crear_para_expediente`` se materializa el siguiente esquema
base dentro del directorio configurado como raíz:

```
<raiz>
├── actuaciones/
│   ├── adjuntos/
│   └── json/
├── documentos_usuario/
└── reportes/
```

Además de crear los directorios, el gestor escribe un archivo ``manifest.json`` que lista las
rutas generadas y permite adjuntar metadatos adicionales (por ejemplo el número de expediente
original y el normalizado).

> 💡 Necesitás más espacios de trabajo? Algunas implementaciones agregan
> `documentos_firmados/` para copias selladas o `tmp/` para intercambiar
> archivos temporales con otras automatizaciones. Podés extender la
> estructura en tiempo de ejecución usando los métodos explicados más
> abajo para sumar estos directorios adicionales sin tocar el código
> fuente.

## Uso básico

```python
from pathlib import Path
from Sistema_v5.gestor_directorios import GestorDirectoriosExpedientes

base = Path("data/expedientes")
manager = GestorDirectoriosExpedientes(base)
manifest = manager.generar_arbol()

print("Directorios creados:")
for ruta in manifest["directories"]:
    print(f" - {ruta}")
```

Para respetar la configuración centralizada del sistema, el gestor también se puede instanciar
directamente desde ``SystemConfig``:

```python
from pathlib import Path
from Sistema_v5.configuracion.core.system_config import SystemConfig
from Sistema_v5.gestor_directorios import GestorDirectoriosExpedientes

config = SystemConfig.from_file("config/sistema.json")
gestor = GestorDirectoriosExpedientes.desde_config(config, base_dir=Path.cwd())

destino, manifest = gestor.crear_para_expediente("Exp 123/2024")
print(f"Estructura creada en {destino}")
```

El método ``crear_para_expediente`` normaliza el número de expediente (por ejemplo ``"Exp 123/2024"``
→ ``"Exp_123_2024"``), genera el árbol completo dentro de esa carpeta y actualiza el manifiesto
con la metadata del expediente, lista para ser consumida por otros módulos del sistema o
interfaces externas.

### Importación masiva desde JSON

Cuando se recibe un lote serializado (por ejemplo, un archivo JSON exportado desde otro
servicio) se puede utilizar ``crear_desde_json`` para procesar cada entrada de forma segura.
Cada elemento debe ser un diccionario con la clave obligatoria ``numero_expediente`` y puede
incluir metadatos adicionales bajo ``metadata`` (diccionario), una ``estructura`` personalizada
(diccionario análogo al formato aceptado por ``generar_arbol``) y la bandera opcional
``fusionar_estructura``. El método genera los expedientes válidos y si alguna entrada falla,
acumula el error por número de expediente y lo reporta en una excepción descriptiva.

## Extender o reemplazar la estructura por expediente

El gestor admite personalizar el árbol generado según las necesidades del flujo
de trabajo. Existen dos caminos complementarios:

1. **Ajustar la instancia para usos futuros** con ``actualizar_estructura``:

   ```python
   gestor.actualizar_estructura(
       {
           "documentos_usuario": {"firmados": None},
           "audiencias": {"multimedia": None},
       }
   )
   gestor.generar_arbol()  # crea las carpetas extra además de las estándar
   ```

   Si necesitás reemplazar por completo la estructura base (por ejemplo en un
   entorno de pruebas aislado) indicá ``reemplazar=True``.

2. **Personalizar cada llamada** usando los parámetros ``estructura`` y
   ``fusionar_estructura`` de ``generar_arbol``. Esto resulta útil cuando sólo
   ciertos expedientes requieren carpetas adicionales:

   ```python
   manifest = gestor.generar_arbol(
       destino=base / "EXP_123_2024",
       estructura={"pericias": {"imagenes": None}},
   )
   ```

   Con ``fusionar_estructura=False`` podés generar árboles totalmente
   personalizados sin alterar la configuración del gestor.

Ambas variantes garantizan que el ``manifest.json`` refleje fielmente las
carpetas creadas, manteniendo sincronizadas las integraciones que dependen del
listado de directorios.
