/**
 * Store Zustand para gestión de Workspaces
 */

import { create } from 'zustand'
import { toast } from 'sonner'
import type {
  Workspace,
  WorkspaceCrear,
  WorkspaceActualizar,
  WorkspaceConExpedientes,
} from '@/types/workspace'
// import apiClient from '@/lib/api'

interface WorkspacesState {
  // Estado
  workspaces: Workspace[]
  workspaceActual: WorkspaceConExpedientes | null
  isLoading: boolean

  // Acciones - CRUD básico
  listarWorkspaces: () => Promise<void>
  obtenerWorkspace: (id: number) => Promise<void>
  crearWorkspace: (data: WorkspaceCrear) => Promise<Workspace | null>
  actualizarWorkspace: (id: number, data: WorkspaceActualizar) => Promise<void>
  eliminarWorkspace: (id: number) => Promise<void>

  // Acciones - Expedientes
  agregarExpediente: (workspaceId: number, expedienteNumero: string) => Promise<void>
  removerExpediente: (workspaceId: number, expedienteNumero: string) => Promise<void>

  // Utilidades
  limpiarWorkspaceActual: () => void
}

export const useWorkspacesStore = create<WorkspacesState>((set, get) => ({
  // Estado inicial
  workspaces: [],
  workspaceActual: null,
  isLoading: false,

  // Listar todos los workspaces del usuario
  listarWorkspaces: async () => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.get<Workspace[]>('/api/v1/workspaces')
      // set({ workspaces: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 800))

      const mockWorkspaces: Workspace[] = [
        {
          id: 1,
          nombre: 'Casos Urgentes',
          descripcion: 'Expedientes que requieren atención inmediata',
          color: '#ef4444',
          icon: 'flag',
          usuario_id: 1,
          expedientes_count: 3,
          created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 2,
          nombre: 'Familia',
          descripcion: 'Expedientes de derecho de familia',
          color: '#3b82f6',
          icon: 'heart',
          usuario_id: 1,
          expedientes_count: 5,
          created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 3,
          nombre: 'Comercial',
          descripcion: 'Demandas comerciales y contratos',
          color: '#22c55e',
          icon: 'briefcase',
          usuario_id: 1,
          expedientes_count: 8,
          created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 4,
          nombre: 'Laboral',
          descripcion: 'Casos de derecho laboral',
          color: '#f59e0b',
          icon: 'clipboard',
          usuario_id: 1,
          expedientes_count: 2,
          created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 5,
          nombre: 'Archivo',
          descripcion: 'Expedientes finalizados para archivo',
          color: '#64748b',
          icon: 'archive',
          usuario_id: 1,
          expedientes_count: 12,
          created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ]

      set({ workspaces: mockWorkspaces })
    } catch (error: any) {
      console.error('Error al listar workspaces:', error)
      toast.error('Error al cargar los workspaces', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
      set({ workspaces: [] })
    } finally {
      set({ isLoading: false })
    }
  },

  // Obtener workspace con expedientes
  obtenerWorkspace: async (id: number) => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.get<WorkspaceConExpedientes>(`/api/v1/workspaces/${id}`)
      // set({ workspaceActual: response.data })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 600))

      const mockWorkspace: WorkspaceConExpedientes = {
        id: id,
        nombre: 'Casos Urgentes',
        descripcion: 'Expedientes que requieren atención inmediata',
        color: '#ef4444',
        icon: 'flag',
        usuario_id: 1,
        expedientes_count: 3,
        created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        expedientes: [
          {
            numero: 'EXP-2024-123-CS',
            caratula: 'PÉREZ JUAN C/ GARCÍA MARÍA S/ DAÑOS Y PERJUICIOS',
            dependencia: 'Juzgado Civil 45 - Secretaría Única',
            situacion: 'EN TRAMITE',
          },
          {
            numero: 'EXP-2024-456-CF',
            caratula: 'RODRÍGUEZ ANA C/ GÓMEZ PEDRO S/ DIVORCIO',
            dependencia: 'Juzgado de Familia 12 - Secretaría 2',
            situacion: 'EN TRAMITE',
          },
          {
            numero: 'EXP-2024-789-CC',
            caratula: 'LÓPEZ CARLOS S/ QUIEBRA',
            dependencia: 'Juzgado Comercial 8 - Secretaría 1',
            situacion: 'SENTENCIA',
          },
        ],
      }

      set({ workspaceActual: mockWorkspace })
    } catch (error: any) {
      console.error('Error al obtener workspace:', error)
      toast.error('Error al cargar el workspace', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
      set({ workspaceActual: null })
    } finally {
      set({ isLoading: false })
    }
  },

  // Crear nuevo workspace
  crearWorkspace: async (data: WorkspaceCrear) => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.post<Workspace>('/api/v1/workspaces', data)
      // const nuevoWorkspace = response.data

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      const nuevoWorkspace: Workspace = {
        id: Date.now(), // ID temporal
        nombre: data.nombre,
        descripcion: data.descripcion,
        color: data.color || '#3b82f6',
        icon: data.icon || 'folder',
        usuario_id: 1,
        expedientes_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Agregar a la lista
      set(state => ({
        workspaces: [...state.workspaces, nuevoWorkspace],
      }))

      toast.success('Workspace creado', {
        description: `"${data.nombre}" se creó correctamente`,
      })

      return nuevoWorkspace
    } catch (error: any) {
      console.error('Error al crear workspace:', error)
      toast.error('Error al crear workspace', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
      return null
    } finally {
      set({ isLoading: false })
    }
  },

  // Actualizar workspace
  actualizarWorkspace: async (id: number, data: WorkspaceActualizar) => {
    set({ isLoading: true })

    try {
      // TODO: Reemplazar con llamada real a la API
      // const response = await apiClient.put<Workspace>(`/api/v1/workspaces/${id}`, data)
      // const workspaceActualizado = response.data

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      // Actualizar en la lista
      set(state => ({
        workspaces: state.workspaces.map(w =>
          w.id === id
            ? { ...w, ...data, updated_at: new Date().toISOString() }
            : w
        ),
      }))

      toast.success('Workspace actualizado', {
        description: 'Los cambios se guardaron correctamente',
      })
    } catch (error: any) {
      console.error('Error al actualizar workspace:', error)
      toast.error('Error al actualizar workspace', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    } finally {
      set({ isLoading: false })
    }
  },

  // Eliminar workspace
  eliminarWorkspace: async (id: number) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.delete(`/api/v1/workspaces/${id}`)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 500))

      const workspace = get().workspaces.find(w => w.id === id)

      // Remover de la lista
      set(state => ({
        workspaces: state.workspaces.filter(w => w.id !== id),
      }))

      toast.success('Workspace eliminado', {
        description: workspace ? `"${workspace.nombre}" se eliminó correctamente` : undefined,
      })
    } catch (error: any) {
      console.error('Error al eliminar workspace:', error)
      toast.error('Error al eliminar workspace', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    }
  },

  // Agregar expediente a workspace
  agregarExpediente: async (workspaceId: number, expedienteNumero: string) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.post(`/api/v1/workspaces/${workspaceId}/expedientes`, {
      //   expediente_numero: expedienteNumero,
      // })

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 400))

      // Incrementar contador
      set(state => ({
        workspaces: state.workspaces.map(w =>
          w.id === workspaceId
            ? { ...w, expedientes_count: w.expedientes_count + 1 }
            : w
        ),
      }))

      toast.success('Expediente agregado al workspace')
    } catch (error: any) {
      console.error('Error al agregar expediente:', error)
      toast.error('Error al agregar expediente', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    }
  },

  // Remover expediente de workspace
  removerExpediente: async (workspaceId: number, expedienteNumero: string) => {
    try {
      // TODO: Reemplazar con llamada real a la API
      // await apiClient.delete(`/api/v1/workspaces/${workspaceId}/expedientes/${expedienteNumero}`)

      // Mock data por ahora
      await new Promise(resolve => setTimeout(resolve, 400))

      // Decrementar contador
      set(state => ({
        workspaces: state.workspaces.map(w =>
          w.id === workspaceId
            ? { ...w, expedientes_count: Math.max(0, w.expedientes_count - 1) }
            : w
        ),
      }))

      // Si estamos viendo el workspace actual, actualizar expedientes
      const { workspaceActual } = get()
      if (workspaceActual && workspaceActual.id === workspaceId) {
        set({
          workspaceActual: {
            ...workspaceActual,
            expedientes: workspaceActual.expedientes.filter(
              e => e.numero !== expedienteNumero
            ),
            expedientes_count: Math.max(0, workspaceActual.expedientes_count - 1),
          },
        })
      }

      toast.success('Expediente removido del workspace')
    } catch (error: any) {
      console.error('Error al remover expediente:', error)
      toast.error('Error al remover expediente', {
        description: error.response?.data?.detail || 'Intenta nuevamente',
      })
    }
  },

  // Limpiar workspace actual
  limpiarWorkspaceActual: () => {
    set({ workspaceActual: null })
  },
}))
