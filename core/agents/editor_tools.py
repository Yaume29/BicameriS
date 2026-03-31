"""
Editor Tools - Outils avec permissions pour l'Éditeur Spécialiste
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from core.agents.tool_permission import ToolPermissionContext, get_permission_context

logger = logging.getLogger("agents.editor_tools")


class EditorTools:
    
    def __init__(self):
        self._current_mode = "chat"
        self._auto_confirm = False
    
    def _get_context(self) -> ToolPermissionContext:
        return get_permission_context(
            current_mode=self._current_mode,
            auto_confirm=self._auto_confirm
        )
    
    def _get_auto_level(self) -> str:
        try:
            from core.system.switchboard import get_switchboard
            sb = get_switchboard()
            
            if sb.is_active("auto_scaffolding_full"):
                return "full"
            elif sb.is_active("auto_scaffolding_limited"):
                return "limited"
            elif sb.is_active("auto_optimization"):
                return "optimization"
            return "none"
        except:
            return "none"
    
    def _check_auto_level(self, required_level: str) -> bool:
        current = self._get_auto_level()
        
        levels = {"none": 0, "optimization": 1, "limited": 2, "full": 3}
        
        current_level = levels.get(current, 0)
        required = levels.get(required_level, 0)
        
        return current_level >= required
    
    def _check(self, action: str, target: str = None) -> Dict:
        """Vérifie si une action est permise (niveau auto-contrôle + mode éditeur)"""
        auto_level = self._get_auto_level()
        
        if action == "command" and target:
            safe_cmds = ["cd", "ls", "dir", "pwd", "cat", "type", "head", "tail", "grep", "find", "where", "echo", "date", "time", "whoami", "hostname"]
            if any(target.startswith(c) for c in safe_cmds):
                return self._check_editor_mode(action, target)
        
        if action in ["agents", "file_write", "execute"]:
            if auto_level == "none":
                return {"allowed": False, "reason": f"Auto-contrôle désactivé. Activez auto_optimization (ou higher) pour {action}"}
            if auto_level == "optimization" and action in ["agents", "file_write", "execute"]:
                return {"allowed": False, "reason": f"Level 'optimization' ne permet pas {action}. Utilisez 'limited' ou 'full'"}
        
        if action == "execute":
            if auto_level not in ["full"]:
                if auto_level == "limited":
                    result = self._check_editor_mode("execute")
                    if not result.get("allowed"):
                        return result
                else:
                    return {"allowed": False, "reason": "Exécution nécessite auto_scaffolding_full"}
        
        if action == "command":
            if auto_level not in ["full", "limited"]:
                return {"allowed": False, "reason": "Commandes nécessite auto_scaffolding_limited ou full"}
        
        return self._check_editor_mode(action, target)
    
    def _check_editor_mode(self, action: str, target: str = None) -> Dict:
        context = self._get_context()
        return context.check(action, target)
    
    def check_permission(self, action: str, target: str = None) -> str:
        """
        Vérifie si une action est autorisée.
        Usage: {{tool:editor_check_permission|action:file_write|target:main.py}}
        """
        result = self._check(action, target)
        if result.get("allowed") == True:
            return f"✓ Permission accordée pour '{action}' sur '{target}'"
        elif result.get("allowed") == "confirm":
            return f"⚠️ Confirmation requise: {result.get('reason')}"
        else:
            return f"✗ Refusé: {result.get('reason')}"
    
    def read_file(self, path: str) -> str:
        """
        Lit un fichier.
        Usage: {{tool:editor_read_file|path:/path/to/file.py}}
        """
        result = self._check("file_read", path)
        if not result.get("allowed"):
            return f"Erreur: {result.get('reason')}"
        
        module = self._get_module()
        if not module:
            return "Erreur: Module non disponible"
        
        try:
            content = Path(path).read_text(encoding="utf-8")
            return f"--- {path} ---\n{content}"
        except Exception as e:
            return f"Erreur de lecture: {str(e)}"
    
    def write_file(self, path: str, content: str) -> str:
        """
        Écrit dans un fichier.
        Usage: {{tool:editor_write_file|path:/path/to/file.py|content:...}}
        """
        result = self._check("file_write", path)
        if not result.get("allowed"):
            return f"Erreur: {result.get('reason')}"
        
        module = self._get_module()
        if not module:
            return "Erreur: Module non disponible"
        
        try:
            Path(path).write_text(content, encoding="utf-8")
            return f"✓ Fichier écrit: {path}"
        except Exception as e:
            return f"Erreur d'écriture: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """
        Exécute une commande système.
        Usage: {{tool:editor_execute_command|command:ls -la}}
        """
        result = self._check("command", command)
        if not result.get("allowed"):
            if result.get("allowed") == "confirm":
                module = self._get_module()
                if module and module._auto_confirm_enabled:
                    pass
                else:
                    return f"⚠️ Confirmation requise: {result.get('reason')}"
            else:
                return f"Erreur: {result.get('reason')}"
        
        module = self._get_module()
        if not module:
            return "Erreur: Module non disponible"
        
        result = module._execute_command({"command": command})
        
        if result.get("status") == "ok":
            output = result.get("stdout", "") + result.get("stderr", "")
            return f"--- Sortie ---\n{output}\n--- Code: {result.get('returncode')} ---"
        else:
            return f"Erreur: {result.get('message')}"
    
    def spawn_agent(self, task: str, agent_type: str = "research") -> str:
        """
        Crée un agent pour une tâche.
        Usage: {{tool:editor_spawn_agent|task:Recherche sur...|agent_type:research}}
        """
        result = self._check("agents")
        if not result.get("allowed"):
            return f"Erreur: {result.get('reason')}"
        
        try:
            from core.agents.super_agent import get_super_agent
            super_agent = get_super_agent()
            
            if not super_agent.enabled:
                super_agent.enable()
            
            import asyncio
            spawn_result = asyncio.run(super_agent.execute_task(task))
            
            return f"✓ Agent créé: {spawn_result.get('agents_created', 0)} pour la tâche: {task[:50]}..."
        except Exception as e:
            return f"Erreur lors de la création de l'agent: {str(e)}"
    
    def web_search(self, query: str) -> str:
        """
        Recherche sur le web.
        Usage: {{tool:editor_web_search|query: latest AI research}}
        """
        result = self._check("web")
        if not result.get("allowed"):
            return f"Erreur: {result.get('reason')}"
        
        try:
            from core.agents.web_tools import get_web_tools
            web_tools = get_web_tools()
            
            import asyncio
            search_results = asyncio.run(web_tools.search.search(query, num_results=5))
            
            if not search_results:
                return "Aucun résultat trouvé"
            
            output = f"--- Résultats pour: {query} ---\n"
            for r in search_results:
                output += f"- {r.title}\n  {r.snippet}\n"
            
            return output
        except Exception as e:
            return f"Erreur de recherche: {str(e)}"
    
    def get_current_mode(self) -> str:
        """
        Retourne le mode actuel de l'éditeur.
        Usage: {{tool:editor_get_mode}}
        """
        module = self._get_module()
        if not module:
            return "chat"
        return module._current_mode
    
    def get_permissions(self) -> str:
        """
        Retourne les permissions actuelles.
        Usage: {{tool:editor_get_permissions}}
        """
        module = self._get_module()
        if not module:
            return "Module non disponible"
        
        result = module._get_mode_permissions({"mode": module._current_mode})
        perms = result.get("permissions", {})
        
        return f"""--- Permissions mode: {module._current_mode} ---
Agents: {'✓' if perms.get('agents') else '✗'}
Lecture: {'✓' if perms.get('file_read') else '✗'}
Écriture: {'✓' if perms.get('file_write') else '✗'}
Extensions: {perms.get('file_extensions', [])}
Exécution: {perms.get('execute')}
Commandes: {perms.get('commands', [])}
Web: {'✓' if perms.get('web') else '✗'}"""
    
    def optimize_llm(self, provider: str = None, model: str = None, temperature: float = None, top_p: float = None, **kwargs) -> str:
        """
        Optimise les paramètres LLM (nécessite auto_optimization).
        Usage: {{tool:optimize_llm|provider:openai|model:gpt-4|temperature:0.7}}
        """
        try:
            from core.cognition.auto_optimizer import get_auto_optimizer
            optimizer = get_auto_optimizer()
            
            result = optimizer.optimize_provider(
                provider=provider,
                model=model,
                temperature=temperature,
                top_p=top_p,
                reason="Auto-optimization",
                **kwargs
            )
            
            if result.get("status") == "SUCCESS":
                return f"✓ Optimisé: {result.get('provider')} - {result.get('new')}"
            else:
                return f"✗ Erreur: {result.get('error')}"
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def switch_llm_provider(self, provider: str, **kwargs) -> str:
        """
        Bascule vers un autre provider LLM.
        Usage: {{tool:switch_llm_provider|provider:anthropic|api_key:sk-...}}
        """
        try:
            from core.cognition.auto_optimizer import get_auto_optimizer
            optimizer = get_auto_optimizer()
            
            result = optimizer.switch_provider(provider, **kwargs)
            
            if result.get("status") == "SUCCESS":
                return f"✓ Provider switched to: {result.get('provider')}"
            else:
                return f"✗ Erreur: {result.get('error')}"
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def list_llm_providers(self) -> str:
        """
        Liste les providers LLM configurés.
        Usage: {{tool:list_llm_providers}}
        """
        try:
            from core.cognition.auto_optimizer import get_auto_optimizer
            optimizer = get_auto_optimizer()
            
            result = optimizer.get_available_providers()
            
            output = "--- Providers LLM ---\n"
            output += f"Actif: {result.get('active', 'aucun')}\n"
            output += f"Configurés: {result.get('count', 0)}\n"
            
            for name, config in result.get("configured", {}).items():
                output += f"\n- {name}: {config}\n"
            
            return output
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def enable_load_balancer(self, providers: List[str] = None, cap: int = 2) -> str:
        """
        Active le load balancer avec round-robin et cap.
        Usage: {{tool:enable_load_balancer|providers:["local","openai"]|cap:2}}
        """
        try:
            from core.cognition.llm_load_balancer import get_load_balancer
            lb = get_load_balancer()
            
            if providers:
                for p in providers:
                    optimizer = get_auto_optimizer()
                    config = optimizer.get_provider_config(p)
                    if config:
                        lb.add_provider(p, max_concurrent=cap)
            
            lb.enable_cap(max_concurrent=cap)
            lb.enable_round_robin()
            
            return f"✓ Load Balancer activé: {providers or 'all'}, cap: {cap}"
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def disable_load_balancer(self) -> str:
        """
        Désactive le load balancer.
        Usage: {{tool:disable_load_balancer}}
        """
        try:
            from core.cognition.llm_load_balancer import get_load_balancer
            lb = get_load_balancer()
            lb.disable_cap()
            return "✓ Load Balancer désactivé"
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def get_load_balancer_stats(self) -> str:
        """
        Retourne les statistiques du load balancer.
        Usage: {{tool:get_load_balancer_stats}}
        """
        try:
            from core.cognition.llm_load_balancer import get_load_balancer
            lb = get_load_balancer()
            
            stats = lb.get_stats()
            
            output = f"""--- Load Balancer ---
Mode: {stats['current_mode']}
Cap: {'ON' if stats['cap_enabled'] else 'OFF'} (max: {stats['max_concurrent']})
Providers: {', '.join(stats['providers'])}

"""
            for name, s in stats['stats'].items():
                output += f"""- {name}:
  Requêtes: {s['total_requests']}
  Succès: {s['successful']} ({s['success_rate']*100:.1f}%)
  Latence avg: {s['avg_latency']:.2f}s
  Actives: {s['active_requests']}

"""
            return output
        except Exception as e:
            return f"✗ Exception: {str(e)}"
    
    def add_provider_to_pool(self, name: str, priority: int = 1, max_concurrent: int = 1, **config) -> str:
        """
        Ajoute un provider au pool de load balancing.
        Usage: {{tool:add_provider_to_pool|name:openai|priority:1|max_concurrent:2}}
        """
        try:
            from core.cognition.llm_load_balancer import get_load_balancer
            lb = get_load_balancer()
            
            lb.add_provider(name, priority=priority, max_concurrent=max_concurrent, **config)
            
            return f"✓ Provider {name} ajouté au pool"
        except Exception as e:
            return f"✗ Exception: {str(e)}"


_editor_tools_instance: Optional[EditorTools] = None


def get_editor_tools() -> EditorTools:
    """Retourne l'instance globale des outils éditeur"""
    global _editor_tools_instance
    if _editor_tools_instance is None:
        _editor_tools_instance = EditorTools()
    return _editor_tools_instance
