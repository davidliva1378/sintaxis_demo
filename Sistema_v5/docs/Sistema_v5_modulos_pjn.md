# Propuesta de reorganización para módulos PJN en Sistema_v5

## Contexto
Los módulos `actuaciones`, `expedientes` y `entradas` obtienen sus datos mediante *scraping* del portal del PJN. Actualmente:

- `actuaciones` vive en el directorio raíz: `Sistema_v4/actuaciones`.
- `expedientes` y `entradas` residen en `Sistema_v4/operaciones/`.

En Sistema_v5 se busca un diseño más limpio que facilite el mantenimiento frente a cambios frecuentes del sitio.

## Directorio recomendado
Propongo agrupar los tres módulos bajo un paquete coherente que explicite su origen y responsabilidades:

```
Sistema_v5/
└── pjn/
    ├── scraping/
    │   ├── __init__.py
    │   ├── expedientes.py
    │   ├── actuaciones.py
    │   └── entradas.py
    ├── parsers/
    │   ├── __init__.py
    │   ├── expedientes_parser.py
    │   ├── actuaciones_parser.py
    │   └── entradas_parser.py
    └── services/
        ├── __init__.py
        ├── expedientes_service.py
        ├── actuaciones_service.py
        └── entradas_service.py
```

### Justificación
- **Paquete `pjn/`**: encapsula toda interacción con el portal. Hace evidente la dependencia externa y permite aislarla si en el futuro se reemplaza o añade otra fuente.
- **Subpaquete `scraping/`**: contiene la lógica de requests, selección de elementos y navegación. Comparte utilidades comunes (sesiones, autenticación, *retry*).
- **Subpaquete `parsers/`**: separa la extracción de datos de la estructura HTML, favoreciendo pruebas unitarias y simplificando los ajustes ante cambios en selectores.
- **Subpaquete `services/`**: orquesta los *use cases* de cada dominio (por ejemplo, armar un expediente completo con sus actuaciones) y expone APIs internas estables.

## Relación expedientes-actuaciones
Dado que las actuaciones pertenecen a un expediente, se recomienda:

- Mantener `actuaciones` como módulo independiente para no sobredimensionar `expedientes`, pero proveer clases o funciones compartidas en `services/` que creen un objeto `Expediente` agregando sus `Actuacion`.
- Implementar modelos de datos compartidos en `pjn/models/` (por ejemplo, `expediente.py`, `actuacion.py`) para garantizar tipos y validaciones comunes.

## ¿Conviene subdividir aún más?
Sí, es conveniente introducir capas adicionales cuando exista lógica especializada:

- **Módulo `pjn/models/`** con `pydantic` o *dataclasses* para representar entidades (`Expediente`, `Actuacion`, `Entrada`).
- **Módulo `pjn/tasks/`** o `pjn/pipelines/` si se automatiza la sincronización periódica.
- **Utilidades compartidas** en `pjn/utils/` (formateo de fechas, normalización de partes, manejo de tokens).

Esta subdivisión mantiene módulos pequeños, testeables y cohesivos, facilita el reemplazo de componentes y acorta la curva de ajuste cuando el sitio cambia su estructura.

## Refactor incremental sugerido
1. Mover el código existente a la nueva jerarquía sin cambios funcionales.
2. Extraer utilidades comunes (sesiones HTTP, manejo de *captcha*, `BeautifulSoup` wrappers) a `pjn/scraping/base.py`. ✅ Implementado: módulo `base.py` con helpers de autenticación Playwright, normalización de texto/fechas y generación de identificadores compartidos.
3. Crear modelos de dominio reutilizables en `pjn/models/`. ✅ Implementado: `Actuacion`,
   `ExpedienteResumen`, `ExpedienteIdentificacion` y `Entrada` con helpers de
   serialización compatibles con los JSON históricos.
4. Reescribir gradualmente las funciones de scraping para que retornen modelos, delegando a los parsers la responsabilidad de interpretar HTML.
   ✅ Iniciado: los scrapers de actuaciones, expedientes y entradas instancian
   dataclasses mediante los nuevos módulos de parsers y exponen funciones
   auxiliares (`obtener_actuaciones_todas_paginas_modelos_async`,
   `extraer_expedientes_completos_modelos`, `extraer_entradas_pjn_modelos`).
5. Añadir pruebas unitarias por módulo (parsers y services) y pruebas de integración con el portal (con *fixtures* controladas).
   ✅ Completado: además de las pruebas unitarias de utilidades y parsers,
   ahora existe una batería de tests de integración ligera en
   `tests/test_pjn_scraping_integration.py` que valida las funciones
   asincrónicas de scraping con *fixtures* controladas ubicadas en
   `tests/fixtures/pjn/`. Estas pruebas simulan la interacción con el portal y
   garantizan que las capas de scraping devuelvan los modelos dataclass
   esperados incluso ante refactors internos.

### Interpretación de resultados de prueba
- **`Process finished with exit code 0`**: indica que el proceso de pruebas finalizó
  sin errores ni fallos. Pytest usa este código para señalar que todas las
  aserciones pasaron correctamente.
- **Códigos distintos de 0** (`1`, `2`, etc.): señalan fallos, interrupciones o
  errores de ejecución. Pytest mostrará además un resumen con los tests que
  fallaron para facilitar el diagnóstico.

Esta organización minimiza dependencias circulares, centraliza la interacción con el PJN y prepara el proyecto para una futura migración a servicios externos o APIs oficiales si estuvieran disponibles.
