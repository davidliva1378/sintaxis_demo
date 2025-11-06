/**
 * Tests para ConfiguracionEnDesarrollo
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ConfiguracionEnDesarrollo from '../ConfiguracionEnDesarrollo'

describe('ConfiguracionEnDesarrollo', () => {
  it('renderiza el componente correctamente', () => {
    render(<ConfiguracionEnDesarrollo />)

    expect(screen.getByText('Configuraciones En Desarrollo')).toBeInTheDocument()
  })

  it('muestra el banner de sección en construcción', () => {
    render(<ConfiguracionEnDesarrollo />)

    expect(screen.getByText(/sección en construcción/i)).toBeInTheDocument()
  })

  it('muestra la lista de próximas configuraciones', () => {
    render(<ConfiguracionEnDesarrollo />)

    expect(screen.getByText(/próximas configuraciones planificadas/i)).toBeInTheDocument()
    expect(screen.getByText(/notificaciones multi-canal/i)).toBeInTheDocument()
    expect(screen.getByText(/OCR para PDFs/i)).toBeInTheDocument()
    expect(screen.getByText(/IA Local/i)).toBeInTheDocument()
    expect(screen.getByText(/procesamiento de PDFs/i)).toBeInTheDocument()
    expect(screen.getByText(/configuración de plugins/i)).toBeInTheDocument()
    expect(screen.getByText(/backup y exportación/i)).toBeInTheDocument()
  })

  it('muestra información para sugerencias', () => {
    render(<ConfiguracionEnDesarrollo />)

    expect(screen.getByText(/¿tienes sugerencias?/i)).toBeInTheDocument()
  })
})
