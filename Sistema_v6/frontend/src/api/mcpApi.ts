/**
 * API client para gestión del servidor MCP.
 */

import {
  MCPStatus,
  MCPConfig,
  MCPConfigUpdate,
  MCPToolsResponse,
  MCPResourcesResponse,
  MCPPromptsResponse,
  MCPLogsResponse,
  MCPToolStats,
  MCPOperationResult,
  ClaudeCodeConfig,
} from '../types/mcp';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Obtiene el estado actual del servidor MCP.
 */
export async function getMCPStatus(): Promise<MCPStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/status`);
  if (!response.ok) {
    throw new Error('Error obteniendo estado del servidor MCP');
  }
  return response.json();
}

/**
 * Inicia el servidor MCP.
 */
export async function startMCPServer(): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error iniciando servidor MCP');
  }
  return response.json();
}

/**
 * Detiene el servidor MCP.
 */
export async function stopMCPServer(): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/stop`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error deteniendo servidor MCP');
  }
  return response.json();
}

/**
 * Reinicia el servidor MCP.
 */
export async function restartMCPServer(): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/restart`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error reiniciando servidor MCP');
  }
  return response.json();
}

/**
 * Obtiene la configuración del servidor MCP.
 */
export async function getMCPConfig(): Promise<MCPConfig> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/config`);
  if (!response.ok) {
    throw new Error('Error obteniendo configuración MCP');
  }
  return response.json();
}

/**
 * Actualiza la configuración del servidor MCP.
 */
export async function updateMCPConfig(
  config: MCPConfigUpdate
): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/config`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error actualizando configuración MCP');
  }
  return response.json();
}

/**
 * Obtiene los logs del servidor MCP.
 */
export async function getMCPLogs(lines: number = 100): Promise<MCPLogsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/logs?lines=${lines}`);
  if (!response.ok) {
    throw new Error('Error obteniendo logs MCP');
  }
  return response.json();
}

/**
 * Limpia los logs del servidor MCP.
 */
export async function clearMCPLogs(): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/logs`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error limpiando logs MCP');
  }
  return response.json();
}

/**
 * Obtiene la lista de tools disponibles.
 */
export async function getMCPTools(): Promise<MCPToolsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/tools`);
  if (!response.ok) {
    throw new Error('Error obteniendo tools MCP');
  }
  return response.json();
}

/**
 * Obtiene la lista de recursos disponibles.
 */
export async function getMCPResources(): Promise<MCPResourcesResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/resources`);
  if (!response.ok) {
    throw new Error('Error obteniendo resources MCP');
  }
  return response.json();
}

/**
 * Obtiene la lista de prompts disponibles.
 */
export async function getMCPPrompts(): Promise<MCPPromptsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/prompts`);
  if (!response.ok) {
    throw new Error('Error obteniendo prompts MCP');
  }
  return response.json();
}

/**
 * Establece las tools habilitadas.
 */
export async function setEnabledTools(
  tools: string[]
): Promise<MCPOperationResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/tools/enable`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tools }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Error actualizando tools habilitadas');
  }
  return response.json();
}

/**
 * Obtiene estadísticas de uso de tools.
 */
export async function getToolStats(): Promise<MCPToolStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/tools/stats`);
  if (!response.ok) {
    throw new Error('Error obteniendo estadísticas de tools');
  }
  return response.json();
}

/**
 * Obtiene la configuración para Claude Code.
 */
export async function getClaudeCodeConfig(): Promise<ClaudeCodeConfig> {
  const response = await fetch(`${API_BASE_URL}/api/v1/mcp/claude-config`);
  if (!response.ok) {
    throw new Error('Error obteniendo configuración de Claude Code');
  }
  return response.json();
}
