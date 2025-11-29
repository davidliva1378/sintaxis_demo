/**
 * ConfiguracionIA - Panel de configuración para RAG y LLM
 */

import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Brain,
  Database,
  Cpu,
  RefreshCw,
  Settings2,
  CheckCircle,
  XCircle,
  Thermometer,
  Search,
  Sparkles,
  Info,
  Save,
  RotateCcw,
} from 'lucide-react'
import { ragApi, type ConfigResponse, type StatsResponse, type HealthCheckResponse, type ModelsResponse } from '@/api/ragApi'
import { getIAStatus, setModelo, type IAStatus } from '@/api/iaApi'
import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ClassificationConfig from './ClassificationConfig'

// Componente de estado de servicio
function ServiceStatusIndicator({
  name,
  status,
  description,
}: {
  name: string
  status: boolean
  description: string
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/50">
      <div className="flex items-center gap-3">
        {status ? (
          <CheckCircle className="h-5 w-5 text-green-500" />
        ) : (
          <XCircle className="h-5 w-5 text-red-500" />
        )}
        <div>
          <p className="font-medium text-gray-900 dark:text-white">{name}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
      <span
        className={cn(
          'rounded-full px-2 py-0.5 text-xs font-medium',
          status
            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        )}
      >
        {status ? 'Online' : 'Offline'}
      </span>
    </div>
  )
}

// Componente de estadística
function StatBox({
  label,
  value,
  icon: Icon,
}: {
  label: string
  value: string | number
  icon: React.ElementType
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/50">
      <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
        <Icon className="h-4 w-4" />
        <span className="text-xs">{label}</span>
      </div>
      <p className="mt-1 text-xl font-bold text-gray-900 dark:text-white">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
    </div>
  )
}

export default function ConfiguracionIA() {
  // Estados
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [health, setHealth] = useState<HealthCheckResponse | null>(null)
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [config, setConfig] = useState<ConfigResponse | null>(null)
  const [models, setModels] = useState<ModelsResponse | null>(null)
  const [iaStatus, setIAStatus] = useState<IAStatus | null>(null)

  // Estado local para edición
  const [selectedModel, setSelectedModel] = useState('')
  const [temperature, setTemperature] = useState(0.7)
  const [denseWeight, setDenseWeight] = useState(0.7)
  const [sparseWeight, setSparseWeight] = useState(0.3)
  const [searchLimit, setSearchLimit] = useState(10)

  // Cargar datos iniciales
  const loadData = async () => {
    setLoading(true)
    try {
      const [healthData, statsData, configData, modelsData, iaStatusData] = await Promise.allSettled([
        ragApi.healthCheck(),
        ragApi.getStats(),
        ragApi.getConfig(),
        ragApi.getModels(),
        getIAStatus(),
      ])

      if (healthData.status === 'fulfilled') setHealth(healthData.value)
      if (statsData.status === 'fulfilled') setStats(statsData.value)
      if (configData.status === 'fulfilled') {
        setConfig(configData.value)
        setSelectedModel(configData.value.model)
        setTemperature(configData.value.temperature)
        setDenseWeight(configData.value.dense_weight)
        setSparseWeight(configData.value.sparse_weight)
        setSearchLimit(configData.value.search_limit)
      }
      if (modelsData.status === 'fulfilled') {
        setModels(modelsData.value)
        if (!selectedModel && modelsData.value.current) {
          setSelectedModel(modelsData.value.current)
        }
      }
      if (iaStatusData.status === 'fulfilled') setIAStatus(iaStatusData.value)
    } catch (error) {
      console.error('Error cargando configuración IA:', error)
      toast.error('Error cargando configuración de IA')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Guardar modelo seleccionado
  const handleSaveModel = async () => {
    if (!selectedModel) return

    setSaving(true)
    try {
      const result = await setModelo(selectedModel)
      if (result.success) {
        toast.success(`Modelo cambiado a ${selectedModel}`)
        loadData()
      } else {
        toast.error(result.message || 'Error al cambiar modelo')
      }
    } catch (error) {
      console.error('Error cambiando modelo:', error)
      toast.error('Error al cambiar el modelo')
    } finally {
      setSaving(false)
    }
  }

  // Resetear a valores por defecto
  const handleReset = () => {
    if (config) {
      setSelectedModel(config.model)
      setTemperature(config.temperature)
      setDenseWeight(config.dense_weight)
      setSparseWeight(config.sparse_weight)
      setSearchLimit(config.search_limit)
      toast.info('Valores restaurados')
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-gray-500 dark:text-gray-400">Cargando configuración...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/30">
            <Brain className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Inteligencia Artificial
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Configuración de RAG, LLM y búsqueda semántica
            </p>
          </div>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </button>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="general">General / RAG</TabsTrigger>
          <TabsTrigger value="classification">Clasificación</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-8">
          {/* Estado de Servicios */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Cpu className="h-5 w-5 text-gray-500" />
              Estado de Servicios
            </h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <ServiceStatusIndicator
                name="Qdrant (Vector DB)"
                status={health?.qdrant || false}
                description="Base de datos vectorial para embeddings"
              />
              <ServiceStatusIndicator
                name="Ollama (LLM)"
                status={health?.ollama || false}
                description="Servidor de modelos de lenguaje"
              />
              <ServiceStatusIndicator
                name="BM25 Index"
                status={health?.bm25 || false}
                description="Índice de búsqueda por keywords"
              />
              <ServiceStatusIndicator
                name="Sistema RAG"
                status={health?.overall || false}
                description="Retrieval-Augmented Generation"
              />
            </div>
          </div>

          {/* Estadísticas de Índices */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Database className="h-5 w-5 text-gray-500" />
              Estadísticas de Índices
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatBox
                label="Vectores (Qdrant)"
                value={stats?.qdrant?.count || 0}
                icon={Sparkles}
              />
              <StatBox
                label="Documentos BM25"
                value={stats?.bm25?.total_documents || 0}
                icon={Search}
              />
              <StatBox
                label="Colección"
                value={stats?.qdrant?.collection || 'actuaciones'}
                icon={Database}
              />
              <StatBox
                label="Peso Dense/Sparse"
                value={`${((stats?.weights?.dense || 0.7) * 100).toFixed(0)}/${((stats?.weights?.sparse || 0.3) * 100).toFixed(0)}`}
                icon={Settings2}
              />
            </div>
          </div>

          {/* Configuración del Modelo */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Brain className="h-5 w-5 text-gray-500" />
              Modelo de Lenguaje (LLM)
            </h3>

            <div className="space-y-4">
              {/* Selector de modelo */}
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Modelo Activo
                </label>
                <div className="flex gap-3">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  >
                    {models?.models.map((model) => (
                      <option key={model} value={model}>
                        {model} {model === models.current && '(actual)'}
                      </option>
                    ))}
                    {(!models || models.models.length === 0) && (
                      <option value="">No hay modelos disponibles</option>
                    )}
                  </select>
                  <button
                    onClick={handleSaveModel}
                    disabled={saving || !selectedModel || selectedModel === models?.current}
                    className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    Aplicar
                  </button>
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Modelo actual: {models?.current || config?.model || 'No configurado'}
                </p>
              </div>

              {/* Temperatura */}
              <div>
                <label className="mb-2 flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  <Thermometer className="h-4 w-4" />
                  Temperatura: {temperature.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>Preciso (0.0)</span>
                  <span>Creativo (1.0)</span>
                </div>
              </div>

              {/* Info box */}
              <div className="flex items-start gap-3 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
                <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-blue-500" />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium">Sobre la temperatura</p>
                  <p className="mt-1 text-blue-700 dark:text-blue-300">
                    Valores bajos (0.0-0.3) generan respuestas más precisas y consistentes.
                    Valores altos (0.7-1.0) producen respuestas más creativas y variadas.
                    Para análisis legal, se recomienda usar valores bajos.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Configuración de Búsqueda Híbrida */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
              <Search className="h-5 w-5 text-gray-500" />
              Búsqueda Híbrida
            </h3>

            <div className="space-y-4">
              {/* Pesos de búsqueda */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Peso Semántico (Dense): {(denseWeight * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={denseWeight}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      setDenseWeight(value)
                      setSparseWeight(1 - value)
                    }}
                    className="w-full accent-purple-600"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Búsqueda por significado y contexto
                  </p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Peso Keywords (Sparse): {(sparseWeight * 100).toFixed(0)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={sparseWeight}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      setSparseWeight(value)
                      setDenseWeight(1 - value)
                    }}
                    className="w-full accent-orange-500"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Búsqueda por palabras clave exactas (BM25)
                  </p>
                </div>
              </div>

              {/* Límite de resultados */}
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Límite de Resultados: {searchLimit}
                </label>
                <input
                  type="range"
                  min="3"
                  max="20"
                  step="1"
                  value={searchLimit}
                  onChange={(e) => setSearchLimit(parseInt(e.target.value))}
                  className="w-full accent-green-600"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Cantidad máxima de resultados a recuperar para el contexto
                </p>
              </div>

              {/* Visualización de balance */}
              <div className="rounded-lg bg-gray-100 p-4 dark:bg-gray-700/50">
                <p className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Balance de Búsqueda
                </p>
                <div className="flex h-4 overflow-hidden rounded-full">
                  <div
                    className="bg-purple-500 transition-all"
                    style={{ width: `${denseWeight * 100}%` }}
                  />
                  <div
                    className="bg-orange-500 transition-all"
                    style={{ width: `${sparseWeight * 100}%` }}
                  />
                </div>
                <div className="mt-2 flex justify-between text-xs">
                  <span className="text-purple-600 dark:text-purple-400">
                    Semántico ({(denseWeight * 100).toFixed(0)}%)
                  </span>
                  <span className="text-orange-600 dark:text-orange-400">
                    Keywords ({(sparseWeight * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Estado de Componentes IA */}
          {iaStatus && (
            <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
                <Settings2 className="h-5 w-5 text-gray-500" />
                Componentes de IA
              </h3>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Clasificador</p>
                  <p className="font-medium text-gray-900 dark:text-white">{iaStatus.clasificador}</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">NER</p>
                  <p className="font-medium text-gray-900 dark:text-white">{iaStatus.ner}</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">RAG</p>
                  <p className="font-medium text-gray-900 dark:text-white">{iaStatus.rag}</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">LLM</p>
                  <p className="font-medium text-gray-900 dark:text-white">{iaStatus.llm}</p>
                </div>
              </div>
            </div>
          )}

          {/* Acciones */}
          <div className="flex justify-end gap-3">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <RotateCcw className="h-4 w-4" />
              Restaurar
            </button>
          </div>
        </TabsContent>

        <TabsContent value="classification">
          <ClassificationConfig />
        </TabsContent>
      </Tabs>
    </div>
  )
}
