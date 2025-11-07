"""Sistema de extracción masiva de expedientes - Versión 6.1.

Este paquete proporciona herramientas para la extracción masiva y estructurada
de expedientes judiciales, incluyendo:

- Gestión de estados de expedientes
- Organización de directorios
- Procesamiento batch con manejo de errores
- Generación de reportes

Componentes principales:
- EstadoExpediente: Enum con estados de expedientes
- ExpedienteInfo: Dataclass para información de expedientes
- EstadosManager: Gestor de estados persistentes
- GestorDirectoriosExpedientes: Creación de estructura de directorios
- ExtractorCompletoBatch: Procesador batch para extracción
"""

from .gestor_directorios import GestorDirectoriosExpedientes
from .gestor_estados import EstadosManager
from .models import EstadoExpediente, ExpedienteInfo
from .procesador_batch import ExtractorCompletoBatch, ResumenBatch, ResultadoExpediente

__version__ = "6.1.0"

__all__ = [
    # Modelos
    "EstadoExpediente",
    "ExpedienteInfo",
    # Gestores
    "EstadosManager",
    "GestorDirectoriosExpedientes",
    # Procesadores
    "ExtractorCompletoBatch",
    "ResumenBatch",
    "ResultadoExpediente",
]
