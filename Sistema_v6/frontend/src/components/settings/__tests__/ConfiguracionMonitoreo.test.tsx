/**
 * Tests para ConfiguracionMonitoreo
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConfiguracionMonitoreo from '../ConfiguracionMonitoreo'

// Mock de fetch
global.fetch = vi.fn()

// Mock de toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('ConfiguracionMonitoreo', () => {
  const mockConfigData = {
    browser: {
      headless: true,
      timeout_ms: 30000,
      navigation_timeout_ms: 60000,
      user_agent: null,
    },
    monitoreo: {
      intervalo_segundos: 1800,
      dias_actividad: 30,
      max_reintentos: 3,
      notificar_cambios: true,
      descargar_archivos: true,
      intervalos_laboral_expedientes: null,
      intervalos_laboral_entradas: null,
      intervalos_no_laboral_expedientes: null,
      intervalos_no_laboral_entradas: null,
      dias_laborales: ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
      hora_inicio: '08:00',
      hora_fin: '18:00',
    },
    scraping: {
      timeout_default: 8000,
      timeout_login: 60000,
      timeout_descarga: 30000,
      max_paginas_expedientes: 200,
      max_reintentos_descarga: 3,
    },
    mcp: {
      habilitar: true,
      puerto: 5000,
      mode: 'stdio',
      workspace_path: 'workspace',
      server_name: 'sintaxis-actuaciones-v6',
      enable_pdf_extraction: true,
      enable_full_text_search: true,
      enable_statistics: true,
      max_pdf_pages: 100,
      max_pdf_size_mb: 50,
    },
    storage: {
      base_path: 'data',
      json_base_file: 'expedientes_base.json',
      json_sistema_file: 'expedientes_sistema.json',
      workspaces_dir: 'workspaces',
      downloads_dir: 'descargas',
      pretty_json: true,
      ensure_ascii: false,
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    ;(global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockConfigData,
    })
  })

  it('renderiza el componente correctamente', async () => {
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByText('Configuración de Monitoreo')).toBeInTheDocument()
    })
  })

  it('carga la configuración actual al montar', async () => {
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/config/sistema')
    })
  })

  it('muestra los campos de configuración básica', async () => {
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByText('Configuración Básica')).toBeInTheDocument()
      expect(screen.getByLabelText(/intervalo de verificación/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/días de actividad/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/máximo de reintentos/i)).toBeInTheDocument()
    })
  })

  it('muestra el toggle de modo avanzado', async () => {
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByText(/modo avanzado/i)).toBeInTheDocument()
    })
  })

  it('muestra configuración avanzada cuando se activa el toggle', async () => {
    const user = userEvent.setup()
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByText(/modo avanzado/i)).toBeInTheDocument()
    })

    const toggle = screen.getByRole('checkbox', { name: /modo avanzado/i })
    await user.click(toggle)

    await waitFor(() => {
      expect(screen.getByText(/configuración avanzada/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/laboral - expedientes/i)).toBeInTheDocument()
    })
  })

  it('deshabilita el intervalo básico cuando está en modo avanzado', async () => {
    const user = userEvent.setup()
    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByLabelText(/intervalo de verificación/i)).not.toBeDisabled()
    })

    const toggle = screen.getByRole('checkbox', { name: /modo avanzado/i })
    await user.click(toggle)

    await waitFor(() => {
      expect(screen.getByLabelText(/intervalo de verificación/i)).toBeDisabled()
    })
  })

  it('envía la actualización al hacer submit', async () => {
    const user = userEvent.setup()
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockConfigData,
    })
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        message: 'Configuración actualizada',
        updates: {},
      }),
    })

    render(<ConfiguracionMonitoreo />)

    await waitFor(() => {
      expect(screen.getByText('Configuración de Monitoreo')).toBeInTheDocument()
    })

    const intervaloInput = screen.getByLabelText(/intervalo de verificación/i)
    await user.clear(intervaloInput)
    await user.type(intervaloInput, '3600')

    const submitButton = screen.getByRole('button', { name: /guardar/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/config/sistema',
        expect.objectContaining({
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })
  })
})
