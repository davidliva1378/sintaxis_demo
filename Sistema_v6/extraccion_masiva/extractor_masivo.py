"""
Extractor Masivo - Obtiene listado completo de expedientes del PJN.

Reutiliza la lógica probada de Sistema_v4 con interfaz simplificada.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from uuid import uuid4

from playwright.async_api import Page, async_playwright

from Sistema_v4.operaciones.expedientes.expedientes_v4 import (
    extraer_expedientes_completos,
)
from .models import (
    ExpedienteListado,
    ConfigExtraccionMasiva,
    ResumenExtraccion,
    SesionExtraccion,
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
                mensaje="Iniciando navegador..."
            )
        else:
            session_id = sesion.session_id

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

                # Extraer todas las páginas
                sesion.estado = "extrayendo"
                sesion.progreso_actual = 0
                sesion.progreso_total = 0
                sesion.mensaje = "Extrayendo expedientes de todas las páginas..."
                if callback_progreso:
                    callback_progreso(sesion)

                # Extraer expedientes con monitoreo de progreso
                # Usamos un wrapper para capturar el progreso de páginas procesadas
                import re
                import sys
                from io import StringIO

                # Capturar stdout para monitorear progreso
                old_stdout = sys.stdout
                captured_output = StringIO()

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

                sys.stdout = ProgressCapture(old_stdout, callback_progreso, sesion)

                try:
                    expedientes_raw, motivo, metadata = await extraer_expedientes_completos(
                        page,
                        fecha_corte=fecha_corte,
                        tiempo_maximo_segundos=None,  # Sin límite de tiempo
                        orden="fecha",  # Ordenar por fecha para facilitar comparación
                    )
                finally:
                    # Restaurar stdout original
                    sys.stdout = old_stdout

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

                # Guardar JSON
                listado_path = self._guardar_listado(
                    session_id, expedientes, metadata
                )

                # Cerrar navegador
                await browser.close()

                # Guardar página count antes de sobrescribir
                paginas_procesadas = sesion.progreso_actual

                # Actualizar sesión
                sesion.estado = "completado"
                sesion.fase = "listado"
                sesion.tiempo_fin = datetime.now().isoformat()
                sesion.paginas_procesadas = paginas_procesadas  # Total de páginas procesadas
                sesion.progreso_actual = len(expedientes)
                sesion.progreso_total = len(expedientes)
                sesion.listado_path = str(listado_path)
                sesion.mensaje = f"Extracción completada: {len(expedientes)} expedientes. Motivo: {motivo}"

                if callback_progreso:
                    callback_progreso(sesion)

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
    ) -> Optional[Dict]:
        """
        Compara listado nuevo con JSON BASE (si existe).

        Args:
            listado_nuevo_path: Path al listado recién extraído
            listado_base_path: Path al JSON BASE (si None, busca el más reciente)

        Returns:
            Dict con estadísticas de comparación o None si no hay BASE
        """
        # Si no se especifica BASE, buscar el más reciente
        if listado_base_path is None:
            archivos = sorted(self.data_dir.glob("listado_*.json"), reverse=True)
            # El primero es el actual, el segundo sería el BASE
            if len(archivos) < 2:
                return None
            listado_base_path = str(archivos[1])

        if not os.path.exists(listado_base_path):
            return None

        # Cargar ambos listados
        nuevo = self.cargar_listado(listado_nuevo_path)
        base = self.cargar_listado(listado_base_path)

        # Crear sets de números de expediente para comparación rápida
        numeros_nuevo = {exp["numero"] for exp in nuevo["expedientes"]}
        numeros_base = {exp["numero"] for exp in base["expedientes"]}

        # Calcular diferencias
        nuevos = numeros_nuevo - numeros_base
        eliminados = numeros_base - numeros_nuevo
        comunes = numeros_nuevo & numeros_base

        return {
            "total_nuevo": len(numeros_nuevo),
            "total_base": len(numeros_base),
            "nuevos": len(nuevos),
            "eliminados": len(eliminados),
            "comunes": len(comunes),
            "listado_base_path": listado_base_path,
            "expedientes_nuevos": list(nuevos),
            "expedientes_eliminados": list(eliminados),
        }
