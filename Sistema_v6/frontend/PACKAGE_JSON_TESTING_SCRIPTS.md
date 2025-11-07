# Scripts de Testing para package.json

Estos son los scripts que deben agregarse al `package.json` del frontend para ejecutar los tests.

## Scripts a Agregar

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:ci": "vitest run --coverage"
  }
}
```

## Dependencias a Instalar

### Dependencias de Desarrollo

```bash
npm install -D vitest @vitest/ui @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/coverage-v8
```

O usando el archivo package.json:

```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "jsdom": "^23.0.0"
  }
}
```

## Descripción de Scripts

### `npm test`
- Ejecuta Vitest en modo watch
- Los tests se re-ejecutan automáticamente cuando cambias archivos
- Ideal para desarrollo

### `npm run test:ui`
- Abre la interfaz gráfica de Vitest
- Permite ver tests visualmente
- Filtrar y ejecutar tests específicos
- Ver coverage en tiempo real

### `npm run test:coverage`
- Genera reporte de coverage
- Crea carpeta `coverage/` con reportes
- Muestra porcentajes en consola
- Genera `coverage/index.html` para ver en navegador

### `npm run test:ci`
- Ejecuta tests en modo CI (Continuous Integration)
- No entra en modo watch
- Genera coverage
- Falla si algún test falla
- Ideal para GitHub Actions, GitLab CI, etc.

## Uso

```bash
# Desarrollo diario
npm test

# Ver tests en UI
npm run test:ui

# Generar coverage antes de PR
npm run test:coverage

# CI/CD pipeline
npm run test:ci
```

## Configuración en CI/CD

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm install

      - name: Run tests
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
```

### GitLab CI

```yaml
test:
  stage: test
  image: node:20
  script:
    - npm install
    - npm run test:ci
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
```

## Notas

- Asegúrate de tener Node.js 18+ instalado
- Vitest requiere `type: "module"` en package.json (ya configurado con Vite)
- Los tests usan la misma configuración de Vite (aliases, etc.)
- jsdom simula el DOM del navegador para tests de componentes React
