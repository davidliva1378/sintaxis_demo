# ✅ CHECKLIST DE IMPLEMENTACIÓN
## Unificación de Extracción Masiva - Solución 1

**Rama**: `claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG`
**Fecha de creación**: 2025-11-07

---

## 📋 ANTES DE COMENZAR

### Verificar Entorno:
- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] Git configurado
- [ ] Rama `sintaxis_parcial` actualizada
- [ ] Dependencias de Python instaladas (`pip install -r requirements.txt`)
- [ ] Dependencias de Node instaladas (`npm install` en frontend/)

### Verificar Archivos Base Existentes:
- [ ] `Sistema_v6/extraccion_masiva/extractor_masivo.py` existe
- [ ] `Sistema_v6/extraccion_masiva/gestor_batch.py` existe
- [ ] `Sistema_v6/application/use_cases/` existe
- [ ] `Sistema_v6/infrastructure/di_container.py` existe
- [ ] `Sistema_v6/presentation/api/rest/main.py` existe
- [ ] `Sistema_v6/frontend/src/stores/expedientesStore.ts` existe

---

## 🔧 IMPLEMENTACIÓN PASO A PASO

### PASO 1: Crear DTOs de Extracción Masiva ✅/❌

- [ ] Crear archivo: `Sistema_v6/application/dtos/extraccion_masiva_commands.py`
  - [ ] Clase `IniciarExtraccionMasivaCommand` implementada
  - [ ] Clase `ControlExtraccionCommand` implementada

- [ ] Crear archivo: `Sistema_v6/application/dtos/extraccion_masiva_responses.py`
  - [ ] Clase `IniciarExtraccionMasivaResponse` implementada
  - [ ] Clase `ProgresoExtraccionResponse` implementada
  - [ ] Clase `ResumenExtraccionResponse` implementada

- [ ] Actualizar: `Sistema_v6/application/dtos/__init__.py`
  - [ ] Imports agregados
  - [ ] `__all__` actualizado

- [ ] **Test**: Importar DTOs sin errores
  ```bash
  python -c "from application.dtos import IniciarExtraccionMasivaCommand; print('✅ DTOs OK')"
  ```

---

### PASO 2: Crear Servicio de Gestión de Sesiones ✅/❌

- [ ] Crear directorio: `Sistema_v6/infrastructure/services/`
- [ ] Crear archivo: `Sistema_v6/infrastructure/services/__init__.py`
- [ ] Crear archivo: `Sistema_v6/infrastructure/services/gestor_sesiones_service.py`
  - [ ] Clase `GestorSesiones` implementada
  - [ ] Método `crear_sesion` implementado
  - [ ] Método `actualizar_progreso` implementado
  - [ ] Método `obtener_sesion` implementado
  - [ ] Método `finalizar_sesion` implementado
  - [ ] Método `marcar_error` implementado
  - [ ] Métodos de WebSocket implementados
  - [ ] Función `get_gestor_sesiones` implementada

- [ ] **Test**: Importar servicio sin errores
  ```bash
  python -c "from infrastructure.services.gestor_sesiones_service import get_gestor_sesiones; print('✅ Gestor OK')"
  ```

---

### PASO 3: Crear Use Case de Extracción Masiva ✅/❌

- [ ] Crear archivo: `Sistema_v6/application/use_cases/extraccion_masiva_use_case.py`
  - [ ] Clase `ExtraccionMasivaUseCase` implementada
  - [ ] Método `iniciar_extraccion` implementado
  - [ ] Método `crear_callbacks` implementado
  - [ ] Método `ejecutar_extraccion_background` implementado
  - [ ] Método `pausar_extraccion` implementado
  - [ ] Método `reanudar_extraccion` implementado
  - [ ] Método `cancelar_extraccion` implementado

- [ ] Actualizar: `Sistema_v6/application/use_cases/__init__.py`
  - [ ] Import agregado
  - [ ] `__all__` actualizado

- [ ] **Test**: Importar use case sin errores
  ```bash
  python -c "from application.use_cases import ExtraccionMasivaUseCase; print('✅ Use Case OK')"
  ```

---

### PASO 4: Actualizar DI Container ✅/❌

- [ ] Actualizar: `Sistema_v6/infrastructure/di_container.py`
  - [ ] Import `ExtraccionMasivaUseCase` agregado
  - [ ] Import `get_gestor_sesiones` agregado
  - [ ] Método `extraccion_masiva_use_case()` agregado a clase `DIContainer`

- [ ] **Test**: Crear instancia del use case
  ```bash
  python -c "from infrastructure.di_container import get_container; c = get_container(); uc = c.extraccion_masiva_use_case(); print('✅ DI Container OK')"
  ```

---

### PASO 5: Crear WebSocket Handler ✅/❌

- [ ] Crear directorio: `Sistema_v6/presentation/api/rest/websocket/`
- [ ] Crear archivo: `Sistema_v6/presentation/api/rest/websocket/__init__.py`
- [ ] Crear archivo: `Sistema_v6/presentation/api/rest/websocket/extraccion_ws.py`
  - [ ] Función `websocket_progreso` implementada
  - [ ] Manejo de conexión/desconexión implementado
  - [ ] Ping/pong implementado
  - [ ] Broadcast de progreso implementado

- [ ] **Test**: Importar handler sin errores
  ```bash
  python -c "from presentation.api.rest.websocket.extraccion_ws import websocket_progreso; print('✅ WebSocket OK')"
  ```

---

### PASO 6: Crear Router de Extracción Masiva ✅/❌

- [ ] Crear archivo: `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`
  - [ ] Schemas Pydantic definidos
  - [ ] Endpoint `POST /masivo` implementado
  - [ ] Endpoint `GET /{session_id}/progreso` implementado
  - [ ] Endpoint `POST /{session_id}/pausar` implementado
  - [ ] Endpoint `POST /{session_id}/reanudar` implementado
  - [ ] Endpoint `POST /{session_id}/cancelar` implementado
  - [ ] Endpoint `GET /{session_id}/resumen` implementado
  - [ ] Endpoint `GET /{session_id}/descargar/{formato}` implementado
  - [ ] Endpoint `WS /{session_id}/ws` implementado

- [ ] **Test**: Importar router sin errores
  ```bash
  python -c "from presentation.api.rest.routers import extraccion_masiva; print('✅ Router OK')"
  ```

---

### PASO 7: Actualizar main.py de la API ✅/❌

- [ ] Actualizar: `Sistema_v6/presentation/api/rest/routers/__init__.py`
  - [ ] Import `extraccion_masiva` agregado

- [ ] Actualizar: `Sistema_v6/presentation/api/rest/main.py`
  - [ ] Import del router agregado
  - [ ] Router incluido con `app.include_router()`
  - [ ] Docstring actualizado con nuevos endpoints

- [ ] **Test**: Iniciar servidor sin errores
  ```bash
  cd Sistema_v6/presentation/api/rest
  timeout 5 uvicorn main:app --host 0.0.0.0 --port 8000 || echo "✅ Server starts OK"
  ```

- [ ] **Test**: Verificar endpoints en Swagger
  - [ ] Abrir http://localhost:8000/docs
  - [ ] Verificar sección "extraccion_masiva" existe
  - [ ] Verificar todos los endpoints listados

---

### PASO 8: Actualizar Frontend React Store ✅/❌

- [ ] Actualizar: `Sistema_v6/frontend/src/stores/expedientesStore.ts`
  - [ ] Interface `ConfigExtraccionMasiva` agregada
  - [ ] Interface `ResumenExtraccion` agregada
  - [ ] Estado `extraccionMasiva` agregado
  - [ ] Acción `iniciarExtraccionMasivaAvanzada` implementada
  - [ ] Acción `conectarWebSocket` implementada
  - [ ] Acción `desconectarWebSocket` implementada
  - [ ] Acción `pausarExtraccion` implementada
  - [ ] Acción `reanudarExtraccion` implementada
  - [ ] Acción `cancelarExtraccion` implementada
  - [ ] Acción `obtenerProgreso` implementada
  - [ ] Acción `obtenerResumen` implementada
  - [ ] Acción `descargarReporte` implementada

- [ ] **Test**: Compilar TypeScript sin errores
  ```bash
  cd Sistema_v6/frontend
  npm run type-check || npm run build
  ```

---

### PASO 9: Actualizar Componente React ✅/❌

- [ ] Actualizar: `Sistema_v6/frontend/src/components/expedientes/ExtraccionMasivaDialog.tsx`
  - [ ] Hooks del store agregados
  - [ ] Controles de pausar/reanudar/cancelar agregados
  - [ ] Visualización de progreso mejorada
  - [ ] Estadísticas en tiempo real agregadas
  - [ ] Botones de descarga agregados
  - [ ] useEffect para cleanup de WebSocket agregado

- [ ] **Test**: Compilar componente sin errores
  ```bash
  cd Sistema_v6/frontend
  npm run dev
  ```

- [ ] **Test Visual**: Verificar en navegador
  - [ ] Abrir http://localhost:3000
  - [ ] Verificar diálogo de extracción masiva
  - [ ] Verificar controles visibles

---

### PASO 10: Testing y Deprecación ✅/❌

#### Testing Backend:
- [ ] Test: Iniciar extracción masiva
  ```bash
  curl -X POST http://localhost:8000/api/v1/expedientes/extraer/masivo \
    -H "Content-Type: application/json" \
    -d '{"usuario":"test","contrasena":"test","headless":true}'
  ```

- [ ] Test: Obtener progreso (usar session_id del paso anterior)
  ```bash
  curl http://localhost:8000/api/v1/expedientes/extraer/{session_id}/progreso
  ```

- [ ] Test: Pausar extracción
  ```bash
  curl -X POST http://localhost:8000/api/v1/expedientes/extraer/{session_id}/pausar
  ```

- [ ] Test: Reanudar extracción
  ```bash
  curl -X POST http://localhost:8000/api/v1/expedientes/extraer/{session_id}/reanudar
  ```

- [ ] Test: Cancelar extracción
  ```bash
  curl -X POST http://localhost:8000/api/v1/expedientes/extraer/{session_id}/cancelar
  ```

#### Testing WebSocket:
- [ ] Test: Conectar WebSocket desde navegador
  ```javascript
  const ws = new WebSocket('ws://localhost:8000/api/v1/expedientes/extraer/{session_id}/ws')
  ws.onmessage = (e) => console.log(JSON.parse(e.data))
  ```

#### Testing Frontend:
- [ ] Test: Iniciar extracción desde UI
- [ ] Test: Pausar extracción desde UI
- [ ] Test: Reanudar extracción desde UI
- [ ] Test: Cancelar extracción desde UI
- [ ] Test: Ver progreso en tiempo real
- [ ] Test: Descargar reportes en diferentes formatos

#### Deprecación del Sistema Legacy:
- [ ] Agregar banner de deprecación en `interfaz_web/backend/templates/`
- [ ] Agregar redirección a nueva interfaz
- [ ] Actualizar README.md del proyecto
- [ ] Actualizar documentación de la API

---

## 📝 COMMIT Y PUSH

- [ ] Verificar que todos los archivos están agregados
  ```bash
  git status
  ```

- [ ] Crear commit descriptivo
  ```bash
  git add .
  git commit -m "feat: Unificar extracción masiva con arquitectura limpia

  - Agregar DTOs de extracción masiva
  - Crear use case de extracción masiva
  - Implementar gestión de sesiones
  - Agregar endpoints REST avanzados
  - Implementar WebSocket para progreso en tiempo real
  - Actualizar frontend React con controles completos
  - Deprecar sistema legacy HTML/JS

  BREAKING CHANGE: Sistema legacy en interfaz_web/ marcado como deprecated"
  ```

- [ ] Push a la rama remota
  ```bash
  git push -u origin claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG
  ```

---

## 🎯 CRITERIOS DE ÉXITO FINALES

- [ ] ✅ Backend inicia sin errores
- [ ] ✅ Frontend compila sin errores
- [ ] ✅ Swagger muestra todos los nuevos endpoints
- [ ] ✅ WebSocket conecta correctamente
- [ ] ✅ Extracción masiva se puede iniciar desde UI
- [ ] ✅ Controles de pausar/reanudar/cancelar funcionan
- [ ] ✅ Progreso se actualiza en tiempo real
- [ ] ✅ Reportes se pueden descargar en todos los formatos
- [ ] ✅ Sistema legacy tiene banner de deprecación
- [ ] ✅ Tests pasan correctamente
- [ ] ✅ Documentación actualizada
- [ ] ✅ Commit creado y pusheado

---

## 📊 MÉTRICAS DE ÉXITO

Al finalizar, verificar:

1. **Código**:
   - ✅ 0 errores de compilación
   - ✅ 0 warnings críticos
   - ✅ Cobertura de código > 80% (opcional)

2. **Funcionalidad**:
   - ✅ Todos los endpoints responden correctamente
   - ✅ WebSocket mantiene conexión estable
   - ✅ Progreso se actualiza sin lag
   - ✅ Reportes se generan correctamente

3. **Arquitectura**:
   - ✅ Separación de capas mantenida
   - ✅ Inyección de dependencias funciona
   - ✅ Use cases desacoplados
   - ✅ DTOs bien definidos

4. **UX**:
   - ✅ Interfaz responsiva
   - ✅ Feedback visual claro
   - ✅ Errores manejados gracefully
   - ✅ Tiempos de respuesta aceptables

---

## 🚨 TROUBLESHOOTING

### Problema: "Module not found"
**Solución**: Verificar que estés en el directorio correcto y que `PYTHONPATH` incluya `Sistema_v6/`
```bash
export PYTHONPATH="${PYTHONPATH}:/home/user/sintaXis/Sistema_v6"
```

### Problema: "WebSocket connection failed"
**Solución**: Verificar que el backend esté corriendo y que la URL sea correcta
```bash
# Verificar backend
curl http://localhost:8000/api/v1/health

# Verificar WebSocket con wscat
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/expedientes/extraer/test/ws
```

### Problema: "CORS error"
**Solución**: Verificar configuración de CORS en `main.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Agregar origen del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problema: "Session not found"
**Solución**: El gestor de sesiones es en memoria, se pierde al reiniciar el servidor
- Implementar persistencia en base de datos (mejora futura)
- Por ahora, reiniciar extracción después de reiniciar servidor

---

## 📚 RECURSOS ADICIONALES

- [Plan completo](./PLAN_UNIFICACION_EXTRACCION_MASIVA.md)
- [Referencia Router](./REFERENCIA_ROUTER_EXTRACCION_MASIVA.py)
- [Referencia Frontend](./REFERENCIA_FRONTEND_UPDATES.md)
- [Documentación FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Documentación Zustand](https://github.com/pmndrs/zustand)

---

**Última actualización**: 2025-11-07
**Status**: ✅ LISTO PARA IMPLEMENTACIÓN
**Tiempo estimado**: 7-10 horas
