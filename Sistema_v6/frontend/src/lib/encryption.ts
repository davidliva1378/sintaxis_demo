import CryptoJS from 'crypto-js';

// Clave de encriptación desde variable de entorno o default
const ENCRYPTION_KEY = import.meta.env.VITE_ENCRYPTION_KEY || 'default-encryption-key-change-in-production';

/**
 * Encripta un texto usando AES
 * @param text - Texto a encriptar
 * @returns Texto encriptado en base64
 */
export function encryptText(text: string): string {
  try {
    const encrypted = CryptoJS.AES.encrypt(text, ENCRYPTION_KEY);
    return encrypted.toString();
  } catch (error) {
    console.error('Error al encriptar:', error);
    throw new Error('Error al encriptar el texto');
  }
}

/**
 * Desencripta un texto encriptado con AES
 * @param encryptedText - Texto encriptado en base64
 * @returns Texto desencriptado
 */
export function decryptText(encryptedText: string): string {
  try {
    const decrypted = CryptoJS.AES.decrypt(encryptedText, ENCRYPTION_KEY);
    return decrypted.toString(CryptoJS.enc.Utf8);
  } catch (error) {
    console.error('Error al desencriptar:', error);
    throw new Error('Error al desencriptar el texto');
  }
}

/**
 * Genera un hash SHA256 de un texto
 * @param text - Texto a hashear
 * @returns Hash en hexadecimal
 */
export function hashText(text: string): string {
  try {
    return CryptoJS.SHA256(text).toString();
  } catch (error) {
    console.error('Error al generar hash:', error);
    throw new Error('Error al generar hash');
  }
}
