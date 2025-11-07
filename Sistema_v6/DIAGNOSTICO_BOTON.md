# 🔍 Diagnóstico: Botón de Extracción Masiva en sintaxis_parcial

**Fecha**: 2025-11-07
**Rama**: sintaxis_parcial
**Estado**: ✅ Todos los archivos presentes

---

## ✅ Verificación Realizada

### Archivos Presentes:

1. **Template HTML** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/templates/index.html
   ```
   - Líneas 22-33: Botón "📥 Extracción Masiva" presente
   - Apunta a: `/extraccion-masiva`

2. **Backend main.py** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/main.py
   ```
   - Línea 18: Router de API incluido
   - Líneas 42-48: Ruta `/extraccion-masiva` configurada
   - Líneas 21-23: Static files montados

3. **Template de Dashboard** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/templates/extraccion_masiva.html
   ```
   - 10,537 bytes (completo)

4. **API REST** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/api/extraccion.py
   ```
   - 22,541 bytes (completo)
   - 7 endpoints + WebSocket

5. **Frontend CSS** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/static/css/extraccion_masiva.css
   ```
   - 11,215 bytes

6. **Frontend JavaScript** ✅
   ```
   /home/user/sintaXis/Sistema_v6/interfaz_web/backend/static/js/extraccion_masiva.js
   ```
   - 18,677 bytes

7. **Backend Extracción Masiva** ✅
   ```
   /home/user/sintaXis/Sistema_v6/extraccion_masiva/
   ```
   - extractor_masivo.py (14,871 bytes)
   - gestor_batch.py (12,165 bytes)
   - exportadores.py (13,681 bytes)

---

## 🐛 Posibles Causas del Problema

### 1. Servidor No Actualizado

**Síntoma**: El botón aparece pero no funciona correctamente

**Causa**: El servidor FastAPI está corriendo con código antiguo

**Solución**:
```bash
# 1. Detener servidor actual (Ctrl+C)
# 2. Asegurarte de estar en la rama correcta
git checkout sintaxis_parcial

# 3. Reiniciar servidor
cd /home/user/sintaXis/Sistema_v6/interfaz_web
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Caché del Navegador

**Síntoma**: El botón aparece pero al hacer clic no funciona

**Causa**: El navegador tiene caché de la versión anterior

**Solución**:
```
1. Abrir DevTools (F12)
2. Clic derecho en el botón de refresh
3. Seleccionar "Empty Cache and Hard Reload"

O simplemente:
- Chrome/Edge: Ctrl + Shift + R
- Firefox: Ctrl + F5
```

### 3. Error al Importar Módulos

**Síntoma**: Error 500 o página en blanco

**Causa**: Falta alguna dependencia de Python

**Solución**:
```bash
# Ver logs del servidor
# Si hay error como "ModuleNotFoundError: No module named 'fastapi'"

pip install fastapi uvicorn[standard] websockets pydantic
```

### 4. Puerto Ocupado

**Síntoma**: Servidor no inicia o dice "Address already in use"

**Solución**:
```bash
# Encontrar proceso en puerto 8000
lsof -i :8000

# Matar proceso
kill -9 <PID>

# O usar otro puerto
uvicorn backend.main:app --reload --port 8001
```

---

## 🧪 Proceso de Verificación Paso a Paso

### Paso 1: Verificar Rama

```bash
cd /home/user/sintaXis
git branch --show-current
```

**Resultado esperado**: `sintaxis_parcial`

Si no:
```bash
git checkout sintaxis_parcial
```

### Paso 2: Verificar Archivos

```bash
# Verificar que index.html tiene el botón
grep -n "Extracción Masiva" Sistema_v6/interfaz_web/backend/templates/index.html
```

**Resultado esperado**:
```
32:        📥 Extracción Masiva
```

### Paso 3: Iniciar Servidor

```bash
cd Sistema_v6/interfaz_web

# Opción 1: Con reload (desarrollo)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Sin reload (más estable)
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Resultado esperado**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Paso 4: Verificar en Navegador

1. **Abrir**: `http://localhost:8000/`

2. **Verificar**: Debes ver DOS botones:
   - Azul: "➕ Agregar Expediente"
   - Verde: "📥 Extracción Masiva"

3. **Hacer clic** en "📥 Extracción Masiva"

4. **Resultado esperado**: Redirige a `http://localhost:8000/extraccion-masiva`

5. **Verificar**: Debes ver el dashboard completo con:
   - Título: "📥 Extracción Masiva de Expedientes"
   - Panel de Configuración con filtros
   - Botón "🚀 Iniciar Extracción"

### Paso 5: Verificar Console del Navegador

1. Abrir DevTools (F12)
2. Ir a pestaña "Console"
3. Buscar mensajes de error

**Resultado esperado**:
```
Sistema de Extracción Masiva inicializado
```

Si hay errores de JavaScript:
- Verificar que `/static/js/extraccion_masiva.js` carga correctamente
- Verificar en Network tab que los archivos CSS/JS se descarguen

### Paso 6: Verificar Network

1. En DevTools, ir a pestaña "Network"
2. Hacer clic en el botón "Extracción Masiva"
3. Verificar que carguen:
   - ✅ `extraccion_masiva.html` (200 OK)
   - ✅ `extraccion_masiva.css` (200 OK)
   - ✅ `extraccion_masiva.js` (200 OK)

---

## 🔧 Soluciones Rápidas

### Si el botón NO aparece:

```bash
# 1. Verificar template
cat Sistema_v6/interfaz_web/backend/templates/index.html | grep -A 10 "Extracción Masiva"

# 2. Si no aparece, el archivo está desactualizado
git checkout sintaxis_parcial -- Sistema_v6/interfaz_web/backend/templates/index.html

# 3. Reiniciar servidor
```

### Si el botón aparece pero da error 404:

```bash
# Verificar que main.py tiene la ruta
grep -n "extraccion-masiva" Sistema_v6/interfaz_web/backend/main.py

# Debe mostrar:
# 42:@app.get("/extraccion-masiva", response_class=HTMLResponse)

# Si no aparece, actualizar main.py
git checkout sintaxis_parcial -- Sistema_v6/interfaz_web/backend/main.py
```

### Si redirige pero la página está en blanco:

```bash
# Verificar que el template existe
ls -lh Sistema_v6/interfaz_web/backend/templates/extraccion_masiva.html

# Si no existe
git checkout sintaxis_parcial -- Sistema_v6/interfaz_web/backend/templates/extraccion_masiva.html
git checkout sintaxis_parcial -- Sistema_v6/interfaz_web/backend/static/
```

### Si hay errores de API:

```bash
# Verificar módulos de backend
ls -lh Sistema_v6/extraccion_masiva/

# Debe mostrar:
# extractor_masivo.py
# gestor_batch.py
# exportadores.py

# Si faltan
git checkout sintaxis_parcial -- Sistema_v6/extraccion_masiva/
git checkout sintaxis_parcial -- Sistema_v6/interfaz_web/backend/api/
```

---

## 📊 Checklist de Verificación

```
[ ] Estoy en la rama sintaxis_parcial
[ ] El archivo index.html tiene el botón verde
[ ] El servidor está corriendo (puerto 8000)
[ ] Accedo a http://localhost:8000/
[ ] Veo el botón "📥 Extracción Masiva"
[ ] Al hacer clic, redirige a /extraccion-masiva
[ ] Veo el dashboard completo
[ ] No hay errores en la consola del navegador
[ ] Los archivos CSS/JS cargan correctamente
```

---

## 🚀 Comando Todo-en-Uno

Si quieres resetear todo y empezar limpio:

```bash
# Ir al directorio raíz
cd /home/user/sintaXis

# Asegurarse de estar en la rama correcta
git checkout sintaxis_parcial

# Actualizar archivos
git pull origin sintaxis_parcial

# Ir al directorio de la web
cd Sistema_v6/interfaz_web

# Iniciar servidor
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Luego en el navegador:
1. Ir a `http://localhost:8000/`
2. Hacer Hard Refresh (Ctrl+Shift+R)
3. Hacer clic en "📥 Extracción Masiva"

---

## 🐛 Debugging Avanzado

Si nada de lo anterior funciona, revisar logs del servidor:

```bash
# Iniciar servidor con más verbose
uvicorn backend.main:app --reload --log-level debug
```

Buscar en los logs:
- `INFO:     Application startup complete.` ✅
- Errores de importación ❌
- `FileNotFoundError` ❌

Si ves errores, copiar y pegar el error completo para diagnóstico.

---

## ✅ Confirmación de Funcionamiento

Cuando todo funcione, deberías ver:

1. **En `http://localhost:8000/`**:
   ```
   [➕ Agregar Expediente] [📥 Extracción Masiva]
   ```

2. **Al hacer clic en el botón verde**:
   - URL cambia a: `http://localhost:8000/extraccion-masiva`
   - Título: "📥 Extracción Masiva de Expedientes"
   - Panel de configuración visible
   - Botón "🚀 Iniciar Extracción" visible

3. **En la consola del navegador (F12)**:
   ```
   Sistema de Extracción Masiva inicializado
   ```

---

**Generado**: 2025-11-07
**Rama**: sintaxis_parcial
**Estado**: ✅ Todos los archivos verificados y presentes
