"""
Diadikos & Palladion - MCP Client Manager
==============================
Model Context Protocol integration for dynamic tool discovery.
Connects to MCP servers defined in mcp_registry.json.
"""

import asyncio
import json
import logging
import os
import queue
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MCPServer:
    """Represents a single MCP server process"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.command = config.get("command", "")
        self.args = config.get("args", [])
        self.env = self._resolve_env(config.get("env", {}))
        self.description = config.get("description", "")
        self._stdout_queue: queue.Queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None

    def _resolve_env(self, env: Dict[str, str]) -> Dict[str, str]:
        """Resolve ${ENV_VAR} placeholders"""
        resolved = {}
        for key, value in env.items():
            if value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = os.environ.get(var_name, "")
            else:
                resolved[key] = value
        return resolved

    def _enqueue_output(self):
        """Thread dédié pour lire le stdout sans bloquer le thread principal"""
        try:
            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self._stdout_queue.put(line)
        except Exception:
            pass
        finally:
            if self.process and self.process.stdout:
                self.process.stdout.close()

    async def start(self):
        """Start the MCP server process"""
        cmd = [self.command] + self.args
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
                text=True,
            )
            self._reader_thread = threading.Thread(target=self._enqueue_output, daemon=True)
            self._reader_thread.start()
            logger.info(f"[MCP] ✅ Server '{self.name}' started (PID: {self.process.pid})")
            return True
        except Exception as e:
            logger.error(f"[MCP] ❌ Failed to start '{self.name}': {e}")
            return False

    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info(f"[MCP] ⏹️ Server '{self.name}' stopped")

    def get_tools(self) -> List[Dict]:
        """Demande la liste des outils au serveur MCP via JSON-RPC"""
        if not self.process or self.process.poll() is not None:
            return []

        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()
            for _ in range(50):
                try:
                    line = self._stdout_queue.get(timeout=5.0)
                except queue.Empty:
                    logger.error(f"[MCP] Timeout: Server '{self.name}' ne répond plus")
                    return []
                try:
                    response = json.loads(line)
                    if response.get("id") == 2:
                        return response.get("result", {}).get("tools", [])
                except json.JSONDecodeError:
                    continue
            return []
        except Exception:
            return []

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict[str, Any]:
        """Call a tool on this MCP server via JSON-RPC"""
        if not self.process or self.process.poll() is not None:
            return {"error": f"Server '{self.name}' not running"}

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            for _ in range(50):
                try:
                    line = self._stdout_queue.get(timeout=5.0)
                except queue.Empty:
                    logger.error(f"[MCP] Timeout: Server '{self.name}' ne répond plus")
                    return {
                        "error": f"Timeout critique: Le serveur MCP '{self.name}' ne répond plus."
                    }
                try:
                    response = json.loads(line)
                    if response.get("id") == 1:
                        return response.get("result", response)
                except json.JSONDecodeError:
                    logger.debug(f"[MCP Server Log: {self.name}] {line.strip()}")
                    continue

            return {"error": "Timeout ou réponse invalide du serveur MCP"}
        except Exception as e:
            return {"error": str(e)}


class MCPClientManager:
    """
    Manages MCP server connections.
    Reads config from mcp_registry.json and spawns servers.
    """

    def __init__(self, config_path: str = "storage/config/mcp_registry.json"):
        self.config_path = Path(config_path)
        self.servers: Dict[str, MCPServer] = {}
        self._config: Dict[str, Any] = {}

    def load_config(self):
        """Load MCP configuration from JSON file"""
        if not self.config_path.exists():
            logger.warning(f"[MCP] Config not found: {self.config_path}")
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(
                f"[MCP] ✅ Config loaded: {len(self._config.get('mcp_servers', {}))} servers"
            )
            return True
        except Exception as e:
            logger.error(f"[MCP] ❌ Config load failed: {e}")
            return False

    async def start_all(self):
        """Start all configured MCP servers"""
        if not self._config:
            self.load_config()

        mcp_servers = self._config.get("mcp_servers", {})
        for name, config in mcp_servers.items():
            server = MCPServer(name, config)
            await server.start()
            self.servers[name] = server

    async def stop_all(self):
        """Stop all MCP servers"""
        for server in self.servers.values():
            await server.stop()
        self.servers.clear()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools from all servers"""
        tools = []
        for name, server in self.servers.items():
            tools.append(
                {
                    "server": name,
                    "description": server.description,
                    "tools": server.get_tools(),
                }
            )
        return tools

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Dict[str, Any]:
        """Call a tool on a specific MCP server"""
        if server_name not in self.servers:
            return {"error": f"Server '{server_name}' not found"}
        return self.servers[server_name].call_tool(tool_name, arguments)

    async def boot_sync_tools(self):
        """Synchronise les outils MCP avec l'Hippocampe (Tool RAG)."""
        try:
            from core.system.hippocampus import get_hippocampus

            hippo = get_hippocampus()

            if not hippo.is_available():
                logging.warning("[MCP] Hippocampus non disponible - skip sync")
                return

            all_capabilities = self.get_available_tools()

            for server in all_capabilities:
                for tool in server.get("tools", []):
                    hippo.index_tool(
                        {
                            "name": f"mcp_{server['server']}_{tool.get('name', '')}",
                            "description": tool.get("description", ""),
                            "server": server["server"],
                            "native_name": tool.get("name", ""),
                        }
                    )

            logging.info(
                f"[MCP] ✅ Tool RAG synchronisé: {sum(len(s.get('tools', [])) for s in all_capabilities)} outils"
            )
        except Exception as e:
            logging.warning(f"[MCP] Erreur sync Tools: {e}")


_mcp_manager = None


def get_mcp_manager() -> MCPClientManager:
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
    return _mcp_manager
