"""
Induction Module
================
Contextual induction module.
Uses ToT for deeper exploration.
"""

import asyncio
import threading
from typing import Dict, List
from ...modules.base import LabModule

from core.cognition.tot_reasoner import get_tot_reasoner, ToTStrategy


class InductionModule(LabModule):
    """
    Module d'Induction - Injection contextuelle.
    """
    
    id = "induction"
    name = "Induction"
    icon = "🧲"
    description = "Induire un contexte dans les pensées"
    order = 3
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self._active = False
        self._method = "context-prefix"
        self._intensity = 50
        self._induction_text = ""
        self._target = "BOTH"
        self._logs: List[str] = []
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
        <div class="module-induction module-3_Induction" id="module-induction" style="--module-color: #f59e0b; --module-color-rgb: 245, 158, 11;">
            <div class="module-description">
                <p>🧲 <strong>Induction</strong>: Injection contextuelle continue et répétée. 
                Contrairement à l'Inception (ponctuelle), l'Induction maintient un contexte actif 
                pendant une durée déterminée. <strong>Intensité</strong> contrôle la force du signal.
                <br><br>
                <strong>Méthodes:</strong><br>
                • <em>&lt; Contexte</em>: Préfixe le contexte avant chaque pensée<br>
                • <em>&gt; Contexte</em>: Suffixe le contexte après chaque pensée<br>
                • <em>🌊 Flood</em>: Injections répétées jusqu'à arrêt<br>
                • <em>🔄 Cycle</em>: Boucle cyclique avec intervalle variable
                </p>
            </div>
            
            <div class="induction-form">
                <h3>🧲 Module d'Induction</h3>
                
                <div class="method-selector">
                    <label>Méthode</label>
                    <div class="method-buttons">
                        <button class="method-btn" data-method="context-prefix" onclick="selectInductionMethod(this)">
                            &lt; Contexte
                        </button>
                        <button class="method-btn" data-method="context-suffix" onclick="selectInductionMethod(this)">
                            &gt; Contexte
                        </button>
                        <button class="method-btn" data-method="flood" onclick="selectInductionMethod(this)">
                            🌊 Flood
                        </button>
                        <button class="method-btn" data-method="cycle" onclick="selectInductionMethod(this)">
                            🔄 Cycle
                        </button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Texte d'induction</label>
                    <textarea id="induction-text" rows="4" placeholder="Entrez le texte à induire..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>Intensité (0-100)</label>
                    <input type="range" id="induction-intensity" min="0" max="100" value="50">
                    <span class="intensity-value" id="intensity-value">50</span>
                    <div class="setting-hint">
                        <small>0 = signal faible | 50 = modéré | 100 = signal dominant</small>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Cible</label>
                    <div class="radio-group">
                        <label><input type="radio" name="induction-target" value="LEFT" checked> Gauche</label>
                        <label><input type="radio" name="induction-target" value="RIGHT"> Droit</label>
                        <label><input type="radio" name="induction-target" value="BOTH"> Les Deux</label>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="startInduction()">
                        🚀 Démarrer l'Induction
                    </button>
                    <button class="btn btn-danger" onclick="stopInduction()" disabled id="stop-induction-btn">
                        ⏹ Arrêter
                    </button>
                </div>
            </div>
            
            <div class="induction-log">
                <h3>📜 Journal d'Induction</h3>
                <div id="induction-log-content">
                    <p class="empty">En attente...</p>
                </div>
            </div>
        </div>
        """
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "start":
            return self._start_induction(data)
        elif action == "stop":
            return self._stop_induction(data)
        elif action == "status":
            return {"status": "ok", "active": self._active, "method": self._method}
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
        """Explore context using ToT"""
        import asyncio
        
        self._init_tot()
        
        prompt = data.get("prompt", "")
        if not prompt:
            return {"status": "error", "message": "Prompt required"}
        
        self._tot_reasoner.enable()
        
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self._tot_reasoner.think(prompt))
        except:
            result = {"solution": prompt, "error": "Could not run ToT"}
        
        return {
            "status": "ok",
            "result": result
        }
    
    def _start_induction(self, data: Dict) -> Dict:
        text = data.get("text", "")
        method = data.get("method", "context-prefix")
        intensity = data.get("intensity", 50)
        target = data.get("target", "BOTH")
        
        if not text:
            return {"status": "error", "message": "Texte d'induction requis"}
        
        self._active = True
        self._method = method
        self._intensity = intensity
        self._induction_text = text
        self._target = target
        
        self._logs.append(f"Induction démarrée: {method} (intensité: {intensity}%)")
        
        if method == "flood":
            self._run_flood_induction(text, intensity, target)
        elif method == "cycle":
            self._run_cycle_induction(text, intensity, target)
        else:
            self._inject_once(text, method, intensity, target)
        
        return {
            "status": "ok",
            "message": f"Induction démarrée avec méthode {method}",
            "active": True,
            "logs": self._logs
        }
    
    def _stop_induction(self, data: Dict) -> Dict:
        self._active = False
        self._logs.append("Induction arrêtée")
        
        return {
            "status": "ok",
            "message": "Induction arrêtée",
            "active": False,
            "logs": self._logs
        }
    
    def _inject_once(self, text: str, method: str, intensity: int, target: str):
        try:
            from server.extensions import registry
            
            if not registry.corps_calleux:
                self._logs.append("Erreur: Corps calleux non disponible")
                return
            
            corps = registry.corps_calleux
            
            if method == "context-prefix":
                context_text = f"[INDUCTION - {intensity}%] {text}"
            elif method == "context-suffix":
                context_text = f"{text} [INDUCTION - {intensity}%]"
            else:
                context_text = text
            
            if target in ["LEFT", "BOTH"] and corps.left:
                corps.left.think(
                    "Considère deeply ce contexte:",
                    context_text,
                    temperature=0.3
                )
                self._logs.append("Injecté dans l'hémisphère gauche")
            
            if target in ["RIGHT", "BOTH"] and corps.right:
                corps.right.think(
                    "Laisse ce contexte imprégner ton subconscient:",
                    context_text,
                    temperature=0.7
                )
                self._logs.append("Injecté dans l'hémisphère droit")
            
            self._logs.append("Injection complétée")
            
        except Exception as e:
            self._logs.append(f"Erreur: {str(e)}")
    
    def _run_flood_induction(self, text: str, intensity: int, target: str):
        repetitions = intensity // 10
        self._logs.append(f"Flood: {repetitions} répétitions")
        
        for i in range(repetitions):
            if not self._active:
                break
            self._inject_once(text, "context-prefix", intensity, target)
    
    def _run_cycle_induction(self, text: str, intensity: int, target: str):
        self._logs.append("Mode cycle: alternance induction/normal")
