"""Ejemplos de uso del sistema de excepciones de Sistema_v5."""

import asyncio
from Sistema_v5.pjn import (
    PJNError,
    CredencialesFaltantes,
    SesionInvalida,
    ExtraccionError,
    TimeoutExtraccion,
    DescargaFallida,
)


# Ejemplo 1: Captura específica de errores de autenticación
async def ejemplo_autenticacion():
    """Muestra cómo manejar errores de autenticación."""
    try:
        # Código que podría fallar por credenciales
        from Sistema_v5.pjn.scraping import obtener_pagina_autenticada
        async with obtener_pagina_autenticada() as (page, _, _):
            pass
    except CredencialesFaltantes:
        print("Por favor configure PJN_USER y PJN_PASSWORD")
    except SesionInvalida:
        print("La sesión expiró, reintentando login...")
    except PJNError as e:
        print(f"Error general del sistema: {e}")


# Ejemplo 2: Captura por jerarquía
async def ejemplo_extraccion():
    """Muestra cómo capturar errores de extracción."""
    try:
        # Código que extrae datos
        pass
    except TimeoutExtraccion:
        # Manejo específico para timeouts
        print("La extracción tardó demasiado, reintentando...")
    except ExtraccionError:
        # Captura cualquier otro error de extracción
        print("Error general durante la extracción")


# Ejemplo 3: Excepciones con contexto
def ejemplo_descarga_fallida():
    """Muestra cómo usar excepciones con metadatos."""
    try:
        raise DescargaFallida(
            "No se pudo descargar el archivo",
            intentos=3,
            error_original=TimeoutError("Connection timeout")
        )
    except DescargaFallida as e:
        print(f"Descarga falló después de {e.intentos} intentos")
        print(f"Error original: {e.error_original}")


# Ejemplo 4: Preservar contexto con 'from'
async def ejemplo_preservar_contexto():
    """Muestra cómo preservar el contexto del error original."""
    try:
        try:
            raise ValueError("Error interno")
        except ValueError as e:
            # Lanzar excepción personalizada preservando contexto
            raise ExtraccionError("Error procesando datos") from e
    except ExtraccionError as e:
        print(f"Error: {e}")
        print(f"Causa original: {e.__cause__}")


# Ejemplo 5: Manejo en scripts
async def ejemplo_script_main():
    """Patrón recomendado para el main de scripts."""
    try:
        # Lógica principal del script
        pass
    except CredencialesFaltantes as e:
        print(f"❌ Credenciales: {e}")
        print("💡 Solución: Configure las variables de entorno")
        return 1
    except SesionInvalida as e:
        print(f"❌ Sesión: {e}")
        print("💡 Solución: Elimine pjn_storage_state.json")
        return 1
    except ExtraccionError as e:
        print(f"❌ Extracción: {e}")
        return 2
    except PJNError as e:
        print(f"❌ Sistema PJN: {e}")
        return 3
    except KeyboardInterrupt:
        print("\n⚠️ Cancelado por el usuario")
        return 130
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 255
    
    return 0


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(ejemplo_autenticacion())
    asyncio.run(ejemplo_extraccion())
    ejemplo_descarga_fallida()
    asyncio.run(ejemplo_preservar_contexto())
