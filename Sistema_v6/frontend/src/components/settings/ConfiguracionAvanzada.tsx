/**
 * ConfiguracionAvanzada - Configuraciones avanzadas (MCP Server y Storage)
 */

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Cog, Save, Server, Database, ChevronDown, ChevronRight } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'

// Schema de validación
const avanzadaSchema = z.object({
  // MCP
  mcp_habilitar: z.boolean(),
  mcp_puerto: z.number().min(1).max(65535),
  mcp_mode: z.enum(['stdio', 'http']),
  mcp_workspace_path: z.string().min(1),
  mcp_server_name: z.string().min(1),
  mcp_enable_pdf_extraction: z.boolean(),
  mcp_enable_full_text_search: z.boolean(),
  mcp_enable_statistics: z.boolean(),
  mcp_max_pdf_pages: z.number().min(1).max(10000),
  mcp_max_pdf_size_mb: z.number().min(1).max(1000),

  // Storage
  storage_base_path: z.string().min(1),
  storage_json_base_file: z.string().min(1),
  storage_json_sistema_file: z.string().min(1),
  storage_workspaces_dir: z.string().min(1),
  storage_downloads_dir: z.string().min(1),
  storage_pretty_json: z.boolean(),
  storage_ensure_ascii: z.boolean(),
})

type AvanzadaForm = z.infer<typeof avanzadaSchema>

export default function ConfiguracionAvanzada() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [mcpExpanded, setMcpExpanded] = useState(true)
  const [storageExpanded, setStorageExpanded] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setValue,
    watch,
  } = useForm<AvanzadaForm>({
    resolver: zodResolver(avanzadaSchema),
    defaultValues: {
      mcp_habilitar: true,
      mcp_puerto: 5000,
      mcp_mode: 'stdio',
      mcp_workspace_path: 'workspace',
      mcp_server_name: 'sintaxis-actuaciones-v6',
      mcp_enable_pdf_extraction: true,
      mcp_enable_full_text_search: true,
      mcp_enable_statistics: true,
      mcp_max_pdf_pages: 100,
      mcp_max_pdf_size_mb: 50,

      storage_base_path: 'data',
      storage_json_base_file: 'expedientes_base.json',
      storage_json_sistema_file: 'expedientes_sistema.json',
      storage_workspaces_dir: 'workspaces',
      storage_downloads_dir: 'descargas',
      storage_pretty_json: true,
      storage_ensure_ascii: false,
    },
  })

  const mcpHabilitado = watch('mcp_habilitar')

  // Cargar configuración actual del servidor
  useEffect(() => {
    const cargarConfiguracion = async () => {
      try {
        const response = await fetch('/api/v1/config/sistema')
        if (!response.ok) throw new Error('Error al cargar configuración')

        const data = await response.json()
        const { mcp, storage } = data

        // MCP
        setValue('mcp_habilitar', mcp.habilitar)
        setValue('mcp_puerto', mcp.puerto)
        setValue('mcp_mode', mcp.mode)
        setValue('mcp_workspace_path', mcp.workspace_path)
        setValue('mcp_server_name', mcp.server_name)
        setValue('mcp_enable_pdf_extraction', mcp.enable_pdf_extraction)
        setValue('mcp_enable_full_text_search', mcp.enable_full_text_search)
        setValue('mcp_enable_statistics', mcp.enable_statistics)
        setValue('mcp_max_pdf_pages', mcp.max_pdf_pages)
        setValue('mcp_max_pdf_size_mb', mcp.max_pdf_size_mb)

        // Storage
        setValue('storage_base_path', storage.base_path)
        setValue('storage_json_base_file', storage.json_base_file)
        setValue('storage_json_sistema_file', storage.json_sistema_file)
        setValue('storage_workspaces_dir', storage.workspaces_dir)
        setValue('storage_downloads_dir', storage.downloads_dir)
        setValue('storage_pretty_json', storage.pretty_json)
        setValue('storage_ensure_ascii', storage.ensure_ascii)

        setIsLoading(false)
      } catch (error) {
        console.error('Error cargando configuración:', error)
        toast.error('Error al cargar configuración')
        setIsLoading(false)
      }
    }

    cargarConfiguracion()
  }, [setValue])

  const onSubmit = async (data: AvanzadaForm) => {
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/v1/config/sistema', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mcp: {
            habilitar: data.mcp_habilitar,
            puerto: data.mcp_puerto,
            mode: data.mcp_mode,
            workspace_path: data.mcp_workspace_path,
            server_name: data.mcp_server_name,
            enable_pdf_extraction: data.mcp_enable_pdf_extraction,
            enable_full_text_search: data.mcp_enable_full_text_search,
            enable_statistics: data.mcp_enable_statistics,
            max_pdf_pages: data.mcp_max_pdf_pages,
            max_pdf_size_mb: data.mcp_max_pdf_size_mb,
          },
          storage: {
            base_path: data.storage_base_path,
            json_base_file: data.storage_json_base_file,
            json_sistema_file: data.storage_json_sistema_file,
            workspaces_dir: data.storage_workspaces_dir,
            downloads_dir: data.storage_downloads_dir,
            pretty_json: data.storage_pretty_json,
            ensure_ascii: data.storage_ensure_ascii,
          },
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Error al actualizar')
      }

      const result = await response.json()

      toast.success('Configuración actualizada', {
        description: result.message,
      })

      reset(data)
    } catch (error: any) {
      console.error('Error al actualizar configuración:', error)
      toast.error('Error al actualizar', {
        description: error.message,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
          <Cog className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configuración Avanzada
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            MCP Server, Storage y otras configuraciones del sistema
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Sección MCP Server */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setMcpExpanded(!mcpExpanded)}
            className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Server className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <div className="text-left">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  MCP Server (Model Context Protocol)
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Servidor para integración con Claude y otros LLMs
                </p>
              </div>
            </div>
            {mcpExpanded ? (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
          </button>

          {mcpExpanded && (
            <div className="p-4 space-y-4">
              {/* Toggle habilitar MCP */}
              <label className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    Habilitar servidor MCP
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Activar el servidor para integración con LLMs
                  </div>
                </div>
                <input
                  {...register('mcp_habilitar')}
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>

              <div className={mcpHabilitado ? '' : 'opacity-50 pointer-events-none'}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Puerto
                    </label>
                    <input
                      {...register('mcp_puerto', { valueAsNumber: true })}
                      type="number"
                      min="1"
                      max="65535"
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                    {errors.mcp_puerto && (
                      <p className="mt-1 text-xs text-red-600">{errors.mcp_puerto.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Modo
                    </label>
                    <select
                      {...register('mcp_mode')}
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="stdio">stdio</option>
                      <option value="http">http</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Workspace Path
                    </label>
                    <input
                      {...register('mcp_workspace_path')}
                      type="text"
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Server Name
                    </label>
                    <input
                      {...register('mcp_server_name')}
                      type="text"
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>

                {/* Features MCP */}
                <div className="space-y-2 pt-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Funcionalidades
                  </h4>

                  <label className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                    <input
                      {...register('mcp_enable_pdf_extraction')}
                      type="checkbox"
                      disabled={!mcpHabilitado}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Extracción de PDFs
                    </span>
                  </label>

                  <label className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                    <input
                      {...register('mcp_enable_full_text_search')}
                      type="checkbox"
                      disabled={!mcpHabilitado}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Búsqueda de texto completo
                    </span>
                  </label>

                  <label className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                    <input
                      {...register('mcp_enable_statistics')}
                      type="checkbox"
                      disabled={!mcpHabilitado}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Estadísticas
                    </span>
                  </label>
                </div>

                {/* Límites PDF */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Máx. páginas por PDF
                    </label>
                    <input
                      {...register('mcp_max_pdf_pages', { valueAsNumber: true })}
                      type="number"
                      min="1"
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Máx. tamaño PDF (MB)
                    </label>
                    <input
                      {...register('mcp_max_pdf_size_mb', { valueAsNumber: true })}
                      type="number"
                      min="1"
                      disabled={!mcpHabilitado}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sección Storage */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setStorageExpanded(!storageExpanded)}
            className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Database className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              <div className="text-left">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                  Storage (Almacenamiento)
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Configuración de rutas y archivos del sistema
                </p>
              </div>
            </div>
            {storageExpanded ? (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-400" />
            )}
          </button>

          {storageExpanded && (
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Directorio base
                </label>
                <input
                  {...register('storage_base_path')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Directorio donde se almacenan todos los datos
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Archivo JSON base
                  </label>
                  <input
                    {...register('storage_json_base_file')}
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Archivo JSON sistema
                  </label>
                  <input
                    {...register('storage_json_sistema_file')}
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Directorio workspaces
                  </label>
                  <input
                    {...register('storage_workspaces_dir')}
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Directorio descargas
                  </label>
                  <input
                    {...register('storage_downloads_dir')}
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              {/* Opciones de formato JSON */}
              <div className="space-y-2 pt-4">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Formato de archivos JSON
                </h4>

                <label className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                  <input
                    {...register('storage_pretty_json')}
                    type="checkbox"
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Pretty JSON (con indentación)
                    </span>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Más legible pero ocupa más espacio
                    </p>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800">
                  <input
                    {...register('storage_ensure_ascii')}
                    type="checkbox"
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      Ensure ASCII
                    </span>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Escapar caracteres no-ASCII (tildes, ñ, etc.)
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Botón Guardar */}
        <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button
            type="submit"
            disabled={!isDirty || isSubmitting}
            className="flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isSubmitting ? 'Guardando...' : 'Guardar configuración'}
          </Button>
        </div>
      </form>
    </Card>
  )
}
