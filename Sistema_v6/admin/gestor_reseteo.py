"""
Gestor de reseteo del sistema.

Proporciona funcionalidades para resetear el sistema con diferentes niveles de alcance,
gestionar backups y obtener estadísticas de uso.
"""

from __future__ import annotations

import json
import os
import shutil
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import mysql.connector
from mysql.connector import Error as MySQLError

logger = logging.getLogger(__name__)


class NivelReseteo(str, Enum):
    """Niveles de reseteo del sistema."""

    LISTADOS = "listados"           # ~5 MB - Solo listados temporales
    PDFS = "pdfs"                   # ~680 MB - PDFs de actuaciones
    EXPEDIENTES = "expedientes"     # ~695 MB - Todos los expedientes
    COMPLETO = "completo"           # ~700 MB - Todo excepto DB/config
    NUCLEAR = "nuclear"             # ~700 MB - Reset absoluto + DB


@dataclass
class EstadisticasSistema:
    """Estadísticas del sistema."""

    espacio_total_mb: float
    expedientes_procesados: int
    pdfs_descargados: int
    sesiones_activas: int
    desglose: Dict[str, float] = field(default_factory=dict)
    ultimo_backup: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "espacio_total_mb": round(self.espacio_total_mb, 2),
            "expedientes_procesados": self.expedientes_procesados,
            "pdfs_descargados": self.pdfs_descargados,
            "sesiones_activas": self.sesiones_activas,
            "desglose": {k: round(v, 2) for k, v in self.desglose.items()},
            "ultimo_backup": self.ultimo_backup
        }


@dataclass
class ResultadoReseteo:
    """Resultado de una operación de reseteo."""

    nivel: NivelReseteo
    archivos_eliminados: int
    espacio_liberado_mb: float
    backup_path: Optional[str]
    dry_run: bool
    timestamp: str
    detalles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nivel": self.nivel.value,
            "archivos_eliminados": self.archivos_eliminados,
            "espacio_liberado_mb": round(self.espacio_liberado_mb, 2),
            "backup_path": self.backup_path,
            "dry_run": self.dry_run,
            "timestamp": self.timestamp,
            "detalles": self.detalles
        }


class GestorReseteo:
    """Gestor de reseteo del sistema."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Inicializa el gestor de reseteo.

        Args:
            data_dir: Directorio base de datos. Si es None, usa ./Sistema_v6/data
        """
        if data_dir is None:
            # Detectar el directorio base del proyecto
            current = Path(__file__).resolve().parent  # Start from directory containing the file
            while current.parent != current:
                if current.name == "Sistema_v6":  # Check if THIS directory is Sistema_v6
                    data_dir = current / "data"
                    break
                current = current.parent
            else:
                # Fallback
                data_dir = Path(__file__).parent.parent / "data"

        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Directorios clave
        self.extraccion_masiva_dir = self.data_dir / "extraccion_masiva"
        self.expedientes_dir = self.data_dir / "expedientes"
        self.cache_dir = self.data_dir / "cache"
        self.logs_dir = self.data_dir / "logs"
        self.db_path = self.data_dir / "sistema.db"
        self.vector_store_dir = self.data_dir / "vector_store"
        self.bm25_index_dir = self.data_dir / "bm25_index"
        self.qdrant_dir = self.data_dir / "qdrant"

    def get_estadisticas_sistema(self) -> EstadisticasSistema:
        """
        Obtiene estadísticas del uso de espacio del sistema.

        Returns:
            EstadisticasSistema con información detallada
        """
        # Calcular tamaños
        extraccion_mb = self._get_dir_size_mb(self.extraccion_masiva_dir)
        expedientes_mb = self._get_dir_size_mb(self.expedientes_dir)
        cache_mb = self._get_dir_size_mb(self.cache_dir)
        logs_mb = self._get_dir_size_mb(self.logs_dir)

        # Contar expedientes procesados
        expedientes_count = 0
        if self.expedientes_dir.exists():
            expedientes_count = len([
                d for d in self.expedientes_dir.iterdir()
                if d.is_dir() and d.name.startswith("00")
            ])

        # Contar PDFs
        pdfs_count = 0
        if self.expedientes_dir.exists():
            pdfs_count = sum(1 for _ in self.expedientes_dir.rglob("*.pdf"))

        # Buscar último backup
        ultimo_backup = None
        if self.backup_dir.exists():
            backups = sorted(self.backup_dir.glob("backup_*"))
            if backups:
                ultimo_backup = backups[-1].name

        return EstadisticasSistema(
            espacio_total_mb=extraccion_mb + expedientes_mb + cache_mb + logs_mb,
            expedientes_procesados=expedientes_count,
            pdfs_descargados=pdfs_count,
            sesiones_activas=0,  # TODO: Implementar conteo de sesiones activas
            desglose={
                "extraccion_masiva_mb": extraccion_mb,
                "expedientes_mb": expedientes_mb,
                "cache_mb": cache_mb,
                "logs_mb": logs_mb
            },
            ultimo_backup=ultimo_backup
        )

    def _resetear_qdrant(self) -> Dict[str, Any]:
        """
        Resetea la colección de Qdrant.

        Returns:
            Dict con resultado de la operación
        """
        resultado = {
            "exito": False,
            "detalles": [],
            "error": None
        }

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
            
            # Usar configuración por defecto o variables de entorno
            host = os.getenv("QDRANT_HOST", "localhost")
            port = int(os.getenv("QDRANT_PORT", "6333"))
            
            client = QdrantClient(host=host, port=port)
            collection_name = "actuaciones"

            # Verificar si existe
            collections = client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if exists:
                client.delete_collection(collection_name)
                resultado["detalles"].append(f"Colección '{collection_name}' eliminada")
            
            # Recrear colección
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            resultado["detalles"].append(f"Colección '{collection_name}' recreada vacía")
            
            resultado["exito"] = True
            logger.info("Reset Qdrant completado exitosamente")

        except Exception as e:
            resultado["error"] = str(e)
            resultado["detalles"].append(f"Error Qdrant: {str(e)}")
            logger.error(f"Error reseteando Qdrant: {e}")

        return resultado

    def resetear(
        self,
        nivel: NivelReseteo,
        dry_run: bool = True,
        crear_backup: bool = True,
        incluir_procesamiento_mysql: bool = False
    ) -> ResultadoReseteo:
        """
        Resetea el sistema según el nivel especificado.

        Args:
            nivel: Nivel de reseteo a aplicar
            dry_run: Si es True, solo simula la operación sin eliminar
            crear_backup: Si es True, crea un backup antes de eliminar
            incluir_procesamiento_mysql: Si es True, limpia tablas MySQL de procesamiento
                                       (FORZADO a True para COMPLETO y NUCLEAR)

        Returns:
            ResultadoReseteo con información de la operación
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = None
        archivos_eliminados = 0
        espacio_liberado_mb = 0.0
        detalles = []

        # FORZAR limpieza de MySQL para niveles altos para evitar huérfanos
        if nivel in (NivelReseteo.COMPLETO, NivelReseteo.NUCLEAR):
            incluir_procesamiento_mysql = True
            if not dry_run:
                detalles.append("NOTA: Limpieza de MySQL forzada para evitar datos huérfanos")

        # Determinar qué eliminar según el nivel
        paths_a_eliminar = self._get_paths_por_nivel(nivel)

        # Calcular impacto
        for path in paths_a_eliminar:
            if path.exists():
                if path.is_file():
                    archivos_eliminados += 1
                    espacio_liberado_mb += path.stat().st_size / (1024 * 1024)
                else:
                    count, size = self._count_files_and_size(path)
                    archivos_eliminados += count
                    espacio_liberado_mb += size

        # Crear backup si no es dry-run y se solicita
        if not dry_run and crear_backup and archivos_eliminados > 0:
            backup_path = str(self.crear_backup(nivel, paths_a_eliminar))
            detalles.append(f"Backup creado en: {backup_path}")

        # Eliminar archivos/directorios
        if not dry_run:
            for path in paths_a_eliminar:
                if path.exists():
                    try:
                        if path.is_file():
                            path.unlink()
                            detalles.append(f"Eliminado archivo: {path.name}")
                        else:
                            # Eliminar contenido pero mantener directorio
                            for item in path.iterdir():
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item)
                            detalles.append(f"Limpiado directorio: {path.name}")
                    except Exception as e:
                        logger.error(f"Error eliminando {path}: {e}")
                        detalles.append(f"Error eliminando {path.name}: {str(e)}")

            # Limpiar datos MySQL de procesamiento si se solicita
            if incluir_procesamiento_mysql:
                mysql_resultado = self._limpiar_procesamiento_mysql(nivel)
                if mysql_resultado["exito"]:
                    detalles.append(f"Limpieza MySQL: {mysql_resultado['registros_eliminados']} registros eliminados")
                    detalles.extend(mysql_resultado["detalles"])
                else:
                    detalles.append(f"Error MySQL: {mysql_resultado['error']}")

            # Limpiar Qdrant si es nivel COMPLETO o NUCLEAR
            if nivel in (NivelReseteo.COMPLETO, NivelReseteo.NUCLEAR):
                qdrant_res = self._resetear_qdrant()
                if qdrant_res["exito"]:
                    detalles.extend(qdrant_res["detalles"])
                else:
                    detalles.append(f"Error Qdrant: {qdrant_res['error']}")

            # Log de la operación
            self._log_operacion(nivel, archivos_eliminados, espacio_liberado_mb, timestamp)
        else:
            detalles.append("Modo dry-run: No se eliminó nada")

            # Mostrar qué se eliminaría en MySQL si está activo
            if incluir_procesamiento_mysql:
                mysql_preview = self._preview_procesamiento_mysql(nivel)
                if mysql_preview["exito"]:
                    detalles.append(f"MySQL (simular): {mysql_preview['registros_a_eliminar']} registros a eliminar")
                    detalles.extend(mysql_preview["detalles"])
            
            # Mostrar aviso de Qdrant
            if nivel in (NivelReseteo.COMPLETO, NivelReseteo.NUCLEAR):
                detalles.append("Qdrant (simular): Se eliminaría y recrearía la colección 'actuaciones'")

        return ResultadoReseteo(
            nivel=nivel,
            archivos_eliminados=archivos_eliminados,
            espacio_liberado_mb=espacio_liberado_mb,
            backup_path=backup_path,
            dry_run=dry_run,
            timestamp=timestamp,
            detalles=detalles
        )

    def crear_backup(
        self,
        nivel: NivelReseteo,
        paths: List[Path]
    ) -> Path:
        """
        Crea un backup de los paths especificados.

        Args:
            nivel: Nivel de reseteo
            paths: Paths a respaldar

        Returns:
            Path del directorio de backup creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{nivel.value}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)

        # Crear manifest del backup
        manifest = {
            "nivel": nivel.value,
            "timestamp": timestamp,
            "paths": [str(p) for p in paths if p.exists()],
            "archivos_respaldados": 0
        }

        # Copiar archivos
        archivos_respaldados = 0
        for path in paths:
            if path.exists():
                try:
                    dest = backup_path / path.name
                    if path.is_file():
                        shutil.copy2(path, dest)
                        archivos_respaldados += 1
                    else:
                        shutil.copytree(path, dest, dirs_exist_ok=True)
                        archivos_respaldados += sum(1 for _ in dest.rglob("*") if _.is_file())
                except Exception as e:
                    logger.error(f"Error creando backup de {path}: {e}")

        manifest["archivos_respaldados"] = archivos_respaldados

        # Guardar manifest
        with open(backup_path / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Backup creado: {backup_path} ({archivos_respaldados} archivos)")
        return backup_path

    def listar_backups(self) -> List[Dict[str, Any]]:
        """
        Lista todos los backups disponibles.

        Returns:
            Lista de diccionarios con información de cada backup
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_dir in sorted(self.backup_dir.glob("backup_*"), reverse=True):
            manifest_path = backup_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)

                    # Calcular tamaño del backup
                    size_mb = self._get_dir_size_mb(backup_dir)

                    backups.append({
                        "id": backup_dir.name,
                        "nivel": manifest.get("nivel"),
                        "timestamp": manifest.get("timestamp"),
                        "archivos": manifest.get("archivos_respaldados", 0),
                        "size_mb": round(size_mb, 2)
                    })
                except Exception as e:
                    logger.error(f"Error leyendo manifest de {backup_dir}: {e}")

        return backups

    def restaurar_backup(self, backup_id: str) -> bool:
        """
        Restaura un backup específico.

        Args:
            backup_id: ID del backup a restaurar

        Returns:
            True si se restauró correctamente, False en caso contrario
        """
        backup_path = self.backup_dir / backup_id
        if not backup_path.exists():
            logger.error(f"Backup no encontrado: {backup_id}")
            return False

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            logger.error(f"Manifest no encontrado para backup: {backup_id}")
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Restaurar cada archivo/directorio
            for item in backup_path.iterdir():
                if item.name == "manifest.json":
                    continue

                # Determinar destino original
                if "extraccion_masiva" in str(item):
                    dest = self.extraccion_masiva_dir / item.name
                elif "expedientes" in str(item):
                    dest = self.expedientes_dir / item.name
                else:
                    dest = self.data_dir / item.name

                # Copiar
                if item.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
                else:
                    shutil.copytree(item, dest, dirs_exist_ok=True)

            logger.info(f"Backup restaurado: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Error restaurando backup {backup_id}: {e}")
            return False

    def verificar_sesiones_activas(self) -> int:
        """
        Verifica si hay sesiones de extracción activas.

        Returns:
            Número de sesiones activas
        """
        # TODO: Implementar verificación con el gestor de sesiones
        # Por ahora retorna 0
        return 0

    def _get_paths_por_nivel(self, nivel: NivelReseteo) -> List[Path]:
        """Obtiene los paths a eliminar según el nivel."""
        paths = []

        if nivel == NivelReseteo.LISTADOS:
            # Solo listados temporales
            if self.extraccion_masiva_dir.exists():
                listados_dir = self.extraccion_masiva_dir / "listados"
                if listados_dir.exists():
                    paths.extend([
                        p for p in listados_dir.glob("listado_*.json")
                        if p.name != "listado_base.json"
                    ])

                reportes_dir = self.extraccion_masiva_dir / "reportes"
                if reportes_dir.exists():
                    paths.append(reportes_dir)

                sesiones_dir = self.extraccion_masiva_dir / "sesiones"
                if sesiones_dir.exists():
                    paths.append(sesiones_dir)

        elif nivel == NivelReseteo.PDFS:
            # Solo PDFs de actuaciones
            if self.expedientes_dir.exists():
                for exp_dir in self.expedientes_dir.glob("00*"):
                    actuaciones_dir = exp_dir / "actuaciones"
                    if actuaciones_dir.exists():
                        paths.append(actuaciones_dir)

        elif nivel == NivelReseteo.EXPEDIENTES:
            # Todos los expedientes (mantener índice)
            if self.expedientes_dir.exists():
                paths.extend([
                    d for d in self.expedientes_dir.iterdir()
                    if d.is_dir() and d.name.startswith("00")
                ])

        elif nivel == NivelReseteo.COMPLETO:
            # Todo excepto DB y configuración
            # NOTA: No incluimos qdrant_dir porque se limpia vía API
            paths.extend([
                self.extraccion_masiva_dir,
                self.expedientes_dir,
                self.cache_dir,
                self.logs_dir,
                self.vector_store_dir,
                self.bm25_index_dir,
                self.data_dir / "expedientes_sistema.json"
            ])

        elif nivel == NivelReseteo.NUCLEAR:
            # Todo incluyendo DB
            # NOTA: No incluimos qdrant_dir porque se limpia vía API
            paths.extend([
                self.extraccion_masiva_dir,
                self.expedientes_dir,
                self.cache_dir,
                self.logs_dir,
                self.vector_store_dir,
                self.bm25_index_dir,
                self.data_dir / "expedientes_sistema.json",
                self.db_path
            ])

        return [p for p in paths if p.exists()]

    def _get_dir_size_mb(self, path: Path) -> float:
        """Calcula el tamaño de un directorio en MB."""
        if not path.exists():
            return 0.0

        if path.is_file():
            return path.stat().st_size / (1024 * 1024)

        total_size = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except PermissionError:
            pass

        return total_size / (1024 * 1024)

    def _count_files_and_size(self, path: Path) -> tuple[int, float]:
        """Cuenta archivos y calcula tamaño en MB."""
        if not path.exists():
            return 0, 0.0

        if path.is_file():
            return 1, path.stat().st_size / (1024 * 1024)

        count = 0
        size = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    count += 1
                    size += item.stat().st_size
        except PermissionError:
            pass

        return count, size / (1024 * 1024)

    def _log_operacion(
        self,
        nivel: NivelReseteo,
        archivos: int,
        espacio_mb: float,
        timestamp: str
    ) -> None:
        """Registra la operación de reseteo en los logs."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / f"admin_{datetime.now().strftime('%Y%m')}.log"

        log_entry = {
            "timestamp": timestamp,
            "operacion": "reseteo",
            "nivel": nivel.value,
            "archivos_eliminados": archivos,
            "espacio_liberado_mb": round(espacio_mb, 2)
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error escribiendo log: {e}")

    def _get_mysql_connection(self):
        """Obtiene conexión a MySQL."""
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "sintaxis"),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )

    def _limpiar_procesamiento_mysql(self, nivel: NivelReseteo = NivelReseteo.COMPLETO) -> Dict[str, Any]:
        """
        Limpia las tablas MySQL de datos de procesamiento.

        Para COMPLETO:
        - duplicados_detectados, vencimientos, actuaciones, procesamiento_estadisticas, entidades_extraidas, expedientes
        - MONITOREO: cambios_detectados, expedientes_monitoreados, monitoreo_configuracion

        Para NUCLEAR (reset absoluto):
        - Todo lo anterior + tablas de usuario (notas, agenda, escritos, plantillas)

        Args:
            nivel: Nivel de reseteo para determinar qué tablas limpiar

        Returns:
            Dict con resultado de la operación
        """
        # Tablas base de procesamiento + monitoreo (orden por dependencias FK)
        tablas = [
            "duplicados_detectados",
            "vencimientos",
            "actuaciones_texto_fts",  # Índice FTS de actuaciones
            "actuaciones",
            "procesamiento_estadisticas",
            "entidades_extraidas",  # Entidades NER (FK a expedientes)
            "expedientes",
            # Tablas de monitoreo (orden: cambios → expedientes_monitoreados → configuracion)
            "cambios_detectados",  # FK a expedientes_monitoreados
            "expedientes_monitoreados",  # FK a usuario (no configurado, pero depende lógicamente)
            "monitoreo_configuracion",  # FK a usuario (no configurado, pero depende lógicamente)
        ]

        # Para NUCLEAR, agregar tablas de usuario
        if nivel == NivelReseteo.NUCLEAR:
            # Tablas adicionales en orden por dependencias FK
            tablas_usuario = [
                "usuario_actuaciones_notas",
                "agenda_evento_etiquetas",  # FK a agenda_eventos y agenda_etiquetas
                "agenda_eventos",
                "agenda_etiquetas",
                "escritos_adjuntos",  # FK a escritos
                "escritos_versiones",  # FK a escritos
                "escritos",
                "plantillas_escritos",
            ]
            tablas = tablas_usuario + tablas

        resultado = {
            "exito": False,
            "registros_eliminados": 0,
            "detalles": [],
            "error": None
        }

        try:
            conn = self._get_mysql_connection()
            cursor = conn.cursor()
            
            # Desactivar checks de FK temporalmente para facilitar limpieza masiva
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            for tabla in tablas:
                try:
                    # Contar registros antes de eliminar
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]

                    if count > 0:
                        # Eliminar todos los registros
                        cursor.execute(f"TRUNCATE TABLE {tabla}")
                        resultado["registros_eliminados"] += count
                        resultado["detalles"].append(f"  - {tabla}: {count} registros eliminados")
                        logger.info(f"Limpieza MySQL: {count} registros eliminados de {tabla}")
                    else:
                        resultado["detalles"].append(f"  - {tabla}: vacía")

                except MySQLError as e:
                    # La tabla puede no existir
                    resultado["detalles"].append(f"  - {tabla}: no encontrada o error ({e.errno})")
                    logger.warning(f"No se pudo limpiar tabla {tabla}: {e}")
            
            # Reactivar checks de FK
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            conn.commit()
            resultado["exito"] = True
            logger.info(f"Limpieza MySQL completada: {resultado['registros_eliminados']} registros eliminados")

        except MySQLError as e:
            resultado["error"] = str(e)
            logger.error(f"Error conectando a MySQL para limpieza: {e}")

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

        return resultado

    def _preview_procesamiento_mysql(self, nivel: NivelReseteo = NivelReseteo.COMPLETO) -> Dict[str, Any]:
        """
        Muestra cuántos registros se eliminarían de MySQL (dry-run).

        Args:
            nivel: Nivel de reseteo para determinar qué tablas incluir

        Returns:
            Dict con preview de la operación
        """
        # Tablas base de procesamiento + monitoreo
        tablas = [
            "duplicados_detectados",
            "vencimientos",
            "actuaciones_texto_fts",  # Índice FTS de actuaciones
            "actuaciones",
            "procesamiento_estadisticas",
            "entidades_extraidas",  # Entidades NER (FK a expedientes)
            "expedientes",
            # Tablas de monitoreo (orden: cambios → expedientes_monitoreados → configuracion)
            "cambios_detectados",  # FK a expedientes_monitoreados
            "expedientes_monitoreados",  # FK a usuario (no configurado, pero depende lógicamente)
            "monitoreo_configuracion",  # FK a usuario (no configurado, pero depende lógicamente)
        ]

        # Para NUCLEAR, agregar tablas de usuario
        if nivel == NivelReseteo.NUCLEAR:
            tablas_usuario = [
                "usuario_actuaciones_notas",
                "agenda_evento_etiquetas",
                "agenda_eventos",
                "agenda_etiquetas",
                "escritos_adjuntos",
                "escritos_versiones",
                "escritos",
                "plantillas_escritos",
            ]
            tablas = tablas_usuario + tablas

        resultado = {
            "exito": False,
            "registros_a_eliminar": 0,
            "detalles": [],
            "error": None
        }

        try:
            conn = self._get_mysql_connection()
            cursor = conn.cursor()

            for tabla in tablas:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    resultado["registros_a_eliminar"] += count
                    resultado["detalles"].append(f"  - {tabla}: {count} registros")

                except MySQLError as e:
                    resultado["detalles"].append(f"  - {tabla}: no encontrada")

            resultado["exito"] = True

        except MySQLError as e:
            resultado["error"] = str(e)
            logger.error(f"Error conectando a MySQL para preview: {e}")

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

        return resultado
