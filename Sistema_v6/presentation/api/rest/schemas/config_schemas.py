"""Schemas para configuración del sistema.

Este módulo define los schemas Pydantic para los endpoints de configuración.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BrowserConfigSchema(BaseModel):
    """Schema para configuración del navegador.

    Attributes:
        headless: Si True, ejecuta el navegador sin interfaz gráfica
        timeout_ms: Timeout general en milisegundos
        navigation_timeout_ms: Timeout de navegación en milisegundos
        user_agent: User agent personalizado (None para usar default)
    """
    headless: bool
    timeout_ms: int
    navigation_timeout_ms: int
    user_agent: str | None = None


class MonitoreoConfigSchema(BaseModel):
    """Schema para configuración de monitoreo.

    Attributes:
        intervalo_segundos: Intervalo entre verificaciones (0 = ejecutar una vez)
        dias_actividad: Días hacia atrás para considerar expediente "activo"
        max_reintentos: Máximo de reintentos en caso de error
        notificar_cambios: Si True, envía notificaciones cuando hay cambios
        descargar_archivos: Si True, descarga archivos nuevos automáticamente

        # Configuración avanzada (opcional)
        intervalos_laboral_expedientes: Intervalo en minutos para expedientes en horario laboral
        intervalos_laboral_entradas: Intervalo en minutos para entradas en horario laboral
        intervalos_no_laboral_expedientes: Intervalo en minutos para expedientes fuera de horario laboral
        intervalos_no_laboral_entradas: Intervalo en minutos para entradas fuera de horario laboral
        dias_laborales: Lista de días laborales (lunes, martes, etc.)
        hora_inicio: Hora de inicio del horario laboral (formato HH:MM)
        hora_fin: Hora de fin del horario laboral (formato HH:MM)
    """
    # Básico
    intervalo_segundos: int
    dias_actividad: int
    max_reintentos: int
    notificar_cambios: bool
    descargar_archivos: bool

    # Opciones de extracción
    fecha_corte_dias: int | None = None
    max_paginas_monitoreo: int | None = None
    tiempo_maximo_extraccion: int | None = None
    detener_en_duplicado: bool = True
    orden_extraccion: str = "fecha"

    # Avanzado (opcional)
    intervalos_laboral_expedientes: int | None = None
    intervalos_laboral_entradas: int | None = None
    intervalos_no_laboral_expedientes: int | None = None
    intervalos_no_laboral_entradas: int | None = None
    dias_laborales: list[str]
    hora_inicio: str
    hora_fin: str


class ScrapingConfigSchema(BaseModel):
    """Schema para configuración de scraping.

    Attributes:
        timeout_default: Timeout por defecto en ms para operaciones de scraping
        timeout_login: Timeout para operaciones de login en ms
        timeout_descarga: Timeout para descarga de archivos en ms
        max_paginas_expedientes: Máximo de páginas a extraer (None = sin límite)
        max_reintentos_descarga: Máximo de reintentos para descargas
    """
    timeout_default: int
    timeout_login: int
    timeout_descarga: int
    max_paginas_expedientes: int | None = None
    max_reintentos_descarga: int


class MCPConfigSchema(BaseModel):
    """Schema para configuración del servidor MCP.

    Attributes:
        habilitar: Si True, habilita el servidor MCP
        puerto: Puerto donde escucha el servidor MCP
        mode: Modo del servidor MCP (stdio, http)
        workspace_path: Path del workspace para MCP
        server_name: Nombre del servidor MCP
        enable_pdf_extraction: Si True, habilita extracción de PDFs
        enable_full_text_search: Si True, habilita búsqueda de texto completo
        enable_statistics: Si True, habilita estadísticas
        max_pdf_pages: Límite de páginas por PDF
        max_pdf_size_mb: Tamaño máximo de PDF en MB
    """
    habilitar: bool
    puerto: int
    mode: Literal["stdio", "http"]
    workspace_path: str
    server_name: str
    enable_pdf_extraction: bool
    enable_full_text_search: bool
    enable_statistics: bool
    max_pdf_pages: int
    max_pdf_size_mb: int


class StorageConfigSchema(BaseModel):
    """Schema para configuración de almacenamiento.

    Attributes:
        base_path: Directorio base para almacenamiento de datos
        json_base_file: Nombre del archivo JSON "base" (todos los expedientes)
        json_sistema_file: Nombre del archivo JSON "sistema" (expedientes seleccionados)
        workspaces_dir: Nombre del directorio de workspaces
        downloads_dir: Nombre del directorio de descargas
        pretty_json: Si True, formatea el JSON con indentación
        ensure_ascii: Si True, escapa caracteres no-ASCII en JSON
    """
    base_path: str
    json_base_file: str
    json_sistema_file: str
    workspaces_dir: str
    downloads_dir: str
    pretty_json: bool
    ensure_ascii: bool


class SystemConfigResponse(BaseModel):
    """Schema de respuesta con toda la configuración del sistema.

    Attributes:
        browser: Configuración del navegador
        monitoreo: Configuración de monitoreo
        scraping: Configuración de scraping
        mcp: Configuración del servidor MCP
        storage: Configuración de almacenamiento
    """
    browser: BrowserConfigSchema
    monitoreo: MonitoreoConfigSchema
    scraping: ScrapingConfigSchema
    mcp: MCPConfigSchema
    storage: StorageConfigSchema


class SystemConfigUpdateRequest(BaseModel):
    """Schema de request para actualizar configuración del sistema.

    Attributes:
        browser: Configuración del navegador (opcional)
        monitoreo: Configuración de monitoreo (opcional)
        scraping: Configuración de scraping (opcional)
        mcp: Configuración del servidor MCP (opcional)
        storage: Configuración de almacenamiento (opcional)
    """
    browser: BrowserConfigSchema | None = None
    monitoreo: MonitoreoConfigSchema | None = None
    scraping: ScrapingConfigSchema | None = None
    mcp: MCPConfigSchema | None = None
    storage: StorageConfigSchema | None = None


class ConfigUpdateResponse(BaseModel):
    """Schema de respuesta tras actualizar configuración.

    Attributes:
        success: Si la actualización fue exitosa
        message: Mensaje descriptivo
        updates: Diccionario con las variables actualizadas
    """
    success: bool
    message: str
    updates: dict[str, str]
