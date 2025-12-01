"""
Servicio de Tools para Asistente IA y MCP.

Proporciona 25+ herramientas para acceso programatico a datos
de expedientes judiciales del PJN.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from sqlalchemy import text
from infrastructure.persistence.database import MySQLSessionLocal

from infrastructure.adapters.repositories.json_actuacion_repository import JsonActuacionRepository
from application.services.monitoreo_service import MonitoreoService

logger = logging.getLogger(__name__)


# === Schemas de respuesta ===

class ExpedienteResumen(BaseModel):
    """Resumen de un expediente."""
    id: str
    numero: str
    caratula: str
    dependencia: str
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    total_actuaciones: int = 0
    ultima_actuacion: Optional[datetime] = None

class ActuacionResumen(BaseModel):
    """Resumen de una actuacion."""
    id: str
    expediente_numero: str
    fecha: datetime
    tipo: str
    titulo: str
    tiene_texto: bool = False
    utilidad: Optional[str] = None
    score_utilidad: Optional[float] = None

class VencimientoInfo(BaseModel):
    """Informacion de vencimiento."""
    id: str
    expediente: str
    descripcion: str
    fecha_vencimiento: datetime
    estado: str
    dias_restantes: int

class EntidadExtraida(BaseModel):
    """Entidad extraida por NER."""
    id: str
    tipo: str
    valor: str
    score: float
    expediente: str
    actuacion_id: Optional[str] = None

class EstadisticasSistema(BaseModel):
    """Estadisticas generales del sistema."""
    total_expedientes: int
    expedientes_activos: int
    total_actuaciones: int
    actuaciones_con_texto: int
    vencimientos_pendientes: int
    vencimientos_urgentes: int
    entidades_extraidas: int


class ToolsService:
    """
    Servicio de herramientas para acceso a datos judiciales.

    Proporciona 25+ tools organizadas en categorias:
    - Expedientes: consulta y busqueda
    - Actuaciones: listado y analisis
    - Vencimientos: plazos y alertas
    - Entidades: NER y personas
    - Estadisticas: metricas del sistema
    - Analisis: IA y duplicados
    """

    def __init__(self):
        """Inicializa el servicio de tools."""
        self._session = None

    def _get_session(self):
        """Obtiene sesion de base de datos MySQL."""
        if self._session is None:
            self._session = MySQLSessionLocal()
        return self._session

    def _execute_query(self, query: str, params: dict = None) -> List[Dict]:
        """Ejecuta query SQL y retorna resultados como lista de dicts."""
        session = self._get_session()
        try:
            result = session.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error ejecutando query: {e}")
            raise

    # ============================================================
    # CATEGORIA 1: EXPEDIENTES (6 tools)
    # ============================================================

    def contar_expedientes(
        self,
        estado: Optional[str] = None,
        dependencia: Optional[str] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Cuenta el total de expedientes con filtros opcionales.

        Args:
            estado: Filtrar por estado (activo, archivado, etc)
            dependencia: Filtrar por juzgado/dependencia
            desde: Fecha minima de creacion
            hasta: Fecha maxima de creacion

        Returns:
            Dict con total y desglose por estado
        """
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN estado_monitoreo = 'activo' THEN 1 ELSE 0 END) as activos,
                SUM(CASE WHEN estado_monitoreo = 'pausado' THEN 1 ELSE 0 END) as pausados,
                SUM(CASE WHEN estado_monitoreo = 'archivado' THEN 1 ELSE 0 END) as archivados
            FROM expedientes
            WHERE 1=1
        """
        params = {}

        if estado:
            query += " AND estado_monitoreo = :estado"
            params['estado'] = estado
        if dependencia:
            query += " AND dependencia LIKE :dependencia"
            params['dependencia'] = f"%{dependencia}%"
        if desde:
            query += " AND fecha_creacion >= :desde"
            params['desde'] = desde
        if hasta:
            query += " AND fecha_creacion <= :hasta"
            params['hasta'] = hasta

        result = self._execute_query(query, params)
        row = result[0] if result else {}

        return {
            "total": row.get('total', 0),
            "activos": row.get('activos', 0),
            "pausados": row.get('pausados', 0),
            "archivados": row.get('archivados', 0)
        }

    def listar_expedientes(
        self,
        estado: Optional[str] = "activo",
        dependencia: Optional[str] = None,
        prioridad: Optional[str] = None,
        limite: int = 20,
        offset: int = 0,
        orden: str = "fecha_ultima_extraccion DESC"
    ) -> List[Dict[str, Any]]:
        """
        Lista expedientes con paginacion y filtros.

        Args:
            estado: Filtrar por estado
            dependencia: Filtrar por juzgado
            prioridad: Filtrar por prioridad (alta, media, baja)
            limite: Maximo de resultados
            offset: Saltar N resultados
            orden: Ordenamiento (campo ASC/DESC)

        Returns:
            Lista de expedientes con resumen
        """
        # Validar orden para evitar SQL injection
        orden_valido = orden if orden in [
            "fecha_ultima_extraccion DESC", "fecha_ultima_extraccion ASC",
            "fecha_creacion DESC", "fecha_creacion ASC",
            "numero ASC", "numero DESC"
        ] else "fecha_ultima_extraccion DESC"

        query = f"""
            SELECT
                e.id, e.numero_normalizado as numero, e.caratula, e.dependencia,
                e.estado_monitoreo as estado, e.prioridad,
                e.fecha_creacion, e.fecha_ultima_extraccion,
                COUNT(a.id) as total_actuaciones,
                MAX(a.fecha) as ultima_actuacion
            FROM expedientes e
            LEFT JOIN actuaciones a ON a.expediente_id = e.id
            WHERE 1=1
        """
        params = {}

        if estado:
            query += " AND e.estado_monitoreo = :estado"
            params['estado'] = estado
        if dependencia:
            query += " AND e.dependencia LIKE :dependencia"
            params['dependencia'] = f"%{dependencia}%"
        if prioridad:
            query += " AND e.prioridad = :prioridad"
            params['prioridad'] = prioridad

        query += f" GROUP BY e.id ORDER BY {orden_valido} LIMIT :limite OFFSET :offset"
        params['limite'] = limite
        params['offset'] = offset

        return self._execute_query(query, params)

    def obtener_expediente(self, numero: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalle completo de un expediente por numero.

        Args:
            numero: Numero del expediente (ej: FPO-006767-2025)

        Returns:
            Dict con todos los datos del expediente o None
        """
        # Normalizar numero si es necesario
        try:
            numero_norm = normalizar_numero_expediente(numero)
        except:
            numero_norm = numero

        query = """
            SELECT
                e.*, e.numero_normalizado as numero,
                COUNT(DISTINCT a.id) as total_actuaciones,
                COUNT(DISTINCT v.id) as total_vencimientos,
                COUNT(DISTINCT ent.id) as total_entidades,
                MAX(a.fecha) as ultima_actuacion,
                MIN(CASE WHEN v.estado = 'pendiente' THEN v.fecha_vencimiento END) as proximo_vencimiento
            FROM expedientes e
            LEFT JOIN actuaciones a ON a.expediente_id = e.id
            LEFT JOIN vencimientos v ON v.expediente_id = e.id
            LEFT JOIN entidades_extraidas ent ON ent.expediente_numero = e.numero_normalizado
            WHERE e.numero_normalizado = :numero OR e.numero_normalizado LIKE :numero_like
            GROUP BY e.id
        """
        result = self._execute_query(query, {'numero': numero_norm, 'numero_like': f'%{numero_norm}%'})
        return result[0] if result else None

    def buscar_expedientes(
        self,
        texto: str,
        campos: List[str] = None,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Busca expedientes por texto en multiples campos.

        Args:
            texto: Texto a buscar
            campos: Campos donde buscar (default: numero, caratula)
            limite: Maximo de resultados

        Returns:
            Lista de expedientes que coinciden
        """
        if campos is None:
            campos = ['numero_normalizado', 'caratula']

        # Intentar normalizar el texto de búsqueda si parece un número de expediente
        try:
            texto_norm = normalizar_numero_expediente(texto)
        except:
            texto_norm = texto

        conditions = []
        params = {'limite': limite}

        for i, campo in enumerate(campos):
            if campo in ['numero_normalizado', 'numero_original', 'caratula', 'dependencia']:
                conditions.append(f"{campo} LIKE :texto_{i}")
                # Buscar tanto el texto original como el normalizado
                params[f'texto_{i}'] = f"%{texto_norm}%"

        if not conditions:
            return []

        query = f"""
            SELECT id, numero_normalizado as numero, caratula, dependencia, estado_monitoreo as estado
            FROM expedientes
            WHERE {' OR '.join(conditions)}
            ORDER BY fecha_ultima_extraccion DESC
            LIMIT :limite
        """

        return self._execute_query(query, params)

    def expedientes_por_dependencia(self, limite_por_dep: int = 5) -> List[Dict[str, Any]]:
        """
        Agrupa expedientes por dependencia/juzgado.

        Args:
            limite_por_dep: Maximo de expedientes por dependencia

        Returns:
            Lista agrupada por dependencia con conteos
        """
        query = """
            SELECT
                dependencia,
                COUNT(*) as total,
                SUM(CASE WHEN estado_monitoreo = 'activo' THEN 1 ELSE 0 END) as activos
            FROM expedientes
            GROUP BY dependencia
            ORDER BY total DESC
        """
        return self._execute_query(query)

    def expedientes_recientes(
        self,
        dias: int = 7,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene expedientes con actividad reciente.

        Args:
            dias: Dias hacia atras a considerar
            limite: Maximo de resultados

        Returns:
            Lista de expedientes con actuaciones recientes
        """
        fecha_limite = datetime.now() - timedelta(days=dias)

        query = """
            SELECT
                e.id, e.numero_normalizado, e.caratula, e.dependencia,
                MAX(a.fecha) as ultima_actuacion,
                COUNT(a.id) as actuaciones_periodo
            FROM expedientes e
            INNER JOIN actuaciones a ON a.expediente_id = e.id
            WHERE a.fecha >= :fecha_limite
            GROUP BY e.id
            ORDER BY ultima_actuacion DESC
            LIMIT :limite
        """

        return self._execute_query(query, {
            'fecha_limite': fecha_limite,
            'limite': limite
        })

    # ============================================================
    # CATEGORIA 2: ACTUACIONES (5 tools)
    # ============================================================

    def listar_actuaciones(
        self,
        expediente_numero: str,
        tipo: Optional[str] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista actuaciones de un expediente.

        Args:
            expediente_numero: Numero del expediente
            tipo: Filtrar por tipo de actuacion
            desde: Fecha minima
            hasta: Fecha maxima
            limite: Maximo de resultados

        Returns:
            Lista de actuaciones ordenadas por fecha
        """
        query = """
            SELECT
                a.id, a.fecha, a.tipo_ia as tipo, a.detalle as titulo,
                a.texto_extraido IS NOT NULL as tiene_texto,
                a.utilidad, a.score,
                NULL as firmantes
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE e.numero_normalizado = :numero
        """
        params = {'numero': expediente_numero, 'limite': limite}

        if tipo:
            query += " AND a.tipo_ia = :tipo"
            params['tipo'] = tipo
        if desde:
            query += " AND a.fecha >= :desde"
            params['desde'] = desde
        if hasta:
            query += " AND a.fecha <= :hasta"
            params['hasta'] = hasta

        query += " ORDER BY a.fecha DESC LIMIT :limite"

        return self._execute_query(query, params)

    def buscar_actuaciones(
        self,
        texto: str,
        expediente_numero: Optional[str] = None,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Busca actuaciones por texto en titulo o contenido.

        Args:
            texto: Texto a buscar
            expediente_numero: Limitar a un expediente
            limite: Maximo de resultados

        Returns:
            Lista de actuaciones que coinciden
        """
        query = """
            SELECT
                a.id, e.numero_normalizado as expediente, a.fecha, a.tipo_ia as tipo,
                a.detalle as titulo,
                CASE WHEN a.texto_extraido LIKE :texto THEN 'contenido' ELSE 'titulo' END as match_en
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE (a.detalle LIKE :texto OR a.texto_extraido LIKE :texto)
        """
        params = {'texto': f"%{texto}%", 'limite': limite}

        if expediente_numero:
            query += " AND e.numero_normalizado = :numero"
            params['numero'] = expediente_numero

        query += " ORDER BY a.fecha DESC LIMIT :limite"

        return self._execute_query(query, params)

    def actuaciones_por_tipo(
        self,
        expediente_numero: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Agrupa actuaciones por tipo.

        Args:
            expediente_numero: Limitar a un expediente (opcional)

        Returns:
            Lista de tipos con conteos
        """
        query = """
            SELECT
                a.tipo_ia as tipo,
                COUNT(*) as total,
                AVG(a.score) as utilidad_promedio
            FROM actuaciones a
        """
        params = {}

        if expediente_numero:
            query += """
                INNER JOIN expedientes e ON e.id = a.expediente_id
                WHERE e.numero_normalizado = :numero
            """
            params['numero'] = expediente_numero

        query += " GROUP BY a.tipo_ia ORDER BY total DESC"

        return self._execute_query(query, params)

    def actuaciones_con_texto(
        self,
        expediente_numero: str,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene actuaciones que tienen texto extraido de PDF.

        Args:
            expediente_numero: Numero del expediente
            limite: Maximo de resultados

        Returns:
            Lista de actuaciones con texto
        """
        query = """
            SELECT
                a.id, a.fecha, a.tipo_ia as tipo, a.detalle as titulo,
                LENGTH(a.texto_extraido) as longitud_texto,
                a.utilidad, a.score
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE e.numero_normalizado = :numero AND a.texto_extraido IS NOT NULL
            ORDER BY a.fecha DESC
            LIMIT :limite
        """

        return self._execute_query(query, {
            'numero': expediente_numero,
            'limite': limite
        })

    def obtener_texto_actuacion(self, actuacion_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el texto extraido de una actuacion.

        Args:
            actuacion_id: ID de la actuacion

        Returns:
            Dict con texto y metadata
        """
        query = """
            SELECT
                a.id, a.detalle as titulo, a.fecha, a.tipo_ia as tipo,
                a.texto_extraido as texto,
                NULL as firmantes, a.utilidad, a.score
            FROM actuaciones a
            WHERE a.id = :id
        """
        result = self._execute_query(query, {'id': actuacion_id})
        return result[0] if result else None

    # ============================================================
    # CATEGORIA 3: VENCIMIENTOS (5 tools)
    # ============================================================

    def vencimientos_pendientes(
        self,
        expediente_numero: Optional[str] = None,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista vencimientos pendientes (no vencidos ni cumplidos).

        Args:
            expediente_numero: Limitar a un expediente
            limite: Maximo de resultados

        Returns:
            Lista de vencimientos pendientes ordenados por fecha
        """
        query = """
            SELECT
                v.id, e.numero_normalizado as expediente, v.descripcion,
                v.fecha_vencimiento, v.estado,
                DATEDIFF(v.fecha_vencimiento, NOW()) as dias_restantes
            FROM vencimientos v
            INNER JOIN expedientes e ON e.id = v.expediente_id
            WHERE v.estado = 'pendiente'
        """
        params = {'limite': limite}

        if expediente_numero:
            query += " AND e.numero_normalizado = :numero"
            params['numero'] = expediente_numero

        query += " ORDER BY v.fecha_vencimiento ASC LIMIT :limite"

        return self._execute_query(query, params)

    def vencimientos_urgentes(
        self,
        dias: int = 7,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene vencimientos proximos a vencer.

        Args:
            dias: Dias hacia adelante a considerar
            limite: Maximo de resultados

        Returns:
            Lista de vencimientos urgentes
        """
        fecha_limite = datetime.now() + timedelta(days=dias)

        query = """
            SELECT
                v.id, e.numero_normalizado as expediente, v.descripcion,
                v.fecha_vencimiento,
                DATEDIFF(v.fecha_vencimiento, NOW()) as dias_restantes
            FROM vencimientos v
            INNER JOIN expedientes e ON e.id = v.expediente_id
            WHERE v.estado = 'pendiente'
              AND v.fecha_vencimiento <= :fecha_limite
              AND v.fecha_vencimiento >= NOW()
            ORDER BY v.fecha_vencimiento ASC
            LIMIT :limite
        """

        return self._execute_query(query, {
            'fecha_limite': fecha_limite,
            'limite': limite
        })

    def vencimientos_vencidos(
        self,
        expediente_numero: Optional[str] = None,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Lista vencimientos que ya pasaron su fecha.

        Args:
            expediente_numero: Limitar a un expediente
            limite: Maximo de resultados

        Returns:
            Lista de vencimientos vencidos
        """
        query = """
            SELECT
                v.id, e.numero_normalizado as expediente, v.descripcion,
                v.fecha_vencimiento,
                DATEDIFF(NOW(), v.fecha_vencimiento) as dias_vencido
            FROM vencimientos v
            INNER JOIN expedientes e ON e.id = v.expediente_id
            WHERE v.estado = 'pendiente' AND v.fecha_vencimiento < NOW()
        """
        params = {'limite': limite}

        if expediente_numero:
            query += " AND e.numero_normalizado = :numero"
            params['numero'] = expediente_numero

        query += " ORDER BY v.fecha_vencimiento DESC LIMIT :limite"

        return self._execute_query(query, params)

    def proximos_vencimientos(
        self,
        dias: int = 30,
        agrupar_por: str = "semana"
    ) -> List[Dict[str, Any]]:
        """
        Calendario de proximos vencimientos agrupados.

        Args:
            dias: Dias hacia adelante
            agrupar_por: Como agrupar (dia, semana, mes)

        Returns:
            Lista agrupada de vencimientos
        """
        fecha_limite = datetime.now() + timedelta(days=dias)

        if agrupar_por == "dia":
            grupo = "DATE(v.fecha_vencimiento)"
        elif agrupar_por == "mes":
            grupo = "DATE_FORMAT(v.fecha_vencimiento, '%Y-%m')"
        else:  # semana
            grupo = "YEARWEEK(v.fecha_vencimiento)"

        query = f"""
            SELECT
                {grupo} as periodo,
                COUNT(*) as total,
                GROUP_CONCAT(e.numero_normalizado) as expedientes
            FROM vencimientos v
            INNER JOIN expedientes e ON e.id = v.expediente_id
            WHERE v.estado = 'pendiente'
              AND v.fecha_vencimiento BETWEEN NOW() AND :fecha_limite
            GROUP BY {grupo}
            ORDER BY periodo ASC
        """

        return self._execute_query(query, {'fecha_limite': fecha_limite})

    def resumen_vencimientos(self) -> Dict[str, Any]:
        """
        Estadisticas generales de vencimientos.

        Returns:
            Dict con conteos por estado
        """
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'atendido' THEN 1 ELSE 0 END) as atendidos,
                SUM(CASE WHEN estado = 'vencido' THEN 1 ELSE 0 END) as vencidos,
                SUM(CASE WHEN estado = 'pendiente' AND fecha_vencimiento < NOW() THEN 1 ELSE 0 END) as atrasados,
                SUM(CASE WHEN estado = 'pendiente' AND fecha_vencimiento BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as urgentes_7dias
            FROM vencimientos
        """
        result = self._execute_query(query)
        return result[0] if result else {}

    # ============================================================
    # CATEGORIA 4: ENTIDADES NER (5 tools)
    # ============================================================

    def listar_entidades(
        self,
        expediente_numero: str,
        tipo: Optional[str] = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista entidades extraidas de un expediente.

        Args:
            expediente_numero: Numero del expediente
            tipo: Filtrar por tipo (PERSONA, ORGANIZACION, etc)
            limite: Maximo de resultados

        Returns:
            Lista de entidades con score
        """
        query = """
            SELECT
                ent.id, ent.entity_type as tipo, ent.entity_value as valor,
                ent.score as score, ent.actuacion_id
            FROM entidades_extraidas ent
            INNER JOIN expedientes e ON e.numero_normalizado = ent.expediente_numero
            WHERE e.numero_normalizado = :numero
        """
        params = {'numero': expediente_numero, 'limite': limite}

        if tipo:
            query += " AND ent.entity_type = :tipo"
            params['tipo'] = tipo

        query += " ORDER BY ent.score DESC LIMIT :limite"

        return self._execute_query(query, params)

    def buscar_entidades(
        self,
        valor: str,
        tipo: Optional[str] = None,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Busca entidades por valor en todos los expedientes.

        Args:
            valor: Texto a buscar
            tipo: Filtrar por tipo
            limite: Maximo de resultados

        Returns:
            Lista de entidades que coinciden
        """
        query = """
            SELECT
                ent.id, ent.entity_type as tipo, ent.entity_value as valor,
                ent.score as score,
                e.numero_normalizado as expediente
            FROM entidades_extraidas ent
            INNER JOIN expedientes e ON e.numero_normalizado = ent.expediente_numero
            WHERE ent.entity_value LIKE :valor
        """
        params = {'valor': f"%{valor}%", 'limite': limite}

        if tipo:
            query += " AND ent.entity_type = :tipo"
            params['tipo'] = tipo

        query += " ORDER BY ent.score DESC LIMIT :limite"

        return self._execute_query(query, params)

    def entidades_por_tipo(
        self,
        expediente_numero: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Agrupa entidades por tipo.

        Args:
            expediente_numero: Limitar a un expediente

        Returns:
            Lista de tipos con conteos
        """
        query = """
            SELECT
                ent.entity_type as tipo,
                COUNT(*) as total,
                AVG(ent.score) as score_promedio
            FROM entidades_extraidas ent
        """
        params = {}

        if expediente_numero:
            query += """
                INNER JOIN expedientes e ON e.numero_normalizado = ent.expediente_numero
                WHERE e.numero_normalizado = :numero
            """
            params['numero'] = expediente_numero

        query += " GROUP BY ent.entity_type ORDER BY total DESC"

        return self._execute_query(query, params)

    def estadisticas_entidades(self) -> Dict[str, Any]:
        """
        Estadisticas generales de entidades extraidas.

        Returns:
            Dict con conteos y metricas
        """
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT entity_type) as tipos_distintos,
                COUNT(DISTINCT expediente_numero) as expedientes_con_entidades,
                AVG(score) as score_promedio
            FROM entidades_extraidas
        """
        result = self._execute_query(query)
        return result[0] if result else {}

    def personas_expediente(
        self,
        expediente_numero: str,
        score_minimo: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Obtiene personas mencionadas en un expediente.

        Args:
            expediente_numero: Numero del expediente
            score_minimo: Score minimo de confianza

        Returns:
            Lista de personas con roles inferidos
        """
        query = """
            SELECT
                ent.entity_value as nombre,
                ent.entity_type as tipo,
                AVG(ent.score) as score,
                COUNT(*) as menciones
            FROM entidades_extraidas ent
            INNER JOIN expedientes e ON e.numero_normalizado = ent.expediente_numero
            WHERE e.numero_normalizado = :numero
              AND ent.entity_type IN ('PERSONA', 'PER', 'ABOGADO', 'JUEZ', 'ACTOR', 'DEMANDADO')
              AND ent.score >= :score_minimo
            GROUP BY ent.entity_value, ent.entity_type
            ORDER BY menciones DESC, score DESC
        """

        return self._execute_query(query, {
            'numero': expediente_numero,
            'score_minimo': score_minimo
        })

    # ============================================================
    # CATEGORIA 5: ESTADISTICAS (4 tools)
    # ============================================================

    def estadisticas_sistema(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas generales del sistema.

        Returns:
            Dict con metricas globales
        """
        queries = {
            'expedientes': "SELECT COUNT(*) as total, SUM(CASE WHEN estado_monitoreo = 'activo' THEN 1 ELSE 0 END) as activos FROM expedientes",
            'actuaciones': "SELECT COUNT(*) as total, SUM(CASE WHEN texto_extraido IS NOT NULL THEN 1 ELSE 0 END) as con_texto FROM actuaciones",
            'vencimientos': "SELECT COUNT(*) as total, SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes FROM vencimientos",
            'entidades': "SELECT COUNT(*) as total FROM entidades_extraidas"
        }

        result = {}
        for key, query in queries.items():
            data = self._execute_query(query)
            if data:
                result[key] = data[0]

        return {
            "total_expedientes": result.get('expedientes', {}).get('total', 0),
            "expedientes_activos": result.get('expedientes', {}).get('activos', 0),
            "total_actuaciones": result.get('actuaciones', {}).get('total', 0),
            "actuaciones_con_texto": result.get('actuaciones', {}).get('con_texto', 0),
            "total_vencimientos": result.get('vencimientos', {}).get('total', 0),
            "vencimientos_pendientes": result.get('vencimientos', {}).get('pendientes', 0),
            "total_entidades": result.get('entidades', {}).get('total', 0)
        }

    def estadisticas_expediente(self, expediente_numero: str) -> Dict[str, Any]:
        """
        Obtiene estadisticas de un expediente especifico.

        Args:
            expediente_numero: Numero del expediente

        Returns:
            Dict con metricas del expediente
        """
        query = """
            SELECT
                e.numero_normalizado, e.caratula, e.estado_monitoreo,
                (SELECT COUNT(*) FROM actuaciones WHERE expediente_id = e.id) as total_actuaciones,
                (SELECT COUNT(*) FROM actuaciones WHERE expediente_id = e.id AND texto_extraido IS NOT NULL) as actuaciones_con_texto,
                (SELECT COUNT(*) FROM actuaciones WHERE expediente_id = e.id AND utilidad = 'alta') as actuaciones_alta,
                (SELECT COUNT(*) FROM actuaciones WHERE expediente_id = e.id AND utilidad = 'media') as actuaciones_media,
                (SELECT COUNT(*) FROM actuaciones WHERE expediente_id = e.id AND utilidad = 'baja') as actuaciones_baja,
                (SELECT COUNT(*) FROM vencimientos WHERE expediente_id = e.id) as total_vencimientos,
                (SELECT COUNT(*) FROM vencimientos WHERE expediente_id = e.id AND estado = 'pendiente') as vencimientos_pendientes,
                (SELECT COUNT(*) FROM entidades_extraidas WHERE expediente_numero = e.numero_normalizado) as total_entidades,
                (SELECT MIN(fecha) FROM actuaciones WHERE expediente_id = e.id) as primera_actuacion,
                (SELECT MAX(fecha) FROM actuaciones WHERE expediente_id = e.id) as ultima_actuacion
            FROM expedientes e
            WHERE e.numero_normalizado = :numero
        """
        result = self._execute_query(query, {'numero': expediente_numero})
        return result[0] if result else {}

    def estadisticas_procesamiento(self) -> Dict[str, Any]:
        """
        Estadisticas de procesamiento de IA.

        Returns:
            Dict con metricas de clasificacion y NER
        """
        query = """
            SELECT
                COUNT(*) as total_actuaciones,
                SUM(CASE WHEN tipo_ia IS NOT NULL THEN 1 ELSE 0 END) as clasificadas,
                SUM(CASE WHEN utilidad IS NOT NULL THEN 1 ELSE 0 END) as con_utilidad,
                AVG(score) as score_promedio
            FROM actuaciones
        """
        result = self._execute_query(query)

        # Contar entidades por tipo
        tipos_query = """
            SELECT entity_type, COUNT(*) as total
            FROM entidades_extraidas
            GROUP BY entity_type
            ORDER BY total DESC
            LIMIT 10
        """
        tipos = self._execute_query(tipos_query)

        base = result[0] if result else {}
        base['entidades_por_tipo'] = tipos
        return base

    def actividad_reciente(
        self,
        dias: int = 7,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Timeline de actividad reciente en el sistema.

        Args:
            dias: Dias hacia atras
            limite: Maximo de eventos

        Returns:
            Lista de eventos ordenados por fecha
        """
        fecha_limite = datetime.now() - timedelta(days=dias)

        query = """
            SELECT
                'actuacion' as tipo_evento,
                a.fecha as fecha,
                e.numero_normalizado as expediente,
                CONVERT(a.detalle USING utf8mb4) as descripcion
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE a.fecha >= :fecha_limite

            UNION ALL

            SELECT
                'vencimiento' as tipo_evento,
                v.fecha_vencimiento as fecha,
                e.numero_normalizado as expediente,
                CONVERT(v.descripcion USING utf8mb4) as descripcion
            FROM vencimientos v
            INNER JOIN expedientes e ON e.id = v.expediente_id
            WHERE v.fecha_vencimiento >= :fecha_limite
              AND v.fecha_vencimiento <= DATE_ADD(:fecha_limite, INTERVAL :dias DAY)

            ORDER BY fecha DESC
            LIMIT :limite
        """

        return self._execute_query(query, {
            'fecha_limite': fecha_limite,
            'dias': dias,
            'limite': limite
        })

    # ============================================================
    # CATEGORIA 6: ANALISIS (4 tools)
    # ============================================================

    def duplicados_detectados(
        self,
        expediente_numero: Optional[str] = None,
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Lista actuaciones marcadas como posibles duplicados.

        Args:
            expediente_numero: Limitar a un expediente
            limite: Maximo de resultados

        Returns:
            Lista de duplicados con scores
        """
        query = """
            SELECT
                a.id, e.numero_normalizado as expediente, a.fecha, a.detalle as titulo,
                a.es_duplicado_probable, NULL as duplicado_de_id,
                a.score as score_similitud
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE a.es_duplicado_probable = 1
        """
        params = {'limite': limite}

        if expediente_numero:
            query += " AND e.numero_normalizado = :numero"
            params['numero'] = expediente_numero

        query += " ORDER BY a.score DESC LIMIT :limite"

        return self._execute_query(query, params)

    def clasificacion_ia(
        self,
        expediente_numero: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene resultados de clasificacion IA de actuaciones.

        Args:
            expediente_numero: Numero del expediente

        Returns:
            Lista de actuaciones con clasificacion
        """
        query = """
            SELECT
                a.id, a.fecha, a.detalle as titulo,
                a.tipo_ia as tipo_clasificado,
                a.utilidad,
                a.score,
                a.justificacion_ia
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE e.numero_normalizado = :numero
              AND a.tipo_ia IS NOT NULL
            ORDER BY a.fecha DESC
        """

        return self._execute_query(query, {'numero': expediente_numero})

    def actuaciones_importantes(
        self,
        expediente_numero: Optional[str] = None,
        utilidad_minima: str = "alta",
        limite: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene actuaciones de alta utilidad.

        Args:
            expediente_numero: Limitar a un expediente
            utilidad_minima: Utilidad minima (alta, media)
            limite: Maximo de resultados

        Returns:
            Lista de actuaciones importantes
        """
        utilidades = ['alta'] if utilidad_minima == 'alta' else ['alta', 'media']

        # Crear placeholders para IN clause
        placeholders = ', '.join([f':util_{i}' for i in range(len(utilidades))])
        
        query = f"""
            SELECT
                a.id, e.numero_normalizado as expediente, a.fecha, a.tipo_ia as tipo,
                a.detalle as titulo, a.utilidad, a.score
            FROM actuaciones a
            INNER JOIN expedientes e ON e.id = a.expediente_id
            WHERE a.utilidad IN ({placeholders})
        """
        params = {f'util_{i}': util for i, util in enumerate(utilidades)}
        params['limite'] = limite

        if expediente_numero:
            query += " AND e.numero_normalizado = :numero"
            params['numero'] = expediente_numero

        query += " ORDER BY a.score DESC, a.fecha DESC LIMIT :limite"

        return self._execute_query(query, params)

    def resumen_expediente(
        self,
        expediente_numero: str,
        incluir_actuaciones: bool = True,
        incluir_vencimientos: bool = True,
        incluir_entidades: bool = True
    ) -> Dict[str, Any]:
        """
        Genera resumen completo de un expediente.

        Args:
            expediente_numero: Numero del expediente
            incluir_actuaciones: Incluir ultimas actuaciones
            incluir_vencimientos: Incluir vencimientos pendientes
            incluir_entidades: Incluir entidades principales

        Returns:
            Dict con resumen estructurado
        """
        # Datos basicos
        expediente = self.obtener_expediente(expediente_numero)
        if not expediente:
            return {"error": f"Expediente {expediente_numero} no encontrado"}

        resumen = {
            "expediente": expediente,
            "estadisticas": self.estadisticas_expediente(expediente_numero)
        }

        if incluir_actuaciones:
            resumen["ultimas_actuaciones"] = self.listar_actuaciones(
                expediente_numero, limite=5
            )
            resumen["actuaciones_importantes"] = self.actuaciones_importantes(
                expediente_numero, limite=5
            )

        if incluir_vencimientos:
            resumen["vencimientos_pendientes"] = self.vencimientos_pendientes(
                expediente_numero, limite=10
            )

        if incluir_entidades:
            resumen["personas"] = self.personas_expediente(expediente_numero)
            resumen["entidades_por_tipo"] = self.entidades_por_tipo(expediente_numero)

        return resumen

    # ============================================================
    # CATEGORIA 7: MONITOREO (8 tools)
    # ============================================================

    def _get_monitoreo_service(self) -> MonitoreoService:
        """Obtiene instancia del servicio de monitoreo."""
        return MonitoreoService()

    def estado_monitoreo(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema de monitoreo.

        Returns:
            Dict con estado del monitoreo (activo, ejecutando, etc)
        """
        service = self._get_monitoreo_service()
        usuario_id = 1  # Usuario por defecto

        config = service.obtener_configuracion(usuario_id)
        stats = service.obtener_estadisticas(usuario_id)

        return {
            "activo": config.get('activo', False),
            "frecuencia": config.get('frecuencia', 'desconocida'),
            "notificar_email": config.get('notificar_email', False),
            "notificar_sistema": config.get('notificar_sistema', True),
            "total_expedientes_monitoreados": stats.get('total_expedientes', 0),
            "expedientes_activos": stats.get('expedientes_activos', 0),
            "cambios_sin_leer": stats.get('cambios_sin_leer', 0),
            "ultima_ejecucion": stats.get('ultima_ejecucion'),
            "proxima_ejecucion": stats.get('proxima_ejecucion')
        }

    def listar_expedientes_monitoreados(
        self,
        solo_activos: bool = False,
        limite: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista los expedientes que están siendo monitoreados.

        Args:
            solo_activos: Solo mostrar expedientes con monitoreo activo
            limite: Máximo de resultados

        Returns:
            Lista de expedientes monitoreados
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        resultado = service.listar_expedientes(
            usuario_id=usuario_id,
            solo_activos=solo_activos,
            pagina=1,
            por_pagina=limite
        )

        return resultado.get('expedientes', [])

    def listar_cambios_monitoreo(
        self,
        solo_no_leidos: bool = False,
        tipo_cambio: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        limite: int = 50
    ) -> Dict[str, Any]:
        """
        Lista los cambios detectados por el monitoreo.

        Args:
            solo_no_leidos: Solo cambios no leídos
            tipo_cambio: Filtrar por tipo (nueva_actuacion, cambio_estado, etc)
            expediente_numero: Filtrar por expediente específico
            limite: Máximo de resultados

        Returns:
            Dict con cambios y total no leídos
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        resultado = service.listar_cambios(
            usuario_id=usuario_id,
            solo_no_leidos=solo_no_leidos,
            tipo_cambio=tipo_cambio,
            expediente_numero=expediente_numero,
            pagina=1,
            por_pagina=limite
        )

        return {
            "cambios": resultado.get('cambios', []),
            "total_no_leidos": resultado.get('total_no_leidos', 0)
        }

    def estadisticas_monitoreo(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de monitoreo.

        Returns:
            Dict con métricas de monitoreo
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        return service.obtener_estadisticas(usuario_id)



    def agregar_expediente_monitoreo(
        self,
        expediente_numero: str,
        prioridad: str = "media",
        notas: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega un expediente al sistema de monitoreo.

        Args:
            expediente_numero: Número del expediente a monitorear
            prioridad: Prioridad del monitoreo (baja, media, alta)
            notas: Notas adicionales

        Returns:
            Dict con expediente agregado
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        try:
            resultado = service.agregar_expediente(
                usuario_id=usuario_id,
                expediente_numero=expediente_numero,
                prioridad=prioridad,
                notas=notas
            )
            return {
                "success": True,
                "mensaje": f"Expediente {expediente_numero} agregado al monitoreo",
                "expediente": resultado
            }
        except ValueError as e:
            return {
                "success": False,
                "mensaje": str(e)
            }

    def pausar_expediente_monitoreo(self, expediente_numero: str) -> Dict[str, Any]:
        """
        Pausa el monitoreo de un expediente.

        Args:
            expediente_numero: Número del expediente

        Returns:
            Dict con resultado
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        resultado = service.pausar_expediente(usuario_id, expediente_numero)

        if resultado:
            return {
                "success": True,
                "mensaje": f"Monitoreo de {expediente_numero} pausado",
                "expediente": resultado
            }
        else:
            return {
                "success": False,
                "mensaje": f"Expediente {expediente_numero} no encontrado en monitoreo"
            }

    def reanudar_expediente_monitoreo(self, expediente_numero: str) -> Dict[str, Any]:
        """
        Reanuda el monitoreo de un expediente pausado.

        Args:
            expediente_numero: Número del expediente

        Returns:
            Dict con resultado
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        resultado = service.reanudar_expediente(usuario_id, expediente_numero)

        if resultado:
            return {
                "success": True,
                "mensaje": f"Monitoreo de {expediente_numero} reanudado",
                "expediente": resultado
            }
        else:
            return {
                "success": False,
                "mensaje": f"Expediente {expediente_numero} no encontrado en monitoreo"
            }

    def sincronizar_expedientes_monitoreo(self) -> Dict[str, Any]:
        """
        Sincroniza expedientes activos del sistema principal al monitoreo.

        Agrega automáticamente los expedientes con estado_monitoreo='activo'
        al sistema de monitoreo si no están ya presentes.

        Returns:
            Dict con estadísticas de sincronización
        """
        service = self._get_monitoreo_service()
        usuario_id = 1

        # Obtener expedientes activos del sistema principal
        query = """
            SELECT numero_normalizado, caratula, dependencia
            FROM expedientes
            WHERE estado_monitoreo = 'activo'
        """
        expedientes = self._execute_query(query)

        agregados = 0
        ya_existentes = 0
        errores = 0

        for exp in expedientes:
            numero = exp['numero_normalizado']
            try:
                # Verificar si ya está en monitoreo
                existente = service.obtener_expediente(usuario_id, numero)
                if existente:
                    ya_existentes += 1
                else:
                    # Agregar al monitoreo
                    service.agregar_expediente(
                        usuario_id=usuario_id,
                        expediente_numero=numero,
                        expediente_caratula=exp.get('caratula'),
                        expediente_dependencia=exp.get('dependencia'),
                        prioridad='media'
                    )
                    agregados += 1
            except Exception as e:
                errores += 1
                logger.error(f"Error sincronizando {numero}: {e}")

        return {
            "success": True,
            "mensaje": f"Sincronización completada",
            "agregados": agregados,
            "ya_existentes": ya_existentes,
            "errores": errores,
            "total_procesados": len(expedientes)
        }

    # ============================================================
    # UTILIDADES
    # ============================================================

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Retorna definiciones de todas las tools para function calling.

        Returns:
            Lista de definiciones en formato OpenAI
        """
        return [
            # Expedientes
            {
                "name": "contar_expedientes",
                "description": "Cuenta el total de expedientes con filtros opcionales",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {"type": "string", "description": "Estado: activo, pausado, archivado"},
                        "dependencia": {"type": "string", "description": "Juzgado/dependencia"},
                        "desde": {"type": "string", "format": "date", "description": "Fecha desde"},
                        "hasta": {"type": "string", "format": "date", "description": "Fecha hasta"}
                    }
                }
            },
            {
                "name": "listar_expedientes",
                "description": "Lista expedientes con paginacion y filtros",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {"type": "string"},
                        "dependencia": {"type": "string"},
                        "prioridad": {"type": "string", "enum": ["alta", "media", "baja"]},
                        "limite": {"type": "integer", "default": 20},
                        "offset": {"type": "integer", "default": 0}
                    }
                }
            },
            {
                "name": "obtener_expediente",
                "description": "Obtiene detalle completo de un expediente por numero",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "string", "description": "Numero del expediente (ej: FPO-006767-2025)"}
                    },
                    "required": ["numero"]
                }
            },
            {
                "name": "buscar_expedientes",
                "description": "Busca expedientes por texto en numero o caratula",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {"type": "string", "description": "Texto a buscar"},
                        "limite": {"type": "integer", "default": 20}
                    },
                    "required": ["texto"]
                }
            },
            {
                "name": "expedientes_recientes",
                "description": "Obtiene expedientes con actividad reciente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dias": {"type": "integer", "default": 7},
                        "limite": {"type": "integer", "default": 20}
                    }
                }
            },
            # Actuaciones
            {
                "name": "listar_actuaciones",
                "description": "Lista actuaciones de un expediente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string", "description": "Numero del expediente"},
                        "tipo": {"type": "string"},
                        "limite": {"type": "integer", "default": 50}
                    },
                    "required": ["expediente_numero"]
                }
            },
            {
                "name": "buscar_actuaciones",
                "description": "Busca actuaciones por texto en titulo o contenido",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texto": {"type": "string"},
                        "expediente_numero": {"type": "string"},
                        "limite": {"type": "integer", "default": 20}
                    },
                    "required": ["texto"]
                }
            },
            {
                "name": "obtener_texto_actuacion",
                "description": "Obtiene el texto extraido de una actuacion",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "actuacion_id": {"type": "string"}
                    },
                    "required": ["actuacion_id"]
                }
            },
            # Vencimientos
            {
                "name": "vencimientos_pendientes",
                "description": "Lista vencimientos pendientes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"},
                        "limite": {"type": "integer", "default": 50}
                    }
                }
            },
            {
                "name": "vencimientos_urgentes",
                "description": "Obtiene vencimientos proximos a vencer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dias": {"type": "integer", "default": 7},
                        "limite": {"type": "integer", "default": 20}
                    }
                }
            },
            {
                "name": "resumen_vencimientos",
                "description": "Estadisticas generales de vencimientos",
                "parameters": {"type": "object", "properties": {}}
            },
            # Entidades
            {
                "name": "listar_entidades",
                "description": "Lista entidades extraidas de un expediente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"},
                        "tipo": {"type": "string"},
                        "limite": {"type": "integer", "default": 100}
                    },
                    "required": ["expediente_numero"]
                }
            },
            {
                "name": "personas_expediente",
                "description": "Obtiene personas mencionadas en un expediente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"}
                    },
                    "required": ["expediente_numero"]
                }
            },
            # Estadisticas
            {
                "name": "estadisticas_sistema",
                "description": "Obtiene estadisticas generales del sistema",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "estadisticas_expediente",
                "description": "Obtiene estadisticas de un expediente especifico",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"}
                    },
                    "required": ["expediente_numero"]
                }
            },
            {
                "name": "actividad_reciente",
                "description": "Timeline de actividad reciente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dias": {"type": "integer", "default": 7},
                        "limite": {"type": "integer", "default": 50}
                    }
                }
            },
            # Analisis
            {
                "name": "actuaciones_importantes",
                "description": "Obtiene actuaciones de alta utilidad",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"},
                        "utilidad_minima": {"type": "string", "enum": ["alta", "media"]},
                        "limite": {"type": "integer", "default": 20}
                    }
                }
            },
            {
                "name": "resumen_expediente",
                "description": "Genera resumen completo de un expediente",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expediente_numero": {"type": "string"}
                    },
                    "required": ["expediente_numero"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Ejecuta una tool por nombre.

        Args:
            tool_name: Nombre de la tool
            params: Parametros de la tool

        Returns:
            Resultado de la tool
        """
        from core.domain.expediente_utils import normalizar_numero_expediente

        # Importar repositorio de expedientes para obtener expediente_id,
        tool_map = {
            # Expedientes
            "contar_expedientes": self.contar_expedientes,
            "listar_expedientes": self.listar_expedientes,
            "obtener_expediente": self.obtener_expediente,
            "buscar_expedientes": self.buscar_expedientes,
            "expedientes_por_dependencia": self.expedientes_por_dependencia,
            "expedientes_recientes": self.expedientes_recientes,
            # Actuaciones
            "listar_actuaciones": self.listar_actuaciones,
            "buscar_actuaciones": self.buscar_actuaciones,
            "actuaciones_por_tipo": self.actuaciones_por_tipo,
            "actuaciones_con_texto": self.actuaciones_con_texto,
            "obtener_texto_actuacion": self.obtener_texto_actuacion,
            # Vencimientos
            "vencimientos_pendientes": self.vencimientos_pendientes,
            "vencimientos_urgentes": self.vencimientos_urgentes,
            "vencimientos_vencidos": self.vencimientos_vencidos,
            "proximos_vencimientos": self.proximos_vencimientos,
            "resumen_vencimientos": self.resumen_vencimientos,
            # Entidades
            "listar_entidades": self.listar_entidades,
            "buscar_entidades": self.buscar_entidades,
            "entidades_por_tipo": self.entidades_por_tipo,
            "estadisticas_entidades": self.estadisticas_entidades,
            "personas_expediente": self.personas_expediente,
            # Estadisticas
            "estadisticas_sistema": self.estadisticas_sistema,
            "estadisticas_expediente": self.estadisticas_expediente,
            "estadisticas_procesamiento": self.estadisticas_procesamiento,
            "actividad_reciente": self.actividad_reciente,
            # Analisis
            "duplicados_detectados": self.duplicados_detectados,
            "clasificacion_ia": self.clasificacion_ia,
            "actuaciones_importantes": self.actuaciones_importantes,
            "resumen_expediente": self.resumen_expediente,
            # Monitoreo
            "estado_monitoreo": self.estado_monitoreo,
            "listar_expedientes_monitoreados": self.listar_expedientes_monitoreados,
            "listar_cambios_monitoreo": self.listar_cambios_monitoreo,
            "estadisticas_monitoreo": self.estadisticas_monitoreo,
            "sincronizar_expedientes_monitoreo": self.sincronizar_expedientes_monitoreo,
            "agregar_expediente_monitoreo": self.agregar_expediente_monitoreo,
            "pausar_expediente_monitoreo": self.pausar_expediente_monitoreo,
            "reanudar_expediente_monitoreo": self.reanudar_expediente_monitoreo,
        }

        if tool_name not in tool_map:
            raise ValueError(f"Tool '{tool_name}' no encontrada")

        return tool_map[tool_name](**params)
