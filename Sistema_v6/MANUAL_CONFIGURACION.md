# Manual de Configuración del Sistema PJN v6

> **Guía completa para configurar todas las opciones del sistema a través de la interfaz web**

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Acceso a la Configuración](#acceso-a-la-configuración)
3. [Configuración de Monitoreo](#configuración-de-monitoreo)
4. [Configuración del Navegador](#configuración-del-navegador)
5. [Configuración de Extracción](#configuración-de-extracción)
6. [Configuración Avanzada](#configuración-avanzada)
7. [Configuraciones en Desarrollo](#configuraciones-en-desarrollo)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## Introducción

El Sistema PJN v6 permite configurar todas las opciones del sistema directamente desde la interfaz web, sin necesidad de editar archivos manualmente. Esta guía describe todas las opciones disponibles y cómo utilizarlas.

### ¿Qué puedo configurar?

- ✅ **Monitoreo automático** de expedientes
- ✅ **Navegador** (Playwright) y scraping
- ✅ **Timeouts y límites** de extracción
- ✅ **MCP Server** para integración con LLMs
- ✅ **Storage** y almacenamiento de datos

---

## Acceso a la Configuración

1. Inicia sesión en el sistema
2. Haz clic en tu perfil (esquina superior derecha)
3. Selecciona **"Configuración"** del menú
4. Navega por los tabs disponibles:
   - **Perfil**: Información personal
   - **Credenciales PJN**: Usuario y contraseña del portal
   - **Contraseña**: Cambiar contraseña del sistema
   - **Preferencias**: Tema, notificaciones, idioma
   - **Monitoreo**: ⭐ Configuración de monitoreo automático
   - **Navegador**: ⭐ Configuración del navegador
   - **Extracción**: ⭐ Timeouts y límites
   - **Avanzado**: ⭐ MCP y Storage
   - **En Desarrollo**: Próximas configuraciones

---

## Configuración de Monitoreo

> **Ruta:** Configuración → Monitoreo

Controla cómo el sistema monitorea cambios en expedientes automáticamente.

### 🎯 Modo Simple (Recomendado)

Ideal para la mayoría de usuarios. Configura un único intervalo de verificación.

#### **Intervalo de verificación**
- **Descripción:** Cada cuánto tiempo el sistema verifica cambios
- **Valores recomendados:**
  - `1800` segundos (30 minutos) - Balance entre rapidez y carga
  - `3600` segundos (1 hora) - Para monitoreo menos frecuente
  - `0` segundos - Ejecutar una sola vez (sin monitoreo continuo)
- **Rango:** 0 - 86400 segundos (24 horas)

#### **Días de actividad**
- **Descripción:** Cuántos días hacia atrás considerar un expediente "activo"
- **Valor recomendado:** `30` días
- **Rango:** 1 - 365 días
- **Nota:** Solo expedientes con actividad reciente se monitorearan

#### **Máximo de reintentos**
- **Descripción:** Intentos de reintento si falla la verificación
- **Valor recomendado:** `3` reintentos
- **Rango:** 1 - 10 reintentos

#### **Notificar cambios**
- ✅ Activado: Envía notificaciones cuando detecta cambios
- ❌ Desactivado: Solo registra cambios en logs

#### **Descargar archivos automáticamente**
- ✅ Activado: Descarga archivos nuevos automáticamente
- ❌ Desactivado: Solo registra archivos sin descargarlos

---

### 🔧 Modo Avanzado (Horarios Laborales)

Para usuarios que necesitan intervalos diferenciados según el horario.

**¿Cuándo usar modo avanzado?**
- Quieres verificar más frecuentemente en horario laboral
- Quieres reducir la carga del sistema fuera de horario
- Necesitas intervalos diferentes para expedientes vs. entradas

#### **Activar modo avanzado**
1. Marca el checkbox "Modo Avanzado (Horarios Laborales)"
2. Configura los intervalos específicos (en minutos):

**Intervalos en Horario Laboral:**
- **Expedientes:** `10` minutos (recomendado)
- **Entradas:** `15` minutos (recomendado)

**Intervalos Fuera de Horario:**
- **Expedientes:** `60` minutos (recomendado)
- **Entradas:** `30` minutos (recomendado)

#### **Días laborales**
Selecciona qué días considerar como "laborales":
- ✅ Por defecto: Lunes a Viernes
- Puedes incluir Sábado y Domingo si es necesario

#### **Horario laboral**
- **Hora inicio:** `08:00` (recomendado)
- **Hora fin:** `18:00` (recomendado)

**Ejemplo de configuración:**
```
Modo: Avanzado
Horario laboral: Lunes a Viernes, 08:00 - 18:00
- Expedientes (laboral): cada 10 minutos
- Entradas (laboral): cada 15 minutos
- Expedientes (no laboral): cada 60 minutos
- Entradas (no laboral): cada 30 minutos
```

---

## Configuración del Navegador

> **Ruta:** Configuración → Navegador

Ajusta el comportamiento de Playwright para scraping del Portal Judicial Nacional.

### 🎭 Modo Headless

**¿Qué es headless?**
- ✅ **Activado** (recomendado): El navegador se ejecuta en segundo plano sin ventana visible
- ❌ **Desactivado**: Muestra la ventana del navegador (útil para debugging)

**⚠️ Importante:** En producción siempre debe estar activado.

---

### ⏱️ Timeouts

#### **Timeout general**
- **Descripción:** Tiempo máximo de espera para operaciones comunes (seleccionar elementos, esperar que aparezca contenido, etc.)
- **Valor por defecto:** `30000` ms (30 segundos)
- **Rango:** 1000 - 300000 ms
- **Cuándo aumentar:** Si experimentas errores de timeout con el PJN lento

#### **Timeout de navegación**
- **Descripción:** Tiempo máximo para cargar páginas completas
- **Valor por defecto:** `60000` ms (60 segundos)
- **Rango:** 1000 - 300000 ms
- **Cuándo aumentar:** Si las páginas del PJN tardan mucho en cargar

**Ejemplos de valores:**
```
PJN rápido:
- Timeout general: 20000 ms (20 seg)
- Timeout navegación: 40000 ms (40 seg)

PJN lento:
- Timeout general: 45000 ms (45 seg)
- Timeout navegación: 90000 ms (90 seg)
```

---

### 🤖 User Agent

**¿Qué es?**
El identificador que el navegador envía al servidor para identificarse.

- **Valor por defecto:** Dejar vacío (usa el User Agent de Playwright)
- **Personalizado:** Solo modificar si el PJN bloquea solicitudes

**Ejemplo de User Agent personalizado:**
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

---

## Configuración de Extracción

> **Ruta:** Configuración → Extracción

Timeouts, límites y reintentos para operaciones de scraping.

### ⏱️ Timeouts de Scraping

#### **Timeout por defecto**
- **Descripción:** Timeout general para operaciones de scraping
- **Valor por defecto:** `8000` ms (8 segundos)
- **Rango:** 1000 - 300000 ms
- **Aplica a:** Búsqueda de elementos, extracción de datos

#### **Timeout de login**
- **Descripción:** Tiempo máximo para completar el login en el PJN
- **Valor por defecto:** `60000` ms (60 segundos)
- **Rango:** 1000 - 300000 ms
- **Nota:** El login puede tardar en momentos de alta carga

#### **Timeout de descarga**
- **Descripción:** Tiempo máximo para descargar un archivo
- **Valor por defecto:** `30000` ms (30 segundos)
- **Rango:** 1000 - 300000 ms
- **Depende de:** Tamaño de archivos y velocidad de conexión

---

### 📄 Límites de Extracción

#### **Máximo de páginas de expedientes**
- **Descripción:** Cuántas páginas extraer de la lista de expedientes
- **Valor por defecto:** `200` páginas
- **Rango:** 1 - 10000 páginas
- **Sin límite:** Hacer clic en "Sin límite" extrae TODAS las páginas

**⚠️ Advertencia:** Sin límite puede tardar horas si tienes muchos expedientes.

**Cálculo aproximado:**
- 1 página = ~10 expedientes
- 200 páginas = ~2000 expedientes
- Tiempo: ~5-10 minutos por cada 100 páginas

---

### 🔁 Reintentos

#### **Máximo de reintentos para descargas**
- **Descripción:** Intentos de reintento si falla la descarga de un archivo
- **Valor por defecto:** `3` reintentos
- **Rango:** 1 - 10 reintentos
- **Balance:** 3 es un buen equilibrio entre robustez y velocidad

---

## Configuración Avanzada

> **Ruta:** Configuración → Avanzado

Configuraciones del MCP Server y Storage del sistema.

### 🖥️ MCP Server (Model Context Protocol)

Servidor para integración con Claude y otros LLMs.

#### **Habilitar servidor MCP**
- ✅ **Activado**: El servidor MCP está disponible
- ❌ **Desactivado**: MCP no estará disponible

#### **Puerto**
- **Valor por defecto:** `5000`
- **Rango:** 1 - 65535
- **Nota:** Asegúrate de que el puerto no esté en uso

#### **Modo**
- **stdio**: Comunicación por entrada/salida estándar (recomendado)
- **http**: Comunicación por HTTP

#### **Workspace Path**
- **Valor por defecto:** `workspace`
- **Descripción:** Directorio donde MCP guarda sus datos

#### **Server Name**
- **Valor por defecto:** `sintaxis-actuaciones-v6`
- **Descripción:** Nombre identificador del servidor MCP

---

#### **Funcionalidades MCP**

**Extracción de PDFs**
- ✅ Activado: Permite extraer texto de PDFs
- ❌ Desactivado: No procesa PDFs

**Búsqueda de texto completo**
- ✅ Activado: Habilita búsqueda en todo el contenido
- ❌ Desactivado: Búsqueda básica solamente

**Estadísticas**
- ✅ Activado: Genera estadísticas de uso
- ❌ Desactivado: No genera estadísticas

---

#### **Límites de PDF**

**Máximo de páginas por PDF**
- **Valor por defecto:** `100` páginas
- **Rango:** 1 - 10000 páginas
- **Nota:** PDFs muy largos pueden tardar en procesarse

**Máximo tamaño de PDF**
- **Valor por defecto:** `50` MB
- **Rango:** 1 - 1000 MB
- **Nota:** PDFs grandes consumen más memoria

---

### 💾 Storage (Almacenamiento)

Configuración de rutas y archivos del sistema.

#### **Directorio base**
- **Valor por defecto:** `data`
- **Descripción:** Directorio raíz donde se almacenan todos los datos
- **Ruta completa:** `Sistema_v6/data/`

#### **Archivo JSON base**
- **Valor por defecto:** `expedientes_base.json`
- **Descripción:** Archivo con TODOS los expedientes extraídos

#### **Archivo JSON sistema**
- **Valor por defecto:** `expedientes_sistema.json`
- **Descripción:** Archivo con expedientes seleccionados para monitoreo

#### **Directorio workspaces**
- **Valor por defecto:** `workspaces`
- **Descripción:** Carpeta donde se crean los workspaces

#### **Directorio descargas**
- **Valor por defecto:** `descargas`
- **Descripción:** Carpeta donde se guardan archivos descargados

---

#### **Formato de archivos JSON**

**Pretty JSON (con indentación)**
- ✅ Activado: JSON formateado y legible
- ❌ Desactivado: JSON compacto (ahorra espacio)

**Ensure ASCII**
- ✅ Activado: Escapa caracteres especiales (tildes, ñ, etc.)
- ❌ Desactivado: Mantiene caracteres Unicode

**Recomendación:** Pretty JSON activado, Ensure ASCII desactivado.

---

## Configuraciones en Desarrollo

> **Ruta:** Configuración → En Desarrollo

Esta sección es un placeholder para futuras configuraciones que se agregarán al sistema.

### 📋 Próximas configuraciones planificadas:

1. **Notificaciones multi-canal**
   - Email, Telegram, WhatsApp, Discord
   - Configuración de webhooks y tokens

2. **OCR para PDFs**
   - Extracción de texto de archivos escaneados
   - Soporte para múltiples idiomas

3. **IA Local (Ollama)**
   - Análisis automático de documentos
   - Resúmenes y clasificación

4. **Procesamiento avanzado de PDFs**
   - NER (Named Entity Recognition)
   - Búsqueda semántica
   - Clasificación de documentos

5. **Configuración de plugins**
   - Habilitar/deshabilitar plugins
   - Gestión de extensiones

6. **Backup y exportación**
   - Respaldos automáticos
   - Exportación a diferentes formatos

---

## Preguntas Frecuentes

### ¿Los cambios se aplican inmediatamente?

**No.** Después de guardar cambios, debes **reiniciar el servidor** para que se apliquen:

```bash
# Detener servidor
Ctrl + C

# Iniciar servidor
python -m presentation.api.rest.main
```

---

### ¿Puedo revertir cambios?

**Sí.** El sistema guarda tus cambios en el archivo `.env`. Puedes:

1. Restaurar desde la UI volviendo a los valores anteriores
2. Editar manualmente el archivo `.env`
3. Restaurar desde backup (si tienes uno)

---

### ¿Qué pasa si pongo valores incorrectos?

El sistema **valida** todos los valores antes de guardar:

- Timeouts mínimos: 1000 ms
- Puertos: 1 - 65535
- Intervalos: >= 0
- Días de actividad: 1 - 365

Si intentas guardar un valor inválido, verás un **mensaje de error** explicando el problema.

---

### ¿Los cambios afectan a otros usuarios?

**Sí.** La configuración es **global** para todo el sistema. Todos los usuarios verán los mismos valores.

---

### ¿Puedo usar diferentes configuraciones para diferentes expedientes?

**No directamente.** La configuración es global. Sin embargo, puedes:

1. Crear **workspaces** separados
2. Ejecutar **múltiples instancias** del sistema con diferentes configuraciones
3. Cambiar temporalmente la configuración según necesites

---

### ¿Cómo sé qué valores usar?

**Valores recomendados por escenario:**

**Usuario promedio (pocos expedientes):**
```
Monitoreo: 1800 seg (30 min)
Timeout general: 30000 ms
Timeout navegación: 60000 ms
Límite páginas: 200
```

**Usuario con muchos expedientes:**
```
Monitoreo: 3600 seg (1 hora)
Timeout general: 45000 ms
Timeout navegación: 90000 ms
Límite páginas: Sin límite
```

**Usuario con PJN lento:**
```
Monitoreo: 1800 seg (30 min)
Timeout general: 60000 ms (1 min)
Timeout navegación: 120000 ms (2 min)
Límite páginas: 100
```

---

### ¿Dónde puedo ver los logs?

Los logs del sistema se guardan en:
```
Sistema_v6/sistema_pjn.log
```

Puedes verlos con:
```bash
tail -f Sistema_v6/sistema_pjn.log
```

---

### ¿Necesito conocimientos técnicos para usar la configuración?

**No.** La interfaz está diseñada para ser intuitiva:

- Cada campo tiene **descripción** y **ayuda contextual**
- Valores recomendados están indicados
- Validaciones previenen errores
- Mensajes claros de éxito/error

---

## 📞 Soporte

¿Tienes dudas o sugerencias?

- **GitHub Issues**: [sintaXis/issues](https://github.com/davidliva1378/sintaXis/issues)
- **Documentación técnica**: `Sistema_v6/README.md`
- **Tests**: `Sistema_v6/tests/README.md`

---

## 📚 Referencias Adicionales

- [README Principal](../README.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Frontend Components Guide](./frontend/src/components/settings/README.md)
- [Tests Documentation](./tests/README.md)

---

**Versión:** 6.0.0
**Última actualización:** 2025-11-06
**Autor:** Sistema sintaXis
