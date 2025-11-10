# Instalación de Dependencias - Extracción Masiva

## ⚠️ Error Común

Si ves el error:
```
Failed to resolve import "@radix-ui/react-checkbox"
Failed to resolve import "@radix-ui/react-select"
```

Es porque faltan las dependencias de Radix UI necesarias para los nuevos componentes.

## 📦 Dependencias Requeridas

La funcionalidad de **Extracción Masiva de Expedientes** utiliza componentes de shadcn/ui que dependen de Radix UI.

### Instalar Dependencias

Ejecuta el siguiente comando en el directorio `Sistema_v6/frontend/`:

```bash
npm install @radix-ui/react-checkbox @radix-ui/react-select
```

O si usas yarn:

```bash
yarn add @radix-ui/react-checkbox @radix-ui/react-select
```

O si usas pnpm:

```bash
pnpm add @radix-ui/react-checkbox @radix-ui/react-select
```

## 📋 Lista Completa de Dependencias

Si estás configurando el proyecto desde cero, asegúrate de tener todas estas dependencias en tu `package.json`:

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",
    "crypto-js": "^4.2.0",
    "lucide-react": "^0.303.0",
    "sonner": "^1.2.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0",

    "@radix-ui/react-checkbox": "^1.0.4",
    "@radix-ui/react-select": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/crypto-js": "^4.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "eslint": "^8.55.0",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0"
  }
}
```

## 🔧 Instalación Rápida

Si tienes un `package.json` existente, solo necesitas agregar estas dos dependencias:

```bash
npm install @radix-ui/react-checkbox@^1.0.4 @radix-ui/react-select@^2.0.0
```

## ✅ Verificar Instalación

Después de instalar las dependencias, reinicia el servidor de desarrollo:

```bash
# Detener el servidor (Ctrl+C)
# Reiniciar
npm run dev
```

El error debería desaparecer y la funcionalidad de Extracción Masiva debería funcionar correctamente.

## 📚 Componentes Agregados

Los siguientes componentes shadcn/ui fueron agregados y requieren estas dependencias:

1. **Checkbox** (`src/components/ui/checkbox.tsx`)
   - Depende de: `@radix-ui/react-checkbox`
   - Usado en: ExtraccionMasivaDialog para selección múltiple

2. **Select** (`src/components/ui/select.tsx`)
   - Depende de: `@radix-ui/react-select`
   - Usado en: Filtros de fuero en ExtraccionMasivaDialog

## 🐛 Troubleshooting

### Error persiste después de instalar

1. Limpia la caché de npm:
   ```bash
   npm cache clean --force
   ```

2. Elimina node_modules y reinstala:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Reinicia el servidor de desarrollo:
   ```bash
   npm run dev
   ```

### Versiones incompatibles

Si tienes problemas con versiones incompatibles, usa las versiones exactas especificadas:

```bash
npm install @radix-ui/react-checkbox@1.0.4 @radix-ui/react-select@2.0.0 --save-exact
```

### TypeScript Errors

Si ves errores de TypeScript relacionados con estos paquetes, asegúrate de tener los types instalados (ya vienen incluidos en los paquetes de Radix UI).

## 📝 Notas

- Estas dependencias son parte de shadcn/ui, una biblioteca de componentes que usa Radix UI como base
- Radix UI es una biblioteca de componentes primitivos accesibles y sin estilos
- Los componentes ya están estilizados con Tailwind CSS en este proyecto
- No necesitas configuración adicional, solo instalar las dependencias

## 🔗 Referencias

- [Radix UI Checkbox](https://www.radix-ui.com/docs/primitives/components/checkbox)
- [Radix UI Select](https://www.radix-ui.com/docs/primitives/components/select)
- [shadcn/ui Documentation](https://ui.shadcn.com/)

---

**Última actualización**: Noviembre 2025
**Relacionado con**: feat: Extracción Masiva de Expedientes (Commits: 1830c9d, ab280f9)
