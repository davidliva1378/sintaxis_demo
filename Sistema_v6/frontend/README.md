# Sistema PJN v6 - Frontend

Frontend del Sistema de Gestión del Portal Judicial Nacional (Argentina) v6.

## Stack Tecnológico

- **Framework**: React 18.3+ con TypeScript
- **Build Tool**: Vite 5+
- **Styling**: Tailwind CSS 3+ con shadcn/ui
- **State Management**: Zustand 4+
- **Data Fetching**: React Query 5+ (TanStack Query)
- **Routing**: React Router v6
- **Forms**: React Hook Form 7+ + Zod
- **HTTP Client**: Axios
- **Encryption**: CryptoJS

## Requisitos Previos

- Node.js 18+ y npm
- Backend de Sistema PJN v6 corriendo en http://localhost:8000

## Instalación

```bash
# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env
```

## Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# El frontend estará disponible en http://localhost:5173
```

## Build

```bash
# Compilar para producción
npm run build

# Preview del build de producción
npm run preview
```

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/        # Componentes React
│   │   ├── ui/           # Componentes base (shadcn/ui)
│   │   ├── layout/       # Componentes de layout
│   │   └── common/       # Componentes compartidos
│   ├── pages/            # Páginas/Vistas
│   │   ├── auth/         # Login, Register
│   │   ├── dashboard/    # Dashboard
│   │   ├── expedientes/  # Gestión de expedientes
│   │   ├── workspaces/   # Gestión de workspaces
│   │   └── settings/     # Configuración
│   ├── stores/           # Zustand stores (estado global)
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilidades
│   │   ├── api.ts        # Cliente Axios
│   │   ├── utils.ts      # Funciones auxiliares
│   │   └── encryption.ts # Encriptación cliente
│   ├── types/            # TypeScript types
│   ├── App.tsx           # Componente principal
│   └── main.tsx          # Entry point
├── public/               # Archivos estáticos
├── index.html            # HTML template
├── package.json          # Dependencias
├── tsconfig.json         # Configuración TypeScript
├── vite.config.ts        # Configuración Vite
└── tailwind.config.js    # Configuración Tailwind

```

## Credenciales de Prueba

```
Usuario: admin
Contraseña: admin123456
```

## Variables de Entorno

- `VITE_API_URL`: URL del backend (default: http://localhost:8000)
- `VITE_ENCRYPTION_KEY`: Clave para encriptación cliente

## API Backend

El frontend consume la API REST del backend en:
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Registro
- `GET /api/v1/auth/me` - Info usuario actual
- `PUT /api/v1/auth/credentials` - Actualizar credenciales PJN
- `GET /api/v1/auth/credentials` - Obtener credenciales PJN
- `DELETE /api/v1/auth/credentials` - Eliminar credenciales PJN

Ver documentación completa en http://localhost:8000/docs

## Características Implementadas

- ✅ Autenticación JWT
- ✅ Login y Registro
- ✅ Protected Routes
- ✅ Dark Mode
- ✅ Dashboard básico
- ✅ Gestión de estado con Zustand
- ✅ Cliente HTTP con interceptores
- ⏳ Módulo de Expedientes (próximamente)
- ⏳ Módulo de Monitoreo (próximamente)
- ⏳ Módulo de Workspaces (próximamente)

## Notas de Desarrollo

- El frontend usa proxy de Vite para redirigir `/api/*` al backend
- Las credenciales PJN se encriptan en el cliente antes de enviarse al backend
- El token JWT se almacena en localStorage
- El estado de autenticación persiste entre sesiones
