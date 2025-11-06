/**
 * Tests para LoadingSpinner components
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  LoadingSpinner,
  PageLoader,
  InlineLoader,
  FullPageLoader,
  LoadingDots,
  LoadingBar,
} from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renderiza correctamente', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renderiza con texto', () => {
    render(<LoadingSpinner text="Cargando..." />)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('aplica size classes correctamente', () => {
    const { container } = render(<LoadingSpinner size="lg" />)
    const svg = container.querySelector('svg')
    expect(svg?.className).toContain('h-8')
    expect(svg?.className).toContain('w-8')
  })

  it('aplica variant classes correctamente', () => {
    const { container } = render(<LoadingSpinner variant="primary" />)
    const svg = container.querySelector('svg')
    expect(svg?.className).toContain('text-blue-600')
  })

  it('renderiza en modo fullscreen', () => {
    const { container } = render(<LoadingSpinner fullscreen />)
    expect(container.querySelector('.fixed')).toBeInTheDocument()
    expect(container.querySelector('.inset-0')).toBeInTheDocument()
  })

  it('aplica className personalizado', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />)
    expect(container.querySelector('.custom-class')).toBeInTheDocument()
  })
})

describe('PageLoader', () => {
  it('renderiza correctamente', () => {
    render(<PageLoader />)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('renderiza con texto personalizado', () => {
    render(<PageLoader text="Cargando datos..." />)
    expect(screen.getByText('Cargando datos...')).toBeInTheDocument()
  })
})

describe('InlineLoader', () => {
  it('renderiza sin texto', () => {
    const { container } = render(<InlineLoader />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('renderiza con texto', () => {
    render(<InlineLoader text="Procesando..." />)
    expect(screen.getByText('Procesando...')).toBeInTheDocument()
  })
})

describe('FullPageLoader', () => {
  it('renderiza en fullscreen', () => {
    const { container } = render(<FullPageLoader />)
    expect(container.querySelector('.fixed')).toBeInTheDocument()
    expect(container.querySelector('.z-50')).toBeInTheDocument()
  })

  it('renderiza con texto personalizado', () => {
    render(<FullPageLoader text="Extrayendo expediente..." />)
    expect(screen.getByText('Extrayendo expediente...')).toBeInTheDocument()
  })
})

describe('LoadingDots', () => {
  it('renderiza 3 dots', () => {
    const { container } = render(<LoadingDots />)
    const dots = container.querySelectorAll('.rounded-full')
    expect(dots.length).toBe(3)
  })

  it('aplica className personalizado', () => {
    const { container } = render(<LoadingDots className="custom-dots" />)
    expect(container.querySelector('.custom-dots')).toBeInTheDocument()
  })
})

describe('LoadingBar', () => {
  it('renderiza correctamente sin progreso', () => {
    const { container } = render(<LoadingBar />)
    const bar = container.querySelector('.bg-blue-600')
    expect(bar).toBeInTheDocument()
  })

  it('renderiza con progreso específico', () => {
    const { container } = render(<LoadingBar progress={75} />)
    const bar = container.querySelector('.bg-blue-600')
    expect(bar).toHaveStyle({ width: '75%' })
  })

  it('renderiza con progreso 0%', () => {
    const { container } = render(<LoadingBar progress={0} />)
    const bar = container.querySelector('.bg-blue-600')
    expect(bar).toHaveStyle({ width: '0%' })
  })

  it('renderiza con progreso 100%', () => {
    const { container } = render(<LoadingBar progress={100} />)
    const bar = container.querySelector('.bg-blue-600')
    expect(bar).toHaveStyle({ width: '100%' })
  })
})
