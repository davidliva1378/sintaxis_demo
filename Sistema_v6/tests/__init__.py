"""Tests package - Suite completa de tests.

Este paquete contiene todos los tests del sistema organizados por tipo.

Estructura:
    - unit: Tests unitarios (por capa: core, application, infrastructure, presentation)
    - integration: Tests de integración entre capas
    - e2e: Tests end-to-end del workflow completo

Ejecutar tests:
    pytest tests/                    # Todos los tests
    pytest tests/unit/               # Solo unit tests
    pytest tests/integration/        # Solo integration tests
    pytest tests/e2e/                # Solo E2E tests
    pytest tests/ --cov              # Con cobertura

Objetivo de cobertura:
    - Domain: 100%
    - Application: 90%+
    - Infrastructure: 80%+
    - Presentation: 70%+
    - Total: 85%+
"""

__version__ = "6.0.0"
