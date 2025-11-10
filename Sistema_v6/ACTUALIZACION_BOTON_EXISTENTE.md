# 🔄 ACTUALIZACIÓN DEL PLAN - Botón Extracción Masiva Existente

**Fecha**: 2025-11-07
**Actualización**: El botón "Extracción Masiva" ya existe en el frontend

---

## ✅ INFORMACIÓN ACTUALIZADA

**Confirmado**: Ya existe un botón "Extracción Masiva" en el frontend de expedientes.

---

## 🎯 LO QUE NECESITA EL BOTÓN PARA FUNCIONAR

### 1. Verificar Configuración Actual del Botón

**Ubicación esperada**: `interfaz_web/backend/templates/index.html`

**Verificar**:
```html
<!-- Botón Extracción Masiva (existente) -->
<a href="/extraccion-masiva" class="btn btn-success">
    📥 Extracción Masiva
</a>
```

**Si la ruta es diferente**, anotar cuál es para ajustar el endpoint en FastAPI.

---

### 2. Crear Endpoint en FastAPI

**Archivo**: `interfaz_web/backend/main.py`

**Agregar**:
```python
@app.get("/extraccion-masiva", response_class=HTMLResponse)
async def vista_extraccion_masiva(request: Request):
    """Vista del dashboard de extracción masiva."""
    return templates.TemplateResponse("extraccion_masiva.html", {
        "request": request,
        "titulo": "Extracción Masiva de Expedientes"
    })
```

---

### 3. Crear Template HTML

**Archivo**: `interfaz_web/backend/templates/extraccion_masiva.html`

Este es el dashboard completo que se mostrará cuando se haga clic en el botón.

**Contenido**: Ver `SEGUIMIENTO_AGENTES.md` sección 3.2 para el HTML completo.

---

### 4. Implementar API REST

**Archivo**: `interfaz_web/backend/api/extraccion.py`

Los endpoints que necesita el dashboard:
- `POST /api/extraccion/masiva/iniciar` - Iniciar extracción
- `GET /api/extraccion/masiva/progreso/{id}` - Ver progreso
- `POST /api/extraccion/masiva/cancelar/{id}` - Cancelar
- `WS /api/extraccion/masiva/ws/{id}` - WebSocket para progreso

---

### 5. Crear JavaScript para WebSocket

**Archivo**: `interfaz_web/static/js/extraccion_masiva.js`

Conecta el frontend con la API REST y WebSocket.

---

## 📋 PLAN ACTUALIZADO DE IMPLEMENTACIÓN

### ✅ YA COMPLETADO
- [x] Botón "Extracción Masiva" en frontend

### ⏳ PENDIENTE DE IMPLEMENTAR

#### Día 1: Backend (4-5 horas)
1. Crear `extraccion_masiva/extractor_masivo.py` (2h)
2. Crear `extraccion_masiva/gestor_batch.py` (1.5h)
3. Crear `extraccion_masiva/exportadores.py` (1h)

#### Día 2: API REST (3-4 horas)
4. Crear `interfaz_web/backend/api/extraccion.py` (2h)
5. Implementar WebSocket en `api/extraccion.py` (1.5h)
6. Actualizar `interfaz_web/backend/main.py`:
   - Incluir router de API
   - Agregar endpoint `/extraccion-masiva` (0.5h)

#### Día 3: Frontend (2-3 horas)
7. Crear `templates/extraccion_masiva.html` (1h)
8. Crear `static/js/extraccion_masiva.js` (1h)
9. Crear `static/css/extraccion_masiva.css` (0.5h)
10. ~~Agregar botón a index.html~~ **✅ YA EXISTE**

#### Día 4: Testing (2-3 horas)
11. Tests unitarios (1.5h)
12. Verificación E2E (1h)

**Total**: 11-15 horas (se ahorró 0.5h del botón)

---

## 🔧 PRIMER PASO INMEDIATO

### Verificar la Ruta del Botón Existente

**Ejecutar**:
```bash
cd /home/user/sintaXis/Sistema_v6
grep -r "extraccion.*masiva\|Extraccion.*[Mm]asiva" interfaz_web/backend/templates/ -i -n
```

**Buscar**:
- ¿A qué ruta apunta el botón? (ej: `/extraccion-masiva`)
- ¿Qué clase CSS tiene?
- ¿Está en `index.html`, `admin_dashboard.html` u otro?

### Ajustar el Endpoint

Una vez identificada la ruta del botón, crear el endpoint correspondiente en `main.py`:

```python
# Si el botón apunta a /extraccion-masiva
@app.get("/extraccion-masiva", response_class=HTMLResponse)
async def vista_extraccion_masiva(request: Request):
    return templates.TemplateResponse("extraccion_masiva.html", {
        "request": request,
        "titulo": "Extracción Masiva"
    })

# Si el botón apunta a otra ruta, ajustar aquí
```

---

## 📊 FLUJO DE USUARIO ACTUALIZADO

```
1. Usuario ve listado de expedientes
   └─> index.html

2. Usuario hace clic en "📥 Extracción Masiva" (YA EXISTE)
   └─> Navega a /extraccion-masiva

3. FastAPI responde con template
   └─> extraccion_masiva.html

4. Usuario configura filtros y hace clic "Iniciar"
   └─> POST /api/extraccion/masiva/iniciar

5. JavaScript conecta WebSocket
   └─> WS /api/extraccion/masiva/ws/{session_id}

6. Backend ejecuta extracción
   └─> ExtractorMasivo.ejecutar_extraccion_completa()

7. WebSocket envía progreso en tiempo real
   └─> JavaScript actualiza UI

8. Extracción finaliza
   └─> Usuario descarga reporte
```

---

## ✅ VENTAJAS DE QUE EL BOTÓN YA EXISTA

1. **Ahorro de tiempo**: -0.5 horas de implementación
2. **UX consistente**: El botón ya sigue el diseño del sistema
3. **Enfoque en funcionalidad**: Nos concentramos en el backend y API

---

## 🚀 PRÓXIMO PASO INMEDIATO

**Acción**: Comenzar con la implementación del backend (Día 1):

```bash
cd /home/user/sintaXis/Sistema_v6/extraccion_masiva
touch extractor_masivo.py
```

Luego copiar el código del **SEGUIMIENTO_AGENTES.md** sección "PASO 1" en `extractor_masivo.py`.

---

## 📝 NOTAS IMPORTANTES

1. **No modificar el botón existente** a menos que sea necesario
2. **Averiguar la ruta exacta** a la que apunta el botón
3. **Mantener consistencia** con el estilo existente del botón
4. **Priorizar funcionalidad** sobre diseño (el botón ya está bien)

---

**Estado**: Plan actualizado y listo
**Tiempo ahorrado**: 0.5 horas
**Tiempo total estimado**: 11-15 horas (antes 12-16h)
