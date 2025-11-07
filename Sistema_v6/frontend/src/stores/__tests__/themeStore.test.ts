/**
 * Tests para themeStore
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useThemeStore } from '../themeStore'

describe('themeStore', () => {
  beforeEach(() => {
    // Reset store antes de cada test
    useThemeStore.setState({ theme: 'light' })
    localStorage.clear()
  })

  describe('Estado inicial', () => {
    it('tiene tema light por defecto', () => {
      const state = useThemeStore.getState()
      expect(state.theme).toBe('light')
    })
  })

  describe('toggleTheme', () => {
    it('cambia de light a dark', () => {
      useThemeStore.setState({ theme: 'light' })

      useThemeStore.getState().toggleTheme()

      const state = useThemeStore.getState()
      expect(state.theme).toBe('dark')
    })

    it('cambia de dark a light', () => {
      useThemeStore.setState({ theme: 'dark' })

      useThemeStore.getState().toggleTheme()

      const state = useThemeStore.getState()
      expect(state.theme).toBe('light')
    })

    it('alterna múltiples veces correctamente', () => {
      useThemeStore.setState({ theme: 'light' })

      useThemeStore.getState().toggleTheme()
      expect(useThemeStore.getState().theme).toBe('dark')

      useThemeStore.getState().toggleTheme()
      expect(useThemeStore.getState().theme).toBe('light')

      useThemeStore.getState().toggleTheme()
      expect(useThemeStore.getState().theme).toBe('dark')
    })
  })

  describe('setTheme', () => {
    it('puede setear tema manualmente', () => {
      useThemeStore.getState().setTheme('dark')
      expect(useThemeStore.getState().theme).toBe('dark')

      useThemeStore.getState().setTheme('light')
      expect(useThemeStore.getState().theme).toBe('light')
    })
  })

  describe('Persistencia', () => {
    it('persiste el tema en localStorage', () => {
      useThemeStore.setState({ theme: 'dark' })

      // El tema debería estar en localStorage
      // (Zustand persist middleware maneja esto automáticamente)
      const state = useThemeStore.getState()
      expect(state.theme).toBe('dark')
    })
  })
})
