"""
Inception Module
================
Thought injection module (Inception).
Uses ToT for deeper thought exploration.
"""

from typing import Dict
from ...modules.base import LabModule

from core.cognition.tot_reasoner import get_tot_reasoner, ToTStrategy


class InceptionModule(LabModule):
    """
    Module d'Inception - Injection de pensées.
    Permet d'injecter des idées dans les hemispheres.
    """
    
    id = "inception"
    name = "Inception"
    icon = "🎯"
    description = "Injecter des idées au coeur des pensées"
    order = 1
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self._active_inceptions = []
        self._tot_reasoner = None

    def _init_tot(self):
        """Initialize ToT with Corps Calleux"""
        if self._tot_reasoner is None:
            self._tot_reasoner = get_tot_reasoner()
            
            from server.extensions import registry
            if registry.corps_calleux:
                self._tot_reasoner.connect_corps_calleux(registry.corps_calleux)
    
    def render(self) -> str:
        return """
        <div class="module-inception module-1_Inception" id="module-inception" style="--module-color: #00d4ff; --module-color-rgb: 0, 212, 255;">
            <div class="module-description">
                <p>🎯 <strong>Inception</strong>: Injection ponctuelle d'une pensée ciblée. 
                Idéal pour introduire un concept, une direction, ou une hypothèse dans le flux cognitif.
                Le <strong>poids</strong> détermine l'influence sur la réflexion (0=ignoré, 100=dominant).</p>
            </div>
            
            <div class="inception-form">
                <h3>🎯 Injection de Pensée</h3>
                
                <div class="form-group">
                    <label>Pensée à injecter</label>
                    <textarea id="inception-prompt" rows="4" placeholder="Entrez la pensée à inoculer..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>Poids de l'Inception (0-100)</label>
                    <input type="range" id="inception-weight" min="0" max="100" value="50">
                    <span class="weight-value" id="weight-value">50</span>
                    <div class="setting-hint">
                        <small>0 = ignoré | 50 = modéré | 100 = dominant dans la réflexion</small>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Cible</label>
                    <div class="radio-group">
                        <label><input type="radio" name="target" value="LEFT" checked> Hémisphère Gauche</label>
                        <label><input type="radio" name="target" value="RIGHT"> Hémisphère Droit</label>
                        <label><input type="radio" name="target" value="BOTH"> Les Deux</label>
                    </div>
                </div>
                
                <button class="btn btn-primary" onclick="sendInception()">
                    🚀 Injecter l'Inception
                </button>
            </div>
            
            <div class="inceptions-list">
                <h3>📜 Inceptions Actives</h3>
                <div id="active-inceptions">
                    <p class="empty">Aucune inception active</p>
                </div>
            </div>
        </div>
        """
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "create":
            return self._create_inception(data)
        elif action == "list":
            return {"status": "ok", "inceptions": self._active_inceptions}
        elif action == "delete":
            return self._delete_inception(data.get("id"))
        elif action == "tot_toggle":
            return self._tot_toggle(data)
        elif action == "tot_status":
            return self._tot_status(data)
        elif action == "explore_with_tot":
            return self._explore_with_tot(data)
        return super().handle_action(action, data)

    def _tot_toggle(self, data: Dict) -> Dict:
        enabled = data.get("enabled", False)
        self._init_tot()
        
        if enabled:
            self._tot_reasoner.enable()
        else:
            self._tot_reasoner.disable()
        
        return {"status": "ok", "enabled": enabled}

    def _tot_status(self, data: Dict) -> Dict:
        self._init_tot()
        return {
            "status": "ok",
            "enabled": self._tot_reasoner.is_enabled(),
            "connected": self._tot_reasoner.is_connected()
        }

    def _explore_with_tot(self, data: Dict) -> Dict:
        """Explore a concept using ToT (sync wrapper)"""
        import asyncio
        
        self._init_tot()
        
        prompt = data.get("prompt", "")
        if not prompt:
            return {"status": "error", "message": "Prompt required"}
        
        self._tot_reasoner.enable()
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                result = loop.run_until_complete(self._tot_reasoner.think(prompt))
            else:
                result = loop.run_until_complete(self._tot_reasoner.think(prompt))
        except:
            result = {"solution": prompt, "error": "Could not run ToT"}
        
        return {
            "status": "ok",
            "result": result
        }
    
    def _create_inception(self, data: Dict) -> Dict:
        prompt = data.get("prompt", "")
        weight = data.get("weight", 50)
        target = data.get("target", "BOTH")
        
        if not prompt:
            return {"status": "error", "message": "Prompt vide"}
        
        inception = {
            "id": f"inc_{len(self._active_inceptions)}",
            "prompt": prompt,
            "weight": weight,
            "target": target,
            "injected": False
        }
        
        try:
            from server.extensions import registry
            
            if registry.corps_calleux:
                corps = registry.corps_calleux
                
                if target in ["LEFT", "BOTH"] and corps.left:
                    injection_prompt = f"[INCEPTION - Poids {weight}%] {prompt}"
                    corps.left.think(
                        "Intègre cette pensée de manière profonde dans ton subconscient.",
                        injection_prompt,
                        temperature=0.3
                    )
                    inception["injected_left"] = True
                
                if target in ["RIGHT", "BOTH"] and corps.right:
                    corps.right.think(
                        "Laisse cette idée germer dans ton subconscient intuitif.",
                        prompt,
                        temperature=0.7
                    )
                    inception["injected_right"] = True
                
                inception["injected"] = True
                
        except Exception as e:
            inception["error"] = str(e)
        
        self._active_inceptions.append(inception)
        
        return {"status": "ok", "inception": inception}
    
    def _delete_inception(self, inception_id: str) -> Dict:
        self._active_inceptions = [i for i in self._active_inceptions if i["id"] != inception_id]
        return {"status": "ok"}
