"""Infrastructure package - Infrastructure Layer.

Este paquete contiene las implementaciones concretas de los adapters que
interactúan con el mundo exterior (bases de datos, APIs, scraping, etc.).

Módulos:
    - scraping: Web scraping con Playwright
    - parsers: Parsers HTML → Domain models
    - persistence: Repositories (JSON, filesystem)
    - config: Configuración del sistema
    - monitoring: Sistema de monitoreo
    - notification: Notificaciones del sistema
    - scheduling: Programación de tareas
    - logging: Sistema de logging
    - pdf: Procesamiento de PDFs

Principios:
    - Implementa los Ports definidos en Application
    - Puede depender de Domain y Application (solo Ports)
    - Contiene todas las dependencias externas (Playwright, FastAPI, etc.)
"""

__version__ = "6.0.0"
