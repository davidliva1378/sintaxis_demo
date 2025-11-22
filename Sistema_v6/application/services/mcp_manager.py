"""
Servicio para gestionar el servidor MCP.

Permite iniciar, detener y monitorear el proceso del servidor MCP.
"""

import logging
import os
import json
import subprocess
import signal
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Rutas de configuracion
BASE_DIR = Path(__file__).parent.parent.parent
MCP_SERVER_PATH = BASE_DIR / "mcp" / "sintaxis_mcp_server.py"
MCP_SERVER_SSE_PATH = BASE_DIR / "mcp" / "sintaxis_mcp_server_sse.py"
CONFIG_DIR = BASE_DIR / "config"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp_settings.json"
MCP_PID_FILE = CONFIG_DIR / "mcp_server.pid"
MCP_LOG_FILE = BASE_DIR / "var" / "logs" / "mcp_server.log"


class MCPManager:
    """
    Gestor del servidor MCP.

    Permite:
    - Iniciar/detener el servidor
    - Verificar estado
    - Obtener logs
    - Configurar opciones
    """

    def __init__(self):
        """Inicializa el gestor MCP."""
        self._ensure_dirs()
        self._load_config()

    def _ensure_dirs(self):
        """Asegura que existan los directorios necesarios."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        MCP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Carga la configuracion desde archivo."""
        self.config = {
            "auto_start": False,
            "mode": "stdio",
            "port": 8765,
            "workspace_path": str(BASE_DIR),
            "enabled_tools": [],  # Vacio = todas habilitadas
            "log_level": "INFO"
        }

        if MCP_CONFIG_FILE.exists():
            try:
                with open(MCP_CONFIG_FILE, 'r') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                logger.warning(f"Error cargando config MCP: {e}")

    def _save_config(self):
        """Guarda la configuracion a archivo."""
        try:
            with open(MCP_CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error guardando config MCP: {e}")
            return False

    def _get_pid(self) -> Optional[int]:
        """Obtiene el PID del proceso MCP si existe."""
        if not MCP_PID_FILE.exists():
            return None

        try:
            with open(MCP_PID_FILE, 'r') as f:
                pid = int(f.read().strip())

            # Verificar que el proceso existe
            os.kill(pid, 0)
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            # Proceso no existe, limpiar archivo
            MCP_PID_FILE.unlink(missing_ok=True)
            return None

    def _save_pid(self, pid: int):
        """Guarda el PID del proceso."""
        with open(MCP_PID_FILE, 'w') as f:
            f.write(str(pid))

    def _clear_pid(self):
        """Limpia el archivo PID."""
        MCP_PID_FILE.unlink(missing_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del servidor MCP.

        Returns:
            Dict con estado, pid, uptime, etc.
        """
        pid = self._get_pid()
        running = pid is not None

        status = {
            "running": running,
            "pid": pid,
            "uptime_seconds": 0,
            "started_at": None,
            "mode": self.config.get("mode", "stdio"),
            "port": self.config.get("port", 8765),
            "auto_start": self.config.get("auto_start", False),
            "enabled_tools_count": len(self.config.get("enabled_tools", [])) or 29,  # 29 = todas
            "log_file": str(MCP_LOG_FILE) if MCP_LOG_FILE.exists() else None
        }

        if running and MCP_PID_FILE.exists():
            try:
                started_at = datetime.fromtimestamp(MCP_PID_FILE.stat().st_mtime)
                status["started_at"] = started_at.isoformat()
                status["uptime_seconds"] = int((datetime.now() - started_at).total_seconds())
            except Exception:
                pass

        return status

    def start(self) -> Dict[str, Any]:
        """
        Inicia el servidor MCP.

        Returns:
            Dict con resultado de la operacion
        """
        # Verificar si ya esta corriendo
        if self._get_pid():
            return {
                "success": False,
                "error": "El servidor MCP ya esta corriendo",
                "pid": self._get_pid()
            }

        # Determinar modo y script a usar
        mode = self.config.get("mode", "stdio")

        if mode == "sse":
            server_path = MCP_SERVER_SSE_PATH
            port = self.config.get("port", 8765)
        else:
            server_path = MCP_SERVER_PATH
            port = None

        # Verificar que existe el script
        if not server_path.exists():
            return {
                "success": False,
                "error": f"Script MCP no encontrado: {server_path}"
            }

        try:
            # Preparar comando
            python_path = f"{BASE_DIR.parent}:{BASE_DIR}"
            env = os.environ.copy()
            env["PYTHONPATH"] = python_path

            # Abrir archivo de log
            log_file = open(MCP_LOG_FILE, 'a')

            # Construir comando segun modo
            if mode == "sse":
                cmd = ["python", str(server_path), "--port", str(port), "--host", "0.0.0.0", "--ssl"]
                stdin_pipe = None  # SSE no necesita stdin
            else:
                cmd = ["python", str(server_path)]
                stdin_pipe = subprocess.PIPE  # stdio necesita stdin abierto

            # Iniciar proceso
            process = subprocess.Popen(
                cmd,
                stdin=stdin_pipe,
                stdout=log_file,
                stderr=log_file,
                env=env,
                cwd=str(BASE_DIR),
                start_new_session=True
            )

            # Guardar PID
            self._save_pid(process.pid)

            # Esperar un momento para verificar que inicio
            time.sleep(0.5)

            if process.poll() is None:
                logger.info(f"Servidor MCP ({mode}) iniciado con PID {process.pid}")
                msg = f"Servidor MCP ({mode}) iniciado correctamente"
                if mode == "sse":
                    msg += f" en puerto {port}"
                return {
                    "success": True,
                    "pid": process.pid,
                    "message": msg,
                    "mode": mode,
                    "port": port
                }
            else:
                self._clear_pid()
                return {
                    "success": False,
                    "error": "El servidor MCP termino inmediatamente",
                    "exit_code": process.returncode
                }

        except Exception as e:
            logger.error(f"Error iniciando servidor MCP: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def stop(self) -> Dict[str, Any]:
        """
        Detiene el servidor MCP.

        Returns:
            Dict con resultado de la operacion
        """
        pid = self._get_pid()

        if not pid:
            return {
                "success": False,
                "error": "El servidor MCP no esta corriendo"
            }

        try:
            # Enviar SIGTERM
            os.kill(pid, signal.SIGTERM)

            # Esperar que termine
            for _ in range(10):  # 5 segundos max
                time.sleep(0.5)
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    # Proceso terminado
                    self._clear_pid()
                    logger.info(f"Servidor MCP detenido (PID {pid})")
                    return {
                        "success": True,
                        "message": "Servidor MCP detenido correctamente"
                    }

            # Si no termino, forzar con SIGKILL
            os.kill(pid, signal.SIGKILL)
            self._clear_pid()

            return {
                "success": True,
                "message": "Servidor MCP forzado a terminar"
            }

        except ProcessLookupError:
            self._clear_pid()
            return {
                "success": True,
                "message": "El servidor MCP ya no estaba corriendo"
            }
        except Exception as e:
            logger.error(f"Error deteniendo servidor MCP: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def restart(self) -> Dict[str, Any]:
        """
        Reinicia el servidor MCP.

        Returns:
            Dict con resultado de la operacion
        """
        stop_result = self.stop()
        if not stop_result.get("success") and "no esta corriendo" not in stop_result.get("error", ""):
            return stop_result

        time.sleep(0.5)
        return self.start()

    def get_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuracion actual.

        Returns:
            Dict con configuracion
        """
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza la configuracion.

        Args:
            new_config: Nuevos valores de configuracion

        Returns:
            Dict con resultado
        """
        # Validar campos
        valid_keys = ["auto_start", "mode", "port", "workspace_path", "enabled_tools", "log_level"]

        for key, value in new_config.items():
            if key in valid_keys:
                self.config[key] = value

        if self._save_config():
            return {
                "success": True,
                "message": "Configuracion actualizada",
                "config": self.config
            }
        else:
            return {
                "success": False,
                "error": "Error guardando configuracion"
            }

    def get_logs(self, lines: int = 100) -> List[str]:
        """
        Obtiene las ultimas lineas del log.

        Args:
            lines: Numero de lineas a retornar

        Returns:
            Lista de lineas de log
        """
        if not MCP_LOG_FILE.exists():
            return []

        try:
            with open(MCP_LOG_FILE, 'r') as f:
                all_lines = f.readlines()
                return [line.rstrip() for line in all_lines[-lines:]]
        except Exception as e:
            logger.error(f"Error leyendo logs MCP: {e}")
            return [f"Error leyendo logs: {e}"]

    def clear_logs(self) -> Dict[str, Any]:
        """
        Limpia el archivo de logs.

        Returns:
            Dict con resultado
        """
        try:
            if MCP_LOG_FILE.exists():
                MCP_LOG_FILE.unlink()
            return {"success": True, "message": "Logs limpiados"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tools_list(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de tools disponibles.

        Returns:
            Lista de tools con nombre, descripcion, categoria, habilitada
        """
        from application.services.ia.tools_service import ToolsService

        tools_service = ToolsService()
        definitions = tools_service.get_tool_definitions()

        enabled = set(self.config.get("enabled_tools", []))
        all_enabled = len(enabled) == 0

        # Categorizar tools
        categories = {
            "expedientes": ["contar_expedientes", "listar_expedientes", "obtener_expediente",
                          "buscar_expedientes", "expedientes_recientes", "expedientes_por_dependencia"],
            "actuaciones": ["listar_actuaciones", "buscar_actuaciones", "obtener_texto_actuacion",
                          "actuaciones_por_tipo", "actuaciones_con_texto"],
            "vencimientos": ["vencimientos_pendientes", "vencimientos_urgentes", "vencimientos_vencidos",
                           "resumen_vencimientos", "proximos_vencimientos"],
            "entidades": ["listar_entidades", "buscar_entidades", "personas_expediente",
                        "entidades_por_tipo", "estadisticas_entidades"],
            "estadisticas": ["estadisticas_sistema", "estadisticas_expediente",
                           "estadisticas_procesamiento", "actividad_reciente"],
            "analisis": ["duplicados_detectados", "clasificacion_ia",
                        "actuaciones_importantes", "resumen_expediente"]
        }

        # Invertir para busqueda rapida
        tool_category = {}
        for cat, tools in categories.items():
            for tool in tools:
                tool_category[tool] = cat

        result = []
        for tool_def in definitions:
            name = tool_def["name"]
            result.append({
                "name": name,
                "description": tool_def.get("description", ""),
                "category": tool_category.get(name, "otro"),
                "enabled": all_enabled or name in enabled,
                "parameters": tool_def.get("parameters", {})
            })

        return result

    def set_enabled_tools(self, tools: List[str]) -> Dict[str, Any]:
        """
        Establece las tools habilitadas.

        Args:
            tools: Lista de nombres de tools (vacio = todas)

        Returns:
            Dict con resultado
        """
        self.config["enabled_tools"] = tools
        return self.update_config({"enabled_tools": tools})

    def get_tool_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas de uso de tools.

        Returns:
            Dict con estadisticas
        """
        # Por ahora retorna datos basicos
        # TODO: Implementar tracking de uso real
        return {
            "total_calls": 0,
            "calls_today": 0,
            "most_used": [],
            "avg_response_time_ms": 0,
            "errors_today": 0
        }

    def generate_claude_config(self) -> str:
        """
        Genera la configuracion JSON para Claude Code/Desktop.

        Returns:
            String JSON con la configuracion
        """
        mode = self.config.get("mode", "stdio")

        if mode == "sse":
            # Configuracion para acceso remoto via SSE con HTTPS
            port = self.config.get("port", 8765)
            config = {
                "mcpServers": {
                    "sintaxis": {
                        "url": f"https://localhost:{port}/sse",
                        "note": "Cambiar 'localhost' por la IP del servidor para acceso remoto"
                    }
                }
            }
        else:
            # Configuracion para uso local via stdio
            config = {
                "mcpServers": {
                    "sintaxis": {
                        "command": "python",
                        "args": [str(MCP_SERVER_PATH)],
                        "env": {
                            "PYTHONPATH": f"{BASE_DIR.parent}:{BASE_DIR}",
                            "MYSQL_PASSWORD": "${MYSQL_PASSWORD}"
                        }
                    }
                }
            }
        return json.dumps(config, indent=2)


# Instancia global
_mcp_manager: Optional[MCPManager] = None

def get_mcp_manager() -> MCPManager:
    """Obtiene la instancia global del gestor MCP."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager
