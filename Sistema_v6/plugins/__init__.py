"""Plugins package - Extensiones del sistema.

Este paquete contiene plugins extensibles que agregan funcionalidad al sistema
sin modificar el core.

Plugins disponibles:
    - auth: Autenticación y permisos multi-usuario
    - notificaciones: Email, Telegram, WhatsApp, Discord
    - oficios_digitales: Envío de oficios al PJN
    - ia_local: Integración con Ollama (RAG, análisis)
    - pdf_processing: OCR, extracción de entidades, búsqueda
    - escritos_automaticos: Generación de escritos con IA

Cada plugin debe implementar PluginInterface y ser cargado por PluginManager.

Ver docs/DEVELOPER_GUIDE.md para crear un plugin personalizado.
"""

__version__ = "6.0.0"
