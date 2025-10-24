# Resumen: Actualización Automática de Actuaciones

**Fecha**: 2025-10-23  
**Estado**: ✅ COMPLETADO  
**Hito**: 1.5 - Actualización automática de actuaciones de expedientes con cambios

---

## 📋 Resumen Ejecutivo

Se implementó exitosamente la funcionalidad de actualización automática de actuaciones cuando el monitor PJN detecta cambios relevantes en expedientes. El sistema ahora puede:

- Detectar cambios de tipo `nueva_actuacion` o `cambio_situacion`
- Abrir automáticamente cada expediente en el portal
- Extraer actuaciones actualizadas
- Descargar adjuntos (PDFs) nuevos
- Reintentar en caso de errores
- Continuar el monitoreo sin interrupciones

---

## 🎯 Configuración

### Archivo: `config/sistema.json`

```json
{
  "actualizar_actuaciones_automaticamente": true,
  "max_reintentos_actualizacion_actuaciones": 3
}
```

### Variables de Entorno (opcional)

```bash
export ACTUALIZAR_ACTUACIONES_AUTOMATICAMENTE=true
export MAX_REINTENTOS_ACTUALIZACION_ACTUACIONES=3
```

---

## 🔧 Archivos Modificados

1. **config/sistema.json** - Añadidas opciones de configuración
2. **configuracion/monitor/shared_config.py** - Añadidos campos `actualizar_actuaciones_automaticamente` y `max_reintentos_actualizacion_actuaciones`
3. **configuracion/core/system_config.py** - Actualizado para cargar desde JSON y variables de entorno
4. **pjn/monitor/core.py** - Implementado método `_actualizar_actuaciones_expedientes()` e integración

---

## 📝 Implementación Técnica

### Método Principal: `_actualizar_actuaciones_expedientes()`

**Ubicación**: `pjn/monitor/core.py` líneas 337-492

**Funcionamiento**:
1. Filtra cambios relevantes (nueva_actuacion, cambio_situacion)
2. Abre sesión de browser autenticada
3. Para cada expediente:
   - Descompone número usando `descomponer_numero_expediente()`
   - Busca expediente con `buscar_expedientes()`
   - Abre expediente con `mostrar_y_elegir_expediente()`
   - Procesa actuaciones con `procesar_actuaciones_expediente()`
   - Descarga adjuntos automáticamente
   - Reintenta hasta 3 veces en caso de error
4. Registra estadísticas de éxito/fallo

**Características**:
- ✅ Asíncrono (async/await)
- ✅ Reintentos configurables con delays
- ✅ Manejo robusto de errores
- ✅ No detiene el monitoreo si falla
- ✅ Logging detallado
- ✅ Reutiliza sesión de browser

---

## 🐛 Bugs Corregidos

### Error de Importación (2025-10-23)

**Problema**:
```python
ImportError: cannot import name 'abrir_expediente' from 'Sistema_v5.pjn.scraping.expedientes'
```

**Causa**: Se intentaba importar función `abrir_expediente` que no existe como función independiente.

**Solución**:
- Reemplazado por flujo correcto: `buscar_expedientes()` + `mostrar_y_elegir_expediente()`
- Añadido `descomponer_numero_expediente()` para normalizar números
- Navegación optimizada a página de consultas

**Líneas modificadas**: `pjn/monitor/core.py:372-432`

---

## ✅ Pruebas Realizadas

### Verificaciones Técnicas
- ✅ Sintaxis correcta - archivo compila sin errores
- ✅ Todos los imports necesarios existen y funcionan
- ✅ Método es async con firma correcta
- ✅ Integración en ciclo de monitoreo verificada
- ✅ Llamada condicional basada en configuración

### Pruebas de Ejecución
- ✅ Monitor ejecutado con 2068 expedientes (138 páginas)
- ✅ Sin errores de importación
- ✅ Sin cambios detectados - comportamiento esperado
- ✅ Sistema listo para actualizar cuando detecte cambios

---

## 📊 Comportamiento Esperado

### Cuando hay cambios:

```
INFO - 📊 Detectados 90 expedientes con cambios
INFO - ✅ Actualizados 90/90 manifests con cambios detectados
INFO - 🔄 Actualizando actuaciones de 90 expediente(s) (de 90 cambios totales)
INFO - ✅ Actuaciones actualizadas para FPA 12345/2024 (129 actuaciones)
INFO - 📊 Resumen actualización de actuaciones: 85 exitosos, 5 fallidos (de 90 expedientes)
```

### Cuando NO hay cambios:

```
INFO - Extraídos 2068 expedientes del portal (motivo: sin_siguiente)
INFO - Sin cambios en expedientes detectados
```

---

## 🔍 Logs a Monitorear

### Inicio del proceso:
```
🔄 Actualizando actuaciones de X expediente(s) (de Y cambios totales)
```

### Por cada expediente exitoso:
```
✅ Actuaciones actualizadas para [NUMERO] (N actuaciones)
```

### Errores:
```
⚠️ Error al actualizar [NUMERO] (intento X): [mensaje]
❌ Fallo definitivo al actualizar [NUMERO] tras 3 intentos: [error]
```

### Resumen final:
```
📊 Resumen actualización de actuaciones: X exitosos, Y fallidos (de Z expedientes)
```

---

## 🎓 Uso

El sistema se activa automáticamente cuando:

1. El monitor detecta cambios en expedientes
2. Los cambios son de tipo relevante:
   - `nueva_actuacion` - Cambió la fecha de última actuación
   - `cambio_situacion` - Cambió el estado del expediente
   - `multiples_cambios` - Que incluya alguno de los anteriores
3. La configuración `actualizar_actuaciones_automaticamente` está en `true`

**No requiere intervención manual** - el monitor actualiza automáticamente.

---

## 📚 Documentación Relacionada

- **Plan de mejoras**: `PLAN_MEJORAS_METADATOS.md` - Hito 1.5
- **Configuración**: `config/sistema.json`
- **Código fuente**: `pjn/monitor/core.py:337-492`
- **Script de prueba**: `test_actualizacion_actuaciones.py`

---

## ✨ Próximos Pasos

1. Monitorear logs en producción cuando detecte cambios reales
2. Ajustar `max_reintentos_actualizacion_actuaciones` según necesidad
3. Implementar Fase 2: Historial de cambios y reportes mejorados

---

**Autor**: Sistema v5 - Monitor PJN  
**Versión**: 2.0  
**Última actualización**: 2025-10-23
