/**
 * Tipos para el servidor MCP (Model Context Protocol).
 */

// Estado del servidor MCP
export interface MCPStatus {
  running: boolean;
  pid: number | null;
  uptime_seconds: number;
  started_at: string | null;
  mode: 'stdio' | 'sse';
  port: number;
  host: string;
  auto_start: boolean;
  enabled_tools_count: number;
  log_file: string | null;
  // Opciones de seguridad (modo SSE)
  ssl_enabled: boolean;
  auth_enabled: boolean;
  rate_limit_enabled: boolean;
  rate_limit_rpm: number;
  rate_limit_rpm_auth: number;
}

// Configuración del servidor MCP
export interface MCPConfig {
  auto_start: boolean;
  mode: 'stdio' | 'sse';
  port: number;
  host: string;
  workspace_path: string;
  enabled_tools: string[];
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  // Opciones de seguridad (modo SSE)
  ssl_enabled: boolean;
  ssl_cert: string | null;
  ssl_key: string | null;
  auth_enabled: boolean;
  rate_limit_enabled: boolean;
  rate_limit_rpm: number;
  rate_limit_rpm_auth: number;
}

// Actualización parcial de configuración
export interface MCPConfigUpdate {
  auto_start?: boolean;
  mode?: 'stdio' | 'sse';
  port?: number;
  host?: string;
  workspace_path?: string;
  log_level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  // Opciones de seguridad (modo SSE)
  ssl_enabled?: boolean;
  ssl_cert?: string;
  ssl_key?: string;
  auth_enabled?: boolean;
  rate_limit_enabled?: boolean;
  rate_limit_rpm?: number;
  rate_limit_rpm_auth?: number;
}

// Tool disponible
export interface MCPTool {
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
}

// Recurso disponible
export interface MCPResource {
  uri: string;
  name: string;
  mimeType: string;
  description: string;
}

// Prompt disponible
export interface MCPPromptArgument {
  name: string;
  description: string;
  required: boolean;
}

export interface MCPPrompt {
  name: string;
  description: string;
  arguments: MCPPromptArgument[];
}

// Lista de tools
export interface MCPToolsResponse {
  tools: MCPTool[];
  total: number;
}

// Lista de recursos
export interface MCPResourcesResponse {
  resources: MCPResource[];
  total: number;
}

// Lista de prompts
export interface MCPPromptsResponse {
  prompts: MCPPrompt[];
  total: number;
}

// Respuesta de logs
export interface MCPLogsResponse {
  logs: string[];
  count: number;
}

// Estadísticas de uso de tools
export interface MCPToolStats {
  total_calls: number;
  calls_today: number;
  most_used: Array<{
    name: string;
    count: number;
  }>;
  avg_response_time_ms: number;
  errors_today: number;
}

// Respuesta de operaciones
export interface MCPOperationResult {
  success: boolean;
  message?: string;
  error?: string;
  pid?: number;
  exit_code?: number;
  config?: MCPConfig;
}

// Configuración de Claude Code
export interface ClaudeCodeConfig {
  config: string;
  instructions: string;
}

// Categorías de tools
export type ToolCategory =
  | 'expedientes'
  | 'actuaciones'
  | 'vencimientos'
  | 'entidades'
  | 'estadisticas'
  | 'analisis'
  | 'monitoreo'
  | 'otro';

// Mapeo de categorías a labels
export const TOOL_CATEGORY_LABELS: Record<ToolCategory, string> = {
  expedientes: 'Expedientes',
  actuaciones: 'Actuaciones',
  vencimientos: 'Vencimientos',
  entidades: 'Entidades NER',
  estadisticas: 'Estadísticas',
  analisis: 'Análisis',
  monitoreo: 'Monitoreo',
  otro: 'Otros',
};

// Colores para categorías
export const TOOL_CATEGORY_COLORS: Record<ToolCategory, string> = {
  expedientes: 'bg-blue-100 text-blue-800',
  actuaciones: 'bg-green-100 text-green-800',
  vencimientos: 'bg-yellow-100 text-yellow-800',
  entidades: 'bg-purple-100 text-purple-800',
  estadisticas: 'bg-pink-100 text-pink-800',
  analisis: 'bg-indigo-100 text-indigo-800',
  monitoreo: 'bg-orange-100 text-orange-800',
  otro: 'bg-gray-100 text-gray-800',
};
