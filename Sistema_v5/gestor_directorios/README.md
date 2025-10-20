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
│   ├── documentos_usuario/
│   └── json/
├── entradas/
│   └── json/
└── expedientes/
    ├── json/
    └── reportes/
```

Además de crear los directorios, el gestor escribe un archivo ``manifest.json`` que lista las
rutas generadas y permite adjuntar metadatos adicionales (por ejemplo el número de expediente
original y el normalizado).

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
