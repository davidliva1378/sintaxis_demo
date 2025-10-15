# Refactorización del Manejo de Excepciones en Sistema_v5

## Resumen

Se ha implementado un sistema completo de excepciones personalizadas para Sistema_v5, mejorando significativamente el manejo de errores, la claridad del código y la experiencia del usuario.

## Cambios Realizados

### 1. Nuevo Módulo de Excepciones (`Sistema_v5/pjn/exceptions.py`)

Se creó una jerarquía de excepciones especializada:

```
PJNError (base)
├── AutenticacionError
│   ├── CredencialesFaltantes
│   └── SesionInvalida
├── ExtraccionError
│   ├── ExpedienteNoEncontrado
│   ├── ActuacionesNoDisponibles
│   └── TimeoutExtraccion
├── ParsingError
│   ├── FormatoInvalido
│   └── DatosIncompletos
├── DescargaError
│   ├── ArchivoNoDisponible
│   └── DescargaFallida (con metadatos)
├── ValidacionError
│   └── ParametroInvalido (con metadatos)
└── SistemaError
    ├── ConfiguracionError
    └── EstadoInvalido
```

**Beneficios:**
- Excepciones específicas para cada tipo de error
- Jerarquía que permite captura granular o general
- Excepciones con contexto adicional (ej: `DescargaFallida` incluye número de intentos)

### 2. Actualización de `base.py`

**Antes:**
```python
class CredencialesFaltantes(EnvironmentError):
    pass

class SesionInvalida(RuntimeError):
    pass
```

**Después:**
```python
from ..exceptions import CredencialesFaltantes, SesionInvalida
```

**Beneficio:** Centralización de excepciones y eliminación de duplicación.

### 3. Refactorización de `actuaciones.py`

#### Mejora en `extraer_actuaciones_historicas`

**Antes:**
```python
try:
    await page_expediente.wait_for_selector(...)
except Exception:
    return [], "Timeout esperando tabla..."
```

**Después:**
```python
try:
    await page_expediente.wait_for_selector(...)
except PlaywrightTimeout as e:
    raise TimeoutExtraccion(
        "Timeout esperando tabla o mensaje de actuaciones históricas"
    ) from e
```

**Beneficios:**
- Preserva el contexto del error original (`from e`)
- Permite captura específica de timeouts
- Mejor stack trace para debugging

#### Mejora en `descargar_archivos_actuaciones`

**Antes:**
```python
except Exception as e:
    if intento == 2:
        print(f"❌ Falló la descarga tras 3 intentos: {e}")
```

**Después:**
```python
except (PlaywrightTimeout, asyncio.TimeoutError) as e:
    ultimo_error = e
    if intento == 2:
        print(f"❌ Timeout en descarga tras 3 intentos")
    # ...
except (OSError, IOError) as e:
    # Errores de I/O no deben reintentar
    print(f"❌ Error de I/O al guardar archivo: {e}")
    ultimo_error = e
    break
except Exception as e:
    ultimo_error = e
    # ...
```

**Beneficios:**
- Manejo diferenciado según tipo de error
- Errores de I/O no reintentan (evita loops innecesarios)
- Timeouts tienen mensaje específico
- Se guarda referencia al último error para análisis

### 4. Actualización del Script Ejecutable

**`rf_test_extraccion_completa.py`**

**Antes:**
```python
if __name__ == "__main__":
    asyncio.run(main())
```

**Después:**
```python
async def main() -> None:
    try:
        # ... código principal ...
    except CredencialesFaltantes as e:
        print(f"\n❌ Error de credenciales: {e}")
        print("💡 Configure las variables PJN_USER y PJN_PASSWORD")
    except SesionInvalida as e:
        print(f"\n❌ Error de sesión: {e}")
        print("💡 Elimine pjn_storage_state.json e intente nuevamente")
    except ExtraccionError as e:
        print(f"\n❌ Error durante la extracción: {e}")
    except PJNError as e:
        print(f"\n❌ Error del sistema PJN: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {type(e).__name__}: {e}")
        traceback.print_exc()
```

**Beneficios:**
- Mensajes específicos según tipo de error
- Sugerencias de solución para el usuario
- Captura explícita de `KeyboardInterrupt`
- Stack trace solo para errores inesperados

### 5. Exportación en `__init__.py`

Se agregaron todas las excepciones al `__all__` del paquete principal:

```python
from .exceptions import (
    PJNError,
    CredencialesFaltantes,
    SesionInvalida,
    ExtraccionError,
    # ... etc
)
```

**Beneficio:** Facilita el uso de excepciones con `from Sistema_v5.pjn import CredencialesFaltantes`

## Comparación: Antes vs Después

### Ejemplo 1: Manejo de Timeout

**Antes:**
```python
try:
    await page.wait_for_selector(...)
except Exception:
    return [], "Timeout..."  # Pierde el contexto del error
```

**Después:**
```python
try:
    await page.wait_for_selector(...)
except PlaywrightTimeout as e:
    raise TimeoutExtraccion("...") from e  # Preserva contexto
```

### Ejemplo 2: Usuario Final

**Antes:**
```
❌ Error: EnvironmentError: Missing PJN_USER
```

**Después:**
```
❌ Error de credenciales: Missing PJN_USER
💡 Configure las variables de entorno PJN_USER y PJN_PASSWORD
```

## Estadísticas

- **Excepciones broad eliminadas:** Convertidas de `Exception` genérico a específicas
- **Nuevas excepciones:** 17 clases especializadas
- **Archivos modificados:** 4 (base.py, actuaciones.py, __init__.py, rf_test_extraccion_completa.py)
- **Archivos nuevos:** 1 (exceptions.py)

## Pruebas Realizadas

✅ Jerarquía de excepciones correcta
✅ Imports funcionan correctamente
✅ Captura polimórfica (ej: `TimeoutExtraccion` se puede capturar como `ExtraccionError`)
✅ Módulos existentes siguen funcionando

## Próximos Pasos Recomendados

1. **Agregar tests unitarios** para excepciones
2. **Documentar** cada excepción con ejemplos de uso
3. **Expandir** el uso de excepciones específicas en expedientes.py y entradas.py
4. **Implementar logging** estructurado junto con excepciones

## Beneficios Generales

1. **Debugging más fácil:** Stack traces preservan contexto completo
2. **Código más mantenible:** Intención clara de qué errores se esperan
3. **Mejor UX:** Mensajes específicos con sugerencias de solución
4. **Más robusto:** Manejo diferenciado evita reintentos innecesarios
5. **Type-safe:** IDEs pueden autocompletar excepciones
