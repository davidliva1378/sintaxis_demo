# 📘 Guías de Uso - Sistema_v5

**Complemento de DOCUMENTACION_COMPLETA.md**

---

## Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Guías por Caso de Uso](#guías-por-caso-de-uso)
3. [Patrones de Diseño Recomendados](#patrones-de-diseño-recomendados)
4. [Ejemplos Completos](#ejemplos-completos)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)

---

## Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd Sistema_v5

# Instalar dependencias
pip install playwright pandas
playwright install chromium

# Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env con tus credenciales
```

### Primer Script

```python
import asyncio
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. Login (implementar según tu flujo)
        await page.goto("https://url-del-pjn")
        # ... login ...

        # 2. Navegar al listado
        await page.goto("https://url-del-listado")

        # 3. Extraer expedientes
        expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
            page,
            max_paginas=5,
        )

        # 4. Procesar resultados
        print(f"Extraídos: {len(expedientes)}")
        for exp in expedientes:
            print(f"{exp.numero}: {exp.caratula}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Guías por Caso de Uso

### Caso 1: Monitoreo Diario de Notificaciones

**Objetivo:** Extraer notificaciones nuevas cada día y guardarlas.

```python
import asyncio
import json
from datetime import date
from pathlib import Path
from playwright.async_api import async_playwright
from pjn.scraping.entradas import extraer_entradas_datos
from pjn.models import Entrada

async def monitoreo_diario():
    """Monitorea notificaciones diarias."""

    # Rutas
    historial_path = Path("datos/historial_notificaciones.json")
    historial_path.parent.mkdir(exist_ok=True)

    # Cargar historial existente
    historial_existente = []
    if historial_path.exists():
        with open(historial_path, "r", encoding="utf-8") as f:
            historial_dicts = json.load(f)
            historial_existente = [
                Entrada.from_dict(d) for d in historial_dicts
            ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Login y navegar a notificaciones
        # ... (implementar según tu flujo)

        # Extraer solo nuevas (deduplicando contra historial)
        nuevas = await extraer_entradas_datos(
            page,
            incluir_tipos=("N",),              # Solo notificaciones
            historial_existente=historial_existente,
        )

        print(f"📬 Nuevas notificaciones: {len(nuevas)}")

        # Procesar nuevas
        for entrada in nuevas:
            print(f"  - {entrada.fecha}: {entrada.numero}")
            # Aquí puedes: enviar email, crear tarea, etc.

        # Actualizar historial
        todas = historial_existente + nuevas
        with open(historial_path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in todas], f, indent=2, ensure_ascii=False)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(monitoreo_diario())
```

### Caso 2: Extracción Completa de Expediente

**Objetivo:** Extraer toda la información de un expediente específico.

```python
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_datos_expediente
from pjn.scraping.actuaciones import (
    extraer_actuaciones_datos,
    descargar_archivos_actuaciones_modelos,
)
from pjn.persistence.actuaciones import guardar_actuaciones_json

async def extraer_expediente_completo(numero_expediente: str):
    """Extrae expediente completo con actuaciones y archivos."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. Buscar y abrir expediente
        # ... (implementar búsqueda)

        # 2. Extraer datos básicos
        datos = await extraer_datos_expediente(page)
        if not datos:
            print("❌ No se pudo extraer datos del expediente")
            return

        print(f"📋 Expediente: {datos['numero']}")
        print(f"   Carátula: {datos['caratula']}")

        # 3. Navegar a actuaciones
        # ... (hacer clic en pestaña de actuaciones)

        # 4. Extraer actuaciones
        archivo = await extraer_actuaciones_datos(page, datos)
        print(f"📄 Actuaciones: {len(archivo.actuaciones)}")

        # 5. Guardar JSON
        carpeta = Path(f"datos/{numero_expediente}")
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_json = guardar_actuaciones_json(archivo, carpeta)
        print(f"💾 Guardado en: {ruta_json}")

        # 6. Descargar archivos adjuntos
        con_archivos = [
            act for act in archivo.actuaciones
            if act.archivos
        ]

        if con_archivos:
            print(f"📎 Descargando archivos de {len(con_archivos)} actuaciones...")
            actualizadas = await descargar_archivos_actuaciones_modelos(
                page,
                con_archivos,
                str(carpeta),
            )

            total_archivos = sum(len(a.archivos) for a in actualizadas)
            print(f"✅ Descargados {total_archivos} archivos")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(extraer_expediente_completo("EXP-123/2024"))
```

### Caso 3: Búsqueda Masiva con Filtros

**Objetivo:** Extraer expedientes con filtros específicos.

```python
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

async def busqueda_masiva():
    """Búsqueda de expedientes con múltiples filtros."""

    # Fecha de corte: últimos 30 días
    fecha_corte = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Estrategia con timeouts largos para estabilidad
    strategy = PrimeFacesPaginationStrategy(
        timeout_ms=20_000,
        max_wait_content_ms=25_000,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Login y búsqueda
        # ... (implementar)

        # Extraer con filtros
        print(f"🔍 Buscando expedientes desde {fecha_corte}...")

        expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
            page,
            max_paginas=100,                    # Hasta 100 páginas
            fecha_corte=fecha_corte,            # Últimos 30 días
            orden="fecha",                      # Ordenar por fecha desc
            omitir_duplicados=True,             # No duplicados
            detener_en_duplicado=True,          # Detener en duplicado
            tiempo_maximo_segundos=600,         # Máximo 10 minutos
            pagination_strategy=strategy,       # Estrategia custom
        )

        print(f"✅ Extracción completada: {motivo}")
        print(f"📊 Total expedientes: {len(expedientes)}")
        print(f"📈 Metadata: {metadata}")

        # Filtrar por situación
        en_tramite = [
            e for e in expedientes
            if "TRÁMITE" in e.situacion.upper()
        ]
        print(f"📌 En trámite: {len(en_tramite)}")

        # Agrupar por dependencia
        por_dependencia = {}
        for exp in expedientes:
            por_dependencia.setdefault(exp.dependencia, []).append(exp)

        print("\n📍 Por dependencia:")
        for dep, exps in sorted(por_dependencia.items()):
            print(f"  {dep}: {len(exps)} expedientes")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(busqueda_masiva())
```

### Caso 4: Pipeline Completo con Procesamiento

**Objetivo:** Pipeline que extrae, procesa y genera reportes.

```python
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

async def pipeline_completo():
    """Pipeline de extracción y análisis."""

    # 1. Extracción
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # ... login ...

        print("⏳ Extrayendo expedientes...")
        expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
            page,
            max_paginas=20,
        )
        await browser.close()

    print(f"✅ Extraídos: {len(expedientes)} expedientes")

    # 2. Conversión a DataFrame
    df = pd.DataFrame([e.to_dict() for e in expedientes])

    # 3. Procesamiento
    print("\n📊 Análisis:")

    # Por situación
    print("\nPor situación:")
    print(df['situacion'].value_counts())

    # Por dependencia
    print("\nPor dependencia:")
    print(df['dependencia'].value_counts().head(10))

    # Distribución temporal
    df['fecha_dt'] = pd.to_datetime(df['ultima_actuacion'])
    df['mes'] = df['fecha_dt'].dt.to_period('M')
    print("\nPor mes:")
    print(df['mes'].value_counts().sort_index())

    # 4. Exportar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("reportes")
    output_dir.mkdir(exist_ok=True)

    # Excel
    excel_path = output_dir / f"expedientes_{timestamp}.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"\n💾 Excel: {excel_path}")

    # CSV
    csv_path = output_dir / f"expedientes_{timestamp}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"💾 CSV: {csv_path}")

    # Resumen JSON
    resumen = {
        "fecha_extraccion": timestamp,
        "total_expedientes": len(expedientes),
        "motivo_finalizacion": motivo,
        "metadata": metadata,
        "estadisticas": {
            "por_situacion": df['situacion'].value_counts().to_dict(),
            "por_dependencia": df['dependencia'].value_counts().head(10).to_dict(),
        }
    }

    import json
    resumen_path = output_dir / f"resumen_{timestamp}.json"
    with open(resumen_path, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"💾 Resumen: {resumen_path}")

if __name__ == "__main__":
    asyncio.run(pipeline_completo())
```

---

## Patrones de Diseño Recomendados

### Patrón 1: Funciones Puras + Persistencia Separada

**✅ RECOMENDADO:**

```python
from pjn.scraping.actuaciones import extraer_actuaciones_datos
from pjn.persistence.actuaciones import guardar_actuaciones_json

# 1. Extraer (puro, sin I/O)
archivo = await extraer_actuaciones_datos(page, expediente)

# 2. Procesar en memoria
for act in archivo.actuaciones:
    # Hacer análisis, transformaciones, etc.
    pass

# 3. Persistir solo si es necesario
if necesito_guardar:
    guardar_actuaciones_json(archivo, "datos/")
```

**❌ EVITAR (Legacy):**

```python
# Función deprecated que mezcla extracción y persistencia
await extraer_actuaciones_completas(page, expediente, "datos/")
# No permite procesar antes de guardar
```

### Patrón 2: Manejo de Excepciones Específico

**✅ RECOMENDADO:**

```python
from pjn.exceptions import TimeoutExtraccion, ActuacionesNoDisponibles, ExtraccionError

try:
    archivo = await extraer_actuaciones_datos(page, expediente)

except TimeoutExtraccion:
    # Manejo específico: reintentar con más timeout
    logger.warning("Timeout - reintentando...")
    # ... reintentar ...

except ActuacionesNoDisponibles:
    # OK - este expediente simplemente no tiene actuaciones
    logger.info("Sin actuaciones - continuando")
    archivo = None

except ExtraccionError as e:
    # Error inesperado - loggear y propagar
    logger.exception("Error crítico")
    raise
```

### Patrón 3: Configuración Inyectable

**✅ RECOMENDADO:**

```python
from pjn.config import Config, ScrapingConfig, set_config

def configurar_para_testing():
    """Configura el sistema para testing."""
    test_config = Config(
        scraping=ScrapingConfig(
            timeout_default=5_000,
            max_paginas_expedientes=2,
        )
    )
    set_config(test_config)

def configurar_para_produccion():
    """Configura para producción."""
    prod_config = Config(
        scraping=ScrapingConfig(
            timeout_default=20_000,
            max_paginas_expedientes=200,
        )
    )
    set_config(prod_config)

# En tu código
if ENVIRONMENT == "test":
    configurar_para_testing()
else:
    configurar_para_produccion()
```

### Patrón 4: Estrategias de Paginación Reutilizables

```python
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

# Crear estrategias reutilizables
STRATEGY_RAPIDA = PrimeFacesPaginationStrategy(
    timeout_ms=5_000,
    max_wait_content_ms=8_000,
)

STRATEGY_ESTABLE = PrimeFacesPaginationStrategy(
    timeout_ms=20_000,
    max_wait_content_ms=30_000,
)

# Usar según contexto
if red_rapida:
    strategy = STRATEGY_RAPIDA
else:
    strategy = STRATEGY_ESTABLE

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,
)
```

### Patrón 5: Composición de Funciones

```python
# Componer funciones puras para workflows complejos

async def workflow_expediente(page, numero):
    """Workflow completo de extracción de expediente."""

    # 1. Buscar y abrir
    await buscar_expediente(page, numero)

    # 2. Extraer datos básicos
    datos = await extraer_datos_expediente(page)

    # 3. Extraer actuaciones
    archivo = await extraer_actuaciones_datos(page, datos)

    # 4. Filtrar actuaciones con archivos
    con_archivos = [
        act for act in archivo.actuaciones
        if act.archivos
    ]

    # 5. Descargar archivos si hay
    if con_archivos:
        archivo_actualizado = await descargar_archivos_actuaciones_modelos(
            page,
            con_archivos,
            f"datos/{numero}",
        )
    else:
        archivo_actualizado = archivo

    # 6. Retornar resultado completo
    return {
        "datos": datos,
        "archivo": archivo_actualizado,
    }
```

---

## Testing

### Testing con Estrategias Mock

```python
import pytest
from pjn.scraping.pagination import PaginationStrategy
from pjn.scraping.expedientes import extraer_expedientes_completos

class MockPaginationStrategy:
    """Estrategia mock para testing."""

    def __init__(self, max_pages=2):
        self.current_page = 0
        self.max_pages = max_pages

    async def navegar_siguiente(self, page, tbody_locator, fingerprint):
        self.current_page += 1
        if self.current_page >= self.max_pages:
            return False, "fin_listado"
        return True, None

@pytest.mark.asyncio
async def test_extraccion_con_limite():
    """Test que verifica límite de páginas."""

    mock_strategy = MockPaginationStrategy(max_pages=3)

    expedientes, motivo, metadata = await extraer_expedientes_completos(
        page,
        pagination_strategy=mock_strategy,
    )

    assert motivo == "fin_listado"
    assert mock_strategy.current_page == 3
```

### Testing con Configuración

```python
import pytest
from pjn.config import Config, ScrapingConfig, set_config, get_config

@pytest.fixture
def test_config():
    """Fixture de configuración para tests."""
    original = get_config()

    test_cfg = Config(
        scraping=ScrapingConfig(
            timeout_default=5_000,
            max_paginas_expedientes=2,
        )
    )
    set_config(test_cfg)

    yield test_cfg

    # Restaurar configuración original
    set_config(original)

def test_con_configuracion(test_config):
    """Test que usa configuración de test."""
    config = get_config()
    assert config.scraping.timeout_default == 5_000
```

---

## Troubleshooting

### Problema 1: Timeouts Frecuentes

**Síntoma:** `TimeoutExtraccion` constante

**Soluciones:**
```python
# Opción 1: Aumentar timeouts globales
from pjn.config import Config, ScrapingConfig, set_config

config = Config(
    scraping=ScrapingConfig(
        timeout_default=30_000,  # 30 segundos
    )
)
set_config(config)

# Opción 2: Estrategia de paginación más lenta
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

strategy = PrimeFacesPaginationStrategy(
    timeout_ms=25_000,
    max_wait_content_ms=35_000,
    poll_interval_ms=1000,  # Polling más lento
)

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,
)
```

### Problema 2: Duplicados No Detectados

**Síntoma:** Expedientes/entradas duplicadas

**Solución:**
```python
# Asegurar que deduplicación esté activa
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    omitir_duplicados=True,          # ✅ Activar
    detener_en_duplicado=True,       # ✅ Detener en duplicado
)

# Para entradas, usar historial
entradas = await extraer_entradas_datos(
    page,
    duplicados=False,                 # ✅ Deduplicar
    historial_existente=historial,   # ✅ Proporcionar historial
)
```

### Problema 3: Memoria Alta en Extracciones Largas

**Síntoma:** Uso de RAM crece continuamente

**Solución:**
```python
# Procesar en lotes
async def extraer_por_lotes(page, max_total=1000):
    """Extrae en lotes para liberar memoria."""

    todos = []
    paginas_por_lote = 20
    max_paginas_total = 100

    for inicio in range(0, max_paginas_total, paginas_por_lote):
        print(f"Lote {inicio // paginas_por_lote + 1}...")

        expedientes, motivo, metadata = await extraer_expedientes_completos(
            page,
            max_paginas=paginas_por_lote,
        )

        # Procesar lote
        todos.extend(expedientes)

        # Guardar intermedio
        guardar_intermedio(expedientes, f"lote_{inicio}")

        # Liberar memoria
        expedientes.clear()

        if motivo != "limite_paginas":
            break

    return todos
```

### Problema 4: Selectores No Encontrados

**Síntoma:** Elementos no encontrados

**Solución:**
```python
from pjn.selectores import SEL_EXPEDIENTES

# Debug: imprimir selector
print(f"Buscando: {SEL_EXPEDIENTES.TABLA_RESULTADOS}")

# Esperar con timeout largo
try:
    await page.wait_for_selector(
        SEL_EXPEDIENTES.TABLA_RESULTADOS,
        state="visible",
        timeout=30_000,
    )
except TimeoutError:
    # Tomar screenshot para debug
    await page.screenshot(path="error_selector.png")
    # Guardar HTML
    html = await page.content()
    with open("error_page.html", "w") as f:
        f.write(html)
    raise
```

### Problema 5: Archivos No Se Descargan

**Síntoma:** Descarga de archivos falla

**Solución:**
```python
from pathlib import Path

# Verificar carpeta de destino
carpeta = Path("datos/expediente-123")
carpeta.mkdir(parents=True, exist_ok=True)

# Verificar permisos
print(f"Carpeta: {carpeta.absolute()}")
print(f"Existe: {carpeta.exists()}")
print(f"Escribible: {carpeta.is_dir() and os.access(carpeta, os.W_OK)}")

# Descargar con manejo de errores
try:
    actualizadas = await descargar_archivos_actuaciones_modelos(
        page,
        actuaciones,
        str(carpeta),
    )
except Exception as e:
    logger.exception("Error descargando archivos")
    # Continuar sin archivos
    actualizadas = actuaciones
```

---

## Mejores Prácticas

### 1. Siempre Usar Type Hints

```python
from typing import List, Optional
from pjn.models import Expediente Resumen

async def procesar_expedientes(
    expedientes: List[ExpedienteResumen],
    filtro: Optional[str] = None
) -> List[ExpedienteResumen]:
    """Procesa expedientes con type hints."""
    # IDE autocompletará correctamente
    return [e for e in expedientes if not filtro or filtro in e.caratula]
```

### 2. Logging Estructurado

```python
from pjn.utils.logging import get_logger

logger = get_logger(__name__)

async def extraer_con_logging(page):
    logger.info("Iniciando extracción", extra={
        "url": page.url,
        "timestamp": datetime.now().isoformat(),
    })

    try:
        resultado = await extraer_expedientes_completos(page)
        logger.info("Extracción exitosa", extra={
            "total": len(resultado[0]),
            "motivo": resultado[1],
        })
        return resultado

    except Exception as e:
        logger.exception("Error en extracción", extra={
            "url": page.url,
        })
        raise
```

### 3. Cleanup de Recursos

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def browser_context():
    """Context manager para browser."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        try:
            yield browser
        finally:
            await browser.close()

# Uso
async def main():
    async with browser_context() as browser:
        page = await browser.new_page()
        # Hacer scraping
        # Browser se cierra automáticamente
```

### 4. Validación de Datos

```python
def validar_expediente(exp: ExpedienteResumen) -> bool:
    """Valida que un expediente tenga datos completos."""
    if not exp.numero or not exp.caratula:
        logger.warning(f"Expediente inválido: {exp}")
        return False

    try:
        # Validar formato de fecha
        datetime.strptime(exp.ultima_actuacion, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Fecha inválida: {exp.ultima_actuacion}")
        return False

    return True

# Usar en pipeline
expedientes_validos = [e for e in expedientes if validar_expediente(e)]
```

---

**Fin de DOCUMENTACION_GUIAS.md**
