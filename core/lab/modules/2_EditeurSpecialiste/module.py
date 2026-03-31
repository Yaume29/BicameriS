"""
Éditeur Spécialiste Module
========================
Chat technique avec thèmes et workspace.
"""

import uuid
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from ...modules.base import LabModule
from .themes import get_themes, get_subtheme, THEMES
from .workspace import WorkspaceManager, get_workspace_manager
from .executor import CodeExecutor, get_executor

from core.cognition.tot_reasoner import get_tot_reasoner, ToTStrategy, create_tot_reasoner
from core.agents.tool_permission import ToolPermissionContext, get_permission_context
from core.agents.session_manager import get_session_manager, SessionState
from core.agents.command_router import get_command_router, CommandResult


class Message:
    def __init__(self, role: str, content: str):
        self.id = str(uuid.uuid4())[:8]
        self.role = role
        self.content = content
        self.timestamp = datetime.now().isoformat()


class EditeurSpecialisteModule(LabModule):
    """
    Module Éditeur Spécialiste - Chat technique avec thèmes.
    """
    
    id = "editeur-specialiste"
    name = "Éditeur Spécialiste"
    icon = "🔧"
    description = "Chat technique avec thèmes spécialisés"
    order = 2
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        
        self._messages: List[Message] = []
        self._current_theme = None
        self._current_subtheme = None
        self._workspace_files: Dict[str, str] = {}
        self._conversation_id = str(uuid.uuid4())[:8]
        
        base_dir = Path(__file__).parent.parent.parent.parent
        self._storage_dir = base_dir / "storage" / "lab" / "editeur"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._workspace_manager = None
        self._executor = None
        self._current_workspace_path = None
        
        self._tot_reasoner = None
        self._tot_enabled = False
        
        self._work_modes = {
            "chat": {
                "name": "💬 Chat", 
                "icon": "💬",
                "permissions": {
                    "agents": False,
                    "file_read": True,
                    "file_write": False,
                    "file_extensions": [],
                    "execute": False,
                    "commands": ["cd", "ls", "dir", "pwd", "cat", "type", "head", "tail", "grep", "find", "where"],
                    "web": True,
                }
            },
            "planifier": {
                "name": "📋 Planifier", 
                "icon": "📋",
                "permissions": {
                    "agents": False,
                    "file_read": True,
                    "file_write": True,
                    "file_extensions": [".md", ".json", ".xml", ".txt"],
                    "execute": False,
                    "commands": ["cd", "ls", "dir", "pwd", "cat", "type", "head", "tail", "grep", "find", "where", "echo", "date", "time", "whoami", "hostname", "git status", "git log", "git diff --stat"],
                    "web": True,
                }
            },
            "construire": {
                "name": "🔨 Construire", 
                "icon": "🔨",
                "permissions": {
                    "agents": True,
                    "file_read": True,
                    "file_write": True,
                    "file_extensions": ["*"],
                    "execute": "confirm",
                    "commands": "*",
                    "web": True,
                }
            },
            "etudier": {
                "name": "📚 Étudier", 
                "icon": "📚",
                "permissions": {
                    "agents": True,
                    "file_read": True,
                    "file_write": True,
                    "file_extensions": [".md"],
                    "execute": False,
                    "commands": ["cd", "ls", "dir", "pwd", "cat", "type", "head", "tail", "grep", "find", "where"],
                    "web": True,
                }
            },
        }
        self._current_mode = "chat"
        self._auto_confirm_enabled = False
    
    settings_schema = {
        "mode": {"type": "select", "label": "Mode", "options": ["chat", "planifier", "construire", "etudier"], "default": "chat"},
        "theme": {"type": "select", "label": "Thème", "options": ["python", "javascript", "rust", "go"], "default": "python"},
        "auto_confirm": {"type": "checkbox", "label": "Auto-confirmer", "default": false}
    }

    def _render_themes_accordion(self) -> str:
        html = ""
        for theme_name, theme_data in THEMES.items():
            icon = theme_data.get("icon", "📁")
            subthemes = theme_data.get("subthemes", {})
            
            html += f"""
            <div class="theme-group">
                <div class="theme-header" onclick="toggleThemeGroup('{theme_name}')">
                    <span class="theme-icon">{icon}</span>
                    <span class="theme-label">{theme_name}</span>
                    <span class="expand-icon">▶</span>
                </div>
                <div class="theme-subthemes" id="subthemes-{theme_name}">
            """
            
            for subtheme_name in subthemes.keys():
                html += f"""
                    <div class="subtheme-item" onclick="selectSubtheme('{theme_name}', '{subtheme_name}')">
                        {subtheme_name}
                    </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        return html
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "select_theme":
            return self._select_theme(data)
        elif action == "send_message":
            return self._send_message(data)
        elif action == "verify_hypotheses":
            return self._verify_hypotheses(data)
        elif action == "send_direction":
            return self._send_direction(data)
        elif action == "create_file":
            return self._create_file(data)
        elif action == "save_file":
            return self._save_file(data)
        elif action == "list_files":
            return self._list_files(data)
        elif action == "read_file":
            return self._read_file(data)
        elif action == "clear_conversation":
            return self._clear_conversation(data)
        elif action == "get_history":
            return self._get_history(data)
        elif action == "get_themes":
            return {"status": "ok", "themes": get_themes()}
        elif action == "get_current_theme":
            return {
                "status": "ok",
                "theme": self._current_theme,
                "subtheme": self._current_subtheme
            }
        elif action == "workspace_create":
            return self._workspace_create(data)
        elif action == "workspace_open":
            return self._workspace_open(data)
        elif action == "workspace_list":
            return self._workspace_list(data)
        elif action == "workspace_tree":
            return self._workspace_tree(data)
        elif action == "workspace_search":
            return self._workspace_search(data)
        elif action == "execute_code":
            return self._execute_code(data)
        elif action == "execute_file":
            return self._execute_file(data)
        elif action == "check_dependencies":
            return self._check_dependencies(data)
        elif action == "list_available":
            return self._list_available(data)
        elif action == "workspace_read":
            return self._workspace_read(data)
        elif action == "workspace_write":
            return self._workspace_write(data)
        elif action == "tot_toggle":
            return self._tot_toggle(data)
        elif action == "tot_status":
            return self._tot_status(data)
        elif action == "tot_visualize":
            return self._tot_visualize(data)
        elif action == "set_mode":
            return self._set_mode(data)
        elif action == "get_modes":
            return self._get_modes(data)
        elif action == "planifier_task":
            return self._planifier_task(data)
        elif action == "construire_task":
            return self._construire_task(data)
        elif action == "etudier_topic":
            return self._etudier_topic(data)
        elif action == "check_permission":
            return self._check_permission(data.get("action"), data.get("target"))
        elif action == "toggle_auto_confirm":
            return self._toggle_auto_confirm(data)
        elif action == "execute_command":
            return self._execute_command(data)
        elif action == "get_mode_permissions":
            return self._get_mode_permissions(data)
        
        return super().handle_action(action, data)
    
    def _select_theme(self, data: Dict) -> Dict:
        theme = data.get("theme", "")
        subtheme = data.get("subtheme", "")
        
        preprompt = get_subtheme(theme, subtheme)
        
        self._current_theme = theme
        self._current_subtheme = subtheme
        
        return {
            "status": "ok",
            "theme": theme,
            "subtheme": subtheme,
            "preprompt": preprompt
        }
    
    def _send_message(self, data: Dict) -> Dict:
        message = data.get("message", "")
        direction = data.get("direction", None)
        
        if not message:
            return {"status": "error", "message": "Message vide"}
        
        if not self._current_theme or not self._current_subtheme:
            return {"status": "error", "message": "Sélectionnez d'abord un thème"}
        
        self._messages.append(Message("user", message))
        
        preprompt = get_subtheme(self._current_theme, self._current_subtheme)
        
        response = self._generate_response(message, preprompt, direction)
        
        self._messages.append(Message("assistant", response))
        
        return {
            "status": "ok",
            "response": response,
            "theme": self._current_theme,
            "subtheme": self._current_subtheme,
            "hypotheses_verified": True
        }
    
    def _generate_response(self, message: str, preprompt: str, direction: str = None) -> str:
        """
        Génère une réponse en utilisant le système cognitif.
        Inclut la boucle de vérification des hypothèses.
        """
        try:
            from server.extensions import registry
            
            history = "\n".join([
                f"{m.role}: {m.content[:150]}" 
                for m in self._messages[-8:]
            ])
            
            direction_text = ""
            if direction:
                direction_text = f"\n\n[DIRECTION DE L'UTILISATEUR]: {direction}\n"
            
            verification_instruction = """
CRITICAL INSTRUCTION - VÉRIFICATION OBLIGATOIRE:
Avant de donner ta réponse finale, tu DOIS:
1. Identifier chaque hypothèse dans ton raisonnement
2. Vérifier chaque hypothèse avec des faits/references
3. Indiquer clairement ce qui est vérifié vs ce qui reste incertain
4. Si une hypothèse ne peut pas être vérifiée, l'indiquer explicitement

 Structure ta réponse ainsi:
[HYPOTHÈSES IDENTIFIÉES]
- H1: [hypothèse] - [VÉRIFIÉE/NON VÉRIFIÉE/INCERTAINE]
- H2: ...

[VÉRIFICATION]
[Details de la verification pour chaque hypothese]

[RÉPONSE FINALE]
[Ta réponse complète ici]
"""
            
            full_prompt = f"""{preprompt}

{direction_text}
Historique de la conversation:
{history}

Question: {message}

{verification_instruction}

Réponds en français, de manière complète et rigoureuse."""

            if registry.corps_calleux and registry.corps_calleux.left and registry.corps_calleux.right:
                corps = registry.corps_calleux
                
                left_resp = corps.left.think(
                    "Tu es un assistant analytique. Vérifie chaque détail, cite tes sources, soit rigoureux.",
                    full_prompt,
                    temperature=0.3
                )
                
                right_resp = corps.right.think(
                    "Tu es un assistant intuitif. Propose des perspectives créatives, des connexions inattendues, des angles originaux.",
                    full_prompt,
                    temperature=0.7
                )
                
                return f"**Analyse (Hémisphère Gauche):**\n{left_resp}\n\n**Intuition (Hémisphère Droit):**\n{right_resp}"
            
            elif registry.corps_calleux:
                hemi = registry.corps_calleux.left or registry.corps_calleux.right
                if hemi:
                    return hemi.think(preprompt + "\n\n" + verification_instruction, message)
            
            return f"[Mode dégradé - Sans hemispheres]\n\n**Thème:** {self._current_theme}/{self._current_subtheme}\n\n**Question:** {message}\n\n{message}"
            
        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"
    
    def _verify_hypotheses(self, data: Dict) -> Dict:
        """
        Force la vérification des hypothèses.
        """
        message = data.get("message", "Vérifie toutes tes hypothèses et explique ce que tu as vérifié.")
        
        preprompt = ""
        if self._current_theme and self._current_subtheme:
            preprompt = get_subtheme(self._current_theme, self._current_subtheme)
        
        preprompt += "\n\nIMPORTANT: Verify every hypothesis. List what you've verified and what remains uncertain."
        
        response = self._generate_response(message, preprompt)
        
        return {
            "status": "ok",
            "response": response,
            "verified": True
        }
    
    def _send_direction(self, data: Dict) -> Dict:
        """
        Envoie une direction à l'IA. La direction est intégrée au prochain message.
        """
        direction = data.get("direction", "")
        
        if not direction:
            return {"status": "error", "message": "Direction vide"}
        
        if not self._current_theme or not self._current_subtheme:
            return {"status": "error", "message": "Sélectionnez d'abord un thème"}
        
        self._messages.append(Message("user", f"[DIRECTION]: {direction}"))
        
        preprompt = get_subtheme(self._current_theme, self._current_subtheme)
        
        response = self._generate_response(
            "Prends en compte cette direction dans ta réponse:", 
            preprompt, 
            direction
        )
        
        self._messages.append(Message("assistant", response))
        
        return {
            "status": "ok",
            "response": response,
            "direction_applied": direction
        }
    
    def _create_file(self, data: Dict) -> Dict:
        filename = data.get("filename", "untitled.txt")
        self._workspace_files[filename] = ""
        
        return {
            "status": "ok",
            "filename": filename
        }
    
    def _save_file(self, data: Dict) -> Dict:
        filename = data.get("filename", "")
        content = data.get("content", "")
        
        if not filename:
            return {"status": "error", "message": "Nom de fichier requis"}
        
        self._workspace_files[filename] = content
        
        file_path = self._storage_dir / filename
        file_path.write_text(content, encoding="utf-8")
        
        return {
            "status": "ok",
            "filename": filename,
            "saved": True
        }
    
    def _list_files(self, data: Dict) -> Dict:
        files = list(self._workspace_files.keys())
        return {
            "status": "ok",
            "files": files
        }
    
    def _read_file(self, data: Dict) -> Dict:
        filename = data.get("filename", "")
        
        if filename in self._workspace_files:
            return {
                "status": "ok",
                "filename": filename,
                "content": self._workspace_files[filename]
            }
        
        file_path = self._storage_dir / filename
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            return {
                "status": "ok",
                "filename": filename,
                "content": content
            }
        
        return {
            "status": "error",
            "message": f"Fichier non trouvé: {filename}"
        }
    
    def _clear_conversation(self, data: Dict) -> Dict:
        self._messages = []
        return {"status": "ok", "message": "Conversation effacée"}
    
    def _get_history(self, data: Dict) -> Dict:
        messages = []
        for msg in self._messages:
            messages.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            })
        return {
            "status": "ok",
            "messages": messages,
            "theme": self._current_theme,
            "subtheme": self._current_subtheme
        }
    
    def _workspace_create(self, data: Dict) -> Dict:
        name = data.get("name", "Nouveau Projet")
        base_path = data.get("base_path", None)
        
        self._workspace_manager = WorkspaceManager()
        result = self._workspace_manager.create_workspace(name, base_path)
        
        if result.get("created"):
            self._current_workspace_path = result["path"]
            self._executor = get_executor(self._current_workspace_path)
        
        return result
    
    def _workspace_open(self, data: Dict) -> Dict:
        path = data.get("path", "")
        
        if not path:
            return {"status": "error", "message": "Chemin requis"}
        
        self._workspace_manager = WorkspaceManager()
        result = self._workspace_manager.open_workspace(path)
        
        if result.get("id"):
            self._current_workspace_path = path
            self._executor = get_executor(self._current_workspace_path)
        
        return result
    
    def _workspace_list(self, data: Dict) -> Dict:
        if not self._workspace_manager:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        pattern = data.get("pattern", "**/*")
        return {
            "status": "ok",
            "files": self._workspace_manager.list_files(pattern)
        }
    
    def _workspace_tree(self, data: Dict) -> Dict:
        if not self._workspace_manager:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        max_depth = data.get("max_depth", 3)
        return self._workspace_manager.get_file_tree(max_depth)
    
    def _workspace_search(self, data: Dict) -> Dict:
        if not self._workspace_manager:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        query = data.get("query", "")
        extensions = data.get("extensions", None)
        
        if not query:
            return {"status": "error", "message": "Requête vide"}
        
        results = self._workspace_manager.search_files(query, extensions)
        return {"status": "ok", "results": results}
    
    def _execute_code(self, data: Dict) -> Dict:
        code = data.get("code", "")
        language = data.get("language", "python")
        timeout = data.get("timeout", None)
        
        if not code:
            return {"status": "error", "message": "Code vide"}
        
        if not self._executor:
            self._executor = get_executor(self._current_workspace_path)
        
        result = self._executor.execute(code, language, timeout)
        return result
    
    def _execute_file(self, data: Dict) -> Dict:
        filepath = data.get("filepath", "")
        language = data.get("language", None)
        timeout = data.get("timeout", None)
        
        if not filepath:
            return {"status": "error", "message": "Chemin de fichier requis"}
        
        if not self._executor:
            self._executor = get_executor(self._current_workspace_path)
        
        result = self._executor.execute_file(filepath, language, timeout)
        return result
    
    def _check_dependencies(self, data: Dict) -> Dict:
        language = data.get("language", "python")
        
        if not self._executor:
            self._executor = get_executor(self._current_workspace_path)
        
        return self._executor.check_dependencies(language)
    
    def _list_available(self, data: Dict) -> Dict:
        if not self._executor:
            self._executor = get_executor(self._current_workspace_path)
        
        return self._executor.list_available()
    
    def _workspace_read(self, data: Dict) -> Dict:
        if not self._workspace_manager:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        filename = data.get("filename", "")
        return self._workspace_manager.read_file(filename)
    
    def _workspace_write(self, data: Dict) -> Dict:
        if not self._workspace_manager:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        filename = data.get("filename", "")
        content = data.get("content", "")
        
        return self._workspace_manager.write_file(filename, content)
    
    def _init_tot_reasoner(self):
        """Initialize ToT reasoner with hemispheres"""
        if self._tot_reasoner is None:
            self._tot_reasoner = create_tot_reasoner(
                strategy=ToTStrategy.BFS,
                max_depth=5,
                max_branches=5
            )
            
            from server.extensions import registry
            if registry.corps_calleux and registry.corps_calleux.left:
                def generate_fn(prompt):
                    return registry.corps_calleux.left.think(
                        "You are a creative problem-solving assistant.",
                        prompt,
                        temperature=0.8
                    )
                self._tot_reasoner.set_llm_generate(generate_fn)
                
                def evaluate_fn(prompt):
                    return registry.corps_calleux.left.think(
                        "Rate this from 0 to 1 as a decimal only.",
                        prompt,
                        temperature=0.2
                    )
                self._tot_reasoner.set_llm_evaluate(evaluate_fn)
    
    def _tot_toggle(self, data: Dict) -> Dict:
        enabled = data.get("enabled", not self._tot_enabled)
        strategy = data.get("strategy", "bfs")
        max_depth = data.get("max_depth", 5)
        max_branches = data.get("max_branches", 5)
        
        self._init_tot_reasoner()
        
        if strategy == "dfs":
            self._tot_reasoner.strategy = ToTStrategy.DFS
        elif strategy == "best_first":
            self._tot_reasoner.strategy = ToTStrategy.BEST_FIRST
        else:
            self._tot_reasoner.strategy = ToTStrategy.BFS
        
        self._tot_reasoner.max_depth = max_depth
        self._tot_reasoner.max_branches = max_branches
        
        if enabled:
            self._tot_reasoner.enable()
        else:
            self._tot_reasoner.disable()
        
        self._tot_enabled = enabled
        
        return {
            "status": "ok",
            "enabled": self._tot_enabled,
            "strategy": self._tot_reasoner.strategy.value,
            "max_depth": max_depth,
            "max_branches": max_branches
        }
    
    def _tot_status(self, data: Dict) -> Dict:
        self._init_tot_reasoner()
        
        return {
            "status": "ok",
            "enabled": self._tot_enabled,
            "has_reasoner": self._tot_reasoner is not None,
            "strategy": self._tot_reasoner.strategy.value if self._tot_reasoner else "bfs",
            "max_depth": self._tot_reasoner.max_depth if self._tot_reasoner else 5,
            "max_branches": self._tot_reasoner.max_branches if self._tot_reasoner else 5
        }
    
    def _tot_visualize(self, data: Dict) -> Dict:
        if not self._tot_reasoner or not self._tot_enabled:
            return {"status": "error", "message": "ToT not enabled"}
        
        return {
            "status": "ok",
            "visualization": self._tot_reasoner.get_tree_visualization()
        }
    
    def _set_mode(self, data: Dict) -> Dict:
        mode = data.get("mode", "chat")
        if mode not in self._work_modes:
            return {"status": "error", "message": f"Invalid mode: {mode}"}
        
        self._current_mode = mode
        
        return {
            "status": "ok",
            "mode": self._current_mode,
            "mode_info": self._work_modes[self._current_mode]
        }
    
    def _get_modes(self, data: Dict) -> Dict:
        return {
            "status": "ok",
            "modes": self._work_modes,
            "current": self._current_mode
        }
    
    def _planifier_task(self, data: Dict) -> Dict:
        task = data.get("task", "")
        
        if not task:
            return {"status": "error", "message": "No task provided"}
        
        preprompt = """Tu es en mode PLANIFICATEUR. Analyse la tâche et crée un plan structuré.
Divise en étapes claires avec:
- Objectifs intermédiaires
- Ressources nécessaires
- Défis potentiels
- Ordre logique des opérations

Sois méthodique et exhaustif."""
        
        response = self._generate_response(task, preprompt)
        
        return {
            "status": "ok",
            "mode": "planifier",
            "task": task,
            "plan": response
        }
    
    def _construire_task(self, data: Dict) -> Dict:
        task = data.get("task", "")
        
        if not task:
            return {"status": "error", "message": "No task provided"}
        
        preprompt = """Tu es en mode CONSTRUCTEUR. Tu dois implémenter la solution.
- Écris le code directement
- Explique chaque étape
- Teste ta logique
- minimise les erreurs

Sois précis et complet."""
        
        response = self._generate_response(task, preprompt)
        
        return {
            "status": "ok",
            "mode": "construire",
            "task": task,
            "implementation": response
        }
    
    def _etudier_topic(self, data: Dict) -> Dict:
        topic = data.get("topic", "")
        
        if not topic:
            return {"status": "error", "message": "No topic provided"}
        
        preprompt = """Tu es en mode ÉTUDIANT. Tu dois apprendre et documenter ce sujet.
Crée un rapport complet avec:
- Définitions et concepts clés
- Exemples concrets
- Sources et références
- Questions pour approfondir
- Résumé pour mémorisation

Documente tout pour apprendre efficacement."""
        
        response = self._generate_response(topic, preprompt)
        
        report_path = self._storage_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text(f"# Rapport d'étude: {topic}\n\n{response}", encoding="utf-8")
        
        return {
            "status": "ok",
            "mode": "etudier",
            "topic": topic,
            "report": response,
            "saved_to": str(report_path)
        }
    
    def _check_permission(self, action: str, target: str = None) -> Dict:
        context = get_permission_context(
            current_mode=self._current_mode,
            auto_confirm=self._auto_confirm_enabled
        )
        return context.check(action, target)
    
    def _toggle_auto_confirm(self, data: Dict) -> Dict:
        enabled = data.get("enabled", None)
        if enabled is None:
            self._auto_confirm_enabled = not self._auto_confirm_enabled
        else:
            self._auto_confirm_enabled = enabled
        
        return {
            "status": "ok",
            "auto_confirm": self._auto_confirm_enabled,
            "mode": self._current_mode
        }
    
    def _execute_command(self, data: Dict) -> Dict:
        command = data.get("command", "")
        
        perm = self._check_permission("command", command)
        if not perm.get("allowed"):
            return {"status": "error", "message": perm.get("reason")}
        
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "status": "ok",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Commande expirée (timeout 30s)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_mode_permissions(self, data: Dict) -> Dict:
        mode = data.get("mode", self._current_mode)
        perms = self._work_modes.get(mode, {}).get("permissions", {})
        
        safe_perms = {
            "agents": perms.get("agents", False),
            "file_read": perms.get("file_read", False),
            "file_write": perms.get("file_write", False),
            "file_extensions": perms.get("file_extensions", []),
            "execute": perms.get("execute", False),
            "commands": perms.get("commands", []),
            "web": perms.get("web", False),
            "auto_confirm_available": perms.get("execute") == "confirm",
        }
        
        return {
            "status": "ok",
            "mode": mode,
            "permissions": safe_perms,
            "auto_confirm_enabled": self._auto_confirm_enabled if perms.get("execute") == "confirm" else False
        }
