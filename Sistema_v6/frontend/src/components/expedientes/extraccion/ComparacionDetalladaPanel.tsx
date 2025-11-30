import React, { useState } from 'react'
import { ChevronDown, ChevronRight, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import type { ComparacionDetallada } from '@/types/expediente'

interface Props {
  comparacion: ComparacionDetallada
}

export const ComparacionDetalladaPanel: React.FC<Props> = ({ comparacion }) => {
  const [expandidoNuevos, setExpandidoNuevos] = useState(false)
  const [expandidoEliminados, setExpandidoEliminados] = useState(false)
  const [expandidoSituacion, setExpandidoSituacion] = useState(false)
  const [expandidoUltimaActuacion, setExpandidoUltimaActuacion] = useState(false)
  const [expandidoDependencia, setExpandidoDependencia] = useState(false)

  return (
    <div className="space-y-4">
      {/* RESUMEN */}
      <div className="grid grid-cols-3 gap-4">
        {/* Card Nuevos */}
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Nuevos</span>
            </div>
            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {comparacion.total_nuevos}
            </span>
          </div>
        </div>

        {/* Card Eliminados */}
        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <span className="text-sm font-medium text-red-900 dark:text-red-100">Eliminados</span>
            </div>
            <span className="text-2xl font-bold text-red-600 dark:text-red-400">
              {comparacion.total_eliminados}
            </span>
          </div>
        </div>

        {/* Card Modificados */}
        <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              <span className="text-sm font-medium text-amber-900 dark:text-amber-100">Modificados</span>
            </div>
            <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {comparacion.total_modificados}
            </span>
          </div>
        </div>
      </div>

      {/* DETALLES EXPANDIBLES */}
      <div className="space-y-2">
        {/* Nuevos */}
        {comparacion.total_nuevos > 0 && (
          <div className="border border-blue-200 dark:border-blue-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoNuevos(!expandidoNuevos)}
              className="w-full px-4 py-3 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-blue-900 dark:text-blue-100">
                Expedientes Nuevos ({comparacion.total_nuevos})
              </span>
              {expandidoNuevos ? (
                <ChevronDown className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              )}
            </button>
            {expandidoNuevos && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-2">
                  {comparacion.nuevos.map((exp) => (
                    <li key={exp.numero} className="text-sm border-l-2 border-blue-400 pl-3 py-1">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{exp.numero}</div>
                      <div className="text-gray-600 dark:text-gray-400">{exp.caratula}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-500">
                        {exp.dependencia} • {exp.situacion}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Eliminados */}
        {comparacion.total_eliminados > 0 && (
          <div className="border border-red-200 dark:border-red-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoEliminados(!expandidoEliminados)}
              className="w-full px-4 py-3 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-red-900 dark:text-red-100">
                Expedientes Eliminados ({comparacion.total_eliminados})
              </span>
              {expandidoEliminados ? (
                <ChevronDown className="h-5 w-5 text-red-600 dark:text-red-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
            </button>
            {expandidoEliminados && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-2">
                  {comparacion.eliminados.map((exp) => (
                    <li key={exp.numero} className="text-sm border-l-2 border-red-400 pl-3 py-1">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{exp.numero}</div>
                      <div className="text-gray-600 dark:text-gray-400">{exp.caratula}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Situación */}
        {comparacion.cambios_situacion.length > 0 && (
          <div className="border border-amber-200 dark:border-amber-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoSituacion(!expandidoSituacion)}
              className="w-full px-4 py-3 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-amber-900 dark:text-amber-100">
                Cambios de Situación ({comparacion.cambios_situacion.length})
              </span>
              {expandidoSituacion ? (
                <ChevronDown className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              )}
            </button>
            {expandidoSituacion && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_situacion.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-amber-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                          {cambio.situacion_anterior}
                        </span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/50 rounded font-medium">
                          {cambio.situacion_nueva}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Última Actuación */}
        {comparacion.cambios_ultima_actuacion.length > 0 && (
          <div className="border border-purple-200 dark:border-purple-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoUltimaActuacion(!expandidoUltimaActuacion)}
              className="w-full px-4 py-3 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-purple-900 dark:text-purple-100">
                Cambios de Última Actuación ({comparacion.cambios_ultima_actuacion.length})
              </span>
              {expandidoUltimaActuacion ? (
                <ChevronDown className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              )}
            </button>
            {expandidoUltimaActuacion && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_ultima_actuacion.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-purple-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="space-y-1">
                        <div className="text-xs">
                          <span className="text-gray-500">Anterior:</span>{' '}
                          <span className="text-gray-700 dark:text-gray-300">{cambio.ultima_actuacion_anterior}</span>
                        </div>
                        <div className="text-xs">
                          <span className="text-gray-500">Nueva:</span>{' '}
                          <span className="text-purple-700 dark:text-purple-300 font-medium">
                            {cambio.ultima_actuacion_nueva}
                          </span>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Cambios de Dependencia */}
        {comparacion.cambios_dependencia.length > 0 && (
          <div className="border border-green-200 dark:border-green-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandidoDependencia(!expandidoDependencia)}
              className="w-full px-4 py-3 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-green-900 dark:text-green-100">
                Cambios de Dependencia ({comparacion.cambios_dependencia.length})
              </span>
              {expandidoDependencia ? (
                <ChevronDown className="h-5 w-5 text-green-600 dark:text-green-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-green-600 dark:text-green-400" />
              )}
            </button>
            {expandidoDependencia && (
              <div className="p-4 bg-white dark:bg-gray-800 max-h-64 overflow-y-auto">
                <ul className="space-y-3">
                  {comparacion.cambios_dependencia.map((cambio) => (
                    <li key={cambio.numero} className="text-sm border-l-2 border-green-400 pl-3 py-2">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{cambio.numero}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">{cambio.caratula}</div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                          {cambio.dependencia_anterior}
                        </span>
                        <span>→</span>
                        <span className="px-2 py-1 bg-green-100 dark:bg-green-900/50 rounded font-medium">
                          {cambio.dependencia_nueva}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
