"""
Registration of Editor Tools in the Tool Registry
==================================================
Ces outils vérifient les permissions selon:
- Niveau auto-contrôle (switchboard): none / optimization / limited / full
- Mode éditeur: chat / planifier / construire / etudier
"""

from core.agents.tool_registry import register_tool
from core.agents.editor_tools import get_editor_tools


def register_editor_tools():
    """Enregistre tous les outils de l'éditeur dans le registry"""
    
    tools = get_editor_tools()
    
    register_tool(
        name="editor_check_permission",
        description="Vérifie si une action est autorisée (niveau auto-contrôle + mode éditeur)",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["agents", "file_read", "file_write", "execute", "command", "web"]},
                "target": {"type": "string", "description": "Cible de l'action (chemin, commande, etc.)"}
            },
            "required": ["action"]
        },
        function=tools.check_permission,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_check_permission|action:file_write|target:main.py}}",
            "{{tool:editor_check_permission|action:execute}}"
        ]
    )
    
    register_tool(
        name="editor_read_file",
        description="Lit le contenu d'un fichier",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Chemin du fichier à lire"}
            },
            "required": ["path"]
        },
        function=tools.read_file,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_read_file|path:/path/to/file.py}}"
        ]
    )
    
    register_tool(
        name="editor_write_file",
        description="Écrit du contenu dans un fichier",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Chemin du fichier"},
                "content": {"type": "string", "description": "Contenu à écrire"}
            },
            "required": ["path", "content"]
        },
        function=tools.write_file,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_write_file|path:/path/to/file.py|content:print('hello')}}"
        ]
    )
    
    register_tool(
        name="editor_execute_command",
        description="Exécute une commande système",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Commande à exécuter"}
            },
            "required": ["command"]
        },
        function=tools.execute_command,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_execute_command|command:ls -la}}",
            "{{tool:editor_execute_command|command:git status}}"
        ]
    )
    
    register_tool(
        name="editor_spawn_agent",
        description="Crée un agent pour effectuer une tâche",
        parameters={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Description de la tâche"},
                "agent_type": {"type": "string", "enum": ["research", "coder", "writer"], "default": "research"}
            },
            "required": ["task"]
        },
        function=tools.spawn_agent,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_spawn_agent|task:Recherche sur les transformer}}",
            "{{tool:editor_spawn_agent|task:Écris un test|agent_type:coder}}"
        ]
    )
    
    register_tool(
        name="editor_web_search",
        description="Effectue une recherche sur le web",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête de recherche"}
            },
            "required": ["query"]
        },
        function=tools.web_search,
        category="editor",
        enabled=False,
        examples=[
            "{{tool:editor_web_search|query:latest AI research 2024}}"
        ]
    )
    
    register_tool(
        name="editor_get_mode",
        description="Retourne le mode actuel de l'éditeur",
        parameters={"type": "object", "properties": {}},
        function=tools.get_current_mode,
        category="editor",
        enabled=False,
        examples=["{{tool:editor_get_mode}}"]
    )
    
    register_tool(
        name="editor_get_permissions",
        description="Retourne les permissions actuelles du mode",
        parameters={"type": "object", "properties": {}},
        function=tools.get_permissions,
        category="editor",
        enabled=False,
        examples=["{{tool:editor_get_permissions}}"]
    )
    
    register_tool(
        name="optimize_llm",
        description="Optimise les paramètres LLM (temperature, top_p, model, etc.) - REQUIRES auto_optimization",
        parameters={
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Provider (local, ollama, lmstudio, openai, anthropic, kimi, ou tout autre)"},
                "model": {"type": "string", "description": "Nom du modèle"},
                "temperature": {"type": "number", "description": "Température (0.0-2.0)"},
                "top_p": {"type": "number", "description": "Top P (0.0-1.0)"},
                "max_tokens": {"type": "integer", "description": "Max tokens"},
                "api_key": {"type": "string", "description": "Clé API (pour providers externes)"},
                "endpoint": {"type": "string", "description": "Endpoint URL"}
            }
        },
        function=tools.optimize_llm,
        category="llm",
        enabled=False,
        examples=[
            "{{tool:optimize_llm|provider:openai|temperature:0.7}}",
            "{{tool:optimize_llm|provider:anthropic|model:claude-3}}"
        ]
    )
    
    register_tool(
        name="switch_llm_provider",
        description="Bascule vers un provider LLM différent",
        parameters={
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Nom du provider"},
                "api_key": {"type": "string", "description": "Clé API"},
                "endpoint": {"type": "string", "description": "Endpoint (optionnel)"},
                "model": {"type": "string", "description": "Modèle (optionnel)"}
            },
            "required": ["provider"]
        },
        function=tools.switch_llm_provider,
        category="llm",
        enabled=False,
        examples=[
            "{{tool:switch_llm_provider|provider:anthropic|api_key:sk-ant-...}}",
            "{{tool:switch_llm_provider|provider:openai}}"
        ]
    )
    
    register_tool(
        name="list_llm_providers",
        description="Liste tous les providers LLM configurés",
        parameters={"type": "object", "properties": {}},
        function=tools.list_llm_providers,
        category="llm",
        enabled=False,
        examples=["{{tool:list_llm_providers}}"]
    )
    
    register_tool(
        name="enable_load_balancer",
        description="Active le load balancer avec round-robin et cap de requetes",
        parameters={
            "type": "object",
            "properties": {
                "providers": {"type": "array", "items": {"type": "string"}, "description": "Providers a utiliser"},
                "cap": {"type": "integer", "description": "Max requetes simultanees", "default": 2}
            }
        },
        function=tools.enable_load_balancer,
        category="llm",
        enabled=False,
        examples=["{{tool:enable_load_balancer|cap:2}}", "{{tool:enable_load_balancer|providers:['local','openai']|cap:2}}"]
    )
    
    register_tool(
        name="disable_load_balancer",
        description="Desactive le load balancer",
        parameters={"type": "object", "properties": {}},
        function=tools.disable_load_balancer,
        category="llm",
        enabled=False,
        examples=["{{tool:disable_load_balancer}}"]
    )
    
    register_tool(
        name="get_load_balancer_stats",
        description="Retourne les statistiques du load balancer",
        parameters={"type": "object", "properties": {}},
        function=tools.get_load_balancer_stats,
        category="llm",
        enabled=False,
        examples=["{{tool:get_load_balancer_stats}}"]
    )


def setup_editor_tools():
    """Appelé au démarrage pour configurer les outils"""
    register_editor_tools()
