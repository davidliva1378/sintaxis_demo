"""
Gestor Batch - Procesa lotes de expedientes seleccionados.

Permite procesar SOLO los expedientes elegidos por el usuario
después del filtrado y selección.
"""

import asyncio
import logging
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
from pjn.scraping.expedientes import (
    buscar_expediente_por_numero,
    buscar_expedientes,
    extraer_datos_expediente
)
from pjn.scraping import descomponer_numero_expediente
from pjn.services.actuaciones import procesar_actuaciones_expediente
from pjn.persistence.actuaciones import cargar_actuaciones_json

# Importar tipos de aplicación para type hints
try:
    from application.ports import IExpedienteRepository
except ImportError:
    IExpedienteRepository = None  # type: ignore

# Importar hook de indexación RAG
try:
    from infrastructure.rag.integration.actuaciones_hook import obtener_hook
    _rag_hook_disponible = True
except ImportError:
    _rag_hook_disponible = False

logger = logging.getLogger(__name__)

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
        caratulas: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            config: Configuración de extracción
            on_progress: Callback para reportar progreso (actual, total, mensaje)
            expediente_repository: Repositorio para guardar expedientes procesados
            caratulas: Diccionario {numero_expediente: caratula} para filtrado preciso
        """
        self.config = config or ConfigExtraccionMasiva()
        self.on_progress = on_progress
        self.expediente_repository = expediente_repository
        self.caratulas = caratulas or {}
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

                        # Obtener carátula del expediente desde el diccionario de carátulas
                        caratula_expediente = self.caratulas.get(numero)

                        resultado = await self._procesar_expediente(
                            page, numero, caratula_expediente, context, browser
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
            logger.error(f"Error crítico en batch: {e}", exc_info=True)
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
        caratula_esperada: str | None,
        context: BrowserContext,
        browser: Browser,
    ) -> Dict:
        """
        Procesa un expediente individual.

        Flujo:
        1. Buscar expediente por número en PJN (con filtrado por carátula opcional)
        2. Extraer datos del expediente (metadata)
        3. Procesar actuaciones usando servicio coordinador de v5
        4. Descargar adjuntos si procesar_con_pdf=True
        5. Clasificar actuaciones (opcional)
        6. Guardar en repositorio

        Args:
            page: Página de Playwright
            numero_expediente: Número del expediente a procesar
            caratula_esperada: Carátula esperada para filtrar búsqueda (None = sin filtro)
            context: Contexto del navegador
            browser: Instancia del navegador

        Returns:
            Dict con success y datos del expediente o error
        """
        try:
            # ==================================================================
            # PASO 1: Buscar expediente en PJN
            # ==================================================================
            logger.info(f"🔍 Buscando expediente: {numero_expediente}")

            # Parsear número usando la función que maneja todos los formatos
            # Soporta: "FPA 001234/2024", "FRE 001234/2024/I", "001234/2024/1", etc.
            _, numero_limpio, anio_limpio, incidente = descomponer_numero_expediente(numero_expediente)

            if not numero_limpio:
                logger.error(f"❌ No se pudo parsear el número de expediente: {numero_expediente}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": "Formato de número inválido"
                }

            logger.debug(f"🔢 Número parseado: {numero_limpio}/{anio_limpio or 'sin año'}")

            # Navegar a la página de búsqueda de expedientes
            logger.debug("🔍 Navegando a página de búsqueda de expedientes...")
            await page.goto("https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam")
            await page.wait_for_load_state("domcontentloaded")

            # Buscar expediente con filtrado por carátula
            logger.info(f"🔍 Buscando expediente: {numero_limpio}/{anio_limpio}" +
                  (f" con carátula: '{caratula_esperada}'" if caratula_esperada else ""))

            # Usar buscar_expedientes con carátula
            filas = await buscar_expedientes(
                page,
                numero=numero_limpio,
                anio=anio_limpio,
                caratula=caratula_esperada
            )

            # Fallback: Reintentar sin carátula si no hay coincidencias
            if not filas and caratula_esperada:
                logger.warning(
                    f"⚠️ No se hallaron coincidencias para carátula '{caratula_esperada}'. "
                    f"Reintentando sin filtro para expediente {numero_expediente}..."
                )
                filas = await buscar_expedientes(
                    page,
                    numero=numero_limpio,
                    anio=anio_limpio,
                    caratula=None
                )

            # Verificar si se encontró el expediente
            if not filas:
                logger.warning(f"❌ No se encontró expediente {numero_expediente}")
                return {
                    "success": False,
                    "error": "Expediente no encontrado",
                    "expediente": numero_expediente
                }

            # Selección de expediente cuando hay múltiples resultados
            fila_seleccionada = filas[0]
            if len(filas) > 1:
                logger.info(f"🔍 Múltiples expedientes ({len(filas)}) encontrados. Analizando candidatos...")
                
                # Importar normalización para comparar carátulas
                from core.domain.utils.text import normalizar_texto
                
                candidatos = []
                
                for fila in filas:
                    texto_fila = await fila.inner_text()
                    texto_fila_upper = texto_fila.upper()
                    es_candidato = False
                    
                    if incidente:
                        # El incidente aparece como sufijo en el número de expediente
                        # Ej: "FPA 21002641/2010/I" o "FPA 21002641/2010/CA1"
                        # Usar regex estricta para evitar coincidencias parciales (ej: /1 coincidiendo con /1/2)
                        import re
                        if anio_limpio:
                            # Busca: AÑO + separador + INCIDENTE + (fin o separador no numérico)
                            # (?![0-9/]) asegura que no siga otro número o barra (ej: /1 no matchea /1/2)
                            patron_incidente = rf'{anio_limpio}\s*[\/-]\s*{re.escape(incidente)}(?![0-9\/])'
                            if re.search(patron_incidente, texto_fila_upper):
                                es_candidato = True
                        else:
                            # Fallback si no hay año (raro): busca /INCIDENTE al final o seguido de espacio
                            if f"/{incidente}" in texto_fila_upper or f"-{incidente}" in texto_fila_upper:
                                es_candidato = True
                    else:
                        # El principal es el que tiene formato NNNN/YYYY sin sufijo
                        # Verificar que no tenga /I, /CA1, /1, etc. después del año
                        import re
                        if numero_limpio and anio_limpio:
                            # Buscar patrón: número/año que NO esté seguido de /sufijo
                            patron_principal = rf'{numero_limpio}\s*/\s*{anio_limpio}(?!\s*/)'
                            if re.search(patron_principal, texto_fila):
                                es_candidato = True
                    
                    if es_candidato:
                        candidatos.append(fila)

                if not candidatos:
                    logger.warning(f"⚠️ Ninguna fila cumple con el criterio exacto (Incidente: {incidente or 'No'}). Usando la primera fila.")
                    fila_seleccionada = filas[0]
                elif len(candidatos) == 1:
                    logger.info(f"✅ Un único candidato válido encontrado.")
                    fila_seleccionada = candidatos[0]
                else:
                    # Múltiples candidatos válidos (ej: misma numeración en distintas jurisdicciones)
                    logger.info(f"⚠️ {len(candidatos)} candidatos válidos encontrados. Intentando desempatar por carátula...")
                    
                    if caratula_esperada:
                        mejor_candidato = None
                        mejor_score = 0
                        caratula_norm = normalizar_texto(caratula_esperada)
                        
                        for cand in candidatos:
                            # Extraer texto de la columna de carátula (usualmente la 3ra columna)
                            try:
                                columnas = await cand.query_selector_all("td")
                                if len(columnas) >= 3:
                                    texto_caratula = await columnas[2].inner_text()
                                    texto_caratula_norm = normalizar_texto(texto_caratula)
                                    
                                    # Score simple: conteo de palabras coincidentes
                                    palabras_esperadas = set(caratula_norm.split())
                                    palabras_encontradas = set(texto_caratula_norm.split())
                                    coincidencias = len(palabras_esperadas.intersection(palabras_encontradas))
                                    
                                    if coincidencias > mejor_score:
                                        mejor_score = coincidencias
                                        mejor_candidato = cand
                            except Exception:
                                pass
                        
                        if mejor_candidato and mejor_score > 0:
                            logger.info(f"✅ Candidato seleccionado por coincidencia de carátula (Score: {mejor_score})")
                            fila_seleccionada = mejor_candidato
                        else:
                            logger.warning("⚠️ No se pudo desempatar por carátula. Usando el primer candidato.")
                            fila_seleccionada = candidatos[0]
                    else:
                        logger.warning("⚠️ Sin carátula esperada para desempatar. Usando el primer candidato.")
                        fila_seleccionada = candidatos[0]

            # Navegar al expediente seleccionado
            try:
                enlace_expediente = await fila_seleccionada.query_selector("a")
                if not enlace_expediente:
                    logger.error(f"❌ No se encontró enlace en fila del expediente {numero_expediente}")
                    return {
                        "success": False,
                        "error": "Enlace de expediente no encontrado",
                        "expediente": numero_expediente
                    }

                await enlace_expediente.click()
                await page.wait_for_load_state("domcontentloaded")
                logger.info(f"✅ Navegado a expediente {numero_expediente}")

            except Exception as e:
                logger.error(f"❌ Error al navegar a expediente {numero_expediente}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Error al navegar: {str(e)}",
                    "expediente": numero_expediente
                }

            # ==================================================================
            # PASO 2: Extraer metadata del expediente
            # ==================================================================
            datos_expediente = await extraer_datos_expediente(page)

            if not datos_expediente:
                logger.error(f"❌ No se pudieron extraer datos: {numero_expediente}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": "No se pudieron extraer datos del expediente"
                }

            logger.info(f"📋 Metadata extraída: {datos_expediente.get('caratula', '')[:50]}...")

            # ==================================================================
            # PASO 3: Procesar actuaciones con servicio coordinador (con reintentos)
            # ==================================================================
            logger.info(f"📥 Extrayendo actuaciones de {numero_expediente}...")

            # Agregar directorio_base y page a datos_expediente
            datos_expediente["directorio_base"] = self.config.directorio_base
            datos_expediente["page"] = page

            ruta_json = None
            resultado = {}
            error_final = None

            # Bucle de reintentos
            intentos_maximos = self.config.max_reintentos if self.config.max_reintentos > 0 else 1
            
            for intento in range(intentos_maximos):
                try:
                    if intento > 0:
                        logger.info(f"🔄 Reintento {intento + 1}/{intentos_maximos} para {numero_expediente}...")
                        await asyncio.sleep(2) # Espera breve entre reintentos

                    ruta_json, resultado = await procesar_actuaciones_expediente(
                        datos_expediente,
                        descargar_adjuntos=self.config.procesar_con_pdf
                    )
                    
                    # Si no hay error en el resultado, salimos del bucle
                    if not resultado.get("error"):
                        error_final = None
                        break
                    else:
                        error_final = resultado.get("error")
                        logger.warning(f"⚠️ Intento {intento + 1} fallido: {error_final}")

                except Exception as e:
                    error_final = str(e)
                    logger.warning(f"⚠️ Excepción en intento {intento + 1}: {e}")
            
            # Verificar si hubo error después de todos los intentos
            if error_final:
                logger.error(f"❌ Error procesando actuaciones tras {intentos_maximos} intentos: {error_final}")
                return {
                    "success": False,
                    "numero": numero_expediente,
                    "error": f"Error en actuaciones: {error_final}"
                }

            # Calcular total de actuaciones
            total_actuaciones = (
                resultado.get("actuaciones_actuales", 0) +
                resultado.get("actuaciones_historicas", 0)
            )
            logger.info(f"✅ Actuaciones extraídas: {total_actuaciones}")

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
                logger.info(f"📎 Archivos descargados: {archivos_descargados}")

            # ==================================================================
            # PASO 4: Clasificación inteligente (opcional)
            # ==================================================================
            actuaciones_clasificadas = None
            if self.config.procesar_con_pdf and ruta_json:
                try:
                    from core.generador_documentos.integracion_procesador import (
                        FiltroContenidoInteligente
                    )

                    logger.info(f"🧠 Clasificando actuaciones por utilidad jurídica...")

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

                    logger.info(f"📊 Clasificación completada: {len(actuaciones_clasificadas)} actuaciones relevantes")

                except Exception as e:
                    logger.warning(f"⚠️ Error en clasificación (no crítico): {e}")

            # ==================================================================
            # PASO 5: Guardar en repositorio (si está disponible)
            # ==================================================================
            if self.expediente_repository:
                try:
                    # Importar modelo de dominio
                    from core.domain.entities import ExpedienteResumen

                    # Obtener última actuación del JSON si existe
                    ultima_actuacion = None
                    try:
                        import json
                        from pathlib import Path

                        # Intentar obtener ruta del JSON de actuaciones
                        ruta_act_str = resultado.get("ruta_actuaciones")
                        if not ruta_act_str and ruta_json:
                            ruta_act_str = str(ruta_json)

                        if ruta_act_str:
                            ruta_act = Path(ruta_act_str)
                            if ruta_act.exists():
                                with open(ruta_act, 'r', encoding='utf-8') as f:
                                    act_data = json.load(f)

                                    # Buscar en actuaciones_actuales primero
                                    actuaciones = act_data.get("actuaciones_actuales", [])

                                    # Si no hay actuales, buscar en históricas
                                    if not actuaciones:
                                        actuaciones = act_data.get("actuaciones_historicas", [])

                                    # También buscar en formato alternativo "Actuaciones"
                                    if not actuaciones:
                                        actuaciones = act_data.get("Actuaciones", [])

                                    if actuaciones and len(actuaciones) > 0:
                                        # Última actuación es la primera en la lista
                                        ultima_actuacion = actuaciones[0].get("Fecha")

                        # Si aún no tenemos fecha, usar la fecha actual
                        if not ultima_actuacion:
                            from datetime import datetime
                            ultima_actuacion = datetime.now().strftime("%Y-%m-%d")
                            logger.warning(f"⚠️ No se encontró fecha de última actuación, usando fecha actual: {ultima_actuacion}")

                    except Exception as e_act:
                        logger.warning(f"⚠️ No se pudo obtener última actuación: {e_act}")
                        # Usar fecha actual como fallback
                        from datetime import datetime
                        ultima_actuacion = datetime.now().strftime("%Y-%m-%d")

                    # Validar que los datos sean válidos antes de guardar
                    dependencia = datos_expediente.get("dependencia", "")
                    caratula = datos_expediente.get("caratula", "")

                    # No guardar expedientes con datos inválidos o "No encontrada"
                    if (dependencia and dependencia != "No encontrada" and
                        caratula and caratula != "No encontrada"):

                        # Crear expediente de dominio
                        expediente_dominio = ExpedienteResumen.from_dict({
                            "numero": datos_expediente.get("numero", numero_expediente),
                            "dependencia": dependencia,
                            "caratula": caratula,
                            "situacion": datos_expediente.get("situacion"),
                            "ultima_actuacion": ultima_actuacion
                        })

                        # Guardar en repositorio
                        await self.expediente_repository.save(expediente_dominio)
                        logger.info(f"💾 Expediente guardado en repositorio: {numero_expediente}")
                    else:
                        logger.warning(f"⚠️ Expediente {numero_expediente} no guardado: datos inválidos o incompletos")

                except Exception as e:
                    logger.warning(f"⚠️ Error guardando en repositorio (no crítico): {e}")

            # ==================================================================
            # PASO 6: Indexar en RAG (si está disponible)
            # ==================================================================
            resultado_final = {
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

            # Ejecutar hook de indexación RAG si está disponible
            if _rag_hook_disponible:
                try:
                    hook = obtener_hook()
                    hook.on_expediente_procesado(numero_expediente, resultado_final)
                except Exception as e:
                    logger.warning(f"⚠️ Error en hook RAG (no crítico): {e}")

            # ==================================================================
            # RETORNAR RESULTADO
            # ==================================================================
            return resultado_final

        except Exception as e:
            logger.error(f"❌ Error procesando expediente {numero_expediente}: {e}", exc_info=True)
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
        logger.info("✅ Login exitoso en PJN")

    def _reportar_progreso(self, actual: int, total: int, mensaje: str):
        """Reporta progreso a través del callback si está configurado."""
        logger.info(f"[{actual}/{total}] {mensaje}")
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
