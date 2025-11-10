/**
 * Diálogo de Filtrado y Selección de Expedientes.
 *
 * Permite al usuario:
 * 1. Ver listado completo de expedientes (2000+)
 * 2. Aplicar 7 tipos de filtros
 * 3. Seleccionar expedientes (individual y masivo)
 * 4. Confirmar selección para procesamiento
 */

import { useState } from 'react';
import { Filter, X, Check, RotateCcw, Calendar } from 'lucide-react';
import type { ExpedienteListado } from '../types/expediente';
import { useFiltrosExpedientes } from '../hooks/useFiltrosExpedientes';
import { useSeleccionMasiva } from '../hooks/useSeleccionMasiva';
import { TablaVirtualizada } from './TablaVirtualizada';

interface FiltradoExpedientesDialogProps {
  expedientes: ExpedienteListado[];
  isOpen: boolean;
  onClose: () => void;
  onConfirmar: (numerosSeleccionados: string[]) => void;
}

export function FiltradoExpedientesDialog({
  expedientes,
  isOpen,
  onClose,
  onConfirmar,
}: FiltradoExpedientesDialogProps) {
  const [mostrarFiltros, setMostrarFiltros] = useState(true);

  // Hooks de filtrado y selección
  const {
    filtros,
    expedientesFiltrados,
    valoresUnicos,
    actualizarFiltro,
    limpiarFiltro,
    limpiarTodos,
    hayFiltrosActivos,
    conteoFiltrosActivos,
    totalOriginal,
    totalFiltrado,
  } = useFiltrosExpedientes(expedientes);

  const {
    seleccionados,
    seleccionarTodos,
    deseleccionarTodos,
    invertirSeleccion,
    seleccionarPorFecha,
    toggleSeleccion,
    todosSeleccionados,
    algunosSeleccionados,
    numerosSeleccionados,
    totalSeleccionados,
  } = useSeleccionMasiva(expedientesFiltrados);

  // Estado para selector de fechas rápido
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  if (!isOpen) return null;

  const handleConfirmar = () => {
    if (totalSeleccionados === 0) {
      alert('Debe seleccionar al menos un expediente');
      return;
    }

    onConfirmar(numerosSeleccionados);
  };

  return (
    <div className="dialog-overlay">
      <div className="dialog-container filtrado-dialog">
        {/* Header */}
        <div className="dialog-header">
          <h2>
            <Filter size={24} />
            Filtrar y Seleccionar Expedientes
          </h2>
          <button
            onClick={onClose}
            className="btn-icon"
            aria-label="Cerrar"
          >
            <X size={24} />
          </button>
        </div>

        {/* Estadísticas principales */}
        <div className="stats-bar">
          <div className="stat">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{totalOriginal.toLocaleString()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Filtrados:</span>
            <span className="stat-value">{totalFiltrado.toLocaleString()}</span>
          </div>
          <div className="stat highlight">
            <span className="stat-label">Seleccionados:</span>
            <span className="stat-value">{totalSeleccionados.toLocaleString()}</span>
          </div>
        </div>

        {/* Toggle panel de filtros */}
        <div className="filtros-toggle">
          <button
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className="btn-secondary"
          >
            <Filter size={16} />
            {mostrarFiltros ? 'Ocultar' : 'Mostrar'} Filtros
            {conteoFiltrosActivos > 0 && (
              <span className="badge">{conteoFiltrosActivos}</span>
            )}
          </button>

          {hayFiltrosActivos && (
            <button
              onClick={limpiarTodos}
              className="btn-secondary"
            >
              <RotateCcw size={16} />
              Limpiar Filtros
            </button>
          )}
        </div>

        {/* Panel de filtros */}
        {mostrarFiltros && (
          <div className="filtros-panel">
            {/* Filtro 1 y 2: Texto */}
            <div className="filtros-row">
              <div className="filtro-group">
                <label>Número de Expediente</label>
                <input
                  type="text"
                  value={filtros.numero || ''}
                  onChange={(e) => actualizarFiltro('numero', e.target.value)}
                  placeholder="Buscar por número..."
                />
              </div>

              <div className="filtro-group">
                <label>Carátula</label>
                <input
                  type="text"
                  value={filtros.caratula || ''}
                  onChange={(e) => actualizarFiltro('caratula', e.target.value)}
                  placeholder="Buscar por carátula..."
                />
              </div>
            </div>

            {/* Filtro 3 y 4: Selección múltiple */}
            <div className="filtros-row">
              <div className="filtro-group">
                <label>Dependencia</label>
                <select
                  multiple
                  value={filtros.dependencia || []}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, (o) => o.value);
                    actualizarFiltro('dependencia', selected);
                  }}
                  size={4}
                >
                  {valoresUnicos.dependencias.map((dep) => (
                    <option key={dep} value={dep}>
                      {dep}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filtro-group">
                <label>Situación</label>
                <select
                  multiple
                  value={filtros.situacion || []}
                  onChange={(e) => {
                    const selected = Array.from(e.target.selectedOptions, (o) => o.value);
                    actualizarFiltro('situacion', selected);
                  }}
                  size={4}
                >
                  {valoresUnicos.situaciones.map((sit) => (
                    <option key={sit} value={sit}>
                      {sit}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Filtro 5: Rango de fecha de inicio */}
            <div className="filtros-row">
              <div className="filtro-group">
                <label>Fecha de Inicio - Desde</label>
                <input
                  type="date"
                  value={filtros.fecha_inicio_desde || ''}
                  onChange={(e) => actualizarFiltro('fecha_inicio_desde', e.target.value)}
                />
              </div>

              <div className="filtro-group">
                <label>Fecha de Inicio - Hasta</label>
                <input
                  type="date"
                  value={filtros.fecha_inicio_hasta || ''}
                  onChange={(e) => actualizarFiltro('fecha_inicio_hasta', e.target.value)}
                />
              </div>
            </div>

            {/* Filtro 6: Rango de última actuación */}
            <div className="filtros-row">
              <div className="filtro-group">
                <label>Última Actuación - Desde</label>
                <input
                  type="date"
                  value={filtros.ultima_actuacion_desde || ''}
                  onChange={(e) => actualizarFiltro('ultima_actuacion_desde', e.target.value)}
                />
              </div>

              <div className="filtro-group">
                <label>Última Actuación - Hasta</label>
                <input
                  type="date"
                  value={filtros.ultima_actuacion_hasta || ''}
                  onChange={(e) => actualizarFiltro('ultima_actuacion_hasta', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        {/* Acciones de selección masiva */}
        <div className="acciones-seleccion">
          <button onClick={seleccionarTodos} className="btn-small">
            <Check size={16} />
            Seleccionar Todos ({totalFiltrado})
          </button>

          <button onClick={deseleccionarTodos} className="btn-small">
            <X size={16} />
            Deseleccionar Todos
          </button>

          <button onClick={invertirSeleccion} className="btn-small">
            <RotateCcw size={16} />
            Invertir Selección
          </button>

          {/* Selección por fecha rápida */}
          <div className="seleccion-fecha-rapida">
            <Calendar size={16} />
            <input
              type="date"
              value={fechaDesde}
              onChange={(e) => setFechaDesde(e.target.value)}
              placeholder="Desde"
              className="input-small"
            />
            <span>-</span>
            <input
              type="date"
              value={fechaHasta}
              onChange={(e) => setFechaHasta(e.target.value)}
              placeholder="Hasta"
              className="input-small"
            />
            <button
              onClick={() => {
                seleccionarPorFecha(fechaDesde || undefined, fechaHasta || undefined);
              }}
              className="btn-small"
              disabled={!fechaDesde && !fechaHasta}
            >
              Seleccionar
            </button>
          </div>
        </div>

        {/* Tabla virtualizada */}
        <TablaVirtualizada
          expedientes={expedientesFiltrados}
          seleccionados={seleccionados}
          onToggleSeleccion={toggleSeleccion}
          onToggleTodos={todosSeleccionados ? deseleccionarTodos : seleccionarTodos}
          todosSeleccionados={todosSeleccionados}
          algunosSeleccionados={algunosSeleccionados}
          height={400}
        />

        {/* Footer con acciones */}
        <div className="dialog-footer">
          <button onClick={onClose} className="btn-secondary">
            Cancelar
          </button>

          <button
            onClick={handleConfirmar}
            className="btn-primary"
            disabled={totalSeleccionados === 0}
          >
            <Check size={20} />
            Procesar {totalSeleccionados} Expedientes
          </button>
        </div>
      </div>
    </div>
  );
}
