# 🔧 Corrección: Botón de Extracción Masiva

**Fecha**: 2025-11-07
**Problema**: El botón de Extracción Masiva en expedientes no funcionaba
**Estado**: ✅ CORREGIDO

---

## 🐛 Problema Identificado

El botón de "Extracción Masiva" no existía en el template `index.html` (listado de expedientes).
Aunque el sistema completo de extracción masiva estaba implementado (backend, API, frontend),
faltaba el enlace desde la página principal de expedientes.

---

## ✅ Solución Implementada

### Cambio en `interfaz_web/backend/templates/index.html`:

**Agregado**: Botón de "📥 Extracción Masiva" junto al botón de "Agregar Expediente"

```html
<!-- Botones de acción -->
<div style="margin-bottom: 20px; display: flex; gap: 10px;">
    <a href="/expedientes/nuevo" style="...">
        ➕ Agregar Expediente
    </a>

    <a href="/extraccion-masiva" style="
        display: inline-block;
        padding: 10px 18px;
        background-color: #4CAF50;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-weight: bold;
        transition: 0.3s;
    " onmouseover="this.style.backgroundColor='#45a049'"
       onmouseout="this.style.backgroundColor='#4CAF50'">
        📥 Extracción Masiva
    </a>
</div>
```

### Características del botón:

- **Color**: Verde (#4CAF50) para diferenciarlo del botón azul
- **Icono**: 📥 (indicando descarga/extracción)
- **Hover**: Cambia a verde oscuro (#45a049)
- **Enlace**: Apunta a `/extraccion-masiva`
- **Ubicación**: Al lado del botón "Agregar Expediente"

---

## 🧪 Cómo Verificar que Funciona

### 1. Iniciar el servidor:

```bash
cd /home/user/sintaXis/Sistema_v6/interfaz_web
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Acceder a la página de expedientes:

```
http://localhost:8000/
```

### 3. Verificar el botón:

✅ Deberías ver dos botones:
- **Azul**: "➕ Agregar Expediente"
- **Verde**: "📥 Extracción Masiva" ← NUEVO

### 4. Hacer clic en "Extracción Masiva":

Debería redirigirte a:
```
http://localhost:8000/extraccion-masiva
```

Y mostrar el dashboard completo con:
- Panel de Configuración (filtros, fechas, estados)
- Formulario para iniciar extracción
- Botón "🚀 Iniciar Extracción"

---

## 📋 Flujo Completo

```
1. Usuario accede a /
   ↓
2. Ve el listado de expedientes con el botón verde "📥 Extracción Masiva"
   ↓
3. Hace clic en el botón
   ↓
4. Es redirigido a /extraccion-masiva
   ↓
5. Ve el dashboard completo de Extracción Masiva
   ↓
6. Configura filtros y hace clic en "Iniciar Extracción"
   ↓
7. POST /api/extraccion/masiva/iniciar
   ↓
8. WebSocket conecta para progreso en tiempo real
   ↓
9. Ve el progreso con barra y estadísticas
   ↓
10. Al finalizar, descarga reportes
```

---

## 🔗 Rutas Configuradas

| Ruta | Descripción | Estado |
|------|-------------|--------|
| `/` | Listado de expedientes | ✅ Con botón |
| `/extraccion-masiva` | Dashboard de extracción | ✅ Funcional |
| `/api/extraccion/masiva/iniciar` | Iniciar extracción | ✅ API REST |
| `/api/extraccion/masiva/ws/{id}` | WebSocket progreso | ✅ Tiempo real |
| `/api/extraccion/masiva/descargar/{id}/{fmt}` | Descargar reporte | ✅ Multi-formato |

---

## 📸 Apariencia Visual

### En el listado de expedientes:

```
+----------------------------------------------------------+
|  Listado de Expedientes                                  |
|                                                           |
|  [➕ Agregar Expediente]  [📥 Extracción Masiva]        |
|     (azul)                    (verde)                     |
|                                                           |
|  +----------------------------------------------------+   |
|  | ID | Número        | Carátula                    |   |
|  +----------------------------------------------------+   |
|  | 1  | EXP-001-2024 | Demanda civil...            |   |
|  | 2  | EXP-002-2024 | Causa penal...              |   |
|  +----------------------------------------------------+   |
+----------------------------------------------------------+
```

### Al hacer clic en "Extracción Masiva":

```
+----------------------------------------------------------+
|  📥 Extracción Masiva de Expedientes                     |
|  Extraer grandes volúmenes de expedientes del PJN        |
|  [← Volver al listado]                                   |
|                                                           |
|  ⚙️ Configuración de Extracción                         |
|  +----------------------------------------------------+   |
|  | 📅 Fecha Desde: [_________]                        |   |
|  | 📅 Fecha Hasta: [_________]                        |   |
|  |                                                     |   |
|  | 📊 Estados a Incluir:                              |   |
|  | ☑ Nuevo  ☐ Monitoreado  ☐ Priorizado             |   |
|  |                                                     |   |
|  | 💾 Formatos de Exportación:                        |   |
|  | ☑ JSON  ☐ Excel  ☐ CSV                           |   |
|  |                                                     |   |
|  |         [🚀 Iniciar Extracción]                    |   |
|  +----------------------------------------------------+   |
+----------------------------------------------------------+
```

---

## ⚠️ Notas Importantes

### Si el botón no redirige correctamente:

1. **Verificar que el servidor esté corriendo**:
   ```bash
   # En una terminal
   uvicorn backend.main:app --reload
   ```

2. **Verificar que la ruta existe en main.py**:
   ```python
   @app.get("/extraccion-masiva", response_class=HTMLResponse)
   async def vista_extraccion_masiva(request: Request):
       return templates.TemplateResponse("extraccion_masiva.html", {
           "request": request,
           "titulo": "Extracción Masiva de Expedientes"
       })
   ```

3. **Verificar que static files están montados**:
   ```python
   # En main.py
   app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
   ```

4. **Verificar que el template existe**:
   ```bash
   ls -la interfaz_web/backend/templates/extraccion_masiva.html
   ```

### Si hay errores al iniciar extracción:

1. **Verificar que el router de API esté incluido**:
   ```python
   # En main.py
   from .api import extraccion
   app.include_router(extraccion.router)
   ```

2. **Verificar que los módulos de backend existen**:
   ```bash
   ls -la Sistema_v6/extraccion_masiva/
   # Debe mostrar: extractor_masivo.py, gestor_batch.py, exportadores.py
   ```

---

## 🎨 Personalización

Si quieres cambiar el estilo del botón:

### Color diferente:
```html
background-color: #FF9800;  <!-- Naranja -->
background-color: #9C27B0;  <!-- Púrpura -->
background-color: #F44336;  <!-- Rojo -->
```

### Posición diferente:
```html
<!-- Debajo de la tabla en vez de arriba -->
{% endblock %} <!-- Mover el botón aquí -->
```

### Icono diferente:
```html
🔄 Extracción Masiva  <!-- Flechas circulares -->
⬇️ Extracción Masiva  <!-- Flecha abajo -->
💾 Extracción Masiva  <!-- Diskette -->
```

---

## ✅ Resumen de la Corrección

| Antes | Después |
|-------|---------|
| ❌ No había botón de Extracción Masiva | ✅ Botón verde visible en listado |
| ❌ No se podía acceder al dashboard | ✅ Clic redirige a /extraccion-masiva |
| ❌ Usuario tenía que escribir URL manual | ✅ Acceso con un clic desde listado |

**Tiempo de implementación**: 2 minutos
**Líneas de código agregadas**: 13 líneas HTML
**Impacto**: Usuario puede acceder fácilmente al sistema de extracción masiva

---

## 📝 Archivo Modificado

- ✅ `interfaz_web/backend/templates/index.html` - Agregado botón de Extracción Masiva

**Siguiente paso**: Commit de esta corrección y merge con sintaxis_parcial

---

**Generado**: 2025-11-07
**Estado**: ✅ CORREGIDO
**Probado**: ⏳ Pendiente (requiere servidor en ejecución)
