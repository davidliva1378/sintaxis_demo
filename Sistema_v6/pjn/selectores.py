"""Selectores CSS centralizados del portal PJN - Sistema v5.

IMPORTANTE: Este módulo es el único punto de verdad para selectores.
Si el sitio PJN cambia, actualizar SOLO AQUÍ.

Última actualización: 2025-10-15
Portal PJN versión: Material UI (nueva interfaz)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class AutenticacionSelectores:
    """Selectores para login en Keycloak."""

    # Inputs del formulario
    USUARIO: ClassVar[str] = "input[name='username']"
    PASSWORD: ClassVar[str] = "input[name='password']"
    BOTON_LOGIN: ClassVar[str] = "#kc-login"

    # Verificación de sesión
    CONFIRMACION_LOGIN: ClassVar[str] = "text='Menú'"


@dataclass(frozen=True)
class EntradasSelectores:
    """Selectores para bandeja de entradas/notificaciones (Material UI)."""

    # Tabla virtualizada
    TABLA: ClassVar[str] = "div.MuiTableContainer-root tr"
    FILAS: ClassVar[str] = "div.MuiTableContainer-root tr"

    # Campos de cada entrada
    EXPEDIENTE_NUMERO: ClassVar[str] = (
        "p.MuiTypography-root.MuiTypography-body1.w-full.css-7t4nkx"
    )
    EXPEDIENTE_CARATULA: ClassVar[str] = (
        "p.MuiTypography-root.MuiTypography-body1.w-full.italic.css-s43c20"
    )
    FECHA_ELEMENTO: ClassVar[str] = "p.MuiTypography-root.MuiTypography-body2.css-diq46q"
    CELDAS_FILA: ClassVar[str] = "td"

    # Scroll infinito
    CONTENEDOR_SCROLL: ClassVar[str] = "#LayoutScrollingContainer"

    # Indicadores de tipo de evento
    ELEMENTOS_CON_ARIA: ClassVar[str] = "[aria-label]"
    AVATAR_LETRA: ClassVar[str] = ".MuiAvatar-root p"

    # Mensajes del sistema (para locators, no CSS directo)
    TEXTO_FIN_EVENTOS: ClassVar[str] = "No hay m[aá]s eventos"
    TEXTO_CARGANDO: ClassVar[str] = "Cargando m[aá]s eventos"


@dataclass(frozen=True)
class ExpedientesSelectores:
    """Selectores para búsqueda y listado de expedientes."""

    # Búsqueda
    PANEL_BUSQUEDA_LINK: ClassVar[str] = "a[href='#collapseOne']"
    PANEL_BUSQUEDA_EXPANDIDO: ClassVar[str] = "#collapseOne.collapse.in"

    # Tabla de resultados
    TABLA_RESULTADOS: ClassVar[str] = "table.table-striped"
    FILAS_RESULTADOS: ClassVar[str] = "table.table-striped tbody tr"
    COLUMNAS_FILA: ClassVar[str] = "td"
    ENLACE_EXPEDIENTE: ClassVar[str] = "a"  # Dentro de fila

    # Detalle del expediente abierto (IDs JSF - frágiles)
    # Última actualización: 2025-11-18
    # Cambio: j_idt96 → j_idt99 (el PJN regeneró los IDs JSF)
    NUMERO_DETALLE: ClassVar[str] = "span[style='color:#000000;']"
    CARATULA_DETALLE: ClassVar[str] = r"#expediente\:j_idt99\:detailCover"
    DEPENDENCIA_DETALLE: ClassVar[str] = r"#expediente\:j_idt99\:detailDependencia"
    JURISDICCION_DETALLE: ClassVar[str] = r"#expediente\:j_idt99\:detailCamera"
    SITUACION_DETALLE: ClassVar[str] = r"#expediente\:j_idt99\:detailSituation"

    # Mensajes
    MENSAJE_SIN_RESULTADOS: ClassVar[str] = "text=No se han encontrado expedientes"


@dataclass(frozen=True)
class ActuacionesSelectores:
    """Selectores para actuaciones actuales e históricas (PrimeFaces)."""

    # Tabla de actuaciones ACTUALES
    TABLA_ACTUALES_ID: ClassVar[str] = "expediente:action-table"
    TABLA_ACTUALES: ClassVar[str] = "#expediente\\:action-table"
    FILAS_ACTUALES: ClassVar[str] = "#expediente\\:action-table tbody tr"

    # Tabla de actuaciones HISTÓRICAS
    TABLA_HISTORICAS_ID: ClassVar[str] = "expediente:action-historic-table"
    TABLA_HISTORICAS: ClassVar[str] = "#expediente\\:action-historic-table"
    FILAS_HISTORICAS: ClassVar[str] = "#expediente\\:action-historic-table tbody tr"
    BOTON_VER_HISTORICAS: ClassVar[str] = "a:has-text('Ver históricas')"

    # Elementos comunes
    COLUMNAS_FILA: ClassVar[str] = "td"
    ICONO_DESCARGA: ClassVar[str] = "i.fa-download"

    # Paginación PrimeFaces
    BOTON_SIGUIENTE: ClassVar[str] = (
        "a:has(span[title='Siguiente']):not(.ui-state-disabled)"
    )
    PAGINA_ACTIVA_PATTERN: ClassVar[str] = ".ui-paginator-page.ui-state-active"

    # Mensajes
    MENSAJE_SIN_HISTORICAS: ClassVar[str] = "div.alert.white-panel"


# ========================================
# Instancias globales para fácil acceso
# ========================================

SEL_AUTH = AutenticacionSelectores()
SEL_ENTRADAS = EntradasSelectores()
SEL_EXPEDIENTES = ExpedientesSelectores()
SEL_ACTUACIONES = ActuacionesSelectores()


# ========================================
# Helpers: Escapar selectores JSF
# ========================================


def escapar_id_jsf_para_css(id_jsf: str) -> str:
    """Escapa dos puntos de IDs JSF para usar en CSS con querySelector.

    Los IDs JSF usan el formato 'formulario:componente:subcomponente'.
    Para usarlos en selectores CSS necesitan escaparse los dos puntos.

    NOTA: Esta función NO agrega el prefijo '#'. Si necesitas un selector
    completo con '#', agrégalo manualmente: f"#{escapar_id_jsf_para_css(id)}"

    Args:
        id_jsf: ID JSF sin formato (ej: 'expediente:action-table')

    Returns:
        ID escapado SIN '#' (ej: 'expediente\\:action-table')

    Example:
        >>> escapar_id_jsf_para_css("expediente:action-table")
        'expediente\\:action-table'
        >>> f"#{escapar_id_jsf_para_css('expediente:action-table')}"
        '#expediente\\:action-table'
    """
    return re.sub(r'(?<!\\\\):', r'\\:', id_jsf)


def escapar_id_jsf_para_js(id_jsf: str) -> str:
    """Escapa dos puntos de IDs JSF para usar en JavaScript/evaluate.

    Similar a escapar_id_jsf_para_css pero con escape doble para JS.

    Args:
        id_jsf: ID JSF sin formato

    Returns:
        ID escapado para JS (ej: 'expediente\\\\:action-table')

    Example:
        >>> escapar_id_jsf_para_js("expediente:action-table")
        'expediente\\\\:action-table'
    """
    return re.sub(r"(?<!\\\\):", r"\\\\:", id_jsf)


__all__ = [
    "AutenticacionSelectores",
    "EntradasSelectores",
    "ExpedientesSelectores",
    "ActuacionesSelectores",
    "SEL_AUTH",
    "SEL_ENTRADAS",
    "SEL_EXPEDIENTES",
    "SEL_ACTUACIONES",
    "escapar_id_jsf_para_css",
    "escapar_id_jsf_para_js",
]
