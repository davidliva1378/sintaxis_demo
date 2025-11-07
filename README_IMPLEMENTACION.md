# 📘 GUÍA DE IMPLEMENTACIÓN - UNIFICACIÓN DE EXTRACCIÓN MASIVA

> **Solución 1**: Migración Progresiva con Backend Unificado
> **Rama**: `claude/setup-react-api-integration-011CUt29qifaHu9UR4UXnemG`
> **Status**: ✅ **LISTO PARA IMPLEMENTACIÓN**
> **Fecha**: 2025-11-07

---

## 🎯 OBJETIVO

Unificar los dos sistemas de extracción masiva existentes en un único sistema que combine:
- ✅ Arquitectura limpia del Sistema React (Hexagonal, DDD, CQRS)
- ✅ Funcionalidades avanzadas del Sistema HTML/JS (WebSocket, control, sesiones)
- ✅ UX moderna del frontend React
- ✅ Capacidades de exportación múltiple

---

## 📚 DOCUMENTACIÓN DISPONIBLE

Este repositorio contiene toda la documentación necesaria para implementar la solución:

### 1️⃣ **PLAN PRINCIPAL** 📋
**Archivo**: [`PLAN_UNIFICACION_EXTRACCION_MASIVA.md`](./PLAN_UNIFICACION_EXTRACCION_MASIVA.md)

**Contenido**:
- Verificación previa de recursos
- Arquitectura objetivo detallada
- Plan de implementación en 10 pasos
- Endpoints finales unificados
- Criterios de éxito
- Estimación de tiempo (7-10 horas)

**Cuándo usar**: Lee este documento primero para entender la solución completa.

---

### 2️⃣ **CHECKLIST DE IMPLEMENTACIÓN** ✅
**Archivo**: [`CHECKLIST_IMPLEMENTACION.md`](./CHECKLIST_IMPLEMENTACION.md)

**Contenido**:
- Verificación del entorno
- Checklist detallado de cada paso
- Tests para cada componente
- Criterios de éxito finales
- Troubleshooting común

**Cuándo usar**: Usa este documento durante la implementación para marcar progreso.

---

### 3️⃣ **REFERENCIA: ROUTER BACKEND** 🔧
**Archivo**: [`REFERENCIA_ROUTER_EXTRACCION_MASIVA.py`](./REFERENCIA_ROUTER_EXTRACCION_MASIVA.py)

**Contenido**:
- Código completo del router FastAPI
- Todos los endpoints implementados
- Schemas Pydantic
- Manejo de errores

**Cuándo usar**: Copia este código para crear el archivo `Sistema_v6/presentation/api/rest/routers/extraccion_masiva.py`.

---

### 4️⃣ **REFERENCIA: FRONTEND REACT** ⚛️
**Archivo**: [`REFERENCIA_FRONTEND_UPDATES.md`](./REFERENCIA_FRONTEND_UPDATES.md)

**Contenido**:
- Actualizaciones del Zustand store
- Código del componente React mejorado
- WebSocket client implementation
- Manejo de estado

**Cuándo usar**: Usa este documento para actualizar el frontend React.

---

## 🚀 INICIO RÁPIDO

### Para Agentes Autónomos:

```bash
# 1. Ir al repositorio
cd /home/user/sintaXis

# 2. Verificar rama actual
git branch --show-current

# 3. Leer el plan completo
cat PLAN_UNIFICACION_EXTRACCION_MASIVA.md

# 4. Seguir el checklist paso a paso
# Usar CHECKLIST_IMPLEMENTACION.md como guía

# 5. Usar archivos de referencia cuando sea necesario
# - REFERENCIA_ROUTER_EXTRACCION_MASIVA.py para backend
# - REFERENCIA_FRONTEND_UPDATES.md para frontend
```

### Para Desarrolladores Humanos:

1. **Lee primero**: `PLAN_UNIFICACION_EXTRACCION_MASIVA.md`
2. **Sigue el checklist**: `CHECKLIST_IMPLEMENTACION.md`
3. **Copia código de referencia** cuando sea necesario
4. **Testea cada paso** antes de continuar

---

## 📊 ESTRUCTURA DE LA IMPLEMENTACIÓN

```
┌─────────────────────────────────────────────────────────────┐
│                    PASO 1-4: BACKEND CORE                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     DTOs     │→ │   Servicio   │→ │  Use Case    │      │
│  │ Commands &   │  │   Gestor     │  │  Extracción  │      │
│  │  Responses   │  │   Sesiones   │  │    Masiva    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           ↓                                  │
│                  ┌──────────────────┐                        │
│                  │   DI Container   │                        │
│                  │    (Updated)     │                        │
│                  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  PASO 5-7: API & WEBSOCKET                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  WebSocket   │→ │    Router    │→ │   main.py    │      │
│  │   Handler    │  │  Extracción  │  │   (Updated)  │      │
│  │              │  │    Masiva    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  PASO 8-9: FRONTEND REACT                    │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │    Store     │→ │  Component   │                         │
│  │   (Updated)  │  │   (Updated)  │                         │
│  │   Zustand    │  │    Dialog    │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    PASO 10: TESTING & DEPLOY                 │
│             Tests → Deprecación → Commit → Push              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ VERIFICACIÓN ANTES DE COMENZAR

Ejecuta estos comandos para verificar que todo está listo:

```bash
# Verificar Python
python --version  # Debe ser 3.10+

# Verificar Node
node --version    # Debe ser 18+

# Verificar git
git status

# Verificar archivos base
ls -la Sistema_v6/extraccion_masiva/
ls -la Sistema_v6/application/use_cases/
ls -la Sistema_v6/frontend/src/stores/

# Verificar dependencias Python
cd Sistema_v6
python -c "import fastapi; print('✅ FastAPI instalado')"
python -c "from Sistema_v6.extraccion_masiva import ExtractorMasivo; print('✅ ExtractorMasivo disponible')"

# Verificar dependencias Node
cd Sistema_v6/frontend
npm list zustand axios
```

Si todos los comandos anteriores se ejecutan sin errores, estás listo para comenzar.

---

## 🎯 ENDPOINTS RESULTANTES

Al finalizar la implementación, tendrás estos endpoints:

### API REST v1 - Extracción Masiva:
```
POST   /api/v1/expedientes/extraer/masivo
       → Inicia extracción masiva, retorna session_id

GET    /api/v1/expedientes/extraer/{session_id}/progreso
       → Obtiene progreso actual

POST   /api/v1/expedientes/extraer/{session_id}/pausar
       → Pausa la extracción

POST   /api/v1/expedientes/extraer/{session_id}/reanudar
       → Reanuda la extracción

POST   /api/v1/expedientes/extraer/{session_id}/cancelar
       → Cancela la extracción

GET    /api/v1/expedientes/extraer/{session_id}/resumen
       → Obtiene resumen final

GET    /api/v1/expedientes/extraer/{session_id}/descargar/{formato}
       → Descarga reporte (json, excel, csv, html)

WS     /api/v1/expedientes/extraer/{session_id}/ws
       → WebSocket para progreso en tiempo real
```

---

## 📈 PROGRESO ESPERADO

| Paso | Descripción | Tiempo | Archivos Creados/Modificados |
|------|-------------|--------|------------------------------|
| 1 | DTOs | 30-45 min | 3 archivos |
| 2 | Servicio Sesiones | 45-60 min | 2 archivos |
| 3 | Use Case | 60-90 min | 2 archivos |
| 4 | DI Container | 15-30 min | 1 archivo |
| 5 | WebSocket Handler | 30-45 min | 2 archivos |
| 6 | Router API | 45-60 min | 1 archivo |
| 7 | Main.py | 15-30 min | 2 archivos |
| 8 | Frontend Store | 60-90 min | 1 archivo |
| 9 | Frontend Component | 45-60 min | 1 archivo |
| 10 | Testing & Deploy | 60-120 min | - |
| **TOTAL** | **Implementación Completa** | **7-10 horas** | **~15 archivos** |

---

## 🚨 PUNTOS CRÍTICOS

### ⚠️ NO OLVIDAR:

1. **Exportar PYTHONPATH** antes de ejecutar tests:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/home/user/sintaXis/Sistema_v6"
   ```

2. **Mantener compatibilidad**: El endpoint `/api/v1/expedientes/extraer` debe seguir funcionando

3. **WebSocket URL**: Ajustar según entorno (dev/prod)

4. **Cleanup**: Agregar `useEffect` cleanup para WebSocket en React

5. **Error Handling**: Todos los endpoints deben manejar errores gracefully

---

## 🔍 TESTING RÁPIDO

Después de cada paso, ejecutar:

```bash
# Test Backend (después de pasos 1-7)
cd Sistema_v6/presentation/api/rest
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# En otra terminal
curl http://localhost:8000/docs  # Ver Swagger

# Test Frontend (después de pasos 8-9)
cd Sistema_v6/frontend
npm run dev

# Abrir http://localhost:3000
```

---

## 📞 SOPORTE

### Si encuentras problemas:

1. **Consulta la sección Troubleshooting** en [`CHECKLIST_IMPLEMENTACION.md`](./CHECKLIST_IMPLEMENTACION.md)

2. **Verifica logs**:
   ```bash
   # Backend
   tail -f /var/log/pjn-api.log

   # Frontend
   # Ver consola del navegador (F12)
   ```

3. **Verifica estado de servicios**:
   ```bash
   # Backend corriendo?
   curl http://localhost:8000/api/v1/health

   # Frontend corriendo?
   curl http://localhost:3000
   ```

---

## 🎓 ARQUITECTURA FINAL

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ExtraccionMasivaDialog.tsx                        │     │
│  │  ┌──────────────────────────────────────────────┐  │     │
│  │  │  • Iniciar/Pausar/Reanudar/Cancelar          │  │     │
│  │  │  • Progreso en tiempo real (WebSocket)       │  │     │
│  │  │  • Estadísticas (velocidad, tiempo estimado) │  │     │
│  │  │  • Descarga de reportes (JSON, Excel, CSV)   │  │     │
│  │  └──────────────────────────────────────────────┘  │     │
│  │                        ↕                            │     │
│  │  expedientesStore.ts (Zustand)                     │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER (FastAPI)                │
│  ┌────────────────────────────────────────────────────┐     │
│  │  extraccion_masiva.py (Router)                     │     │
│  │  • POST /masivo                                    │     │
│  │  • GET /{id}/progreso                              │     │
│  │  • POST /{id}/pausar/reanudar/cancelar            │     │
│  │  • GET /{id}/resumen                               │     │
│  │  • GET /{id}/descargar/{formato}                   │     │
│  │  • WS /{id}/ws                                     │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  extraccion_ws.py (WebSocket Handler)              │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER (Use Cases)               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ExtraccionMasivaUseCase                           │     │
│  │  • iniciar_extraccion()                            │     │
│  │  • ejecutar_extraccion_background()                │     │
│  │  • pausar_extraccion()                             │     │
│  │  • reanudar_extraccion()                           │     │
│  │  • cancelar_extraccion()                           │     │
│  │  • crear_callbacks()                               │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER (Services)              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  GestorSesiones                                    │     │
│  │  • crear_sesion()                                  │     │
│  │  • actualizar_progreso()                           │     │
│  │  • finalizar_sesion()                              │     │
│  │  • WebSocket broadcast                             │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  ExtractorMasivo (Existente)                       │     │
│  │  • ejecutar_extraccion_completa()                  │     │
│  │  • Callbacks para progreso                         │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 ENTREGABLES FINALES

Al completar la implementación, habrás creado:

✅ **Backend**:
- [ ] 3 DTOs nuevos (Commands & Responses)
- [ ] 1 Servicio (GestorSesiones)
- [ ] 1 Use Case (ExtraccionMasivaUseCase)
- [ ] 1 WebSocket Handler
- [ ] 1 Router completo con 8 endpoints
- [ ] Actualizaciones en DI Container y main.py

✅ **Frontend**:
- [ ] Store actualizado con 9 acciones nuevas
- [ ] Componente mejorado con controles completos
- [ ] WebSocket client integrado
- [ ] Visualización de progreso en tiempo real

✅ **Testing & Documentación**:
- [ ] Tests de endpoints
- [ ] Tests de WebSocket
- [ ] Tests de UI
- [ ] Documentación actualizada
- [ ] README actualizado

✅ **Deprecación**:
- [ ] Banner en sistema legacy
- [ ] Redirección configurada
- [ ] Documentación de migración

---

## 🏁 SIGUIENTE PASO

**Para comenzar la implementación**:

```bash
# 1. Abrir el checklist
cat CHECKLIST_IMPLEMENTACION.md

# 2. Comenzar con el Paso 1
# Seguir las instrucciones detalladas en:
cat PLAN_UNIFICACION_EXTRACCION_MASIVA.md | grep -A 50 "PASO 1"

# 3. Marcar progreso en el checklist
```

---

**¡Éxito en la implementación!** 🚀

---

**Documentos relacionados**:
- [Plan Principal](./PLAN_UNIFICACION_EXTRACCION_MASIVA.md)
- [Checklist](./CHECKLIST_IMPLEMENTACION.md)
- [Referencia Router](./REFERENCIA_ROUTER_EXTRACCION_MASIVA.py)
- [Referencia Frontend](./REFERENCIA_FRONTEND_UPDATES.md)

**Última actualización**: 2025-11-07
**Status**: ✅ LISTO PARA IMPLEMENTACIÓN
