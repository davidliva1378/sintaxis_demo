"""
Módulo core del servidor MCP Sintaxis.

Proporciona componentes compartidos entre los servidores STDIO y SSE:
- ToolsRegistry: Registro unificado de definiciones de tools
- CertificateManager: Gestión de certificados SSL persistentes
- Logging: Configuración de logs con rotación
- Metrics: Sistema de métricas y telemetría
- Cache: Cache LRU para resultados de tools
"""

from .tools_registry import ToolsRegistry, ToolDefinition, ToolCategory
from .certificate_manager import CertificateManager, get_certificate_manager
from .logging_config import setup_mcp_logging, get_log_stats, cleanup_old_logs
from .metrics import (
    MetricsCollector,
    get_metrics,
    record_call,
    MetricsContext
)
from .cache import (
    ResultCache,
    get_cache,
    cached_call,
    CacheContext
)

__all__ = [
    # Tools Registry
    "ToolsRegistry",
    "ToolDefinition",
    "ToolCategory",
    # Certificate Manager
    "CertificateManager",
    "get_certificate_manager",
    # Logging
    "setup_mcp_logging",
    "get_log_stats",
    "cleanup_old_logs",
    # Metrics
    "MetricsCollector",
    "get_metrics",
    "record_call",
    "MetricsContext",
    # Cache
    "ResultCache",
    "get_cache",
    "cached_call",
    "CacheContext"
]
