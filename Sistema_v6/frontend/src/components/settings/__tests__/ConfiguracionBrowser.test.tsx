/**
 * Tests para ConfiguracionBrowser
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConfiguracionBrowser from '../ConfiguracionBrowser'

// Mock de fetch
global.fetch = vi.fn()

// Mock de toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('ConfiguracionBrowser', () => {
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
      dias_laborales: ['lunes'],
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
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(screen.getByText('Configuración del Navegador')).toBeInTheDocument()
    })
  })

  it('carga la configuración actual al montar', async () => {
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/config/sistema')
    })
  })

  it('muestra el toggle de modo headless', async () => {
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(screen.getByText(/modo headless/i)).toBeInTheDocument()
    })
  })

  it('muestra los campos de timeouts', async () => {
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(screen.getByLabelText(/timeout general/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/timeout de navegación/i)).toBeInTheDocument()
    })
  })

  it('muestra el campo de user agent', async () => {
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(screen.getByLabelText(/user agent/i)).toBeInTheDocument()
    })
  })

  it('muestra información sobre timeouts', async () => {
    render(<ConfiguracionBrowser />)

    await waitFor(() => {
      expect(screen.getByText(/información sobre timeouts/i)).toBeInTheDocument()
    })
  })
})
