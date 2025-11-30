// import { useState } from 'react' - Eliminado
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { X, Download, Loader2 } from 'lucide-react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import type { SolicitudExtraccion } from '@/types/expediente'

const extraerSchema = z.object({
  numero: z.string().min(1, 'El número del expediente es requerido'),
  anio: z.string()
    .min(4, 'El año debe tener 4 dígitos')
    .max(4, 'El año debe tener 4 dígitos')
    .regex(/^\d{4}$/, 'El año debe ser un número válido'),
  dependencia: z.string().optional(),
})

type ExtraerForm = z.infer<typeof extraerSchema>

interface ExtraerExpedienteDialogProps {
  onClose: () => void
  onSuccess?: (numero: string) => void
}

export default function ExtraerExpedienteDialog({ onClose, onSuccess }: ExtraerExpedienteDialogProps) {
  const { extraerExpediente, isExtracting } = useExpedientesStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ExtraerForm>({
    resolver: zodResolver(extraerSchema),
    defaultValues: {
      numero: '',
      anio: new Date().getFullYear().toString(),
      dependencia: '',
    },
  })

  const onSubmit = async (data: ExtraerForm) => {
    try {
      const solicitud: SolicitudExtraccion = {
        numero: data.numero,
        anio: data.anio,
        dependencia: data.dependencia || undefined,
        tipo: 'completo',
      }

      await extraerExpediente(solicitud)

      if (onSuccess) {
        onSuccess(`${data.numero}-${data.anio}`)
      }

      onClose()
    } catch (error) {
      // El error ya es manejado por el store con toast
      console.error('Error al extraer expediente:', error)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isExtracting) {
          onClose()
        }
      }}
    >
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-blue-600" />
              <CardTitle>Extraer Expediente</CardTitle>
            </div>
            <button
              onClick={onClose}
              disabled={isExtracting}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-50"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <CardDescription>
            Extraer expediente del Portal Judicial Nacional
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Número de Expediente *
              </label>
              <Input
                {...register('numero')}
                placeholder="Ej: 000632"
                disabled={isExtracting}
                className={errors.numero ? 'border-red-500' : ''}
              />
              {errors.numero && (
                <p className="text-sm text-red-500">{errors.numero.message}</p>
              )}
              <p className="text-xs text-gray-500">
                Solo el número, sin prefijos ni año
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Año *
              </label>
              <Input
                {...register('anio')}
                placeholder="Ej: 2024"
                disabled={isExtracting}
                className={errors.anio ? 'border-red-500' : ''}
              />
              {errors.anio && (
                <p className="text-sm text-red-500">{errors.anio.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                Dependencia (Opcional)
              </label>
              <Input
                {...register('dependencia')}
                placeholder="Ej: JUZGADO FEDERAL N°1"
                disabled={isExtracting}
              />
              <p className="text-xs text-gray-500">
                Si conoces la dependencia, puedes especificarla
              </p>
            </div>

            <div className="flex gap-2 pt-4">
              <Button
                type="submit"
                disabled={isExtracting}
                className="flex-1"
              >
                {isExtracting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Extrayendo...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Extraer
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isExtracting}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
