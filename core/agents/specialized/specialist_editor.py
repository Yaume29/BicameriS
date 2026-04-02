"""
Specialist Editor Agent
=======================
Agent Éditeur Spécialiste - Fusion des capacités de:
- gpt-researcher (recherche récursive)
- AutoGPT (modes de pensée)
- AI-Scientist-v2 (auto-expérimentation)

C'est le seul endroit où l'IA reprend un rôle d'outil.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger("specialist.editor")


class EditorMode(Enum):
    """Modes de l'éditeur"""
    CHAT = "chat"               # Dialogue simple
    RESEARCH = "research"       # Recherche récursive
    CODE = "code"               # Auto-expérimentation
    FALSIFICATION = "falsification"  # Boucle de falsification


class SpecialistEditorAgent:
    """
    Agent Éditeur Spécialiste.
    
    Capacités:
    - Recherche récursive (gpt-researcher)
    - Auto-expérimentation (AI-Scientist-v2)
    - Modes de pensée (AutoGPT)
    - Boucle de falsification
    - Rapports académiques EU-US
    
    C'est le seul endroit où l'IA reprend un rôle d'outil.
    """
    
    def __init__(self):
        self._mode = EditorMode.CHAT
        self._is_active = False
        self._memory_sleeping = False
        
        self._thinking_modes = None
        self._logic_templates = None
        self._memory_sleep_manager = None
        self._falsification_engine = None
        self._code_executor = None
        self._workspace_manager = None
        
        self._session_history: List[Dict] = []
        self._current_session_id = None
        
        base_dir = Path(__file__).parent.parent.parent.parent
        self._storage_dir = base_dir / "storage" / "specialist_editor"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    def activate(self, mode: str = "chat", capabilities: Dict = None) -> Dict:
        """
        Active l'Éditeur Spécialiste.
        
        Args:
            mode: Mode initial (chat, research, code, falsification)
            capabilities: Capacités activées/désactivées
        
        Returns:
            Dict avec status et configuration
        """
        if self._is_active:
            return {"status": "already_active", "message": "Éditeur déjà actif"}
        
        try:
            self._mode = EditorMode(mode)
        except ValueError:
            self._mode = EditorMode.CHAT
        
        self._is_active = True
        self._current_session_id = f"session_{datetime.now().timestamp()}"
        
        self._memory_sleep_manager = self._get_memory_sleep_manager()
        sleep_result = self._memory_sleep_manager.sleep()
        self._memory_sleeping = sleep_result.get("status") == "sleeping"
        
        session_data = {
            "session_id": self._current_session_id,
            "mode": self._mode.value,
            "activated_at": datetime.now().isoformat(),
            "capabilities": capabilities or {},
            "memory_sleeping": self._memory_sleeping
        }
        self._session_history.append(session_data)
        
        logger.info(f"[SpecialistEditor] Activated - Mode: {self._mode.value}")
        
        return {
            "status": "active",
            "mode": self._mode.value,
            "session_id": self._current_session_id,
            "memory_sleeping": self._memory_sleeping,
            "message": f"Éditeur Spécialiste activé en mode {self._mode.value}"
        }
    
    def deactivate(self) -> Dict:
        """Désactive l'Éditeur Spécialiste"""
        if not self._is_active:
            return {"status": "already_inactive", "message": "Éditeur déjà inactif"}
        
        try:
            if self._memory_sleeping:
                wake_result = self._memory_sleep_manager.wake()
                self._memory_sleeping = False
            
            self._is_active = False
            self._mode = EditorMode.CHAT
            
            logger.info("[SpecialistEditor] Deactivated")
            
            return {
                "status": "inactive",
                "message": "Éditeur Spécialiste désactivé. Mémoire restaurée."
            }
            
        except Exception as e:
            logger.error(f"[SpecialistEditor] Deactivation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def process(self, input_text: str, context: Dict = None) -> Dict:
        """
        Traite une entrée selon le mode actuel.
        
        Args:
            input_text: Texte d'entrée
            context: Contexte supplémentaire
        
        Returns:
            Dict avec résultat
        """
        if not self._is_active:
            return {"status": "error", "message": "Éditeur non actif"}
        
        context = context or {}
        
        if self._mode == EditorMode.CHAT:
            return self._process_chat(input_text, context)
        elif self._mode == EditorMode.RESEARCH:
            return self._process_research(input_text, context)
        elif self._mode == EditorMode.CODE:
            return self._process_code(input_text, context)
        elif self._mode == EditorMode.FALSIFICATION:
            return self._process_falsification(input_text, context)
        else:
            return {"status": "error", "message": f"Mode inconnu: {self._mode}"}
    
    def _process_chat(self, input_text: str, context: Dict) -> Dict:
        """Mode Chat - Dialogue simple avec l'entité"""
        thinking_mode = context.get("thinking_mode", "react")
        
        tm = self._get_thinking_modes()
        if tm:
            result = tm.execute(thinking_mode, input_text)
            return {
                "status": "ok",
                "mode": "chat",
                "thinking_mode": thinking_mode,
                "result": result
            }
        
        return {
            "status": "ok",
            "mode": "chat",
            "result": input_text
        }
    
    def _process_research(self, input_text: str, context: Dict) -> Dict:
        """Mode Research - Recherche récursive avec rapport académique"""
        template = context.get("template", "research")
        
        lt = self._get_logic_templates()
        prompt = lt.generate_prompt(template, input_text) if lt else input_text
        
        tm = self._get_thinking_modes()
        if tm:
            result = tm.execute("plan_execute", prompt)
        else:
            result = {"result": prompt}
        
        return {
            "status": "ok",
            "mode": "research",
            "template": template,
            "result": result
        }
    
    def _process_code(self, input_text: str, context: Dict) -> Dict:
        """Mode Code - Auto-expérimentation jusqu'à preuve"""
        tm = self._get_thinking_modes()
        
        if tm:
            result = tm.execute("critic_refine", input_text)
        else:
            result = {"result": input_text}
        
        return {
            "status": "ok",
            "mode": "code",
            "result": result
        }
    
    def _process_falsification(self, input_text: str, context: Dict) -> Dict:
        """Mode Falsification - Boucle de vérification stricte"""
        fe = self._get_falsification_engine()
        
        if fe:
            result = fe.run_falsification(input_text)
        else:
            result = {"result": input_text, "status": "no_engine"}
        
        return {
            "status": "ok",
            "mode": "falsification",
            "result": result
        }
    
    def set_mode(self, mode: str) -> Dict:
        """Change le mode de l'éditeur"""
        if not self._is_active:
            return {"status": "error", "message": "Éditeur non actif"}
        
        try:
            self._mode = EditorMode(mode)
            return {"status": "ok", "mode": self._mode.value}
        except ValueError:
            return {"status": "error", "message": f"Mode invalide: {mode}"}
    
    def get_status(self) -> Dict:
        """Retourne le statut de l'éditeur"""
        return {
            "is_active": self._is_active,
            "mode": self._mode.value if self._is_active else None,
            "memory_sleeping": self._memory_sleeping,
            "session_id": self._current_session_id,
            "sessions_count": len(self._session_history)
        }
    
    def _get_thinking_modes(self):
        """Lazy load du gestionnaire de modes de pensée"""
        if self._thinking_modes is None:
            try:
                from core.agents.specialized.thinking_modes import get_thinking_mode_manager
                self._thinking_modes = get_thinking_mode_manager()
            except Exception as e:
                logger.warning(f"[SpecialistEditor] Thinking modes unavailable: {e}")
        return self._thinking_modes
    
    def _get_logic_templates(self):
        """Lazy load du moteur de templates logiques"""
        if self._logic_templates is None:
            try:
                from core.agents.specialized.logic_templates import get_logic_template_engine
                self._logic_templates = get_logic_template_engine()
            except Exception as e:
                logger.warning(f"[SpecialistEditor] Logic templates unavailable: {e}")
        return self._logic_templates
    
    def _get_memory_sleep_manager(self):
        """Lazy load du gestionnaire de veille mémoire"""
        if self._memory_sleep_manager is None:
            try:
                from core.agents.specialized.memory_sleep import get_memory_sleep_manager
                self._memory_sleep_manager = get_memory_sleep_manager()
            except Exception as e:
                logger.warning(f"[SpecialistEditor] Memory sleep manager unavailable: {e}")
        return self._memory_sleep_manager
    
    def _get_falsification_engine(self):
        """Lazy load du moteur de falsification"""
        if self._falsification_engine is None:
            try:
                from core.agents.specialized.falsification_engine import get_falsification_engine
                self._falsification_engine = get_falsification_engine()
            except Exception as e:
                logger.warning(f"[SpecialistEditor] Falsification engine unavailable: {e}")
        return self._falsification_engine


# Instance globale
_specialist_editor: Optional[SpecialistEditorAgent] = None


def get_specialist_editor() -> SpecialistEditorAgent:
    """Récupère l'instance de l'Éditeur Spécialiste"""
    global _specialist_editor
    if _specialist_editor is None:
        _specialist_editor = SpecialistEditorAgent()
    return _specialist_editor
