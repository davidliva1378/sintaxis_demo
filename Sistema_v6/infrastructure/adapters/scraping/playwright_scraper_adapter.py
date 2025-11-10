"""Adapter de scraping usando Playwright para el Portal Judicial Nacional.

Implementa IScraperPort para extracción de datos del portal PJN usando Playwright.
Integra session_manager, pagination y parsers para extracción completa.

Migrado de: Sistema_v5/pjn/scraping/ (expedientes.py, entradas.py, actuaciones.py)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from playwright.async_api import Error, Page, TimeoutError

from application.ports import IScraperPort
from core.domain.entities import (
    ActuacionesArchivo,
    Entrada,
    ExpedienteIdentificacion,
    ExpedienteResumen,
)
from infrastructure.config import Settings, get_settings
from infrastructure.exceptions import ExtraccionError, SesionInvalida

from .pagination import DEFAULT_PAGINATION_STRATEGY, PaginationStrategy
from .parsers import (
    construir_actuaciones_archivo,
    parse_actuacion_row,
    parse_entrada,
    parse_expediente_resumen,
)
from .selectores import SEL_ACTUACIONES, SEL_ENTRADAS, SEL_EXPEDIENTES
from .session_manager import obtener_sesion_autenticada

logger = logging.getLogger(__name__)

# Constantes para ordenamiento de tabla de expedientes
_ORDEN_MAP = {
    "fecha": "FECHA",
    "caratula": "CARATULA",
    "oficina": "OFICINA",
    "situacion": "SITUACION",
}

# Selectores para ordenamiento (específicos del portal PJN)
_SEL_ORDEN_SELECT = "#j_idt150\\:order_by_form\\:camara"
_SEL_ORDENAR_LINK = "a:has-text('Ordenar')"

# Selector para total de expedientes encontrados
_SEL_TOTAL_EXPEDIENTES = "strong:has-text('Se han encontrado')"


class PlaywrightScraperAdapter(IScraperPort):
    """Implementación de IScraperPort usando Playwright.

    Este adapter usa Playwright para extraer datos del Portal Judicial Nacional,
    implementando las tres operaciones principales:
    - Extracción de expedientes (con paginación)
    - Extracción de entradas/notificaciones (con scroll infinito)
    - Extracción de actuaciones (con tabs de actuales/históricas)

    Attributes:
        _login_url: URL de login del PJN
        _session_file: Path del archivo de sesión de Playwright
        _settings: Configuración del sistema
        _max_scrolls_entradas: Límite máximo de scrolls para extracción de entradas
    """

    def __init__(
        self,
        *,
        login_url: str,
        session_file: Path | None = None,
        settings: Settings | None = None,
        max_scrolls_entradas: int = 100,
    ):
        """Inicializa el adapter.

        Args:
            login_url: URL de login del PJN
            session_file: Path del archivo de sesión (None para usar default)
            settings: Settings del sistema (None para usar default)
            max_scrolls_entradas: Límite máximo de scrolls al extraer entradas.
                Default: 100. Usar valores mayores si hay muchas entradas,
                o menores para limitar el tiempo de extracción.
        """
        if settings is None:
            settings = get_settings()

        self._login_url = login_url
        self._session_file = session_file or (settings.storage.base_path / settings.auth.session_file_name)
        self._settings = settings
        self._max_scrolls_entradas = max_scrolls_entradas

    async def extraer_expedientes(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
        orden: str | None = None,
        fecha_corte: str | None = None,
    ) -> list[ExpedienteResumen]:
        """Extrae la lista completa de expedientes del usuario.

        Implementa extracción con paginación automática, manejo de duplicados,
        ordenamiento opcional, fecha de corte y parsing de filas HTML a objetos del dominio.

        Args:
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica
            orden: Criterio de ordenamiento opcional. Valores válidos:
                'fecha', 'caratula', 'oficina', 'situacion'.
                Si es None, mantiene el orden por defecto del portal.
            fecha_corte: Fecha de corte opcional para actualizaciones incrementales.
                Formatos aceptados: 'YYYY-MM-DD' o 'DD/MM/YYYY'.
                La extracción se detiene al encontrar un expediente con fecha
                de última actuación anterior a esta fecha.
                Si es None, extrae todos los expedientes.

        Returns:
            Lista de expedientes extraídos (ordenados si se especifica, hasta fecha_corte si aplica)

        Raises:
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ExtraccionError: Si ocurre un error durante el scraping
            ValueError: Si fecha_corte tiene formato inválido

        Example:
            >>> adapter = PlaywrightScraperAdapter(login_url=URL)

            >>> # Extraer todos con ordenamiento
            >>> expedientes = await adapter.extraer_expedientes(
            ...     credenciales=("user", "pass"),
            ...     orden="fecha"
            ... )

            >>> # Actualización incremental desde fecha
            >>> expedientes_nuevos = await adapter.extraer_expedientes(
            ...     credenciales=("user", "pass"),
            ...     orden="fecha",
            ...     fecha_corte="2024-01-01"
            ... )
        """
        logger.info("Iniciando extracción de expedientes del PJN")

        usuario = credenciales[0] if credenciales else None
        contrasena = credenciales[1] if credenciales else None

        # Parsear y validar fecha de corte si se especifica
        fecha_corte_dt: datetime | None = None
        if fecha_corte:
            fecha_corte_dt = self._parsear_fecha_corte(fecha_corte)
            if fecha_corte_dt:
                logger.info(f"📅 Fecha de corte configurada: {fecha_corte_dt.strftime('%Y-%m-%d')}")
            else:
                logger.warning(f"⚠️ Formato de fecha_corte inválido: {fecha_corte}. Ignorando.")

        try:
            async with obtener_sesion_autenticada(
                usuario=usuario,
                contraseña=contrasena,
                session_file=self._session_file,
                headless=headless,
                login_url=self._login_url,
                settings=self._settings,
            ) as page:
                # Después del login, ya estamos en la página correcta
                # No es necesario navegar a otra URL
                await page.wait_for_load_state("domcontentloaded")

                # Esperar a que aparezca la tabla de expedientes
                tabla = page.locator(SEL_EXPEDIENTES.TABLA_RESULTADOS)
                try:
                    await tabla.wait_for(state="visible", timeout=30000)
                except TimeoutError:
                    logger.warning("No se encontró tabla de expedientes, retornando lista vacía")
                    return []

                # Aplicar ordenamiento si se especifica
                if orden:
                    await self._aplicar_ordenamiento_tabla(page, tabla, orden)

                # Extraer expedientes con paginación (con fecha de corte si aplica)
                expedientes = await self._extraer_expedientes_con_paginacion(
                    page,
                    fecha_corte_dt=fecha_corte_dt
                )

                logger.info(f"Extracción completada: {len(expedientes)} expedientes")
                return expedientes

        except Exception as e:
            logger.exception("Error durante extracción de expedientes")
            raise ExtraccionError(f"Fallo en extracción de expedientes: {e}") from e

    async def _aplicar_ordenamiento_tabla(
        self,
        page: Page,
        tabla,
        orden: str,
    ) -> None:
        """Aplica ordenamiento a la tabla de expedientes.

        Selecciona el criterio de ordenamiento en el dropdown y hace clic
        en el botón "Ordenar". Espera a que la tabla se recargue con los
        datos ordenados.

        Args:
            page: Página de Playwright
            tabla: Locator de la tabla de expedientes
            orden: Criterio de ordenamiento. Valores válidos:
                'fecha', 'caratula', 'oficina', 'situacion'

        Note:
            Si el ordenamiento falla (timeout, selector no encontrado, etc.),
            solo registra un warning y continúa. No lanza excepción para no
            interrumpir la extracción de expedientes.

        Example:
            >>> await self._aplicar_ordenamiento_tabla(page, tabla, "fecha")
            🔽 Tabla ordenada por FECHA
        """
        # Resolver valor del select
        valor_orden = _ORDEN_MAP.get(orden.lower())

        if not valor_orden:
            logger.warning(
                f"⚠️ Valor de orden desconocido: {orden}. "
                f"Opciones válidas: {list(_ORDEN_MAP.keys())}"
            )
            return

        try:
            # Seleccionar opción en dropdown
            await page.select_option(_SEL_ORDEN_SELECT, value=valor_orden)
            logger.debug(f"Opción de ordenamiento seleccionada: {valor_orden}")

            # Click en botón "Ordenar"
            await page.locator(_SEL_ORDENAR_LINK).click()
            logger.debug("Click en botón 'Ordenar'")

            # Esperar que la tabla se oculte (recargando)
            try:
                await tabla.wait_for(state="hidden", timeout=8000)
            except TimeoutError:
                # La tabla puede no ocultarse en algunos casos, continuar
                pass

            # Esperar que reaparezca con datos ordenados
            await tabla.wait_for(state="visible", timeout=25000)

            logger.info(f"🔽 Tabla ordenada por {orden.upper()}")

        except TimeoutError as exc:
            logger.warning(
                f"⚠️ El reordenamiento por {orden} no se completó a tiempo: {exc}"
            )
            # Continuar extracción de todos modos

        except Exception as exc:
            logger.warning(
                f"⚠️ No se pudo reordenar la tabla por {orden}: {exc}"
            )
            # Continuar extracción de todos modos

    async def _extraer_total_esperado(self, page: Page) -> int | None:
        """Intenta leer el total anunciado en el encabezado del listado.

        Busca el mensaje "Se han encontrado X expedientes" y extrae el número
        para validar que se extrajeron todos los expedientes esperados.

        Args:
            page: Página de Playwright

        Returns:
            int: Número total de expedientes encontrados según el portal
            None: Si no se pudo leer el total (selector no encontrado, error de parsing, etc.)

        Example:
            >>> total = await self._extraer_total_esperado(page)
            >>> if total:
            ...     print(f"Total esperado: {total}")

        Note:
            Esta función es robusta y no lanza excepciones. Retorna None
            si hay cualquier error durante la lectura.
        """
        try:
            total_locator = page.locator(_SEL_TOTAL_EXPEDIENTES)
            if await total_locator.count() <= 0:
                logger.debug("No se encontró mensaje de total de expedientes")
                return None

            texto = await total_locator.first.inner_text()
        except Error as e:
            logger.debug(f"Error leyendo total de expedientes: {e}")
            return None

        # Intentar extraer número del texto
        # Primero buscar patrón "total de X"
        coincidencia = re.search(r"total de\s*([\d.,]+)", texto, re.IGNORECASE)
        if not coincidencia:
            # Si no, buscar cualquier número en el texto
            coincidencia = re.search(r"([\d][\d.,]*)", texto)

        if not coincidencia:
            logger.debug(f"No se encontró número en texto: {texto}")
            return None

        # Limpiar número (remover puntos y comas de separadores de miles)
        numero_str = re.sub(r"[^\d]", "", coincidencia.group(1))
        if not numero_str:
            return None

        try:
            total = int(numero_str)
            logger.debug(f"Total de expedientes encontrados según portal: {total}")
            return total
        except ValueError as e:
            logger.debug(f"Error convirtiendo '{numero_str}' a int: {e}")
            return None

    def _parsear_fecha_corte(self, fecha_corte: str) -> datetime | None:
        """Parsea y valida una fecha de corte.

        Args:
            fecha_corte: Fecha en formato 'YYYY-MM-DD' o 'DD/MM/YYYY'

        Returns:
            datetime: Objeto datetime si el parsing es exitoso
            None: Si el formato es inválido

        Example:
            >>> dt = self._parsear_fecha_corte("2024-01-15")
            >>> dt = self._parsear_fecha_corte("15/01/2024")
        """
        fecha_norm = (fecha_corte or "").strip()
        if not fecha_norm:
            return None

        # Intentar formato YYYY-MM-DD
        try:
            return datetime.strptime(fecha_norm, "%Y-%m-%d")
        except ValueError:
            pass

        # Intentar formato DD/MM/YYYY
        match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", fecha_norm)
        if match:
            dia, mes, año = match.groups()
            if len(año) == 2:
                año = "20" + año
            try:
                return datetime(int(año), int(mes), int(dia))
            except ValueError:
                logger.debug(f"Fecha inválida: {fecha_norm}")
                return None

        logger.debug(f"Formato de fecha no reconocido: {fecha_norm}")
        return None

    async def _extraer_expedientes_con_paginacion(
        self,
        page: Page,
        pagination_strategy: PaginationStrategy | None = None,
        fecha_corte_dt: datetime | None = None,
    ) -> list[ExpedienteResumen]:
        """Extrae expedientes de todas las páginas usando paginación.

        Args:
            page: Página de Playwright ya posicionada
            pagination_strategy: Estrategia de paginación (None para usar default)
            fecha_corte_dt: Fecha de corte opcional. La extracción se detiene al
                encontrar un expediente con fecha de última actuación anterior
                a esta fecha. Si es None, extrae todos los expedientes.

        Returns:
            Lista de todos los expedientes extraídos (hasta fecha_corte si aplica)
        """
        if pagination_strategy is None:
            pagination_strategy = DEFAULT_PAGINATION_STRATEGY

        expedientes: list[ExpedienteResumen] = []
        huellas: set[tuple[str, str, str]] = set()  # Para detectar duplicados
        pagina = 0

        # Intentar extraer total esperado del portal
        total_esperado = await self._extraer_total_esperado(page)
        if total_esperado is not None:
            logger.info(f"📊 Total de expedientes según portal: {total_esperado}")

        tbody_locator = page.locator(f"{SEL_EXPEDIENTES.TABLA_RESULTADOS} tbody")

        while True:
            pagina += 1
            logger.info(f"Procesando página {pagina}")

            # Calcular fingerprint de la página actual
            fingerprint_actual = await self._calcular_fingerprint(tbody_locator)

            # Extraer filas de la página actual
            filas = await page.evaluate(
                """(tbodySelector) => Array.from(
                    document.querySelectorAll(`${tbodySelector} tr`),
                    tr => Array.from(tr.cells, c => c.innerText.trim())
                )""",
                f"{SEL_EXPEDIENTES.TABLA_RESULTADOS} tbody",
            )

            # Parsear filas
            for cols in filas:
                expediente = parse_expediente_resumen(cols)
                if expediente is None:
                    continue

                # Verificar fecha de corte (si está configurada)
                if fecha_corte_dt and expediente.ultima_actuacion:
                    try:
                        # Parsear fecha de última actuación (formato YYYY-MM-DD)
                        ultima_actuacion_dt = datetime.strptime(
                            expediente.ultima_actuacion,
                            "%Y-%m-%d"
                        )

                        # Si la fecha del expediente es anterior a la fecha de corte, detener
                        if ultima_actuacion_dt < fecha_corte_dt:
                            logger.info(
                                f"⏹️ Fecha de corte alcanzada. Expediente {expediente.numero} "
                                f"con fecha {expediente.ultima_actuacion} < "
                                f"{fecha_corte_dt.strftime('%Y-%m-%d')}. "
                                f"Deteniendo extracción."
                            )
                            # Retornar expedientes extraídos hasta ahora
                            return expedientes
                    except ValueError:
                        # Si no se puede parsear la fecha, continuar
                        logger.debug(
                            f"No se pudo parsear fecha {expediente.ultima_actuacion} "
                            f"del expediente {expediente.numero}"
                        )

                # Detectar duplicados
                huella = (expediente.numero, expediente.caratula, expediente.dependencia)
                if huella in huellas:
                    continue

                huellas.add(huella)
                expedientes.append(expediente)

            logger.debug(f"Página {pagina}: extraídos {len(filas)} filas, total acumulado: {len(expedientes)}")

            # Intentar navegar a siguiente página
            exito, motivo = await pagination_strategy.navegar_siguiente(
                page, tbody_locator, fingerprint_actual
            )

            if not exito:
                logger.info(f"Fin de paginación: {motivo}")
                break

            # Límite de seguridad
            if pagina >= 1000:
                logger.warning("Límite de páginas alcanzado (1000), deteniendo")
                break

        # Validar total extraído vs. total esperado
        if total_esperado is not None:
            total_extraido = len(expedientes)
            if total_extraido == total_esperado:
                logger.info(f"✅ Validación exitosa: {total_extraido}/{total_esperado} expedientes")
            elif total_extraido < total_esperado:
                logger.warning(
                    f"⚠️ Se extrajeron menos expedientes ({total_extraido}) "
                    f"que los esperados ({total_esperado}). "
                    f"Faltantes: {total_esperado - total_extraido}"
                )
            else:
                logger.warning(
                    f"⚠️ Se extrajeron más expedientes ({total_extraido}) "
                    f"que los esperados ({total_esperado}). "
                    f"Extras: {total_extraido - total_esperado} (posibles duplicados)"
                )

        return expedientes

    async def extraer_entradas(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[Entrada]:
        """Extrae entradas/notificaciones de la bandeja del usuario.

        Implementa extracción con scroll infinito para cargar todas las entradas.

        Args:
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Lista de entradas extraídas

        Raises:
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ExtraccionError: Si ocurre un error durante el scraping
        """
        logger.info("Iniciando extracción de entradas del PJN")

        usuario = credenciales[0] if credenciales else None
        contrasena = credenciales[1] if credenciales else None

        try:
            async with obtener_sesion_autenticada(
                usuario=usuario,
                contraseña=contrasena,
                session_file=self._session_file,
                headless=headless,
                login_url=self._login_url,
                settings=self._settings,
            ) as page:
                # Navegar a bandeja de entradas
                await page.goto(f"{self._login_url}/bandeja-entradas")
                await page.wait_for_load_state("domcontentloaded")

                # Esperar tabla de entradas
                try:
                    await page.wait_for_selector(SEL_ENTRADAS.TABLA, timeout=30000)
                except TimeoutError:
                    logger.warning("No se encontró tabla de entradas, retornando lista vacía")
                    return []

                # Extraer entradas con scroll
                entradas = await self._extraer_entradas_con_scroll(page)

                logger.info(f"Extracción completada: {len(entradas)} entradas")
                return entradas

        except Exception as e:
            logger.exception("Error durante extracción de entradas")
            raise ExtraccionError(f"Fallo en extracción de entradas: {e}") from e

    async def _extraer_entradas_con_scroll(self, page: Page) -> list[Entrada]:
        """Extrae entradas usando scroll infinito.

        Args:
            page: Página de Playwright ya posicionada

        Returns:
            Lista de todas las entradas extraídas
        """
        entradas: list[Entrada] = []
        timestamp_extraccion = datetime.now().isoformat()

        contenedor = page.locator(SEL_ENTRADAS.CONTENEDOR_SCROLL)
        filas_anteriores = 0

        # Hacer scroll hasta cargar todas las entradas
        for intento in range(self._max_scrolls_entradas):
            # Contar filas actuales
            filas = page.locator(SEL_ENTRADAS.FILAS)
            filas_count = await filas.count()

            if filas_count == filas_anteriores:
                # No se cargaron más filas, verificar si hay mensaje de fin
                try:
                    await page.wait_for_selector(
                        f"text=/{SEL_ENTRADAS.TEXTO_FIN_EVENTOS}/",
                        timeout=2000,
                    )
                    logger.info("Mensaje de fin de eventos encontrado")
                    break
                except TimeoutError:
                    # No hay mensaje de fin, pero tampoco más filas
                    logger.info("No se cargaron más filas, finalizando scroll")
                    break

            filas_anteriores = filas_count

            # Scroll hacia abajo
            await contenedor.evaluate("el => el.scrollBy(0, 1000)")
            await page.wait_for_timeout(500)

            logger.debug(f"Scroll {intento + 1}: {filas_count} filas visibles")
        else:
            # Se alcanzó el límite de scrolls sin encontrar el fin
            logger.warning(
                f"⚠️ Se alcanzó el límite de {self._max_scrolls_entradas} scrolls. "
                f"Puede haber más entradas. Considere aumentar max_scrolls_entradas."
            )

        # Parsear todas las filas visibles
        logger.info(f"Parseando {filas_count} filas de entradas")

        for i in range(filas_count):
            try:
                fila = filas.nth(i)

                # Extraer datos de la fila
                celdas = await fila.locator(SEL_ENTRADAS.CELDAS_FILA).all()
                if len(celdas) < 3:
                    continue

                numero_elem = await celdas[0].locator(SEL_ENTRADAS.EXPEDIENTE_NUMERO).first.text_content()
                caratula_elem = await celdas[0].locator(SEL_ENTRADAS.EXPEDIENTE_CARATULA).first.text_content()
                fecha_elem = await celdas[1].locator(SEL_ENTRADAS.FECHA_ELEMENTO).first.text_content()

                # Extraer evento/tipo_evento (puede no estar presente)
                evento = None
                tipo_evento = None
                try:
                    evento_elem = await celdas[2].text_content()
                    evento = evento_elem.strip() if evento_elem else None
                except Exception:
                    pass

                # Crear entrada
                entrada = parse_entrada(
                    numero=numero_elem or "",
                    caratula=caratula_elem or "",
                    fecha=fecha_elem or "",
                    evento=evento,
                    tipo_evento=tipo_evento,
                    extraida_en=timestamp_extraccion,
                )

                entradas.append(entrada)

            except Exception as e:
                logger.warning(f"Error parseando fila {i}: {e}")
                continue

        return entradas

    async def extraer_actuaciones(
        self,
        identificacion: ExpedienteIdentificacion,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> ActuacionesArchivo:
        """Extrae actuaciones de un expediente específico.

        Extrae actuaciones actuales e históricas, con manejo de paginación
        en cada sección.

        Args:
            identificacion: Identificación del expediente a extraer
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            ActuacionesArchivo con todas las actuaciones del expediente

        Raises:
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ExtraccionError: Si ocurre un error durante el scraping
        """
        logger.info(f"Iniciando extracción de actuaciones para {identificacion.numero}")

        usuario = credenciales[0] if credenciales else None
        contrasena = credenciales[1] if credenciales else None

        try:
            async with obtener_sesion_autenticada(
                usuario=usuario,
                contraseña=contrasena,
                session_file=self._session_file,
                headless=headless,
                login_url=self._login_url,
                settings=self._settings,
            ) as page:
                # Buscar y abrir expediente
                await self._navegar_a_expediente(page, identificacion.numero)

                # Extraer actuaciones actuales
                actuaciones_actuales = await self._extraer_actuaciones_tab(
                    page,
                    SEL_ACTUACIONES.TABLA_ACTUALES_ID,
                    es_historica=False,
                    indice_inicial=1,
                )

                # Intentar extraer históricas
                actuaciones_historicas = []
                try:
                    boton_historicas = page.locator(SEL_ACTUACIONES.BOTON_VER_HISTORICAS)
                    if await boton_historicas.count() > 0:
                        await boton_historicas.click()
                        await page.wait_for_timeout(2000)

                        # Las históricas continúan numeración después de actuales
                        indice_historicas = len(actuaciones_actuales) + 1

                        actuaciones_historicas = await self._extraer_actuaciones_tab(
                            page,
                            SEL_ACTUACIONES.TABLA_HISTORICAS_ID,
                            es_historica=True,
                            indice_inicial=indice_historicas,
                        )
                except Exception as e:
                    logger.warning(f"No se pudieron extraer actuaciones históricas: {e}")

                # Construir archivo
                timestamp = datetime.now().isoformat()
                expediente_datos = {
                    "numero": identificacion.numero,
                    "caratula": identificacion.caratula or "Sin carátula",
                    "dependencia": "No disponible",
                    "jurisdiccion": identificacion.jurisdiccion,
                    "situacion": "No disponible",
                }

                archivo = construir_actuaciones_archivo(
                    expediente_datos,
                    actuaciones_actuales,
                    actuaciones_historicas,
                    incluye_historicas=len(actuaciones_historicas) > 0,
                    timestamp_generacion=timestamp,
                )

                logger.info(
                    f"Extracción completada: {len(actuaciones_actuales)} actuales, {len(actuaciones_historicas)} históricas"
                )
                return archivo

        except Exception as e:
            logger.exception("Error durante extracción de actuaciones")
            raise ExtraccionError(f"Fallo en extracción de actuaciones: {e}") from e

    async def descargar_archivo_actuacion(
        self,
        actuacion: "Actuacion",
        destino: Path,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> Path:
        """Descarga el archivo adjunto de una actuación.

        Args:
            actuacion: Actuación que contiene el archivo
            destino: Ruta donde guardar el archivo
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Path del archivo descargado

        Raises:
            ExtraccionError: Si la actuación no tiene archivo o falla la descarga
        """
        from infrastructure.exceptions import ExtraccionError

        if not actuacion.tiene_archivo:
            raise ExtraccionError(
                f"La actuación {actuacion.secuencia} no tiene archivo adjunto"
            )

        if not actuacion.onclick:
            raise ExtraccionError(
                f"La actuación {actuacion.secuencia} no tiene atributo onclick para descarga"
            )

        try:
            usuario, contraseña = (
                credenciales
                if credenciales
                else (self._settings.auth.usuario, self._settings.auth.password)
            )

            async with obtener_sesion_autenticada(
                usuario=usuario,
                contraseña=contraseña,
                session_file=self._session_file,
                headless=headless,
                login_url=self._login_url,
                settings=self._settings,
            ) as page:
                # Navegar al expediente que contiene la actuación
                # Esto es simplificado - en producción necesitaría el número de expediente
                logger.info(
                    f"Descargando archivo de actuación {actuacion.secuencia}: {actuacion.nombre_archivo}"
                )

                # Configurar descarga
                async with page.expect_download() as download_info:
                    # Ejecutar el onclick de la actuación
                    await page.evaluate(actuacion.onclick)

                download = await download_info.value

                # Guardar archivo en destino
                await download.save_as(destino)

                logger.info(f"Archivo descargado exitosamente: {destino}")
                return destino

        except Exception as e:
            logger.exception("Error durante descarga de archivo")
            raise ExtraccionError(f"Fallo en descarga de archivo: {e}") from e

    async def _navegar_a_expediente(self, page: Page, numero: str) -> None:
        """Navega al expediente especificado desde la lista.

        Args:
            page: Página de Playwright
            numero: Número del expediente a abrir
        """
        # Ir a inicio
        await page.goto(f"{self._login_url}/inicio")
        await page.wait_for_load_state("domcontentloaded")

        # Buscar expediente en la tabla
        await page.wait_for_selector(SEL_EXPEDIENTES.TABLA_RESULTADOS, timeout=30000)

        # Buscar link del expediente
        # Esto es simplificado - en producción necesitaría buscar en múltiples páginas
        enlace = page.locator(f"a:has-text('{numero}')").first
        await enlace.click()
        await page.wait_for_load_state("domcontentloaded")

    async def _extraer_actuaciones_tab(
        self,
        page: Page,
        tabla_id: str,
        es_historica: bool,
        indice_inicial: int = 1,
    ) -> list:
        """Extrae actuaciones de una tab (actuales o históricas) con paginación.

        Para actuaciones históricas, implementa loop de paginación para extraer
        TODAS las páginas disponibles. Para actuaciones actuales (sin paginación),
        extrae solo la página visible.

        Args:
            page: Página de Playwright
            tabla_id: ID de la tabla a extraer (sin #), ej: 'expediente:action-historic-table'
            es_historica: Si son actuaciones históricas (usa paginación)
            indice_inicial: Índice inicial para numerar actuaciones (default: 1)

        Returns:
            Lista de actuaciones extraídas (puede abarcar múltiples páginas si es histórica)

        Note:
            Solo las actuaciones históricas tienen paginación. Las actuales se
            muestran en una sola página.
        """
        from core.domain.entities import Actuacion
        from .selectores import escapar_id_jsf_para_css

        actuaciones: list[Actuacion] = []
        timestamp = datetime.now().isoformat()

        # Detectar mensaje "no posee actuaciones históricas" (solo para históricas)
        if es_historica:
            mensaje = await page.query_selector(SEL_ACTUACIONES.MENSAJE_SIN_HISTORICAS)
            if mensaje:
                texto_mensaje = await mensaje.inner_text()
                if texto_mensaje and "no posee actuaciones históricas" in texto_mensaje.lower():
                    logger.info("✅ El expediente no posee actuaciones históricas")
                    return []

        # Selector de tabla con escape JSF
        tabla_selector_css = escapar_id_jsf_para_css(f"#{tabla_id}")
        filas_selector = f"{tabla_selector_css} tbody tr"

        # Esperar tabla
        try:
            await page.wait_for_selector(tabla_selector_css, timeout=10000)
        except TimeoutError:
            logger.warning(f"⚠️ No se encontró tabla {tabla_id}")
            return []

        # Variables para paginación
        pagina = 1
        indice_actual = indice_inicial

        # LOOP DE PAGINACIÓN (solo para históricas)
        while True:
            if es_historica:
                logger.info(f"📄 Página {pagina} (históricas): extrayendo...")
            else:
                logger.debug(f"📄 Extrayendo actuaciones actuales (sin paginación)...")

            # Obtener filas de la página actual
            filas = await page.query_selector_all(filas_selector)

            if not filas:
                if es_historica:
                    logger.warning(f"⚠️ No se encontraron filas en página {pagina} de actuaciones históricas")
                break

            # Procesar filas de la página actual
            for fila in filas:
                try:
                    actuacion = await parse_actuacion_row(
                        page,
                        fila,
                        indice=indice_actual,
                        timestamp_extraccion=timestamp,
                        es_historica=es_historica,
                    )

                    if actuacion:
                        actuaciones.append(actuacion)
                        indice_actual += 1

                except Exception as e:
                    logger.warning(f"⚠️ Error parseando actuación {indice_actual}: {e}")
                    indice_actual += 1
                    continue

            # Si no es histórica, no hay paginación - terminar
            if not es_historica:
                break

            # --- PAGINACIÓN: Buscar botón "Siguiente" ---

            # Selector para botón siguiente (PrimeFaces)
            # Buscar botón con texto "Siguiente" que NO esté deshabilitado
            boton_siguiente = await page.query_selector(
                f"a[id^='{tabla_id}:j_idt']:not(.ui-state-disabled):has-text('Siguiente')"
            )

            if boton_siguiente:
                try:
                    # Guardar fingerprint antes de navegar
                    html_anterior = await page.inner_html(tabla_selector_css)

                    # Obtener paginador activo antes de click
                    paginador_selector_js, pagina_activa = await self._obtener_paginador_activo(
                        page, tabla_id
                    )

                    # Click en botón "Siguiente"
                    await boton_siguiente.click()
                    pagina += 1

                    # Esperar a que aparezcan las filas nuevamente
                    await page.wait_for_selector(filas_selector, timeout=8000)

                    # Esperar cambio de página (usa ambas estrategias)
                    await self._esperar_cambio_pagina(
                        page,
                        tabla_id,
                        html_anterior,
                        paginador_selector_js,
                        pagina_activa,
                    )

                    # Continuar con siguiente iteración del loop

                except TimeoutError as e:
                    logger.error(f"❌ Timeout esperando cambio de página {pagina}: {e}")
                    break

                except Exception as e:
                    logger.error(f"❌ No se pudo avanzar a página {pagina}: {e}")
                    break
            else:
                # No hay botón siguiente - fin de paginación
                logger.info(f"✅ No hay más páginas históricas (total: {pagina} páginas)")
                break

        logger.info(f"✅ Extraídas {len(actuaciones)} actuaciones ({'históricas' if es_historica else 'actuales'})")
        return actuaciones

    async def _obtener_paginador_activo(
        self,
        page: Page,
        tabla_id: str
    ) -> tuple[str | None, str | None]:
        """Obtiene el selector y número de página activo de un datatable PrimeFaces.

        Busca el elemento con clase .ui-state-active en el paginador de la tabla.
        Retorna el selector JavaScript y el número de página visible.

        Args:
            page: Página de Playwright
            tabla_id: ID de la tabla (sin #), ej: 'expediente:action-historic-table'

        Returns:
            tuple[selector_js, numero_pagina]:
                - selector_js: Selector JavaScript para el elemento activo
                - numero_pagina: Texto del número de página (ej: "2")
                - Ambos None si no se encuentra paginador

        Example:
            >>> selector, num = await self._obtener_paginador_activo(page, "expediente:action-historic-table")
            >>> print(f"Selector: {selector}, Página: {num}")
            Selector: #expediente\\:action-historic-table_paginator_bottom .ui-state-active, Página: 2
        """
        from .selectores import escapar_id_jsf_para_css, escapar_id_jsf_para_js

        # PrimeFaces puede tener paginador arriba (_paginator_top) o abajo (_paginator_bottom)
        sufijos = ("_paginator_bottom", "_paginator_top")

        for sufijo in sufijos:
            # Selector base para página activa
            selector_base = f"#{tabla_id}{sufijo} .ui-paginator-page.ui-state-active"

            # Escapar para CSS (Playwright query)
            selector_css = escapar_id_jsf_para_css(selector_base)

            # Buscar elemento
            elemento = await page.query_selector(selector_css)

            if elemento:
                # Obtener texto del número de página
                pagina_activa = (await elemento.inner_text() or "").strip()

                # Escapar para JavaScript (wait_for_function)
                selector_js = escapar_id_jsf_para_js(selector_base)

                logger.debug(f"Paginador encontrado: {selector_js} = página {pagina_activa}")
                return selector_js, pagina_activa

        logger.debug(f"No se encontró paginador para tabla {tabla_id}")
        return None, None

    async def _esperar_cambio_pagina(
        self,
        page: Page,
        tabla_id: str,
        html_anterior: str,
        paginador_selector_js: str | None,
        pagina_anterior: str | None,
    ) -> None:
        """Espera a que se actualice la tabla tras navegar a otra página.

        Usa dos estrategias para detectar el cambio:
        1. Espera cambio en número de página activo del paginador (más rápido)
        2. Espera cambio en HTML de la tabla (fallback)

        Args:
            page: Página de Playwright
            tabla_id: ID de la tabla (sin #), ej: 'expediente:action-historic-table'
            html_anterior: HTML de la tabla antes de navegar
            paginador_selector_js: Selector JS del número de página activo
            pagina_anterior: Número de página antes de navegar (ej: "2")

        Raises:
            TimeoutError: Si no cambia en 8 segundos

        Example:
            >>> html_anterior = await page.inner_html(f"#{tabla_id}")
            >>> selector_js, pagina = await self._obtener_paginador_activo(page, tabla_id)
            >>> await boton_siguiente.click()
            >>> await self._esperar_cambio_pagina(page, tabla_id, html_anterior, selector_js, pagina)
        """
        # Estrategia 1: Esperar cambio en paginador (más rápido)
        if paginador_selector_js and pagina_anterior:
            try:
                await page.wait_for_function(
                    r"""
                    ({ selector, paginaAnterior }) => {
                        const elemento = document.querySelector(selector);
                        return elemento && elemento.textContent.trim() !== paginaAnterior;
                    }
                    """,
                    arg={"selector": paginador_selector_js, "paginaAnterior": pagina_anterior},
                    timeout=8000,
                )
                logger.debug("✅ Cambio de página detectado vía paginador")
                return
            except TimeoutError:
                # Si el paginador no cambia, intentar con contenido de tabla
                logger.debug("⚠️ Paginador no cambió, verificando contenido de tabla")

        # Estrategia 2: Esperar cambio en HTML de tabla (fallback)
        await page.wait_for_function(
            r"""
            ({ tablaId, htmlPrevio }) => {
                const tabla = document.getElementById(tablaId);
                return tabla && tabla.innerHTML !== htmlPrevio;
            }
            """,
            arg={
                "tablaId": tabla_id,
                "htmlPrevio": html_anterior,
            },
            timeout=8000,
        )
        logger.debug("✅ Cambio de página detectado vía HTML de tabla")

    async def _calcular_fingerprint(
        self,
        locator,
        max_len: int = 4096
    ) -> str:
        """Calcula un fingerprint robusto del contenido de un locator.

        Usa longitud + HTML interno para detectar cambios de forma más
        confiable que solo el texto visible. Este enfoque detecta cambios
        en atributos, estructura HTML, y contenido oculto.

        Args:
            locator: Locator de Playwright
            max_len: Longitud máxima del fingerprint (default: 4096)

        Returns:
            str: Fingerprint en formato "{longitud}::{html_truncado}"

        Example:
            >>> fingerprint = await self._calcular_fingerprint(tbody_locator)
            >>> print(fingerprint)
            12450::<html content...>

        Note:
            Usar inner_html en lugar de inner_text permite detectar:
            - Cambios en atributos HTML (class, id, data-*, etc.)
            - Elementos ocultos con display:none o visibility:hidden
            - Cambios en la estructura del DOM
        """
        try:
            # Usar inner_HTML en lugar de inner_text para mayor sensibilidad
            html = await locator.inner_html()

            # Formato: longitud + :: + contenido HTML
            signature = f"{len(html)}::{html}"

            # Truncar si excede max_len
            if max_len is not None and len(signature) > max_len:
                signature = signature[:max_len]

            return signature

        except Exception as e:
            logger.debug(f"Error calculando fingerprint: {e}")
            return ""


__all__ = ["PlaywrightScraperAdapter"]
