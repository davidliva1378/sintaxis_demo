/**
 * Tests para EmptyState component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FileText } from 'lucide-react'
import { EmptyState, EmptyExpedientes, EmptyWorkspaces } from '../EmptyState'

describe('EmptyState', () => {
  it('renderiza con título y descripción', () => {
    render(
      <EmptyState
        title="No hay datos"
        description="No se encontraron registros"
      />
    )

    expect(screen.getByText('No hay datos')).toBeInTheDocument()
    expect(screen.getByText('No se encontraron registros')).toBeInTheDocument()
  })

  it('renderiza con emoji', () => {
    render(
      <EmptyState
        emoji="📋"
        title="Sin datos"
        description="Lista vacía"
      />
    )

    expect(screen.getByText('📋')).toBeInTheDocument()
  })

  it('renderiza con icono de Lucide', () => {
    const { container } = render(
      <EmptyState
        icon={FileText}
        title="Sin datos"
        description="Lista vacía"
      />
    )

    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('llama action.onClick cuando se hace click en botón primario', () => {
    const handleClick = vi.fn()

    render(
      <EmptyState
        title="Sin datos"
        description="Lista vacía"
        action={{
          label: 'Agregar nuevo',
          onClick: handleClick,
        }}
      />
    )

    fireEvent.click(screen.getByText('Agregar nuevo'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('renderiza acción secundaria', () => {
    const handlePrimary = vi.fn()
    const handleSecondary = vi.fn()

    render(
      <EmptyState
        title="Sin datos"
        description="Lista vacía"
        action={{
          label: 'Primario',
          onClick: handlePrimary,
        }}
        secondaryAction={{
          label: 'Secundario',
          onClick: handleSecondary,
        }}
      />
    )

    expect(screen.getByText('Primario')).toBeInTheDocument()
    expect(screen.getByText('Secundario')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Secundario'))
    expect(handleSecondary).toHaveBeenCalledTimes(1)
  })

  it('renderiza como card cuando variant="card"', () => {
    const { container } = render(
      <EmptyState
        title="Sin datos"
        description="Lista vacía"
        variant="card"
      />
    )

    // Card tiene clases específicas de border y background
    expect(container.querySelector('.border')).toBeInTheDocument()
  })
})

describe('EmptyExpedientes', () => {
  it('renderiza correctamente', () => {
    const handleExtraer = vi.fn()

    render(<EmptyExpedientes onExtraer={handleExtraer} />)

    expect(screen.getByText('No hay expedientes')).toBeInTheDocument()
    expect(screen.getByText('Extraer Primer Expediente')).toBeInTheDocument()
  })

  it('llama onExtraer cuando se hace click', () => {
    const handleExtraer = vi.fn()

    render(<EmptyExpedientes onExtraer={handleExtraer} />)

    fireEvent.click(screen.getByText('Extraer Primer Expediente'))
    expect(handleExtraer).toHaveBeenCalledTimes(1)
  })
})

describe('EmptyWorkspaces', () => {
  it('renderiza correctamente', () => {
    const handleCreate = vi.fn()

    render(<EmptyWorkspaces onCreate={handleCreate} />)

    expect(screen.getByText('No hay workspaces')).toBeInTheDocument()
    expect(screen.getByText('Crear Workspace')).toBeInTheDocument()
  })

  it('llama onCreate cuando se hace click', () => {
    const handleCreate = vi.fn()

    render(<EmptyWorkspaces onCreate={handleCreate} />)

    fireEvent.click(screen.getByText('Crear Workspace'))
    expect(handleCreate).toHaveBeenCalledTimes(1)
  })
})
