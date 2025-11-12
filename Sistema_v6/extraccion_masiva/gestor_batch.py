"""
Gestor Batch - Procesa lotes de expedientes seleccionados.

Permite procesar SOLO los expedientes elegidos por el usuario
después del filtrado y selección.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from uuid import uuid4

from playwright.async_api import Page, async_playwright, Browser, BrowserContext

from .models import (
    EstadoExpediente,
    ConfigExtraccionMasiva,
    ResumenExtraccion,
    SesionExtraccion,
)

# Importar funciones de procesamiento de v5/v6
from Sistema_v6.pjn.scraping.expedientes import (
    buscar_expediente_por_numero,
    extraer_datos_expediente
)
from Sistema_v6.pjn.scraping import descomponer_numero_expediente
from Sistema_v6.pjn.services.actuaciones import procesar_actuaciones_expediente
from Sistema_v6.pjn.persistence.actuaciones import cargar_actuaciones_json

# Importar tipos de aplicación para type hints
try:
    from application.ports import IExpedienteRepository
except ImportError:
    IExpedienteRepository = None  # type: ignore


class GestorBatch:
    """
    Gestor de procesamiento por lotes de expedientes seleccionados.

    Flujo:
    1. Recibe lista de números de expediente a procesar
    2. Navega al PJN y procesa SOLO esos expedientes
    3. Actualiza estados en tiempo real
    4. Guarda solo los procesados exitosamente
    """

    def __init__(
        self,
        config: Optional[ConfigExtraccionMasiva] = None,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        expediente_repository: Optional["IExpedienteRepository"] = None,
    ):
        """
        Args:
            config: Configuración de extracción
            on_progress: Callback para reportar progreso (actual, total, mensaje)
            expediente_repository: Repositorio para guardar expedientes procesados
        """
        self.config = config or ConfigExtraccionMasiva()
        self.on_progress = on_progress
        self.expediente_repository = expediente_repository
        self._estados: Dict[str, EstadoExpediente] = {}
        self._errores: List[Dict] = []

    async def procesar_seleccionados(
        self,
        numeros_expedientes: List[str],
        username: str,
        password: str,
    ) -> ResumenExtraccion:
        """
        Procesa solo los expedientes seleccionados.

        Args:
            numeros_expedientes: Lista de números de expediente a procesar
            username: Usuario PJN
            password: Contraseña PJN

        Returns:
            ResumenExtraccion con estadísticas del procesamiento
        """
        inicio = datetime.now()
        total = len(numeros_expedientes)
        exitosos = 0
        errores = 0
        omitidos = 0
        total_archivos_descargados = 0  # Acumulador de archivos descargados

        # Inicializar estados
        for numero in numeros_expedientes:
            self._estados[numero] = EstadoExpediente.PENDIENTE

        self._reportar_progreso(0, total, "Iniciando navegador...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.config.headless
                )
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.config.timeout_pagina)

                # Login en PJN
                self._reportar_progreso(0, total, "Autenticando en PJN...")
                await self._login_pjn(page, username, password)

                # Procesar cada expediente
                for idx, numero in enumerate(numeros_expedientes, 1):
                    self._reportar_progreso(
                        idx - 1, total, f"Procesando {numero}..."
                    )

                    try:
                        self._estados[numero] = EstadoExpediente.PROCESANDO

                        # TODO: Implementar procesamiento real del expediente
                        # Por ahora, placeholder que simula procesamiento
                        resultado = await self._procesar_expediente(
                            page, numero, context, browser
                        )

                        if resultado["success"]:
                            self._estados[numero] = EstadoExpediente.PROCESADO
                            exitosos += 1
                            # Acumular archivos descargados de este expediente
                            if "data" in resultado and "archivos_descargados" in resultado["data"]:
                                total_archivos_descargados += resultado["data"]["archivos_descargados"]
                        else:
                            self._estados[numero] = EstadoExpediente.ERROR
                            errores += 1
                            self._errores.append({
                                "numero": numero,
                                "error": resultado.get("error", "Error desconocido"),
                            })

                    except Exception as e:
                        self._estados[numero] = EstadoExpediente.ERROR
                        errores += 1
                        self._errores.append({
                            "numero": numero,
                            "error": str(e),
                        })

                    # Verificar umbral de errores
                    if errores >= self.config.umbral_errores:
                        self._reportar_progreso(
                            idx, total,
                            f"Detenido: umbral de errores alcanzado ({errores})"
                        )
                        # Marcar pendientes como omitidos
                        for num in numeros_expedientes[idx:]:
                            if self._estados.get(num) == EstadoExpediente.PENDIENTE:
                                self._estados[num] = EstadoExpediente.OMITIDO
                                omitidos += 1
                        break

                await browser.close()

        except Exception as e:
            # Error global - marcar todos los pendientes como omitidos
            for numero, estado in self._estados.items():
                if estado == EstadoExpediente.PENDIENTE:
                    self._estados[numero] = EstadoExpediente.OMITIDO
                    omitidos += 1

            self._errores.append({
                "numero": "GLOBAL",
                "error": f"Error crítico: {str(e)}",
            })
            raise

        finally:
            fin = datetime.now()
            tiempo_total = (fin - inicio).total_seconds()

            self._reportar_progreso(
                total, total,
                f"Completado: {exitosos} exitosos, {errores} errores"
            )

            return ResumenExtraccion(
                total=total,
                exitosos=exitosos,
                errores=errores,
                omitidos=omitidos,
                tiempo_total=tiempo_total,
                errores_detalles=self._errores.copy(),
                archivos_descargados=total_archivos_descargados,
            )

    async def _procesar_expediente(
        self,
        page: Page,
        numero_expediente: str,
        context: BrowserContext,
        browser: Browser,
    ) -> Dict:
        """
        Procesa un expediente individual.

        Flujo:
        1. Buscar expediente por número en PJN
        2. Extraer datos del expediente (metadata)
        3. Procesar actuaciones usando servicio coordinador de v5
        4. Descargar adjuntos si procesar_con_pdf=True
        5. Clasificar actuaciones (opcional)
        6. Guardar en repositorio

        Args:
            page: Página de Playwright
            numero_expediente: Número del expediente a procesar
            context: Contexto del navegador
            browser: Instancia del navegador

        Returns:
            Dict con success y datos del expediente o error
        """
        try:
            # ==================================================================
            # PASO 1: Buscar expediente en PJN
            # ==================================================================
            print(f"🔍 Buscando expediente: {numero_expediente}")

            # Parsear número usando la función que maneja todos los formatos
            # Soporta: "FPA 001234/2024", "FRE 001234/2024/I", "001234/2024/1", etc.
            _, numero_limpio, anio_limpio = descomponer_numero_expediente(numero_expediente)

            if not numero_limpio:
                print(f"❌ No se pudo parsear el número de expediente: {numero_expediente}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": "Formato de número inválido"
                }

            print(f"🔢 Número parseado: {numero_limpio}/{anio_limpio or 'sin año'}")

            # Navegar a la página de búsqueda de expedientes
            print("🔍 Navegando a página de búsqueda de expedientes...")
            await page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")
            await page.wait_for_load_state("domcontentloaded")

            exito, motivo = await buscar_expediente_por_numero(page, numero_limpio, anio_limpio)

            if not exito:
                print(f"❌ Expediente no encontrado: {numero_expediente} - {motivo}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": f"No encontrado: {motivo}"
                }

            print(f"✅ Expediente encontrado en resultados: {numero_expediente}")

            # ==================================================================
            # Hacer clic en el enlace del expediente para abrir su página
            # ==================================================================
            print("👁 Abriendo página del expediente...")
            try:
                # Buscar el primer enlace del expediente en la tabla de resultados
                enlace_expediente = await page.query_selector("table.table-striped tbody tr td a")
                if not enlace_expediente:
                    print(f"❌ No se encontró enlace para abrir expediente: {numero_expediente}")
                    return {
                        "success": False,
                        "numero": numero_expediente,
                        "error": "No se encontró enlace del expediente"
                    }

                await enlace_expediente.click()
                await page.wait_for_load_state("load")
                await page.wait_for_timeout(2000)  # Esperar a que cargue completamente
                print(f"✅ Página del expediente abierta: {numero_expediente}")

            except Exception as e:
                print(f"❌ Error abriendo expediente: {e}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": f"Error abriendo expediente: {str(e)}"
                }

            # ==================================================================
            # PASO 2: Extraer metadata del expediente
            # ==================================================================
            datos_expediente = await extraer_datos_expediente(page)

            if not datos_expediente:
                print(f"❌ No se pudieron extraer datos: {numero_expediente}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": "No se pudieron extraer datos del expediente"
                }

            print(f"📋 Metadata extraída: {datos_expediente.get('caratula', '')[:50]}...")

            # ==================================================================
            # PASO 3: Procesar actuaciones con servicio coordinador
            # ==================================================================
            print(f"📥 Extrayendo actuaciones de {numero_expediente}...")

            # Agregar directorio_base y page a datos_expediente
            datos_expediente["directorio_base"] = self.config.directorio_base
            datos_expediente["page"] = page

            ruta_json, resultado = await procesar_actuaciones_expediente(
                datos_expediente,
                descargar_adjuntos=self.config.procesar_con_pdf
            )

            # Verificar si hubo error
            error_msg = resultado.get("error")
            if error_msg:
                print(f"❌ Error procesando actuaciones: {error_msg}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": f"Error en actuaciones: {error_msg}"
                }

            # Calcular total de actuaciones
            total_actuaciones = (
                resultado.get("actuaciones_actuales", 0) +
                resultado.get("actuaciones_historicas", 0)
            )
            print(f"✅ Actuaciones extraídas: {total_actuaciones}")

            # Contar archivos descargados si se ejecutaron descargas
            archivos_descargados = 0
            if resultado.get("descargas_ejecutadas") and resultado.get("carpeta_adjuntos"):
                try:
                    from pathlib import Path
                    adjuntos_path = Path(resultado["carpeta_adjuntos"]) / "adjuntos"
                    if adjuntos_path.exists():
                        archivos_descargados = len(list(adjuntos_path.glob("*.*")))
                except Exception:
                    pass
            if self.config.procesar_con_pdf:
                print(f"📎 Archivos descargados: {archivos_descargados}")

            # ==================================================================
            # PASO 4: Clasificación inteligente (opcional)
            # ==================================================================
            actuaciones_clasificadas = None
            if self.config.procesar_con_pdf and ruta_json:
                try:
                    from Sistema_v5.generador_documentos.integracion_procesador import (
                        FiltroContenidoInteligente
                    )

                    print(f"🧠 Clasificando actuaciones por utilidad jurídica...")

                    # Cargar actuaciones desde JSON
                    datos_actuaciones = cargar_actuaciones_json(str(ruta_json))
                    actuaciones = datos_actuaciones.get("Actuaciones", [])

                    # Aplicar filtro
                    filtro = FiltroContenidoInteligente(
                        min_utilidad=self.config.min_utilidad,
                        incluir_vencimientos=True,
                        ordenar_por_prioridad=True
                    )

                    actuaciones_clasificadas = filtro.filtrar_actuaciones(
                        actuaciones,
                        incluir_estadisticas=True
                    )

                    print(f"📊 Clasificación completada: {len(actuaciones_clasificadas)} actuaciones relevantes")

                except Exception as e:
                    print(f"⚠️ Error en clasificación (no crítico): {e}")

            # ==================================================================
            # PASO 5: Guardar en repositorio (si está disponible)
            # ==================================================================
            if self.expediente_repository:
                try:
                    # TODO: Convertir a modelo de dominio y guardar
                    # expediente_dominio = ExpedienteDominio(...)
                    # self.expediente_repository.save(expediente_dominio)
                    pass
                except Exception as e:
                    print(f"⚠️ Error guardando en repositorio (no crítico): {e}")

            # ==================================================================
            # RETORNAR RESULTADO
            # ==================================================================
            return {
                "success": True,
                "numero": numero_expediente,
                "data": {
                    "numero": numero_expediente,
                    "caratula": datos_expediente.get("caratula", ""),
                    "ruta_json": str(ruta_json) if ruta_json else None,
                    "total_actuaciones": total_actuaciones,
                    "archivos_descargados": archivos_descargados,
                    "tiempo_procesamiento": resultado.get("tiempo_procesamiento", 0),
                    "actuaciones_clasificadas": len(actuaciones_clasificadas) if actuaciones_clasificadas else 0
                }
            }

        except Exception as e:
            print(f"❌ Error procesando expediente {numero_expediente}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "numero": numero_expediente,
                "error": str(e),
            }

    async def _login_pjn(self, page: Page, username: str, password: str):
        """Realiza login en el portal PJN."""
        url_login = "https://portalpjn.pjn.gov.ar/inicio"

        await page.goto(url_login)
        await page.wait_for_load_state("domcontentloaded")

        # Selectores correctos del PJN
        await page.fill("input[name='username']", username)
        await page.fill("input[name='password']", password)

        await page.click("#kc-login")

        # Esperar confirmación de login exitoso
        await page.wait_for_selector("text='Menú'", timeout=60000)
        print("✅ Login exitoso en PJN")

    def _reportar_progreso(self, actual: int, total: int, mensaje: str):
        """Reporta progreso a través del callback si está configurado."""
        if self.on_progress:
            self.on_progress(actual, total, mensaje)

    def obtener_estado(self, numero_expediente: str) -> Optional[EstadoExpediente]:
        """Obtiene el estado actual de un expediente."""
        return self._estados.get(numero_expediente)

    def obtener_todos_estados(self) -> Dict[str, EstadoExpediente]:
        """Obtiene todos los estados de expedientes procesados."""
        return self._estados.copy()

    def obtener_errores(self) -> List[Dict]:
        """Obtiene la lista de errores ocurridos."""
        return self._errores.copy()
