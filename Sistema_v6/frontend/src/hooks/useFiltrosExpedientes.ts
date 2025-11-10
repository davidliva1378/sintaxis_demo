/**
 * Hook para filtrado de expedientes con 7 tipos de filtros.
 *
 * Filtros implementados:
 * 1. Por número de expediente (búsqueda parcial)
 * 2. Por carátula (búsqueda parcial)
 * 3. Por dependencia (selección múltiple)
 * 4. Por situación (selección múltiple)
 * 5. Por rango de fecha de inicio
 * 6. Por rango de última actuación
 * 7. Combinación de todos los anteriores
 */

import { useState, useMemo } from 'react';
import type { ExpedienteListado, FiltrosExpedientes } from '../types/expediente';

export function useFiltrosExpedientes(expedientes: ExpedienteListado[]) {
  const [filtros, setFiltros] = useState<FiltrosExpedientes>({});

  /**
   * Expedientes filtrados según los criterios activos
   */
  const expedientesFiltrados = useMemo(() => {
    return expedientes.filter((exp) => {
      // Filtro 1: Número de expediente
      if (filtros.numero && !exp.numero.toLowerCase().includes(filtros.numero.toLowerCase())) {
        return false;
      }

      // Filtro 2: Carátula
      if (filtros.caratula && !exp.caratula.toLowerCase().includes(filtros.caratula.toLowerCase())) {
        return false;
      }

      // Filtro 3: Dependencia (selección múltiple)
      if (filtros.dependencia && filtros.dependencia.length > 0) {
        if (!filtros.dependencia.includes(exp.dependencia)) {
          return false;
        }
      }

      // Filtro 4: Situación (selección múltiple)
      if (filtros.situacion && filtros.situacion.length > 0) {
        if (!filtros.situacion.includes(exp.situacion)) {
          return false;
        }
      }

      // Filtro 5: Rango de fecha de inicio
      if (filtros.fecha_inicio_desde) {
        if (exp.fecha_inicio < filtros.fecha_inicio_desde) {
          return false;
        }
      }
      if (filtros.fecha_inicio_hasta) {
        if (exp.fecha_inicio > filtros.fecha_inicio_hasta) {
          return false;
        }
      }

      // Filtro 6: Rango de última actuación
      if (filtros.ultima_actuacion_desde) {
        if (exp.ultima_actuacion < filtros.ultima_actuacion_desde) {
          return false;
        }
      }
      if (filtros.ultima_actuacion_hasta) {
        if (exp.ultima_actuacion > filtros.ultima_actuacion_hasta) {
          return false;
        }
      }

      // Pasó todos los filtros
      return true;
    });
  }, [expedientes, filtros]);

  /**
   * Valores únicos para filtros de selección múltiple
   */
  const valoresUnicos = useMemo(() => {
    const dependencias = new Set<string>();
    const situaciones = new Set<string>();

    expedientes.forEach((exp) => {
      dependencias.add(exp.dependencia);
      situaciones.add(exp.situacion);
    });

    return {
      dependencias: Array.from(dependencias).sort(),
      situaciones: Array.from(situaciones).sort(),
    };
  }, [expedientes]);

  /**
   * Actualiza un filtro específico
   */
  const actualizarFiltro = <K extends keyof FiltrosExpedientes>(
    key: K,
    value: FiltrosExpedientes[K]
  ) => {
    setFiltros((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  /**
   * Limpia un filtro específico
   */
  const limpiarFiltro = (key: keyof FiltrosExpedientes) => {
    setFiltros((prev) => {
      const newFiltros = { ...prev };
      delete newFiltros[key];
      return newFiltros;
    });
  };

  /**
   * Limpia todos los filtros
   */
  const limpiarTodos = () => {
    setFiltros({});
  };

  /**
   * Verifica si hay filtros activos
   */
  const hayFiltrosActivos = useMemo(() => {
    return Object.keys(filtros).length > 0;
  }, [filtros]);

  /**
   * Cuenta de filtros activos
   */
  const conteoFiltrosActivos = useMemo(() => {
    let count = 0;
    if (filtros.numero) count++;
    if (filtros.caratula) count++;
    if (filtros.dependencia && filtros.dependencia.length > 0) count++;
    if (filtros.situacion && filtros.situacion.length > 0) count++;
    if (filtros.fecha_inicio_desde || filtros.fecha_inicio_hasta) count++;
    if (filtros.ultima_actuacion_desde || filtros.ultima_actuacion_hasta) count++;
    return count;
  }, [filtros]);

  return {
    filtros,
    expedientesFiltrados,
    valoresUnicos,
    actualizarFiltro,
    limpiarFiltro,
    limpiarTodos,
    hayFiltrosActivos,
    conteoFiltrosActivos,
    totalOriginal: expedientes.length,
    totalFiltrado: expedientesFiltrados.length,
  };
}
