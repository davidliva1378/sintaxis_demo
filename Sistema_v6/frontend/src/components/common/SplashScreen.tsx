/**
 * SplashScreen - Animación matrix estilo "sintaXis"
 *
 * Replica la animación del splash.py (PySide6) en React:
 * 1. Grid de caracteres aleatorios que cambian
 * 2. Desaparición secuencial de caracteres
 * 3. Formación de "sintaXis" letra por letra
 */

import { useState, useEffect, useMemo, useCallback, useRef } from 'react'

interface CellState {
  char: string
  visible: boolean
  isSintaxis: boolean
  finalChar?: string
}

const COLS = 50
const ROWS = 30
const CHARACTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'
const SINTAXIS_WORD = 'sintaXis'

type AnimationPhase = 'changing' | 'disappearing' | 'forming' | 'complete'

interface SplashScreenProps {
  onComplete?: () => void
  duration?: number // milliseconds before starting disappear phase
}

export default function SplashScreen({ onComplete, duration = 3000 }: SplashScreenProps) {
  const [phase, setPhase] = useState<AnimationPhase>('changing')
  const [grid, setGrid] = useState<CellState[]>([])
  const disappearIndexRef = useRef(0)
  const formIndexRef = useRef(0)

  // Posiciones de "sintaXis" en la última fila (esquina inferior derecha)
  const sintaxisPositions = useMemo(() => {
    const lastRowStart = (ROWS - 1) * COLS
    const wordStartCol = COLS - SINTAXIS_WORD.length
    return SINTAXIS_WORD.split('').map((_, i) => lastRowStart + wordStartCol + i)
  }, [])

  // Índices a desaparecer (excluyendo sintaXis)
  const indicesToDisappear = useMemo(() => {
    const indices: number[] = []
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        const idx = row * COLS + col
        if (!sintaxisPositions.includes(idx)) {
          indices.push(idx)
        }
      }
    }
    return indices
  }, [sintaxisPositions])

  // Inicializar grid
  useEffect(() => {
    const initialGrid: CellState[] = []
    for (let i = 0; i < ROWS * COLS; i++) {
      const isSintaxis = sintaxisPositions.includes(i)
      const charIndex = sintaxisPositions.indexOf(i)
      initialGrid.push({
        char: CHARACTERS[Math.floor(Math.random() * CHARACTERS.length)],
        visible: true,
        isSintaxis,
        finalChar: isSintaxis ? SINTAXIS_WORD[charIndex] : undefined
      })
    }
    setGrid(initialGrid)
  }, [sintaxisPositions])

  // Fase 1: Cambio de caracteres aleatorios (efecto ruido)
  useEffect(() => {
    if (phase !== 'changing' && phase !== 'disappearing') return

    const interval = setInterval(() => {
      setGrid(prev => prev.map(cell => {
        if (!cell.visible) return cell
        // En fase changing: 15% de cambio, en disappearing: 8%
        if (Math.random() > (phase === 'changing' ? 0.85 : 0.92)) {
          return { ...cell, char: CHARACTERS[Math.floor(Math.random() * CHARACTERS.length)] }
        }
        return cell
      }))
    }, 60)

    return () => clearInterval(interval)
  }, [phase])

  // Transición a fase "disappearing" después de duration
  useEffect(() => {
    if (phase !== 'changing') return
    const timeout = setTimeout(() => {
      disappearIndexRef.current = 0
      setPhase('disappearing')
    }, duration)
    return () => clearTimeout(timeout)
  }, [phase, duration])

  // Fase 2: Desaparición secuencial
  useEffect(() => {
    if (phase !== 'disappearing') return

    const interval = setInterval(() => {
      if (disappearIndexRef.current >= indicesToDisappear.length) {
        clearInterval(interval)
        setTimeout(() => {
          formIndexRef.current = 0
          setPhase('forming')
        }, 500)
        return
      }

      const idx = indicesToDisappear[disappearIndexRef.current]
      setGrid(g => g.map((cell, i) => i === idx ? { ...cell, visible: false } : cell))
      disappearIndexRef.current++
    }, 14) // mismo timing que PySide6

    return () => clearInterval(interval)
  }, [phase, indicesToDisappear])

  // Fase 3: Formar "sintaXis" letra por letra
  useEffect(() => {
    if (phase !== 'forming') return

    const formLetter = () => {
      if (formIndexRef.current >= sintaxisPositions.length) {
        // Esperar 2 segundos mostrando "sintaXis" antes de cerrar
        setTimeout(() => {
          setPhase('complete')
          onComplete?.()
        }, 2000)
        return
      }

      const pos = sintaxisPositions[formIndexRef.current]
      setGrid(g => g.map((cell, i) => {
        if (i === pos && cell.finalChar) {
          return { ...cell, char: cell.finalChar, visible: true }
        }
        return cell
      }))
      formIndexRef.current++

      // Siguiente letra en 150ms
      setTimeout(formLetter, 150)
    }

    formLetter()
  }, [phase, sintaxisPositions, onComplete])

  // Permitir skip con click o tecla
  const handleSkip = useCallback(() => {
    setPhase('complete')
    onComplete?.()
  }, [onComplete])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
        handleSkip()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSkip])

  if (phase === 'complete') return null

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0f0f23] font-mono cursor-pointer select-none"
      onClick={handleSkip}
      role="button"
      tabIndex={0}
      aria-label="Splash screen - click or press any key to skip"
    >
      {/* Grid de caracteres */}
      <div
        className="grid gap-0 p-4"
        style={{
          gridTemplateColumns: `repeat(${COLS}, 1fr)`,
          maxWidth: '100vw',
          maxHeight: '100vh',
        }}
      >
        {grid.map((cell, i) => (
          <span
            key={i}
            className={`
              text-center transition-opacity duration-75
              ${!cell.visible ? 'opacity-0' : 'opacity-100'}
              ${cell.isSintaxis && (phase === 'forming' || phase === 'complete')
                ? 'text-white font-bold'
                : 'text-white/70'}
            `}
            style={{
              fontSize: 'clamp(8px, 1.5vw, 16px)',
              width: 'clamp(10px, 2vw, 24px)',
              height: 'clamp(14px, 2.8vw, 28px)',
              lineHeight: 'clamp(14px, 2.8vw, 28px)',
            }}
          >
            {cell.visible ? cell.char : ''}
          </span>
        ))}
      </div>

      {/* Hint para saltar */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/30 text-xs">
        Click o presiona cualquier tecla para saltar
      </div>
    </div>
  )
}
