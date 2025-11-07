/**
 * Toast - Utilidades para notificaciones toast consistentes
 * Wrapper alrededor de sonner para mensajes estandarizados
 */

import { toast as sonnerToast } from 'sonner'

/**
 * Mensajes de toast para operaciones comunes
 */
export const toast = {
  // Operaciones CRUD
  created: (entity: string, name?: string) => {
    sonnerToast.success(`${entity} creado`, {
      description: name ? `"${name}" fue creado correctamente` : 'Creado correctamente',
    })
  },

  updated: (entity: string, name?: string) => {
    sonnerToast.success(`${entity} actualizado`, {
      description: name ? `"${name}" fue actualizado correctamente` : 'Actualizado correctamente',
    })
  },

  deleted: (entity: string, name?: string) => {
    sonnerToast.success(`${entity} eliminado`, {
      description: name ? `"${name}" fue eliminado correctamente` : 'Eliminado correctamente',
    })
  },

  // Operaciones de red
  loading: (message: string) => {
    return sonnerToast.loading(message, {
      description: 'Por favor espera...',
    })
  },

  success: (message: string, description?: string) => {
    sonnerToast.success(message, {
      description,
    })
  },

  error: (message: string, description?: string) => {
    sonnerToast.error(message, {
      description: description || 'Por favor intenta nuevamente',
    })
  },

  warning: (message: string, description?: string) => {
    sonnerToast.warning(message, {
      description,
    })
  },

  info: (message: string, description?: string) => {
    sonnerToast.info(message, {
      description,
    })
  },

  // Operaciones específicas del sistema
  auth: {
    loginSuccess: (username: string) => {
      sonnerToast.success('Sesión iniciada', {
        description: `Bienvenido, ${username}`,
      })
    },

    logoutSuccess: () => {
      sonnerToast.info('Sesión cerrada', {
        description: 'Hasta pronto',
      })
    },

    registerSuccess: () => {
      sonnerToast.success('Cuenta creada', {
        description: 'Iniciando sesión...',
      })
    },

    passwordChanged: () => {
      sonnerToast.success('Contraseña actualizada', {
        description: 'Tu contraseña se cambió correctamente',
      })
    },

    credentialsUpdated: () => {
      sonnerToast.success('Credenciales actualizadas', {
        description: 'Tus credenciales PJN se guardaron de forma segura',
      })
    },

    credentialsDeleted: () => {
      sonnerToast.success('Credenciales eliminadas', {
        description: 'Las credenciales PJN fueron eliminadas',
      })
    },
  },

  expediente: {
    extracted: (numero: string) => {
      sonnerToast.success('Expediente extraído', {
        description: `Expediente ${numero} descargado correctamente`,
      })
    },

    extracting: (numero: string) => {
      return sonnerToast.loading('Extrayendo expediente', {
        description: `Descargando ${numero} del PJN...`,
      })
    },

    notFound: (numero: string) => {
      sonnerToast.error('Expediente no encontrado', {
        description: `El expediente ${numero} no existe o no es accesible`,
      })
    },
  },

  workspace: {
    created: (nombre: string) => {
      sonnerToast.success('Workspace creado', {
        description: `"${nombre}" fue creado correctamente`,
      })
    },

    updated: (nombre: string) => {
      sonnerToast.success('Workspace actualizado', {
        description: `"${nombre}" fue actualizado correctamente`,
      })
    },

    deleted: (nombre: string) => {
      sonnerToast.success('Workspace eliminado', {
        description: `"${nombre}" fue eliminado correctamente`,
      })
    },

    expedienteAdded: (expedienteNumero: string, workspaceName: string) => {
      sonnerToast.success('Expediente agregado', {
        description: `${expedienteNumero} fue agregado a "${workspaceName}"`,
      })
    },

    expedienteRemoved: (expedienteNumero: string) => {
      sonnerToast.success('Expediente removido', {
        description: `${expedienteNumero} fue removido del workspace`,
      })
    },
  },

  monitoreo: {
    started: (expedienteNumero: string) => {
      sonnerToast.success('Monitoreo iniciado', {
        description: `${expedienteNumero} está siendo monitoreado`,
      })
    },

    stopped: (expedienteNumero: string) => {
      sonnerToast.info('Monitoreo detenido', {
        description: `${expedienteNumero} ya no está siendo monitoreado`,
      })
    },

    paused: (expedienteNumero: string) => {
      sonnerToast.info('Monitoreo pausado', {
        description: `${expedienteNumero} fue pausado temporalmente`,
      })
    },

    resumed: (expedienteNumero: string) => {
      sonnerToast.success('Monitoreo reanudado', {
        description: `${expedienteNumero} volvió a ser monitoreado`,
      })
    },

    cambioDetectado: (expedienteNumero: string, tipo: string) => {
      sonnerToast.warning('Cambio detectado', {
        description: `${tipo} en ${expedienteNumero}`,
      })
    },

    verified: (expedienteNumero: string) => {
      sonnerToast.success('Verificación completa', {
        description: `${expedienteNumero} no tiene cambios nuevos`,
      })
    },

    configUpdated: () => {
      sonnerToast.success('Configuración actualizada', {
        description: 'La configuración del monitoreo fue guardada',
      })
    },
  },

  // Manejo de promesas
  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string
      success: string
      error: string
    }
  ) => {
    return sonnerToast.promise(promise, messages)
  },

  // Dismiss toast by ID
  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId)
  },
}
