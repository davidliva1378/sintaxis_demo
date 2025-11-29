/**
 * Componente para configuración del servidor MCP.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import {
  Play,
  Square,
  RotateCcw,
  Settings,
  Code,
  FileText,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  Server,
  Wrench,
  Database,
  MessageSquare,
} from 'lucide-react';
import {
  getMCPStatus,
  startMCPServer,
  stopMCPServer,
  restartMCPServer,
  getMCPConfig,
  updateMCPConfig,
  getMCPLogs,
  clearMCPLogs,
  getMCPTools,
  setEnabledTools,
  getClaudeCodeConfig,
  getMCPResources,
  getMCPPrompts,
} from '../../api/mcpApi';
import {
  MCPStatus,
  MCPConfig,
  MCPTool,
  MCPResource,
  MCPPrompt,
  ToolCategory,
  TOOL_CATEGORY_LABELS,
  TOOL_CATEGORY_COLORS,
} from '../../types/mcp';

export function ConfiguracionMCP() {
  // Estado
  const [status, setStatus] = useState<MCPStatus | null>(null);
  const [config, setConfig] = useState<MCPConfig | null>(null);
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [prompts, setPrompts] = useState<MCPPrompt[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [claudeConfig, setClaudeConfig] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cargar datos iniciales
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusData, configData, toolsData, resourcesData, promptsData, logsData, claudeData] = await Promise.all([
        getMCPStatus(),
        getMCPConfig(),
        getMCPTools(),
        getMCPResources(),
        getMCPPrompts(),
        getMCPLogs(100),
        getClaudeCodeConfig(),
      ]);
      setStatus(statusData);
      setConfig(configData);
      setTools(toolsData.tools);
      setResources(resourcesData.resources);
      setPrompts(promptsData.prompts);
      setLogs(logsData.logs);
      setClaudeConfig(claudeData.config);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Acciones del servidor
  const handleStart = async () => {
    try {
      setActionLoading(true);
      await startMCPServer();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error iniciando servidor');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setActionLoading(true);
      await stopMCPServer();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error deteniendo servidor');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestart = async () => {
    try {
      setActionLoading(true);
      await restartMCPServer();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error reiniciando servidor');
    } finally {
      setActionLoading(false);
    }
  };

  // Actualizar configuración
  const handleConfigChange = async (key: string, value: boolean | string | number) => {
    try {
      await updateMCPConfig({ [key]: value });
      setConfig(prev => prev ? { ...prev, [key]: value } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error actualizando configuración');
    }
  };

  // Toggle tool
  const handleToolToggle = async (toolName: string, enabled: boolean) => {
    const currentEnabled = tools.filter(t => t.enabled).map(t => t.name);
    let newEnabled: string[];

    if (enabled) {
      newEnabled = [...currentEnabled, toolName];
    } else {
      newEnabled = currentEnabled.filter(n => n !== toolName);
    }

    try {
      await setEnabledTools(newEnabled);
      setTools(prev =>
        prev.map(t => (t.name === toolName ? { ...t, enabled } : t))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error actualizando tools');
    }
  };

  // Limpiar logs
  const handleClearLogs = async () => {
    try {
      await clearMCPLogs();
      setLogs([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error limpiando logs');
    }
  };

  // Copiar configuración
  const handleCopyConfig = async () => {
    try {
      await navigator.clipboard.writeText(claudeConfig);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Error copiando al portapapeles');
    }
  };

  // Formatear uptime
  const formatUptime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  // Agrupar tools por categoría
  const toolsByCategory = tools.reduce((acc, tool) => {
    const cat = tool.category as ToolCategory;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tool);
    return acc;
  }, {} as Record<ToolCategory, MCPTool[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Estado del Servidor */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              <CardTitle className="text-lg">Estado del Servidor</CardTitle>
            </div>
            <Badge variant={status?.running ? 'default' : 'secondary'}>
              {status?.running ? 'Activo' : 'Detenido'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleStart}
              disabled={actionLoading || status?.running}
              className="gap-1"
            >
              <Play className="h-4 w-4" />
              Iniciar
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleStop}
              disabled={actionLoading || !status?.running}
              className="gap-1"
            >
              <Square className="h-4 w-4" />
              Detener
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleRestart}
              disabled={actionLoading}
              className="gap-1"
            >
              <RotateCcw className="h-4 w-4" />
              Reiniciar
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={loadData}
              disabled={loading}
              className="gap-1"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {status?.running && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">PID:</span>{' '}
                <span className="font-mono">{status.pid}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Uptime:</span>{' '}
                <span>{formatUptime(status.uptime_seconds)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Modo:</span>{' '}
                <span className="uppercase">{status.mode}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Tools:</span>{' '}
                <span>{status.enabled_tools_count}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tabs de configuración */}
      <Tabs defaultValue="config" className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="config" className="gap-1">
            <Settings className="h-4 w-4" />
            Config
          </TabsTrigger>
          <TabsTrigger value="tools" className="gap-1">
            <Wrench className="h-4 w-4" />
            Tools
          </TabsTrigger>
          <TabsTrigger value="resources" className="gap-1">
            <Database className="h-4 w-4" />
            Recursos
          </TabsTrigger>
          <TabsTrigger value="prompts" className="gap-1">
            <MessageSquare className="h-4 w-4" />
            Prompts
          </TabsTrigger>
          <TabsTrigger value="logs" className="gap-1">
            <FileText className="h-4 w-4" />
            Logs
          </TabsTrigger>
          <TabsTrigger value="claude" className="gap-1">
            <Code className="h-4 w-4" />
            Claude
          </TabsTrigger>
        </TabsList>

        {/* Configuración */}
        <TabsContent value="config">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Configuración General</CardTitle>
              <CardDescription>
                Opciones de inicio y comportamiento del servidor MCP
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Inicio automático</div>
                  <div className="text-sm text-muted-foreground">
                    Iniciar el servidor al arrancar la API
                  </div>
                </div>
                <Switch
                  checked={config?.auto_start ?? false}
                  onCheckedChange={(checked) => handleConfigChange('auto_start', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Modo de transporte</div>
                  <div className="text-sm text-muted-foreground">
                    stdio: local, SSE: acceso remoto
                  </div>
                </div>
                <select
                  value={config?.mode ?? 'stdio'}
                  onChange={(e) => handleConfigChange('mode', e.target.value)}
                  className="px-3 py-1 border rounded-md text-sm"
                >
                  <option value="stdio">STDIO (local)</option>
                  <option value="sse">SSE (remoto)</option>
                </select>
              </div>

              {config?.mode === 'sse' && (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Puerto SSE</div>
                    <div className="text-sm text-muted-foreground">
                      Puerto para conexiones remotas
                    </div>
                  </div>
                  <Input
                    type="number"
                    value={config?.port ?? 8765}
                    onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
                    className="w-24 text-sm"
                    min={1024}
                    max={65535}
                  />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Nivel de log</div>
                  <div className="text-sm text-muted-foreground">
                    Detalle de los logs del servidor
                  </div>
                </div>
                <select
                  value={config?.log_level ?? 'INFO'}
                  onChange={(e) => handleConfigChange('log_level', e.target.value)}
                  className="px-3 py-1 border rounded-md text-sm"
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </div>

              {config?.mode === 'sse' && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md text-sm">
                  <div className="font-medium text-blue-700 dark:text-blue-300">
                    Modo SSE con HTTPS habilitado
                  </div>
                  <div className="text-blue-600 dark:text-blue-400 mt-1">
                    El servidor escuchará en el puerto {config?.port ?? 8765}.
                    Configura Claude Desktop con la URL: https://IP:{config?.port ?? 8765}/sse
                  </div>
                  <div className="text-blue-500 dark:text-blue-500 mt-2 text-xs">
                    Nota: Se genera un certificado auto-firmado. Es posible que necesites
                    importarlo como confiable en tu sistema.
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Herramientas */}
        <TabsContent value="tools">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Herramientas Disponibles</CardTitle>
              <CardDescription>
                Habilita o deshabilita herramientas para el servidor MCP ({tools.length} total)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
                <div key={category}>
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${TOOL_CATEGORY_COLORS[category as ToolCategory]}`}>
                      {TOOL_CATEGORY_LABELS[category as ToolCategory]}
                    </span>
                    <span className="text-muted-foreground text-sm">
                      ({categoryTools.length})
                    </span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {categoryTools.map((tool) => (
                      <div
                        key={tool.name}
                        className="flex items-center justify-between p-2 border rounded-md hover:bg-muted/50"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="font-mono text-sm truncate">{tool.name}</div>
                          <div className="text-xs text-muted-foreground truncate">
                            {tool.description}
                          </div>
                        </div>
                        <Switch
                          checked={tool.enabled}
                          onCheckedChange={(checked) => handleToolToggle(tool.name, checked)}
                          className="ml-2"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Recursos */}
        <TabsContent value="resources">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recursos Disponibles</CardTitle>
              <CardDescription>
                Recursos de datos expuestos por el servidor MCP ({resources.length} total)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {resources.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No hay recursos disponibles
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {resources.map((resource) => (
                    <div
                      key={resource.uri}
                      className="p-3 border rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm">{resource.name}</span>
                            <Badge variant="outline" className="text-xs font-mono">
                              {resource.mimeType}
                            </Badge>
                          </div>
                          <div className="text-xs text-muted-foreground mb-2">
                            {resource.description}
                          </div>
                          <div className="bg-muted p-1.5 rounded text-xs font-mono truncate text-muted-foreground">
                            {resource.uri}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Prompts */}
        <TabsContent value="prompts">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Prompts Disponibles</CardTitle>
              <CardDescription>
                Plantillas de prompts predefinidas ({prompts.length} total)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {prompts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No hay prompts disponibles
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3">
                  {prompts.map((prompt) => (
                    <div
                      key={prompt.name}
                      className="p-3 border rounded-md hover:bg-muted/50 transition-colors"
                    >
                      <div className="mb-2">
                        <div className="font-medium text-sm flex items-center gap-2">
                          {prompt.name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {prompt.description}
                        </div>
                      </div>

                      {prompt.arguments && prompt.arguments.length > 0 && (
                        <div className="mt-3 pt-3 border-t">
                          <div className="text-xs font-medium text-muted-foreground mb-2">Argumentos:</div>
                          <div className="space-y-1">
                            {prompt.arguments.map((arg) => (
                              <div key={arg.name} className="flex items-center text-xs gap-2">
                                <span className="font-mono bg-muted px-1 rounded">{arg.name}</span>
                                <span className="text-muted-foreground">- {arg.description}</span>
                                {arg.required && (
                                  <Badge variant="secondary" className="h-4 px-1 text-[10px]">Required</Badge>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs */}
        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Logs del Servidor</CardTitle>
                  <CardDescription>
                    Últimas {logs.length} líneas del log
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={loadData} className="gap-1">
                    <RefreshCw className="h-3 w-3" />
                    Actualizar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleClearLogs}
                    className="gap-1"
                  >
                    <Trash2 className="h-3 w-3" />
                    Limpiar
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="bg-muted rounded-md p-3 h-64 overflow-auto font-mono text-xs">
                {logs.length === 0 ? (
                  <div className="text-muted-foreground">Sin logs disponibles</div>
                ) : (
                  logs.map((line, i) => (
                    <div key={i} className="whitespace-pre-wrap">
                      {line}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Configuración Claude */}
        <TabsContent value="claude">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Configuración para Claude Code</CardTitle>
                  <CardDescription>
                    Copia este JSON a ~/.config/claude-code/mcp.json
                  </CardDescription>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyConfig}
                  className="gap-1"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3" />
                      Copiado
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      Copiar
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted rounded-md p-3 overflow-auto font-mono text-xs">
                {claudeConfig}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
