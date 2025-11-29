import { useState, useEffect } from 'react'
import { Plus, Save, Trash2, Play, Settings, Info } from 'lucide-react'
import { toast } from 'sonner'
import { ragApi } from '@/api/ragApi'

interface RulePattern {
    texto: string
    confianza: number
}

interface ClassificationRule {
    tipo: string
    patrones: RulePattern[]
}

interface ClassificationConfigData {
    threshold: number
    model: string | null
}

interface TestResponse {
    tipo: string
    confianza: number
    justificacion: string
    metodo: string
}

export default function ClassificationConfig() {
    const [rules, setRules] = useState<ClassificationRule[]>([])
    const [config, setConfig] = useState<ClassificationConfigData>({ threshold: 0.9, model: null })
    const [availableModels, setAvailableModels] = useState<string[]>([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    // Test state
    const [testText, setTestText] = useState('')
    const [testResult, setTestResult] = useState<TestResponse | null>(null)
    const [testing, setTesting] = useState(false)

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            const [rulesResponse, modelsData] = await Promise.all([
                fetch('http://localhost:8000/api/v1/classification/rules'),
                ragApi.getModels().catch(() => ({ models: [] }))
            ])

            if (!rulesResponse.ok) throw new Error('Error cargando reglas')

            const data = await rulesResponse.json()

            // Handle backward compatibility or new format
            if (Array.isArray(data)) {
                setRules(data)
            } else {
                setRules(data.rules || [])
                setConfig({
                    threshold: data.config?.threshold ?? 0.9,
                    model: data.config?.model ?? null
                })
            }

            if (modelsData && modelsData.models) {
                setAvailableModels(modelsData.models)
            }
        } catch (error) {
            console.error(error)
            toast.error('No se pudieron cargar los datos de clasificación')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const payload = {
                rules,
                config
            }

            const response = await fetch('http://localhost:8000/api/v1/classification/rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            if (!response.ok) throw new Error('Error guardando reglas')

            toast.success('Configuración guardada correctamente')
        } catch (error) {
            console.error(error)
            toast.error('Error al guardar la configuración')
        } finally {
            setSaving(false)
        }
    }

    const handleTest = async () => {
        if (!testText.trim()) return

        setTesting(true)
        setTestResult(null)
        try {
            const response = await fetch('http://localhost:8000/api/v1/classification/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ texto: testText }),
            })

            if (!response.ok) throw new Error('Error en prueba')
            const data = await response.json()
            setTestResult(data)
        } catch (error) {
            console.error(error)
            toast.error('Error al probar clasificación')
        } finally {
            setTesting(false)
        }
    }

    const addRule = () => {
        setRules([...rules, { tipo: 'NUEVA_REGLA', patrones: [] }])
    }

    const removeRule = (index: number) => {
        const newRules = [...rules]
        newRules.splice(index, 1)
        setRules(newRules)
    }

    const updateRuleType = (index: number, newType: string) => {
        const newRules = [...rules]
        newRules[index].tipo = newType
        setRules(newRules)
    }

    const addPattern = (ruleIndex: number) => {
        const newRules = [...rules]
        newRules[ruleIndex].patrones.push({ texto: '', confianza: 0.8 })
        setRules(newRules)
    }

    const removePattern = (ruleIndex: number, patternIndex: number) => {
        const newRules = [...rules]
        newRules[ruleIndex].patrones.splice(patternIndex, 1)
        setRules(newRules)
    }

    const updatePattern = (ruleIndex: number, patternIndex: number, field: keyof RulePattern, value: string | number) => {
        const newRules = [...rules]
        // @ts-ignore
        newRules[ruleIndex].patrones[patternIndex][field] = value
        setRules(newRules)
    }

    if (loading) return <div className="p-8 text-center">Cargando configuración...</div>

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-lg font-medium text-gray-900 dark:text-white">Reglas de Clasificación</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Configura cómo el sistema identifica automáticamente el tipo de actuación.
                    </p>
                </div>
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? 'Guardando...' : 'Guardar Cambios'}
                </button>
            </div>

            {/* Global Settings */}
            <div className="bg-white dark:bg-gray-800 shadow sm:rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Settings className="h-4 w-4 text-gray-500" />
                    Configuración Global
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Umbral de Confianza: {(config.threshold * 100).toFixed(0)}%
                        </label>
                        <input
                            type="range"
                            min="0.5"
                            max="1.0"
                            step="0.05"
                            value={config.threshold}
                            onChange={(e) => setConfig({ ...config, threshold: parseFloat(e.target.value) })}
                            className="w-full accent-blue-600"
                        />
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Si la confianza de una regla supera este valor, se acepta sin consultar al LLM.
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Modelo de Clasificación (Fallback)
                        </label>
                        <select
                            value={config.model || ''}
                            onChange={(e) => setConfig({ ...config, model: e.target.value || null })}
                            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        >
                            <option value="">Usar modelo por defecto del sistema</option>
                            {availableModels.map((model) => (
                                <option key={model} value={model}>
                                    {model}
                                </option>
                            ))}
                        </select>
                        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Modelo LLM a usar cuando las reglas no son suficientes.
                        </p>
                    </div>
                </div>
            </div>

            {/* Test Area */}
            <div className="bg-white dark:bg-gray-800 shadow sm:rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Play className="h-4 w-4 text-green-500" />
                    Probador de Clasificación
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Texto de la actuación
                        </label>
                        <textarea
                            rows={4}
                            className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                            placeholder="Pegue aquí el texto de una actuación para probar..."
                            value={testText}
                            onChange={(e) => setTestText(e.target.value)}
                        />
                        <div className="mt-2 text-right">
                            <button
                                onClick={handleTest}
                                disabled={testing || !testText}
                                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                            >
                                {testing ? 'Analizando...' : 'Probar Clasificación'}
                            </button>
                        </div>
                    </div>

                    <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-4 border border-gray-200 dark:border-gray-700">
                        <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                            Resultado
                        </label>
                        {testResult ? (
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-gray-900 dark:text-white">Tipo:</span>
                                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                        {testResult.tipo}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-gray-900 dark:text-white">Confianza:</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${testResult.confianza >= 0.9 ? 'bg-green-100 text-green-800' :
                                        testResult.confianza >= 0.7 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                                        }`}>
                                        {(testResult.confianza * 100).toFixed(0)}%
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-gray-900 dark:text-white">Método:</span>
                                    <span className="text-sm text-gray-600 dark:text-gray-300">{testResult.metodo}</span>
                                </div>
                                <div className="mt-2 text-xs text-gray-500 italic border-t pt-2 border-gray-200 dark:border-gray-700">
                                    "{testResult.justificacion}"
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400 text-sm italic">
                                El resultado aparecerá aquí
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Rules List */}
            <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <Settings className="h-4 w-4 text-gray-500" />
                    Reglas Manuales
                </h3>
                {rules.map((rule, ruleIndex) => (
                    <div key={ruleIndex} className="bg-white dark:bg-gray-800 shadow sm:rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                            <div className="flex items-center gap-2 w-full max-w-md">
                                <span className="text-sm font-medium text-gray-500">Tipo:</span>
                                <input
                                    type="text"
                                    value={rule.tipo}
                                    onChange={(e) => updateRuleType(ruleIndex, e.target.value)}
                                    className="flex-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-800 dark:border-gray-600 dark:text-white px-2 py-1"
                                />
                            </div>
                            <button
                                onClick={() => removeRule(ruleIndex)}
                                className="text-red-600 hover:text-red-800 p-1"
                                title="Eliminar regla"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="p-4">
                            <div className="space-y-2">
                                {rule.patrones.map((pattern, patternIndex) => (
                                    <div key={patternIndex} className="flex items-center gap-2">
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                value={pattern.texto}
                                                onChange={(e) => updatePattern(ruleIndex, patternIndex, 'texto', e.target.value)}
                                                placeholder="Texto o patrón..."
                                                className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white px-2 py-1"
                                            />
                                        </div>
                                        <div className="w-24">
                                            <input
                                                type="number"
                                                step="0.05"
                                                min="0"
                                                max="1"
                                                value={pattern.confianza}
                                                onChange={(e) => updatePattern(ruleIndex, patternIndex, 'confianza', parseFloat(e.target.value))}
                                                className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white px-2 py-1"
                                            />
                                        </div>
                                        <button
                                            onClick={() => removePattern(ruleIndex, patternIndex)}
                                            className="text-gray-400 hover:text-red-500"
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </button>
                                    </div>
                                ))}

                                <button
                                    onClick={() => addPattern(ruleIndex)}
                                    className="mt-2 inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600"
                                >
                                    <Plus className="h-3 w-3 mr-1" />
                                    Agregar Patrón
                                </button>
                            </div>
                        </div>
                    </div>
                ))}

                <button
                    onClick={addRule}
                    className="w-full border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:border-gray-700 dark:hover:border-gray-600"
                >
                    <Plus className="mx-auto h-8 w-8 text-gray-400" />
                    <span className="mt-2 block text-sm font-medium text-gray-900 dark:text-white">
                        Crear nueva regla de clasificación
                    </span>
                </button>
            </div>
        </div>
    )
}
