/**
 * Tests para Button component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from '../button'

describe('Button', () => {
  it('renderiza correctamente con texto', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('llama onClick cuando se hace click', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('no llama onClick cuando está disabled', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick} disabled>Click me</Button>)

    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('aplica variant classes correctamente', () => {
    const { container } = render(<Button variant="outline">Outline</Button>)
    const button = container.querySelector('button')
    expect(button?.className).toContain('border')
  })

  it('aplica size classes correctamente', () => {
    const { container } = render(<Button size="sm">Small</Button>)
    const button = container.querySelector('button')
    expect(button?.className).toContain('h-8')
  })

  it('renderiza children correctamente', () => {
    render(
      <Button>
        <span data-testid="icon">🔍</span>
        Search
      </Button>
    )

    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('Search')).toBeInTheDocument()
  })

  it('aplica className personalizado', () => {
    const { container } = render(<Button className="custom-class">Button</Button>)
    const button = container.querySelector('button')
    expect(button?.className).toContain('custom-class')
  })

  it('soporta type submit', () => {
    const { container } = render(<Button type="submit">Submit</Button>)
    const button = container.querySelector('button')
    expect(button?.type).toBe('submit')
  })
})
