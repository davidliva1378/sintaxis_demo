import { useState, useEffect } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Calendar, Save, Brain, Plus, Trash2, RotateCcw } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import apiClient from '@/api/client'

const customTermSchema = z.object({
    nombre: z.string().min(1, "El nombre es requerido"),
    dias: z.coerce.number().min(1, "Mínimo 1 día"),
    habiles: z.boolean()
})

const vencimientosSchema = z.object({
    hybrid_analysis_enabled: z.boolean(),
    analysis_margin_days: z.coerce.number().min(1).max(30),
    llm_model: z.string().optional().nullable(),
    system_prompt: z.string().min(10),
    custom_terms: z.array(customTermSchema)
})

type VencimientosForm = z.infer<typeof vencimientosSchema>

const DEFAULT_PROMPT = `Eres un experto legal. Analiza el texto y extrae FECHAS DE NOTIFICACIÓN y PLAZOS.
Formato JSON requerido:
{
  "vencimientos": [
    {
      "fecha_notificacion": "YYYY-MM-DD",
      "tipo": "CEDULA_ELECTRONICA" | "CEDULA_FISICA" | "TRASLADO" | "OTRO",
      "plazo_dias": int,
      "dias_habiles": true,
      "texto_fuente": "..."
    }
  ]
}
Si no hay vencimientos, devuelve lista vacía.`

export default function ConfiguracionVencimientos() {
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    const {
        register,
        control,
        handleSubmit,
        formState: { errors, isDirty },
        reset,
        setValue,
        watch,
    } = useForm<VencimientosForm>({
        resolver: zodResolver(vencimientosSchema),
        defaultValues: {
            hybrid_analysis_enabled: false,
            analysis_margin_days: 7,
            system_prompt: DEFAULT_PROMPT,
            custom_terms: []
        },
    })

    const { fields, append, remove } = useFieldArray({
        control,
        name: "custom_terms"
    })

    const hybridEnabled = watch('hybrid_analysis_enabled')

    useEffect(() => {
        const loadConfig = async () => {
            try {
                const response = await apiClient.get('/api/v1/config/vencimientos')
                reset(response.data)
            } catch (error) {
                console.error('Error loading config:', error)
                toast.error('Error al cargar configuración')
            } finally {
                setIsLoading(false)
            }
        }
        loadConfig()
    }, [reset])

    const onSubmit = async (data: VencimientosForm) => {
        setIsSubmitting(true)
        try {
            await apiClient.post('/api/v1/config/vencimientos', data)
            toast.success('Configuración guardada')
            reset(data) // Reset dirty state
        } catch (error) {
            console.error('Error saving config:', error)
            toast.error('Error al guardar configuración')
        } finally {
            setIsSubmitting(false)
        }
    }

    const restoreDefaultPrompt = () => {
        setValue('system_prompt', DEFAULT_PROMPT, { shouldDirty: true })
    }

    if (isLoading) return <div className="p-6">Cargando...</div>

    return (
        <Card className="p-6">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
                    <Calendar className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Configuración de Vencimientos
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Gestiona cómo el sistema detecta y calcula los plazos procesales
                    </p>
                </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">

                {/* Análisis Híbrido */}
                <div className="space-y-4 border-b border-gray-200 dark:border-gray-700 pb-6">
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label className="text-base">Análisis Híbrido (IA)</Label>
                            <p className="text-sm text-gray-500">
                                Combina reglas determinísticas con Inteligencia Artificial para mayor precisión.
                            </p>
                        </div>
                        <Switch
                            checked={hybridEnabled}
                            onCheckedChange={(checked) => setValue('hybrid_analysis_enabled', checked, { shouldDirty: true })}
                        />
                    </div>

                    {hybridEnabled && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg space-y-4">
                            <div className="flex gap-2 text-blue-700 dark:text-blue-300 text-sm">
                                <Brain className="h-5 w-5 flex-shrink-0" />
                                <p>
                                    El análisis por IA se ejecutará solo en actuaciones recientes para optimizar recursos.
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label>Margen de días para análisis profundo</Label>
                                <div className="flex items-center gap-4">
                                    <Input
                                        type="number"
                                        {...register('analysis_margin_days')}
                                        className="w-24"
                                        min={1}
                                        max={30}
                                    />
                                    <span className="text-sm text-gray-500">días hacia atrás desde hoy</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Prompt Editor */}
                <div className="space-y-4 border-b border-gray-200 dark:border-gray-700 pb-6">
                    <div className="flex items-center justify-between">
                        <Label className="text-base">Instrucciones para la IA (System Prompt)</Label>
                        <Button type="button" variant="ghost" size="sm" onClick={restoreDefaultPrompt}>
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Restaurar Default
                        </Button>
                    </div>
                    <p className="text-sm text-gray-500">
                        Define cómo debe comportarse el modelo al analizar el texto.
                    </p>
                    <Textarea
                        {...register('system_prompt')}
                        className="font-mono text-sm h-48"
                    />
                    {errors.system_prompt && <p className="text-red-500 text-sm">{errors.system_prompt.message}</p>}
                </div>

                {/* Custom Terms */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <Label className="text-base">Plazos Personalizados</Label>
                        <Button type="button" variant="outline" size="sm" onClick={() => append({ nombre: '', dias: 5, habiles: true })}>
                            <Plus className="h-4 w-4 mr-2" />
                            Agregar Plazo
                        </Button>
                    </div>
                    <p className="text-sm text-gray-500">
                        Define reglas específicas que se inyectarán en el prompt.
                    </p>

                    <div className="space-y-3">
                        {fields.map((field, index) => (
                            <div key={field.id} className="flex gap-3 items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                <div className="flex-1 space-y-2">
                                    <Input
                                        {...register(`custom_terms.${index}.nombre`)}
                                        placeholder="Ej: Apelación sentencia"
                                    />
                                    {errors.custom_terms?.[index]?.nombre && (
                                        <p className="text-red-500 text-xs">{errors.custom_terms[index]?.nombre?.message}</p>
                                    )}
                                </div>
                                <div className="w-24 space-y-2">
                                    <Input
                                        type="number"
                                        {...register(`custom_terms.${index}.dias`)}
                                        placeholder="Días"
                                    />
                                </div>
                                <div className="flex items-center h-10">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            {...register(`custom_terms.${index}.habiles`)}
                                            className="rounded border-gray-300"
                                        />
                                        <span className="text-sm">Hábiles</span>
                                    </label>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon"
                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                    onClick={() => remove(index)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                        {fields.length === 0 && (
                            <div className="text-center py-6 text-gray-400 border-2 border-dashed rounded-lg">
                                No hay plazos personalizados definidos
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex justify-end pt-4">
                    <Button type="submit" disabled={!isDirty || isSubmitting}>
                        <Save className="h-4 w-4 mr-2" />
                        {isSubmitting ? 'Guardando...' : 'Guardar Configuración'}
                    </Button>
                </div>
            </form>
        </Card>
    )
}
