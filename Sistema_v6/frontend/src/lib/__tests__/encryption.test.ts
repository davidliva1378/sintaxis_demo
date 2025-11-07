/**
 * Tests para encryption utilities
 */

import { describe, it, expect } from 'vitest'
import { encryptText, decryptText } from '../encryption'

describe('encryption', () => {
  describe('encryptText', () => {
    it('encripta texto correctamente', () => {
      const plaintext = 'secret password'
      const encrypted = encryptText(plaintext)

      expect(encrypted).toBeDefined()
      expect(encrypted).not.toBe(plaintext)
      expect(encrypted.length).toBeGreaterThan(0)
    })

    it('produce diferentes valores encriptados para el mismo texto', () => {
      const plaintext = 'same password'
      const encrypted1 = encryptText(plaintext)
      const encrypted2 = encryptText(plaintext)

      // Debido al IV aleatorio, deberían ser diferentes
      expect(encrypted1).not.toBe(encrypted2)
    })

    it('encripta strings vacíos', () => {
      const encrypted = encryptText('')
      expect(encrypted).toBeDefined()
      expect(encrypted.length).toBeGreaterThan(0)
    })

    it('encripta texto con caracteres especiales', () => {
      const plaintext = '¡Contraseña123!@#$%^&*()'
      const encrypted = encryptText(plaintext)

      expect(encrypted).toBeDefined()
      expect(encrypted).not.toBe(plaintext)
    })

    it('encripta texto largo', () => {
      const plaintext = 'a'.repeat(1000)
      const encrypted = encryptText(plaintext)

      expect(encrypted).toBeDefined()
      expect(encrypted).not.toBe(plaintext)
    })
  })

  describe('decryptText', () => {
    it('desencripta texto correctamente', () => {
      const plaintext = 'secret password'
      const encrypted = encryptText(plaintext)
      const decrypted = decryptText(encrypted)

      expect(decrypted).toBe(plaintext)
    })

    it('desencripta strings vacíos', () => {
      const encrypted = encryptText('')
      const decrypted = decryptText(encrypted)

      expect(decrypted).toBe('')
    })

    it('desencripta texto con caracteres especiales', () => {
      const plaintext = '¡Contraseña123!@#$%^&*()'
      const encrypted = encryptText(plaintext)
      const decrypted = decryptText(encrypted)

      expect(decrypted).toBe(plaintext)
    })

    it('desencripta texto largo', () => {
      const plaintext = 'a'.repeat(1000)
      const encrypted = encryptText(plaintext)
      const decrypted = decryptText(encrypted)

      expect(decrypted).toBe(plaintext)
    })

    it('falla con texto encriptado inválido', () => {
      expect(() => decryptText('invalid encrypted text')).toThrow()
    })

    it('falla con string vacío', () => {
      expect(() => decryptText('')).toThrow()
    })
  })

  describe('encriptar y desencriptar', () => {
    it('round-trip funciona correctamente', () => {
      const testCases = [
        'password123',
        'admin@example.com',
        '¡Hola Mundo!',
        'user@domain.com',
        'P@ssw0rd!#$%',
        '123456789',
        'a',
        'Very Long Password With Many Characters 1234567890',
      ]

      testCases.forEach((plaintext) => {
        const encrypted = encryptText(plaintext)
        const decrypted = decryptText(encrypted)
        expect(decrypted).toBe(plaintext)
      })
    })

    it('múltiples encriptaciones producen el mismo plaintext al desencriptar', () => {
      const plaintext = 'test password'

      const encrypted1 = encryptText(plaintext)
      const encrypted2 = encryptText(plaintext)
      const encrypted3 = encryptText(plaintext)

      expect(decryptText(encrypted1)).toBe(plaintext)
      expect(decryptText(encrypted2)).toBe(plaintext)
      expect(decryptText(encrypted3)).toBe(plaintext)
    })
  })
})
