# 📄 Documentación Mejorada: `utils.py`

Módulo de funciones auxiliares comunes.

## Funciones

### `limpiar_texto(texto)`
- **Descripción:** Elimina saltos de línea y espacios innecesarios.
- **Ejemplo:**
```python
limpiar_texto(" Hola\nMundo ")  # → "Hola Mundo"
```

### `normalizar_texto(texto)`
- **Descripción:** Convierte a minúsculas, sin tildes ni caracteres especiales. Útil para comparar claves textuales o detectar duplicados.
- **Ejemplo:**
```python
normalizar_texto("Expediente Nº Á123")  # → "expediente n 123"
```

## Uso en otros módulos
Se utiliza en:
- `expedientes.py` para normalizar comparaciones de expedientes.
- `entradas.py` para evitar duplicados de notificaciones.
- `actuaciones.py` para generar hashes únicos de documentos.
