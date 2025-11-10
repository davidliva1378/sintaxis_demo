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
    ) -> SesionExtraccion:
        """
        Extrae el listado completo de expedientes del PJN.

        Args:
            username: Usuario PJN
            password: Contraseña PJN
            fecha_corte: Fecha mínima (YYYY-MM-DD) para detener extracción

        Returns:
            SesionExtraccion con información de la extracción y path al JSON
        """
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
                await self._login_pjn(page, username, password)

                # Navegar a listado de expedientes
                sesion.mensaje = "Navegando a listado de expedientes..."
                await self._navegar_a_listado(page)

                # Extraer todas las páginas
                sesion.estado = "extrayendo"
                sesion.mensaje = "Extrayendo expedientes de todas las páginas..."

                expedientes_raw, motivo, metadata = await extraer_expedientes_completos(
                    page,
                    fecha_corte=fecha_corte,
                    tiempo_maximo_segundos=None,  # Sin límite de tiempo
                    orden="fecha",  # Ordenar por fecha para facilitar comparación
                )

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

                # Actualizar sesión
                sesion.estado = "completado"
                sesion.fase = "listado"
                sesion.tiempo_fin = datetime.now().isoformat()
                sesion.progreso_actual = len(expedientes)
                sesion.progreso_total = len(expedientes)
                sesion.listado_path = str(listado_path)
                sesion.mensaje = f"Extracción completada: {len(expedientes)} expedientes. Motivo: {motivo}"

                return sesion

        except Exception as e:
            sesion.estado = "error"
            sesion.tiempo_fin = datetime.now().isoformat()
            sesion.mensaje = f"Error en extracción: {str(e)}"
            raise

    async def _login_pjn(self, page: Page, username: str, password: str):
        """Realiza login en el portal PJN."""
        # URL del portal PJN Neuquén
        url_login = "https://jnqn.jusneuquen.gov.ar/portalCiudadanoNeuquen/login.seam"

        await page.goto(url_login)
        await page.wait_for_load_state("networkidle")

        # Completar formulario de login
        await page.fill("input[name*='username'], input[id*='username']", username)
        await page.fill("input[name*='password'], input[id*='password']", password)

        # Click en botón de login
        await page.click("button[type='submit'], input[type='submit']")
        await page.wait_for_load_state("networkidle")

    async def _navegar_a_listado(self, page: Page):
        """Navega a la página de listado de expedientes."""
        # Esta URL puede variar según el portal - ajustar según sea necesario
        url_listado = "https://jnqn.jusneuquen.gov.ar/portalCiudadanoNeuquen/private/listaExpedientes.seam"

        await page.goto(url_listado)
        await page.wait_for_load_state("networkidle")

        # Esperar que aparezca la tabla
        await page.wait_for_selector("table.table-striped", timeout=30000)

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
