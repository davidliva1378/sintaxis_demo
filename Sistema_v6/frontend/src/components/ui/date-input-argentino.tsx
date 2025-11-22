import React, { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { parse, format, isValid } from 'date-fns'

interface DateInputArgentinoProps {
  value?: string  // Valor en YYYY-MM-DD (desde backend)
  onChange: (value: string | undefined) => void  // Emite YYYY-MM-DD o undefined
  placeholder?: string
  label?: string
  error?: string
  disabled?: boolean
  className?: string
}

/**
 * Input de fecha con formato argentino (dd/mm/aaaa).
 *
 * - El usuario ingresa en formato dd/mm/aaaa
 * - Aplica máscara automática mientras escribe
 * - Valida que la fecha sea real
 * - Convierte automáticamente a YYYY-MM-DD para el backend
 * - Acepta y muestra valores en YYYY-MM-DD del backend
 */
export function DateInputArgentino({
  value,
  onChange,
  placeholder = 'dd/mm/aaaa',
  label,
  error,
  disabled = false,
  className = '',
}: DateInputArgentinoProps) {
  const [inputValue, setInputValue] = useState('')

  // Convertir YYYY-MM-DD → dd/mm/aaaa para mostrar
  useEffect(() => {
    if (value) {
      try {
        const date = parse(value, 'yyyy-MM-dd', new Date())
        if (isValid(date)) {
          setInputValue(format(date, 'dd/MM/yyyy'))
        }
      } catch (e) {
        setInputValue('')
      }
    } else {
      setInputValue('')
    }
  }, [value])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let newValue = e.target.value

    // Aplicar máscara mientras el usuario escribe
    // Solo permitir dígitos
    newValue = newValue.replace(/\D/g, '')

    if (newValue.length > 0) {
      // Aplicar formato dd/mm/aaaa automáticamente
      if (newValue.length <= 2) {
        newValue = newValue
      } else if (newValue.length <= 4) {
        newValue = `${newValue.slice(0, 2)}/${newValue.slice(2)}`
      } else {
        newValue = `${newValue.slice(0, 2)}/${newValue.slice(2, 4)}/${newValue.slice(4, 8)}`
      }
    }

    setInputValue(newValue)

    // Validar y convertir a YYYY-MM-DD cuando está completo
    if (newValue.length === 10) {
      const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/
      const match = newValue.match(regex)

      if (match) {
        const [, day, month, year] = match
        try {
          const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))

          // Validar que la fecha sea real (ej: 31/02/2024 es inválida)
          if (
            date.getDate() === parseInt(day) &&
            date.getMonth() === parseInt(month) - 1 &&
            date.getFullYear() === parseInt(year)
          ) {
            // Emitir en formato YYYY-MM-DD
            onChange(format(date, 'yyyy-MM-dd'))
          } else {
            // Fecha inválida, no emitir
            onChange(undefined)
          }
        } catch (e) {
          // Error al crear la fecha
          onChange(undefined)
        }
      }
    } else if (newValue.length === 0) {
      // Campo vacío
      onChange(undefined)
    }
  }

  const handleBlur = () => {
    // Validar al perder foco
    if (inputValue.length > 0 && inputValue.length !== 10) {
      // Formato incompleto, limpiar
      setInputValue('')
      onChange(undefined)
    }
  }

  return (
    <div className="space-y-2">
      {label && <label className="text-sm font-medium">{label}</label>}
      <Input
        type="text"
        value={inputValue}
        onChange={handleChange}
        onBlur={handleBlur}
        placeholder={placeholder}
        disabled={disabled}
        className={`${error ? 'border-red-500' : ''} ${className}`}
        maxLength={10}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
      {!error && inputValue.length > 0 && inputValue.length < 10 && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Formato: dd/mm/aaaa
        </p>
      )}
    </div>
  )
}
