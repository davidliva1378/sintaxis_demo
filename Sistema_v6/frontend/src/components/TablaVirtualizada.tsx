/**
 * Tabla virtualizada para renderizar eficientemente +2000 expedientes.
 *
 * Usa @tanstack/react-virtual para virtualizar filas y mantener
 * rendimiento óptimo incluso con miles de items.
 */

import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { ExpedienteListado } from '../types/expediente';
import { Check } from 'lucide-react';

interface TablaVirtualizadaProps {
  expedientes: ExpedienteListado[];
  seleccionados: Set<string>;
  onToggleSeleccion: (numero: string) => void;
  onToggleTodos: () => void;
  todosSeleccionados: boolean;
  algunosSeleccionados: boolean;
  height?: number;
}

export function TablaVirtualizada({
  expedientes,
  seleccionados,
  onToggleSeleccion,
  onToggleTodos,
  todosSeleccionados,
  algunosSeleccionados,
  height = 600,
}: TablaVirtualizadaProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Configurar virtualizer
  const rowVirtualizer = useVirtualizer({
    count: expedientes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // Altura estimada de cada fila
    overscan: 10, // Renderizar 10 filas extra arriba/abajo para scroll suave
  });

  return (
    <div className="tabla-virtualizada">
      {/* Header fijo */}
      <div className="tabla-header">
        <div className="tabla-header-row">
          <div className="tabla-header-cell checkbox-cell">
            <input
              type="checkbox"
              checked={todosSeleccionados}
              ref={(el) => {
                if (el) el.indeterminate = algunosSeleccionados;
              }}
              onChange={onToggleTodos}
              aria-label="Seleccionar todos"
            />
          </div>
          <div className="tabla-header-cell numero-cell">Número</div>
          <div className="tabla-header-cell caratula-cell">Carátula</div>
          <div className="tabla-header-cell dependencia-cell">Dependencia</div>
          <div className="tabla-header-cell situacion-cell">Situación</div>
          <div className="tabla-header-cell fecha-cell">Fecha Inicio</div>
          <div className="tabla-header-cell fecha-cell">Última Actuación</div>
        </div>
      </div>

      {/* Contenedor virtualizado */}
      <div
        ref={parentRef}
        className="tabla-body-container"
        style={{
          height: `${height}px`,
          overflow: 'auto',
        }}
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const expediente = expedientes[virtualRow.index];
            const estaSeleccionado = seleccionados.has(expediente.numero);

            return (
              <div
                key={expediente.numero}
                className={`tabla-row ${estaSeleccionado ? 'seleccionado' : ''}`}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
                onClick={() => onToggleSeleccion(expediente.numero)}
              >
                <div className="tabla-cell checkbox-cell">
                  <input
                    type="checkbox"
                    checked={estaSeleccionado}
                    onChange={(e) => {
                      e.stopPropagation();
                      onToggleSeleccion(expediente.numero);
                    }}
                    aria-label={`Seleccionar expediente ${expediente.numero}`}
                  />
                </div>
                <div className="tabla-cell numero-cell" title={expediente.numero}>
                  {expediente.numero}
                  {estaSeleccionado && (
                    <Check className="icono-seleccionado" size={16} />
                  )}
                </div>
                <div className="tabla-cell caratula-cell" title={expediente.caratula}>
                  {expediente.caratula}
                </div>
                <div className="tabla-cell dependencia-cell" title={expediente.dependencia}>
                  {expediente.dependencia}
                </div>
                <div className="tabla-cell situacion-cell" title={expediente.situacion}>
                  {expediente.situacion}
                </div>
                <div className="tabla-cell fecha-cell">
                  {formatearFecha(expediente.fecha_inicio)}
                </div>
                <div className="tabla-cell fecha-cell">
                  {formatearFecha(expediente.ultima_actuacion)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer con estadísticas */}
      <div className="tabla-footer">
        <div className="tabla-footer-stats">
          <span>
            Mostrando {expedientes.length.toLocaleString()} expedientes
          </span>
          {seleccionados.size > 0 && (
            <span className="seleccionados-count">
              {seleccionados.size.toLocaleString()} seleccionados
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Formatea una fecha YYYY-MM-DD a DD/MM/YYYY
 */
function formatearFecha(fecha: string): string {
  if (!fecha) return '';

  // Si ya viene en formato DD/MM/YYYY, retornar tal cual
  if (fecha.includes('/')) return fecha;

  // Si viene en formato YYYY-MM-DD, convertir
  const partes = fecha.split('-');
  if (partes.length === 3) {
    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  return fecha;
}
