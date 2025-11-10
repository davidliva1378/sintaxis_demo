/**
 * Hook para selección masiva de expedientes.
 *
 * Funciones implementadas:
 * 1. Seleccionar todos los filtrados
 * 2. Deseleccionar todos
 * 3. Invertir selección (de los filtrados)
 * 4. Seleccionar por rango de fechas
 * 5. Seleccionar individual (toggle)
 */

import { useState, useCallback, useMemo } from 'react';
import type { ExpedienteListado } from '../types/expediente';

export function useSeleccionMasiva(expedientes: ExpedienteListado[]) {
  const [seleccionados, setSeleccionados] = useState<Set<string>>(new Set());

  /**
   * Función 1: Seleccionar todos los expedientes visibles
   */
  const seleccionarTodos = useCallback(() => {
    const nuevosSeleccionados = new Set(seleccionados);
    expedientes.forEach((exp) => {
      nuevosSeleccionados.add(exp.numero);
    });
    setSeleccionados(nuevosSeleccionados);
  }, [expedientes, seleccionados]);

  /**
   * Función 2: Deseleccionar todos
   */
  const deseleccionarTodos = useCallback(() => {
    setSeleccionados(new Set());
  }, []);

  /**
   * Función 3: Invertir selección de los expedientes visibles
   */
  const invertirSeleccion = useCallback(() => {
    const nuevosSeleccionados = new Set(seleccionados);
    expedientes.forEach((exp) => {
      if (nuevosSeleccionados.has(exp.numero)) {
        nuevosSeleccionados.delete(exp.numero);
      } else {
        nuevosSeleccionados.add(exp.numero);
      }
    });
    setSeleccionados(nuevosSeleccionados);
  }, [expedientes, seleccionados]);

  /**
   * Función 4: Seleccionar por rango de fechas de última actuación
   */
  const seleccionarPorFecha = useCallback(
    (desde?: string, hasta?: string) => {
      const nuevosSeleccionados = new Set(seleccionados);

      expedientes.forEach((exp) => {
        let cumple = true;

        if (desde && exp.ultima_actuacion < desde) {
          cumple = false;
        }

        if (hasta && exp.ultima_actuacion > hasta) {
          cumple = false;
        }

        if (cumple) {
          nuevosSeleccionados.add(exp.numero);
        }
      });

      setSeleccionados(nuevosSeleccionados);
    },
    [expedientes, seleccionados]
  );

  /**
   * Función 5: Toggle selección individual
   */
  const toggleSeleccion = useCallback(
    (numero: string) => {
      const nuevosSeleccionados = new Set(seleccionados);

      if (nuevosSeleccionados.has(numero)) {
        nuevosSeleccionados.delete(numero);
      } else {
        nuevosSeleccionados.add(numero);
      }

      setSeleccionados(nuevosSeleccionados);
    },
    [seleccionados]
  );

  /**
   * Verifica si un expediente está seleccionado
   */
  const estaSeleccionado = useCallback(
    (numero: string) => {
      return seleccionados.has(numero);
    },
    [seleccionados]
  );

  /**
   * Verifica si todos los expedientes visibles están seleccionados
   */
  const todosSeleccionados = useMemo(() => {
    if (expedientes.length === 0) return false;
    return expedientes.every((exp) => seleccionados.has(exp.numero));
  }, [expedientes, seleccionados]);

  /**
   * Verifica si algunos (pero no todos) están seleccionados
   */
  const algunosSeleccionados = useMemo(() => {
    if (expedientes.length === 0) return false;
    const algunosSi = expedientes.some((exp) => seleccionados.has(exp.numero));
    const todosSi = expedientes.every((exp) => seleccionados.has(exp.numero));
    return algunosSi && !todosSi;
  }, [expedientes, seleccionados]);

  /**
   * Obtiene los expedientes seleccionados
   */
  const expedientesSeleccionados = useMemo(() => {
    return expedientes.filter((exp) => seleccionados.has(exp.numero));
  }, [expedientes, seleccionados]);

  /**
   * Obtiene solo los números seleccionados
   */
  const numerosSeleccionados = useMemo(() => {
    return Array.from(seleccionados);
  }, [seleccionados]);

  return {
    seleccionados,
    seleccionarTodos,
    deseleccionarTodos,
    invertirSeleccion,
    seleccionarPorFecha,
    toggleSeleccion,
    estaSeleccionado,
    todosSeleccionados,
    algunosSeleccionados,
    expedientesSeleccionados,
    numerosSeleccionados,
    totalSeleccionados: seleccionados.size,
  };
}
