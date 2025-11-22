/**
 * Cliente API para Sistema v6 - Extracción Masiva
 */

import axios from 'axios';
import type {
  ListadoResponse,
  ConfigExtraccion,
  ResumenExtraccion,
  SesionExtraccion,
} from '../types/expediente';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token JWT a todas las peticiones
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido - limpiar y redirigir a login
      localStorage.removeItem('access_token');
      // Evitar bucle infinito: solo redirigir si no estamos en login
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * API para extracción masiva
 */
export const extraccionMasivaApi = {
  /**
   * Extrae el listado completo de expedientes del PJN
   */
  async extraerListado(
    fecha_corte?: string,
    config?: ConfigExtraccion
  ): Promise<ListadoResponse> {
    const response = await apiClient.post<ListadoResponse>(
      '/extraccion-masiva/listado',
      {
        fecha_corte,
        config,
      }
    );
    return response.data;
  },

  /**
   * Procesa expedientes seleccionados
   */
  async procesarSeleccionados(
    numeros_expedientes: string[],
    config?: ConfigExtraccion
  ): Promise<{ session_id: string; resumen: ResumenExtraccion }> {
    const response = await apiClient.post(
      '/extraccion-masiva/procesar-seleccionados',
      {
        numeros_expedientes,
        config,
      }
    );
    return response.data;
  },

  /**
   * Obtiene el estado de una sesión
   */
  async obtenerSesion(session_id: string): Promise<SesionExtraccion> {
    const response = await apiClient.get<SesionExtraccion>(
      `/extraccion-masiva/sesion/${session_id}`
    );
    return response.data;
  },

  /**
   * Lista todas las sesiones
   */
  async listarSesiones(): Promise<SesionExtraccion[]> {
    const response = await apiClient.get<SesionExtraccion[]>(
      '/extraccion-masiva/sesiones'
    );
    return response.data;
  },

  /**
   * Carga un listado desde el servidor
   */
  async cargarListado(listado_path: string): Promise<{
    session_id: string;
    timestamp: string;
    total: number;
    metadata: Record<string, unknown>;
    expedientes: Array<{
      numero: string;
      caratula: string;
      dependencia: string;
      situacion: string;
      fecha_inicio: string;
      ultima_actuacion: string;
    }>;
  }> {
    // TODO: Implementar endpoint para cargar listado guardado
    // Por ahora, placeholder
    throw new Error('No implementado: cargar listado desde servidor');
  },
};

export { apiClient };
export default apiClient;
