import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Plus, Loader2, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { useExpedientesStore } from '@/stores/expedientesStore'
import { useMonitoreoStore } from '@/stores/monitoreoStore'
import ExpedienteCard from '@/components/expedientes/ExpedienteCard'
import ExpedientesFiltros from '@/components/expedientes/ExpedientesFiltros'
import ExtraerExpedienteDialog from '@/components/expedientes/ExtraerExpedienteDialog'
import ExtraccionMasivaDialog from '@/components/expedientes/ExtraccionMasivaDialog'
import AddToWorkspaceDialog from '@/components/workspaces/AddToWorkspaceDialog'

export default function ExpedientesPage() {
  const navigate = useNavigate()
  const [mostrarExtraer, setMostrarExtraer] = useState(false)
  const [mostrarExtraccionMasiva, setMostrarExtraccionMasiva] = useState(false)
  const [mostrarAgregarWorkspace, setMostrarAgregarWorkspace] = useState(false)
  const [expedienteSeleccionado, setExpedienteSeleccionado] = useState<{
    numero: string
    caratula: string
    dependencia?: string
  } | null>(null)

  const {
    expedientes,
    filtros,
    paginacion,
    isLoading,
    listarExpedientes,
    setFiltros,
    limpiarFiltros,
    setPagina,
  } = useExpedientesStore()

  useEffect(() => {
    listarExpedientes()
  }, [])

  const handleBuscar = () => {
    listarExpedientes(filtros, 1)
  }

  const handleLimpiarFiltros = () => {
    limpiarFiltros()
    listarExpedientes({}, 1)
  }

  const handleVerDetalle = (numero: string) => {
    navigate(`/expedientes/${numero}`)
  }

  const handleAgregarAWorkspace = (numero: string, caratula: string) => {
    setExpedienteSeleccionado({ numero, caratula })
    setMostrarAgregarWorkspace(true)
  }

  const { agregarExpediente } = useMonitoreoStore()

  const handleAgregarAMonitoreo = async (numero: string, caratula: string, dependencia?: string) => {
    await agregarExpediente({
      expediente_numero: numero,
      expediente_caratula: caratula,
      expediente_dependencia: dependencia,
    })
  }

  const handlePaginaAnterior = () => {
    if (paginacion.pagina > 1) {
      setPagina(paginacion.pagina - 1)
    }
  }

  const handlePaginaSiguiente = () => {
    if (paginacion.pagina < paginacion.total_paginas) {
      setPagina(paginacion.pagina + 1)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Expedientes
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Gestión de expedientes del Portal Judicial Nacional
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setMostrarExtraer(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Extraer Expediente
          </Button>
          <Button
            variant="outline"
            onClick={() => setMostrarExtraccionMasiva(true)}
          >
            <Download className="h-4 w-4 mr-2" />
            Extracción Masiva
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <ExpedientesFiltros
        filtros={filtros}
        onFiltrosChange={setFiltros}
        onLimpiar={handleLimpiarFiltros}
        onBuscar={handleBuscar}
      />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
          <div className="text-2xl font-bold">{paginacion.total}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">Página Actual</div>
          <div className="text-2xl font-bold">{paginacion.pagina}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">Por Página</div>
          <div className="text-2xl font-bold">{paginacion.por_pagina}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Páginas</div>
          <div className="text-2xl font-bold">{paginacion.total_paginas}</div>
        </Card>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Expedientes Grid */}
      {!isLoading && expedientes.length > 0 && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {expedientes.map((expediente) => (
              <ExpedienteCard
                key={expediente.numero}
                expediente={expediente}
                onView={handleVerDetalle}
                onAddToWorkspace={handleAgregarAWorkspace}
                onAddToMonitoreo={handleAgregarAMonitoreo}
              />
            ))}
          </div>

          {/* Paginación */}
          {paginacion.total_paginas > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                onClick={handlePaginaAnterior}
                disabled={paginacion.pagina === 1}
              >
                <ChevronLeft className="h-4 w-4" />
                Anterior
              </Button>
              <div className="px-4 py-2 text-sm">
                Página {paginacion.pagina} de {paginacion.total_paginas}
              </div>
              <Button
                variant="outline"
                onClick={handlePaginaSiguiente}
                disabled={paginacion.pagina === paginacion.total_paginas}
              >
                Siguiente
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!isLoading && expedientes.length === 0 && (
        <Card>
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">📋</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No hay expedientes
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Comienza extrayendo expedientes del Portal Judicial Nacional
            </p>
            <Button onClick={() => setMostrarExtraer(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Extraer Primer Expediente
            </Button>
          </div>
        </Card>
      )}

      {/* Modal de Extracción */}
      {mostrarExtraer && (
        <ExtraerExpedienteDialog
          onClose={() => setMostrarExtraer(false)}
          onSuccess={(numero) => handleVerDetalle(numero)}
        />
      )}

      {/* Modal de Extracción Masiva */}
      {mostrarExtraccionMasiva && (
        <ExtraccionMasivaDialog
          onClose={() => setMostrarExtraccionMasiva(false)}
          onSuccess={(expedientes) => {
            // Actualizar la lista de expedientes
            listarExpedientes()
          }}
        />
      )}

      {/* Modal de Agregar a Workspace */}
      {mostrarAgregarWorkspace && expedienteSeleccionado && (
        <AddToWorkspaceDialog
          isOpen={mostrarAgregarWorkspace}
          onClose={() => {
            setMostrarAgregarWorkspace(false)
            setExpedienteSeleccionado(null)
          }}
          expedienteNumero={expedienteSeleccionado.numero}
          expedienteCaratula={expedienteSeleccionado.caratula}
        />
      )}
    </div>
  )
}
