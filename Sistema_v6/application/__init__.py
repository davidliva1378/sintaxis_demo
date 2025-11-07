"""Application package - Application Layer.

Este paquete contiene los casos de uso y servicios de aplicación que orquestan
la lógica de negocio del sistema.

Módulos:
    - use_cases: Casos de uso de las 4 fases del sistema
    - services: Servicios de aplicación reutilizables
    - dto: Data Transfer Objects para comunicación entre capas
    - ports: Interfaces (abstracciones) para inversión de dependencias

Principios:
    - Depende solo de Domain (core)
    - Infrastructure implementa los Ports
    - Orquesta lógica de negocio sin implementar detalles técnicos
"""

__version__ = "6.0.0"
