# Instrucciones de Instalación y Ejecución - Frontend

## ✅ Estado del Proyecto

El proyecto frontend está **completamente configurado y listo** para ejecutarse. Solo necesitas instalar Node.js y las dependencias.

## 📋 Requisitos Previos

### 1. Instalar Node.js

**Descargar Node.js 20+ LTS** (recomendado):
- Visita: https://nodejs.org/
- Descarga la versión LTS (Long Term Support)
- Ejecuta el instalador y sigue las instrucciones
- Asegúrate de marcar la opción "Add to PATH"

**Verificar instalación**:
```bash
node --version
npm --version
```

Deberías ver algo como:
```
v20.x.x
10.x.x
```

## 🚀 Instalación y Ejecución

### Paso 1: Instalar Dependencias

Abre una terminal en el directorio `Sistema_v6/frontend` y ejecuta:

```bash
npm install
```

Esto instalará todas las dependencias necesarias (~300MB). Puede tomar 2-3 minutos.

### Paso 2: Verificar Backend

Asegúrate de que el **backend está corriendo**:

```bash
cd ../
python -m uvicorn presentation.api.rest.main:app --host 127.0.0.1 --port 8000
```

El backend debe estar disponible en: http://localhost:8000

### Paso 3: Iniciar Frontend

En otra terminal, desde el directorio `frontend`:

```bash
npm run dev
```

El frontend estará disponible en: **http://localhost:5173**

## 🔐 Credenciales de Prueba

```
Usuario: admin
Contraseña: admin123456
```

## 📝 Comandos Útiles

### Desarrollo
```bash
npm run dev        # Iniciar servidor de desarrollo (con hot reload)
```

### Producción
```bash
npm run build      # Compilar para producción (genera carpeta dist/)
npm run preview    # Preview del build de producción
```

### Linting
```bash
npm run lint       # Ejecutar linter de TypeScript
```

## 🎨 Características Implementadas

- ✅ **Autenticación JWT** - Login y registro funcional
- ✅ **Protected Routes** - Rutas protegidas con redirección
- ✅ **Dark Mode** - Toggle entre modo claro y oscuro
- ✅ **Responsive Design** - Diseño adaptativo (desktop-first)
- ✅ **Dashboard** - Vista de bienvenida con información del usuario
- ✅ **State Management** - Zustand para estado global
- ✅ **API Client** - Axios con interceptores para JWT
- ✅ **Form Validation** - React Hook Form + Zod

## 🗂️ Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Componentes base (Button, Input, Card)
│   │   └── layout/          # ProtectedRoute
│   ├── pages/
│   │   ├── auth/            # LoginPage, RegisterPage
│   │   └── dashboard/       # DashboardPage
│   ├── stores/
│   │   ├── authStore.ts     # Estado de autenticación (Zustand)
│   │   └── themeStore.ts    # Estado del tema (Zustand)
│   ├── lib/
│   │   ├── api.ts           # Cliente Axios con interceptores
│   │   ├── encryption.ts    # Encriptación cliente (CryptoJS)
│   │   └── utils.ts         # Utilidades (cn para Tailwind)
│   ├── types/
│   │   └── auth.ts          # TypeScript types para auth
│   ├── App.tsx              # Router principal
│   ├── main.tsx             # Entry point + React Query setup
│   └── index.css            # Estilos globales + Tailwind
├── public/                  # Archivos estáticos
├── .env                     # Variables de entorno
├── package.json             # Dependencias
├── vite.config.ts           # Configuración Vite (proxy a backend)
├── tailwind.config.js       # Configuración Tailwind + shadcn/ui
└── tsconfig.json            # Configuración TypeScript
```

## 🔄 Flujo de Autenticación

1. **Login**:
   - Usuario ingresa username y password
   - Frontend envía POST a `/api/v1/auth/login`
   - Backend devuelve JWT token
   - Token se guarda en `localStorage`
   - Usuario es redirigido al Dashboard

2. **Requests Autenticados**:
   - Axios interceptor agrega header `Authorization: Bearer <token>`
   - Backend valida el token
   - Si token es inválido (401), usuario es redirigido a login

3. **Logout**:
   - Token se elimina de `localStorage`
   - Usuario es redirigido a login

## 🔧 Configuración

### Variables de Entorno (`.env`)

```bash
# URL del backend
VITE_API_URL=http://localhost:8000

# Clave para encriptación cliente
VITE_ENCRYPTION_KEY=sistema-pjn-v6-client-encryption-key
```

### Proxy de Vite

El frontend usa proxy para redirigir requests a la API:
```
/api/* → http://localhost:8000/api/*
```

Esto evita problemas de CORS durante desarrollo.

## ⚠️ Problemas Comunes

### 1. "Cannot find module 'X'"

**Solución**: Reinstalar dependencias
```bash
rm -rf node_modules package-lock.json
npm install
```

### 2. "Port 5173 is already in use"

**Solución**: Cambiar puerto en `vite.config.ts`:
```typescript
server: {
  port: 5174,  // Cambiar a otro puerto
  ...
}
```

### 3. "Network Error" al hacer login

**Solución**: Verificar que el backend está corriendo en http://localhost:8000

```bash
curl http://localhost:8000/api/v1/health
```

### 4. Error de CORS

**Solución**: El backend ya tiene CORS configurado para `http://localhost:5173`. Si cambias el puerto, actualiza `infrastructure/config/settings.py`:

```python
cors_origins: list[str] = [
    "http://localhost:5173",
    "http://localhost:5174",  # Agregar nuevo puerto
]
```

## 📚 Próximas Funcionalidades

Las siguientes funcionalidades están **documentadas en el plan** pero aún no implementadas:

- ⏳ **Módulo Expedientes** - Listar, filtrar, extraer expedientes
- ⏳ **Módulo Monitoreo** - Monitorear cambios en expedientes
- ⏳ **Módulo Workspaces** - Gestión de espacios de trabajo
- ⏳ **Configuración de Usuario** - Gestión de credenciales PJN
- ⏳ **Notificaciones** - Toast notifications para feedback
- ⏳ **Mejoras de UX** - Loading states, skeleton loaders, etc.

Ver plan completo en: `docs/WEB_UI_PLAN.md`

## 💡 Tips de Desarrollo

1. **Hot Reload**: Los cambios en el código se reflejan automáticamente en el navegador
2. **React DevTools**: Instala la extensión para debugging
3. **Tailwind IntelliSense**: Instala la extensión de VSCode para autocompletado de clases
4. **TypeScript**: El proyecto usa TypeScript para type safety
5. **ESLint**: El linter ayuda a mantener código consistente

## 📞 Soporte

Si encuentras problemas:
1. Verifica que Node.js está instalado correctamente
2. Verifica que el backend está corriendo
3. Revisa la consola del navegador para errores
4. Revisa la terminal para errores de compilación
5. Consulta `docs/WEB_UI_PLAN.md` para más detalles

---

**Última actualización**: 2025-11-05
**Versión**: 6.0.0
