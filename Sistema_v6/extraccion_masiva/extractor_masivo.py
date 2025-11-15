"""
Extractor Masivo - Obtiene listado completo de expedientes del PJN.

Reutiliza la lógica probada de Sistema_v4 con interfaz simplificada.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from uuid import uuid4

from playwright.async_api import Page, async_playwright

# Definición de motivos exitosos vs errores
# EXITOSOS: La extracción terminó correctamente (llegó al final o alcanzó límite configurado)
MOTIVOS_EXITOSOS = {
    "fin_listado",              # Final natural del paginado
    "limite_paginas",           # Alcanzó max_paginas configurado
    "limite_fecha",             # Superó fecha_corte configurada
    "duplicado_encontrado",     # Detectó expediente repetido (con detener_en_duplicado=True)
    "limite_tiempo",            # Superó tiempo_maximo_segundos
    "sin_siguiente",            # No existe control para pasar de página (llegó al final)
    "sin_siguiente_habilitado", # No hay botón "Siguiente" habilitado (llegó al final)
}

# ERRORES: La extracción falló por problemas técnicos
# - "siguiente_timeout": el botón "Siguiente" no apareció a tiempo
# - "siguiente_deshabilitado": el botón se deshabilitó al intentar usarlo
# - "error_click": falló el clic en "Siguiente"
# - "bucle_detectado": se detectó un ciclo al intentar avanzar

# Delays progresivos para reintentos (segundos)
DELAYS_REINTENTOS = [5, 10, 20]

from Sistema_v4.operaciones.expedientes.expedientes_v4 import (
    extraer_expedientes_completos,
)
from .models import (
    ExpedienteListado,
    ConfigExtraccionMasiva,
    ResumenExtraccion,
    SesionExtraccion,
    ComparacionDetallada,
    CambioSituacion,
    CambioUltimaActuacion,
    CambioDependencia,
)


class ExtractorMasivo:
    """
    Extractor masivo de expedientes del PJN.

    Flujo:
    1. Navega al portal PJN con credenciales
    2. Extrae listado completo (todas las páginas)
    3. Guarda JSON con metadata básica
    4. Retorna sesión con path al archivo
    """

    def __init__(
        self,
        config: Optional[ConfigExtraccionMasiva] = None,
        data_dir: str = "./Sistema_v6/data/extraccion_masiva/listados"
    ):
        """
        Args:
            config: Configuración de extracción (headless, timeouts, etc.)
            data_dir: Directorio donde guardar los listados extraídos
        """
        self.config = config or ConfigExtraccionMasiva()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def extraer_listado_completo(
        self,
        username: str,
        password: str,
        fecha_corte: Optional[str] = None,
        sesion: Optional[SesionExtraccion] = None,
        callback_progreso: Optional[callable] = None,
    ) -> SesionExtraccion:
        """
        Extrae el listado completo de expedientes del PJN.

        Args:
            username: Usuario PJN
            password: Contraseña PJN
            fecha_corte: Fecha mínima (YYYY-MM-DD) para detener extracción
            sesion: Sesión existente a actualizar (opcional, se crea una nueva si no se provee)
            callback_progreso: Función a llamar para reportar progreso (opcional)

        Returns:
            SesionExtraccion con información de la extracción y path al JSON
        """
        if sesion is None:
            session_id = str(uuid4())
            tiempo_inicio = datetime.now().isoformat()
            sesion = SesionExtraccion(
                session_id=session_id,
                estado="iniciando",
                fase="listado",
                tiempo_inicio=tiempo_inicio,
                config=self.config.to_dict(),
                mensaje="Iniciando navegador...",
                intentos_maximos=self.config.max_reintentos
            )
        else:
            session_id = sesion.session_id
            # Asegurar que intentos_maximos esté configurado
            if sesion.intentos_maximos == 0:
                sesion.intentos_maximos = self.config.max_reintentos

        try:
            async with async_playwright() as p:
                # Iniciar navegador
                browser = await p.chromium.launch(
                    headless=self.config.headless
                )
                context = await browser.new_context()
                page = await context.new_page()
                page.set_default_timeout(self.config.timeout_pagina)

                # Login en PJN
                sesion.mensaje = "Autenticando en PJN..."
                if callback_progreso:
                    callback_progreso(sesion)
                await self._login_pjn(page, username, password)

                # Navegar a listado de expedientes
                sesion.mensaje = "Navegando a listado de expedientes..."
                if callback_progreso:
                    callback_progreso(sesion)
                await self._navegar_a_listado(page)

                # Intentar obtener el total esperado del PJN
                try:
                    from Sistema_v4.operaciones.expedientes.expedientes_v4 import _extraer_total_esperado, EXPEDIENTES_POR_PAGINA
                    total_esperado = await _extraer_total_esperado(page)
                    if total_esperado and isinstance(total_esperado, int):
                        # Calcular páginas esperadas (15 expedientes por página por defecto en PJN)
                        import math
                        paginas_esperadas = math.ceil(total_esperado / EXPEDIENTES_POR_PAGINA)
                        sesion.progreso_total = paginas_esperadas
                        print(f"\n📊 El PJN reporta {total_esperado:,} expedientes disponibles (~{paginas_esperadas} páginas)\n")
                        if callback_progreso:
                            callback_progreso(sesion)
                except Exception as e:
                    print(f"⚠️ No se pudo obtener total esperado: {e}")

                # Extraer todas las páginas
                sesion.estado = "extrayendo"
                sesion.progreso_actual = 0
                # progreso_total ya puede estar configurado si se obtuvo total_esperado
                sesion.mensaje = "Extrayendo expedientes de todas las páginas..."
                if callback_progreso:
                    callback_progreso(sesion)

                # Preparar monitoreo de progreso
                import re
                import sys
                from io import StringIO

                # Capturar stdout para monitorear progreso
                old_stdout = sys.stdout

                class ProgressCapture:
                    def __init__(self, original_stdout, callback, sesion_obj):
                        self.original = original_stdout
                        self.callback = callback
                        self.sesion = sesion_obj
                        self._processing = False  # Flag para evitar recursión

                    def write(self, text):
                        self.original.write(text)  # Mantener output original
                        self.original.flush()

                        # Evitar recursión infinita
                        if self._processing:
                            return

                        # Detectar "Procesando página X"
                        match = re.search(r'Procesando página (\d+)', text)
                        if match:
                            self._processing = True  # Activar flag
                            try:
                                pagina_actual = int(match.group(1))
                                self.sesion.progreso_actual = pagina_actual
                                self.sesion.mensaje = f"Procesando página {pagina_actual}"
                                if self.callback:
                                    self.callback(self.sesion)
                            finally:
                                self._processing = False  # Desactivar flag

                    def flush(self):
                        self.original.flush()

                # LOOP DE REINTENTOS
                motivo = None
                expedientes_raw = None
                metadata = None
                exito = False

                while sesion.intentos_realizados < sesion.intentos_maximos and not exito:
                    sesion.intentos_realizados += 1
                    print(f"\n{'='*60}")
                    print(f"🔄 Intento {sesion.intentos_realizados}/{sesion.intentos_maximos}")
                    print(f"{'='*60}\n")

                    try:
                        # Activar captura de progreso
                        sys.stdout = ProgressCapture(old_stdout, callback_progreso, sesion)

                        # Extraer expedientes con monitoreo de progreso
                        expedientes_raw, motivo, metadata = await extraer_expedientes_completos(
                            page,
                            fecha_corte=fecha_corte,
                            tiempo_maximo_segundos=self.config.tiempo_maximo_segundos,
                            orden="fecha",  # Ordenar por fecha para facilitar comparación
                            detener_en_duplicado=self.config.detener_en_duplicado,
                            omitir_duplicados=self.config.omitir_duplicados,
                            max_paginas=self.config.max_paginas,
                        )

                        # Restaurar stdout
                        sys.stdout = old_stdout

                        # Actualizar progreso_total si tenemos paginas_esperadas en metadata
                        if metadata and "paginas_esperadas" in metadata:
                            sesion.progreso_total = metadata["paginas_esperadas"]
                            if callback_progreso:
                                callback_progreso(sesion)

                        # Registrar intento en historial
                        sesion.historial_intentos.append({
                            "intento": sesion.intentos_realizados,
                            "timestamp": datetime.now().isoformat(),
                            "motivo": motivo,
                            "total_expedientes": len(expedientes_raw) if expedientes_raw else 0,
                            "metadata": metadata
                        })

                        # Verificar si el motivo es exitoso
                        if motivo in MOTIVOS_EXITOSOS:
                            print(f"\n✅ Extracción exitosa: {motivo}")
                            exito = True
                        else:
                            print(f"\n❌ Error en extracción: {motivo}")
                            # Si quedan intentos, esperar y reintentar
                            if sesion.intentos_realizados < sesion.intentos_maximos:
                                delay_idx = sesion.intentos_realizados - 1
                                delay = DELAYS_REINTENTOS[min(delay_idx, len(DELAYS_REINTENTOS) - 1)]
                                print(f"⏳ Esperando {delay}s antes de reintentar...")
                                sesion.mensaje = f"Error: {motivo}. Reintentando en {delay}s..."
                                if callback_progreso:
                                    callback_progreso(sesion)
                                await asyncio.sleep(delay)
                                # Volver a navegar al listado para reintentar
                                await self._navegar_a_listado(page)
                            else:
                                # Agotados los reintentos
                                print(f"\n🚫 Reintentos agotados. Último motivo: {motivo}")
                                sesion.estado = "error_agotado"

                    except Exception as e_intento:
                        # Restaurar stdout en caso de error
                        sys.stdout = old_stdout

                        # Determinar tipo de error con mejor precisión
                        error_str = str(e_intento).lower()
                        error_type = type(e_intento).__name__

                        if any(keyword in error_str for keyword in ['target closed', 'browser', 'context closed', 'connection closed']):
                            motivo = "navegador_cerrado"
                            print(f"\n❌ El navegador se cerró inesperadamente durante intento {sesion.intentos_realizados}")
                        elif error_type == 'TimeoutError' or 'timeout' in error_str:
                            motivo = "timeout_conexion"
                            print(f"\n❌ Timeout de conexión durante intento {sesion.intentos_realizados}")
                            print(f"   Detalles: {e_intento}")
                        else:
                            motivo = "error_desconocido"
                            print(f"\n❌ Error durante intento {sesion.intentos_realizados}")
                            print(f"   Tipo: {error_type}")
                            print(f"   Mensaje: {e_intento}")

                        # Registrar error en historial
                        sesion.historial_intentos.append({
                            "intento": sesion.intentos_realizados,
                            "timestamp": datetime.now().isoformat(),
                            "motivo": motivo,
                            "error": str(e_intento),
                            "total_expedientes": 0
                        })

                        # Si el navegador se cerró, no tiene sentido reintentar
                        if motivo == "navegador_cerrado":
                            print(f"\n🚫 No se puede reintentar con navegador cerrado")
                            sesion.estado = "error_agotado"
                            sesion.mensaje = "El navegador se cerró inesperadamente"
                            sesion.motivo_finalizacion = "navegador_cerrado"
                            if callback_progreso:
                                callback_progreso(sesion)
                            raise Exception("Navegador cerrado - no se puede continuar")

                        # Si quedan intentos, esperar y reintentar
                        if sesion.intentos_realizados < sesion.intentos_maximos:
                            delay_idx = sesion.intentos_realizados - 1
                            delay = DELAYS_REINTENTOS[min(delay_idx, len(DELAYS_REINTENTOS) - 1)]
                            print(f"⏳ Esperando {delay}s antes de reintentar...")
                            sesion.mensaje = f"Error: {motivo}. Reintentando en {delay}s..."
                            if callback_progreso:
                                callback_progreso(sesion)
                            await asyncio.sleep(delay)
                            # Volver a navegar al listado para reintentar
                            try:
                                await self._navegar_a_listado(page)
                            except Exception as nav_error:
                                print(f"⚠️ Error al renavegar: {nav_error}")
                                # Si no puede navegar, probablemente el navegador está muerto
                                if 'closed' in str(nav_error).lower():
                                    print(f"🚫 Navegador no disponible - abortando")
                                    sesion.estado = "error_agotado"
                                    raise
                        else:
                            # Agotados los reintentos
                            print(f"\n🚫 Reintentos agotados. Último error: {e_intento}")
                            sesion.estado = "error_agotado"
                            raise

                # Verificar si se agotaron los reintentos sin éxito
                if sesion.estado == "error_agotado":
                    sesion.tiempo_fin = datetime.now().isoformat()
                    sesion.mensaje = f"❌ Extracción fallida tras {sesion.intentos_realizados} intentos. Último motivo: {motivo}"
                    sesion.motivo_finalizacion = motivo
                    if callback_progreso:
                        callback_progreso(sesion)
                    raise Exception(f"Extracción fallida tras {sesion.intentos_realizados} intentos: {motivo}")

                # Convertir a ExpedienteListado
                expedientes = [
                    ExpedienteListado(
                        numero=exp.get("numero", ""),
                        caratula=exp.get("caratula", ""),
                        dependencia=exp.get("dependencia", ""),
                        situacion=exp.get("situacion", ""),
                        fecha_inicio=exp.get("fecha_inicio", ""),
                        ultima_actuacion=exp.get("ultima_actuacion", ""),
                    )
                    for exp in expedientes_raw
                ]

                # Agregar motivo de finalización al metadata
                metadata["motivo_finalizacion"] = motivo
                print(f"📊 Motivo de finalización: {motivo}")

                # Guardar JSON
                listado_path = self._guardar_listado(
                    session_id, expedientes, metadata
                )

                # Actualizar BASE permanente
                try:
                    base_path = self.actualizar_base_permanente(str(listado_path))
                    print(f"✅ BASE permanente actualizado: {base_path}")
                except Exception as e:
                    print(f"⚠️ Error actualizando BASE (no crítico): {e}")

                # Comparar con BASE si existe
                try:
                    comparacion = self.comparar_con_base(str(listado_path))
                    if comparacion:
                        sesion.comparacion = comparacion.to_dict()
                except Exception as e:
                    print(f"⚠️ Error en comparación (no crítico): {e}")

                # Guardar página count antes de sobrescribir
                paginas_procesadas = sesion.progreso_actual

                # Actualizar sesión
                print(f"\n{'='*60}")
                print(f"✅ FINALIZANDO EXTRACCIÓN")
                print(f"   Total expedientes: {len(expedientes)}")
                print(f"   Motivo: {motivo}")
                print(f"   Estableciendo estado = 'completado'")
                print(f"{'='*60}\n")
                sesion.estado = "completado"
                sesion.fase = "listado"
                sesion.tiempo_fin = datetime.now().isoformat()
                sesion.paginas_procesadas = paginas_procesadas  # Total de páginas procesadas
                sesion.progreso_actual = len(expedientes)
                sesion.progreso_total = len(expedientes)
                sesion.listado_path = str(listado_path)
                sesion.metadata = metadata  # Incluye total_esperado, paginas_esperadas, etc.

                # Generar mensaje descriptivo según el motivo
                mensaje_motivo = self._describir_motivo(motivo, metadata)

                # Construir mensaje con información de total_esperado si está disponible
                total_esperado = metadata.get("total_esperado")
                if total_esperado:
                    porcentaje = (len(expedientes) / total_esperado * 100) if total_esperado > 0 else 0
                    completitud = f"{len(expedientes)}/{total_esperado} ({porcentaje:.1f}%)"
                    sesion.mensaje = f"✅ Extracción completada: {completitud} expedientes. {mensaje_motivo}"
                else:
                    sesion.mensaje = f"✅ Extracción completada: {len(expedientes)} expedientes extraídos. {mensaje_motivo}"

                sesion.motivo_finalizacion = mensaje_motivo  # Guardar motivo descriptivo para el frontend

                if callback_progreso:
                    print(f"📡 Llamando callback_progreso con estado = '{sesion.estado}'")
                    callback_progreso(sesion)
                    print(f"✓ Callback ejecutado correctamente")
                else:
                    print(f"⚠️ No hay callback_progreso configurado")

                print(f"✅ Retornando sesión con estado = '{sesion.estado}'")
                return sesion

        except Exception as e:
            sesion.estado = "error"
            sesion.tiempo_fin = datetime.now().isoformat()
            sesion.mensaje = f"Error en extracción: {str(e)}"
            if callback_progreso:
                callback_progreso(sesion)
            raise

    async def _login_pjn(self, page: Page, username: str, password: str):
        """Realiza login en el portal PJN."""
        # URL correcta del portal PJN
        url_login = "https://portalpjn.pjn.gov.ar/inicio"

        await page.goto(url_login)
        await page.wait_for_load_state("domcontentloaded")

        # Completar formulario de login con selectores correctos
        await page.fill("input[name='username']", username)
        await page.fill("input[name='password']", password)

        # Click en botón de login
        await page.click("#kc-login")

        # Esperar confirmación de login exitoso
        await page.wait_for_selector("text='Menú'", timeout=60000)
        print("✅ Login exitoso en PJN")

    async def _navegar_a_listado(self, page: Page):
        """Navega a la página de listado de expedientes."""
        # URL correcta del sistema de consultas del PJN
        url_consultas = "https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam"

        await page.goto(url_consultas)
        await page.wait_for_load_state("networkidle")

        # Esperar que aparezca la tabla de expedientes con el selector correcto
        try:
            await page.wait_for_selector("table.table-striped", timeout=30000)
            print("✅ Tabla de expedientes encontrada")
        except Exception as e:
            print(f"⚠️ No se encontró tabla de expedientes: {e}")
            raise

    def _guardar_listado(
        self,
        session_id: str,
        expedientes: List[ExpedienteListado],
        metadata: Dict,
    ) -> Path:
        """
        Guarda el listado extraído en JSON.

        Formato:
        {
            "session_id": "...",
            "timestamp": "...",
            "total": 2000,
            "metadata": {...},
            "expedientes": [...]
        }
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"listado_{timestamp}_{session_id[:8]}.json"
        filepath = self.data_dir / filename

        data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "total": len(expedientes),
            "metadata": metadata,
            "expedientes": [exp.to_dict() for exp in expedientes],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def cargar_listado(self, listado_path: str) -> Dict:
        """Carga un listado previamente guardado."""
        with open(listado_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def comparar_con_base(
        self,
        listado_nuevo_path: str,
        listado_base_path: Optional[str] = None
    ) -> Optional[ComparacionDetallada]:
        """
        Compara un listado nuevo con el BASE y detecta cambios detallados.

        Cambios detectados:
        - Nuevos expedientes
        - Expedientes eliminados
        - Cambios en situación
        - Cambios en última actuación
        - Cambios en dependencia

        Args:
            listado_nuevo_path: Ruta al listado nuevo
            listado_base_path: Ruta al BASE (si None, busca automáticamente)

        Returns:
            ComparacionDetallada con todos los cambios detectados
        """
        # Auto-buscar BASE si no se proporciona
        if listado_base_path is None:
            # Buscar listado_base.json primero
            base_permanente = self.data_dir / "listado_base.json"
            if base_permanente.exists():
                listado_base_path = str(base_permanente)
            else:
                # Fallback: buscar segundo archivo más reciente
                archivos = sorted(self.data_dir.glob("listado_*.json"), reverse=True)
                if len(archivos) < 2:
                    print("⚠️ No hay BASE para comparar (primera extracción)")
                    return None
                listado_base_path = str(archivos[1])

        print(f"📊 Comparando con BASE: {listado_base_path}")

        # Cargar ambos listados
        try:
            with open(listado_base_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
            with open(listado_nuevo_path, 'r', encoding='utf-8') as f:
                nuevo_data = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando archivos para comparación: {e}")
            return None

        # Convertir a diccionarios indexados por número
        base_dict = {
            exp["numero"]: exp
            for exp in base_data.get("expedientes", [])
        }
        nuevo_dict = {
            exp["numero"]: exp
            for exp in nuevo_data.get("expedientes", [])
        }

        # Conjuntos de números
        numeros_base = set(base_dict.keys())
        numeros_nuevo = set(nuevo_dict.keys())

        # 1. NUEVOS
        nuevos_numeros = numeros_nuevo - numeros_base
        nuevos = [
            ExpedienteListado(**nuevo_dict[num])
            for num in nuevos_numeros
        ]

        # 2. ELIMINADOS
        eliminados_numeros = numeros_base - numeros_nuevo
        eliminados = [
            ExpedienteListado(**base_dict[num])
            for num in eliminados_numeros
        ]

        # 3. COMUNES (para detectar cambios)
        comunes = numeros_base & numeros_nuevo

        cambios_situacion = []
        cambios_ultima_actuacion = []
        cambios_dependencia = []

        for numero in comunes:
            exp_base = base_dict[numero]
            exp_nuevo = nuevo_dict[numero]

            # Detectar cambio en SITUACION
            if exp_base.get("situacion") != exp_nuevo.get("situacion"):
                cambios_situacion.append(CambioSituacion(
                    numero=numero,
                    caratula=exp_nuevo.get("caratula", ""),
                    situacion_anterior=exp_base.get("situacion", ""),
                    situacion_nueva=exp_nuevo.get("situacion", "")
                ))

            # Detectar cambio en ULTIMA_ACTUACION
            if exp_base.get("ultima_actuacion") != exp_nuevo.get("ultima_actuacion"):
                cambios_ultima_actuacion.append(CambioUltimaActuacion(
                    numero=numero,
                    caratula=exp_nuevo.get("caratula", ""),
                    ultima_actuacion_anterior=exp_base.get("ultima_actuacion", ""),
                    ultima_actuacion_nueva=exp_nuevo.get("ultima_actuacion", "")
                ))

            # Detectar cambio en DEPENDENCIA
            if exp_base.get("dependencia") != exp_nuevo.get("dependencia"):
                cambios_dependencia.append(CambioDependencia(
                    numero=numero,
                    caratula=exp_nuevo.get("caratula", ""),
                    dependencia_anterior=exp_base.get("dependencia", ""),
                    dependencia_nueva=exp_nuevo.get("dependencia", "")
                ))

        total_cambios = (
            len(nuevos) +
            len(eliminados) +
            len(cambios_situacion) +
            len(cambios_ultima_actuacion) +
            len(cambios_dependencia)
        )

        comparacion = ComparacionDetallada(
            nuevos=nuevos,
            eliminados=eliminados,
            cambios_situacion=cambios_situacion,
            cambios_ultima_actuacion=cambios_ultima_actuacion,
            cambios_dependencia=cambios_dependencia,
            total_cambios=total_cambios
        )

        print(f"✅ Comparación completada:")
        print(f"   📌 Nuevos: {len(nuevos)}")
        print(f"   📌 Eliminados: {len(eliminados)}")
        print(f"   📌 Cambios situación: {len(cambios_situacion)}")
        print(f"   📌 Cambios última actuación: {len(cambios_ultima_actuacion)}")
        print(f"   📌 Cambios dependencia: {len(cambios_dependencia)}")

        return comparacion

    def _describir_motivo(self, motivo: str, metadata: Dict) -> str:
        """
        Convierte el código de motivo técnico en un mensaje descriptivo para el usuario.

        Args:
            motivo: Código del motivo de finalización
            metadata: Metadatos con información adicional

        Returns:
            Mensaje descriptivo para mostrar al usuario
        """
        paginas = metadata.get("paginas_recorridas", metadata.get("paginas_procesadas", "?"))

        descripciones = {
            # EXITOSOS
            "fin_listado": f"📄 Se procesaron todas las páginas disponibles ({paginas} páginas).",
            "limite_paginas": f"📄 Se alcanzó el límite de páginas configurado ({paginas} páginas).",
            "limite_tiempo": f"⏱️ Se alcanzó el tiempo máximo de extracción ({paginas} páginas procesadas).",
            "duplicado_encontrado": f"🔄 Se encontraron expedientes duplicados y se detuvo la extracción ({paginas} páginas).",
            "limite_fecha": f"📅 Se alcanzó la fecha de corte configurada ({paginas} páginas procesadas).",
            "sin_siguiente": f"✅ Se llegó al final del listado - no hay más páginas ({paginas} páginas).",
            "sin_siguiente_habilitado": f"✅ Se llegó al final del listado - última página alcanzada ({paginas} páginas).",
            # ERRORES
            "bucle_detectado": f"🔁 Se detectó un bucle en la paginación y se detuvo ({paginas} páginas).",
            "siguiente_timeout": f"⏱️ Timeout esperando botón 'Siguiente' ({paginas} páginas procesadas).",
            "siguiente_deshabilitado": f"⚠️ El botón 'Siguiente' se deshabilitó inesperadamente ({paginas} páginas).",
            "error_click": f"❌ Error al hacer clic en botón 'Siguiente' ({paginas} páginas).",
        }

        return descripciones.get(motivo, f"ℹ️ Finalizado: {motivo} ({paginas} páginas)")

    def actualizar_base_permanente(
        self,
        listado_nuevo_path: str
    ) -> str:
        """
        Actualiza el JSON BASE permanente con los datos del listado nuevo.

        Estrategia de Merge:
        1. Si no existe listado_base.json → crearlo con el nuevo listado
        2. Si existe:
           - AGREGAR expedientes nuevos
           - ACTUALIZAR expedientes existentes (situación, última actuación, etc.)
           - NUNCA ELIMINAR expedientes

        Args:
            listado_nuevo_path: Ruta al listado recién extraído

        Returns:
            Ruta al listado_base.json actualizado
        """
        base_path = self.data_dir / "listado_base.json"

        # Cargar listado nuevo
        try:
            with open(listado_nuevo_path, 'r', encoding='utf-8') as f:
                nuevo_data = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando listado nuevo: {e}")
            raise

        # Si no existe BASE, crearlo
        if not base_path.exists():
            print(f"📝 Creando BASE permanente por primera vez...")
            with open(base_path, 'w', encoding='utf-8') as f:
                json.dump(nuevo_data, f, ensure_ascii=False, indent=2)
            print(f"✅ BASE creado: {base_path}")
            return str(base_path)

        # Cargar BASE existente
        try:
            with open(base_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
        except Exception as e:
            print(f"❌ Error cargando BASE existente: {e}")
            raise

        # Convertir a diccionarios indexados por número
        base_dict = {
            exp["numero"]: exp
            for exp in base_data.get("expedientes", [])
        }
        nuevo_dict = {
            exp["numero"]: exp
            for exp in nuevo_data.get("expedientes", [])
        }

        # Contadores
        agregados = 0
        actualizados = 0

        # MERGE: Agregar nuevos + Actualizar existentes
        for numero, exp_nuevo in nuevo_dict.items():
            if numero not in base_dict:
                # AGREGAR nuevo
                base_dict[numero] = exp_nuevo
                agregados += 1
            else:
                # ACTUALIZAR existente (solo si hay cambios)
                exp_base = base_dict[numero]
                cambio = False

                # Comparar cada campo y actualizar si cambió
                for campo in ["situacion", "ultima_actuacion", "dependencia", "caratula", "fecha_inicio"]:
                    if exp_base.get(campo) != exp_nuevo.get(campo):
                        exp_base[campo] = exp_nuevo.get(campo)
                        cambio = True

                if cambio:
                    actualizados += 1

        # Guardar BASE actualizado
        base_data["expedientes"] = list(base_dict.values())
        base_data["metadata"] = {
            "total": len(base_dict),
            "ultima_actualizacion": datetime.now().isoformat(),
            "total_agregados_ultima_vez": agregados,
            "total_actualizados_ultima_vez": actualizados
        }

        with open(base_path, 'w', encoding='utf-8') as f:
            json.dump(base_data, f, ensure_ascii=False, indent=2)

        print(f"✅ BASE actualizado:")
        print(f"   📌 Total en BASE: {len(base_dict)}")
        print(f"   📌 Agregados: {agregados}")
        print(f"   📌 Actualizados: {actualizados}")

        return str(base_path)
