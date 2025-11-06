"""API Schemas - Pydantic models for request/response validation."""

from .auth_schemas import (
    PJNCredentialsResponse,
    PJNCredentialsUpdate,
    Token,
    TokenData,
    UserLogin,
    UserRegister,
    UserResponse,
)
from .expediente_schemas import (
    ActuacionResponse,
    ExpedienteResponse,
    ExtraerExpedientesRequest,
    ExtraerExpedientesResponse,
    FiltrarExpedientesRequest,
    FiltrarExpedientesResponse,
    ListarExpedientesResponse,
)
from .monitoreo_schemas import (
    IniciarMonitoreoRequest,
    MonitoreoResponse,
)
from .workspace_schemas import (
    CrearWorkspacesRequest,
    CrearWorkspacesResponse,
)
from .config_schemas import (
    BrowserConfigSchema,
    MonitoreoConfigSchema,
    ScrapingConfigSchema,
    MCPConfigSchema,
    StorageConfigSchema,
    SystemConfigResponse,
    SystemConfigUpdateRequest,
    ConfigUpdateResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
    "UserResponse",
    "PJNCredentialsUpdate",
    "PJNCredentialsResponse",
    # Expedientes
    "ExpedienteResponse",
    "ActuacionResponse",
    "ExtraerExpedientesRequest",
    "ExtraerExpedientesResponse",
    "FiltrarExpedientesRequest",
    "FiltrarExpedientesResponse",
    "ListarExpedientesResponse",
    # Monitoreo
    "IniciarMonitoreoRequest",
    "MonitoreoResponse",
    # Workspaces
    "CrearWorkspacesRequest",
    "CrearWorkspacesResponse",
    # Config
    "BrowserConfigSchema",
    "MonitoreoConfigSchema",
    "ScrapingConfigSchema",
    "MCPConfigSchema",
    "StorageConfigSchema",
    "SystemConfigResponse",
    "SystemConfigUpdateRequest",
    "ConfigUpdateResponse",
]
