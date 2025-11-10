"""Core package - Domain Layer.

Este paquete contiene la lógica de negocio pura del sistema, sin dependencias externas.

Módulos:
    - domain: Entidades, value objects, utils y excepciones del dominio
    - plugins: Sistema de plugins extensible

Principios:
    - Sin dependencias de infrastructure, application o presentation
    - Funciones puras sin side effects
    - Inmutabilidad en modelos de dominio
    - Type hints completos
"""

__version__ = "6.0.0"
