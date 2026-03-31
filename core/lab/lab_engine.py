"""
Lab Engine - Moteur profond du Laboratoire
=========================================
INTÉGRATION COMPLÈTE avec le système cognitif bicaméral.
Ce n'est pas cosmétique - c'est le vrai cerveau qui bosse.
"""

import asyncio
import json
import logging
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dataclasses import dataclass, asdict, field

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
LAB_DIR = BASE_DIR / "storage" / "lab"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lab_engine")


@dataclass
class LabMessage:
    id: str
    role: str
    content: str
    timestamp: str
    specialist_id: str = ""
    attachments: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class LabConversation:
    id: str
    specialist_id: str
    workspace_id: str
    title: str
    messages: List[LabMessage]
    created_at: str
    updated_at: str
    status: str = "active"
    autonomous: bool = False


@dataclass  
class Workspace:
    id: str
    name: str
    path: str
    files: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class LabTool:
    """Outil exécutable dans le Lab"""
    
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
    
    async def execute(self, **kwargs) -> Dict:
        try:
            result = self.func(**kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return {"status": "ok", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


class ToolRegistry:
    """Registre des outils disponibles"""
    
    def __init__(self):
        self.tools: Dict[str, LabTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Enregistre les outils par défaut"""
        
        def read_file(path: str) -> str:
            p = Path(path)
            if p.exists():
                return p.read_text(encoding="utf-8")
            return f"Fichier non trouvé: {path}"
        
        def write_file(path: str, content: str) -> str:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Écrit: {path}"
        
        def list_directory(path: str) -> List[Dict]:
            p = Path(path)
            if not p.exists():
                return []
            return [{"name": f.name, "type": "dir" if f.is_dir() else "file"} for f in p.iterdir()]
        
        def run_command(cmd: str, cwd: str = None) -> str:
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    cwd=cwd or str(BASE_DIR), timeout=30
                )
                return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nReturn: {result.returncode}"
            except subprocess.TimeoutExpired:
                return "Timeout - commande trop longue"
            except Exception as e:
                return f"Erreur: {str(e)}"
        
        def search_code(pattern: str, path: str = None) -> List[str]:
            search_path = Path(path) if path else BASE_DIR
            results = []
            for f in search_path.rglob("*.py"):
                try:
                    content = f.read_text(encoding="utf-8")
                    if pattern.lower() in content.lower():
                        results.append(str(f.relative_to(BASE_DIR)))
                except:
                    pass
            return results[:20]
        
        def get_workspace_files(workspace_id: str = None) -> List[str]:
            return []
        
        self.register("read_file", "Lire un fichier", read_file)
        self.register("write_file", "Écrire dans un fichier", write_file)
        self.register("list_directory", "Lister un répertoire", list_directory)
        self.register("run_command", "Exécuter une commande shell", run_command)
        self.register("search_code", "Rechercher dans le code", search_code)
        self.register("get_workspace_files", "Lister fichiers workspace", get_workspace_files)
    
    def register(self, name: str, description: str, func: Callable):
        self.tools[name] = LabTool(name, description, func)
    
    def get_tool(self, name: str) -> Optional[LabTool]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        return [{"name": t.name, "description": t.description} for t in self.tools.values()]


class LabBrain:
    """
    Le vrai cerveau du Lab - utilise le système cognitif bicaméral.
    """
    
    def __init__(self, engine):
        self.engine = engine
        self.tools = ToolRegistry()
    
    async def think(
        self,
        message: str,
        specialist_id: str,
        context: Dict = None
    ) -> Dict:
        """
        Réfléchit en utilisant les hemispheres.
        """
        from server.extensions import registry
        
        result = {
            "response": "",
            "thoughts": {},
            "tools_used": [],
            "memory_used": False
        }
        
        context = context or {}
        
        specialist = self._get_specialist(specialist_id)
        
        try:
            if registry.corps_calleux and registry.corps_calleux.left and registry.corps_calleux.right:
                result["thoughts"] = await self._bicameral_think(message, specialist, context)
            elif registry.corps_calleux:
                result["thoughts"]["monolateral"] = await self._monolateral_think(message, specialist, context)
            else:
                result["response"] = "Aucun hemisphere disponible - mode dégradé"
        except Exception as e:
            logger.error(f"LabBrain think error: {e}")
            result["response"] = f"Erreur de réflexion: {str(e)}"
        
        if not result["response"] and result["thoughts"]:
            result["response"] = self._synthesize_thoughts(result["thoughts"])
        
        return result
    
    def _get_specialist(self, specialist_id: str) -> Dict:
        from core.lab.specialist import get_specialist
        spec = get_specialist(specialist_id)
        if spec:
            return {
                "name": spec.name,
                "system_prompt": spec.system_prompt,
                "temperature": spec.temperature,
                "hemisphere": spec.hemisphere,
                "capabilities": spec.capabilities
            }
        return {"name": "Assistant", "system_prompt": "Tu es un assistant.", "temperature": 0.7, "hemisphere": "both"}
    
    async def _bicameral_think(self, message: str, specialist: Dict, context: Dict) -> Dict:
        """Pensée bicamérale via corps calleux"""
        from server.extensions import registry
        
        corps = registry.corps_calleux
        
        workspace_context = context.get("workspace_context", "")
        conversation_history = context.get("history", [])
        
        history_text = "\n".join([
            f"{m.role}: {m.content[:100]}" 
            for m in conversation_history[-5:]
        ])
        
        full_prompt = f"""{specialist['system_prompt']}

Contexte workspace:
{workspace_context}

Historique:
{history_text}

Question: {message}

Réfléchis attentivement puis répond."""

        left_temp = 0.3
        right_temp = specialist.get("temperature", 0.8)
        
        try:
            left_resp = corps.left.think(
                "You are the analytical hemisphere. Respond logically and factually.",
                full_prompt,
                temperature=left_temp
            )
            
            right_resp = corps.right.think(
                "You are the intuitive hemisphere. Propose creative and new ideas.",
                full_prompt,
                temperature=right_temp
            )
            
            return {
                "left": left_resp,
                "right": right_resp,
                "synthesis": f"**Analysis (DIA):** {left_resp}\n\n**Intuition (PAL):** {right_resp}"
            }
        except Exception as e:
            logger.error(f"Bicameral think error: {e}")
            return {"error": str(e)}
    
    async def _monolateral_think(self, message: str, specialist: Dict, context: Dict) -> str:
        """Thought with single hemisphere"""
        from server.extensions import registry
        
        corps = registry.corps_calleux
        hemi = corps.left or corps.right
        
        workspace_context = context.get("workspace_context", "")
        full_prompt = f"{specialist['system_prompt']}\n\nContexte: {workspace_context}\n\nQuestion: {message}"
        
        return hemi.think(
            "Tu es un assistant utile.",
            full_prompt,
            temperature=specialist.get("temperature", 0.7)
        )
    
    def _synthesize_thoughts(self, thoughts: Dict) -> str:
        if "synthesis" in thoughts:
            return thoughts["synthesis"]
        if "error" in thoughts:
            return thoughts["error"]
        if "left" in thoughts and "right" in thoughts:
            return f"**Analyse:** {thoughts['left']}\n\n**Intuition:** {thoughts['right']}"
        return str(thoughts)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """Exécute un outil"""
        tool = self.tools.get_tool(tool_name)
        if not tool:
            return {"status": "error", "error": f"Outil non trouvé: {tool_name}"}
        
        result = await tool.execute(**kwargs)
        return result
    
    async def recall_memory(self, query: str, limit: int = 3) -> List[Dict]:
        """Rappelle des souvenirs via WovenMemory"""
        try:
            from core.system.woven_memory import get_woven_memory
            wm = get_woven_memory()
            
            if not wm.is_enabled():
                return []
            
            synapses = wm.recall(query, limit=limit)
            return [{"content": s.content, "source": s.source, "timestamp": s.timestamp} for s in synapses]
        except Exception as e:
            logger.error(f"Memory recall error: {e}")
            return []
    
    async def weave_memory(self, content: str, source: str = "lab", category: str = "general"):
        """Tisse un souvenir dans la mémoire"""
        try:
            from core.system.woven_memory import get_woven_memory
            wm = get_woven_memory()
            wm.weave(content, source=source, category=category)
        except Exception as e:
            logger.error(f"Memory weave error: {e}")


class LabEngine:
    """
    Moteur principal du Laboratoire - INTÉGRATION COMPLÈTE.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        LAB_DIR.mkdir(parents=True, exist_ok=True)
        
        self.conversations: Dict[str, LabConversation] = {}
        self.workspaces: Dict[str, Workspace] = {}
        self.active_conversation: Optional[str] = None
        self.active_workspace: Optional[str] = None
        
        self.brain = LabBrain(self)
        
        self._load_conversations()
        
        logger.info(f"[LabEngine] Initialisé - {len(self.conversations)} conversations, brain={bool(self.brain)}")
    
    def _load_conversations(self):
        conv_file = LAB_DIR / "conversations.json"
        if conv_file.exists():
            try:
                with open(conv_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for conv_data in data.get("conversations", []):
                        conv = LabConversation(**conv_data)
                        self.conversations[conv.id] = conv
            except Exception as e:
                logger.warning(f"[LabEngine] Load error: {e}")
    
    def _save_conversations(self):
        conv_file = LAB_DIR / "conversations.json"
        try:
            with open(conv_file, "w", encoding="utf-8") as f:
                json.dump({
                    "conversations": [asdict(c) for c in self.conversations.values()]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[LabEngine] Save error: {e}")
    
    def create_conversation(
        self, 
        specialist_id: str = "multi", 
        workspace_name: str = "Nouveau Projet",
        autonomous: bool = False
    ) -> LabConversation:
        conv_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        workspace_id = self.create_workspace(workspace_name)
        
        conv = LabConversation(
            id=conv_id,
            specialist_id=specialist_id,
            workspace_id=workspace_id,
            title=workspace_name,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            autonomous=autonomous
        )
        
        self.conversations[conv_id] = conv
        self.active_conversation = conv_id
        self._save_conversations()
        
        logger.info(f"[LabEngine] Conversation créée: {conv_id} (autonomous={autonomous})")
        return conv
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        specialist_id: str = ""
    ) -> LabMessage:
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        message = LabMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            specialist_id=specialist_id
        )
        
        self.conversations[conversation_id].messages.append(message)
        self.conversations[conversation_id].updated_at = datetime.now().isoformat()
        self._save_conversations()
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[LabConversation]:
        return self.conversations.get(conversation_id)
    
    def list_conversations(self, specialist_id: str = None) -> List[LabConversation]:
        convs = list(self.conversations.values())
        if specialist_id:
            convs = [c for c in convs if c.specialist_id == specialist_id]
        return sorted(convs, key=lambda c: c.updated_at, reverse=True)
    
    def create_workspace(self, name: str) -> str:
        workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
        
        workspace_path = LAB_DIR / "workspaces" / workspace_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            path=str(workspace_path),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.workspaces[workspace_id] = workspace
        self.active_workspace = workspace_id
        
        logger.info(f"[LabEngine] Workspace créé: {workspace_id}")
        return workspace_id
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self.workspaces.get(workspace_id)
    
    def add_file_to_workspace(
        self,
        workspace_id: str,
        filename: str,
        content: str
    ):
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace not found: {workspace_id}")
        
        workspace = self.workspaces[workspace_id]
        workspace.files[filename] = content
        
        file_path = Path(workspace.path) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        workspace.updated_at = datetime.now().isoformat()
        
        logger.info(f"[LabEngine] Fichier ajouté: {filename} -> {workspace_id}")
    
    def get_file_content(self, workspace_id: str, filename: str) -> Optional[str]:
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None
        
        if filename in workspace.files:
            return workspace.files[filename]
        
        file_path = Path(workspace.path) / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        
        return None
    
    def list_workspace_files(self, workspace_id: str) -> List[Dict]:
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return []
        
        files = []
        workspace_path = Path(workspace.path)
        
        if workspace_path.exists():
            for f in workspace_path.rglob("*"):
                if f.is_file():
                    rel_path = f.relative_to(workspace_path)
                    files.append({
                        "name": str(rel_path),
                        "path": str(f),
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
        
        return files
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        specialist_id: str
    ) -> Dict:
        """
        Traite un message avec le brain intégré.
        """
        conv = self.conversations.get(conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        self.add_message(conversation_id, "user", message, specialist_id)
        
        workspace = self.workspaces.get(conv.workspace_id)
        workspace_context = ""
        if workspace:
            files = self.list_workspace_files(workspace.id)
            if files:
                workspace_context = f"\n[Fichiers workspace: {', '.join([f['name'] for f in files[:10]])}]"
        
        result = await self.brain.think(
            message=message,
            specialist_id=specialist_id,
            context={
                "workspace_context": workspace_context,
                "history": conv.messages[-10:],
                "workspace_id": conv.workspace_id
            }
        )
        
        self.add_message(conversation_id, "specialist", result.get("response", ""), specialist_id)
        
        return result
    
    async def process_autonomous(self, conversation_id: str, task: str) -> Dict:
        """
        Mode autonome - l'IA travaille seule.
        """
        conv = self.conversations.get(conversation_id)
        if not conv:
            return {"status": "error", "error": "Conversation non trouvée"}
        
        conv.autonomous = True
        self._save_conversations()
        
        logger.info(f"[LabEngine] Mode autonome启动: {conversation_id} - {task}")
        
        result = await self.brain.think(
            message=f"Tâche autonome: {task}",
            specialist_id=conv.specialist_id,
            context={
                "workspace_id": conv.workspace_id,
                "autonomous": True
            }
        )
        
        self.add_message(conversation_id, "system", f"[AUTONOME] {task}", "system")
        self.add_message(conversation_id, "specialist", result.get("response", ""), conv.specialist_id)
        
        return {
            "status": "ok",
            "task": task,
            "result": result
        }
    
    async def run_tool(self, tool_name: str, conversation_id: str = None, **kwargs) -> Dict:
        """Exécute un outil"""
        result = await self.brain.execute_tool(tool_name, **kwargs)
        
        if conversation_id and result.get("status") == "ok":
            self.add_message(
                conversation_id, 
                "system", 
                f"[OUTIL] {tool_name}: {str(result.get('result', ''))[:200]}",
                "system"
            )
        
        return result
    
    def get_config(self) -> Dict:
        return self.config
    
    def update_config(self, config: Dict):
        self.config.update(config)


_lab_engine = None


def get_lab_engine(config: Dict = None) -> LabEngine:
    global _lab_engine
    if _lab_engine is None:
        _lab_engine = LabEngine(config)
    return _lab_engine


def get_workspace(workspace_id: str = None):
    engine = get_lab_engine()
    if workspace_id:
        return engine.get_workspace(workspace_id)
    return engine.get_workspace(engine.active_workspace) if engine.active_workspace else None
