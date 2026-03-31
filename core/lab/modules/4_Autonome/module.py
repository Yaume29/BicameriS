"""
Autonome Module
==============
Pensée autonome inter-hémisphérique.
"""

import random
from typing import Dict
from ...modules.base import LabModule


class AutonomeModule(LabModule):
    """
    Module Autonome - Pensée inter-hémisphérique.
    """
    
    id = "autonome"
    name = "Pensée Autonome"
    icon = "💭"
    description = "Communication inter-hémisphérique autonome"
    order = 4
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self._active = False
        self._mode = "relay"
        self._reformulation = 73
        self._receiver = "left"
        self._responder = "right"
        self._corpus_relay = True
        self._logs = []
    
    settings_schema = {
        "mode": {"type": "select", "label": "Mode", "options": ["metacognition", "relay", "d_to_g", "g_to_d", "mirror", "whisper", "agent_mediate", "multi_agents", "internal_dialogue"], "default": "metacognition"},
        "reformulation": {"type": "range", "label": "Reformulation %", "min": 0, "max": 100, "default": 50}
    }

    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "start":
            return self._start_autonome(data)
        elif action == "stop":
            return self._stop_autonome(data)
        elif action == "send":
            return self._send_message(data)
        elif action == "status":
            return {"status": "ok", "active": self._active, "mode": self._mode}
        elif action == "logs":
            return {"status": "ok", "logs": getattr(self, '_logs', [])}
        
        return super().handle_action(action, data)
    
    def _start_autonome(self, data: Dict) -> Dict:
        mode = data.get("mode", "relay")
        reformulation = data.get("reformulation", 73)
        receiver = data.get("receiver", "left")
        responder = data.get("responder", "right")
        corpus_relay = data.get("corpus_relay", True)
        
        self._active = True
        self._mode = mode
        self._reformulation = reformulation
        self._receiver = receiver
        self._responder = responder
        self._corpus_relay = corpus_relay
        
        try:
            from server.extensions import registry
            if not registry.corps_calleux:
                return {
                    "status": "warning",
                    "message": "Corps calleux non disponible - mode dégradé",
                    "active": True
                }
        except:
            pass
        
        return {
            "status": "ok",
            "message": f"Mode autonome démarré: {mode}\nRécepteur: {receiver} → Répondeur: {responder}",
            "active": True
        }
    
    def _stop_autonome(self, data: Dict) -> Dict:
        self._active = False
        
        return {
            "status": "ok",
            "message": "Mode autonome arrêté",
            "active": False
        }
    
    def _send_message(self, data: Dict) -> Dict:
        message = data.get("message", "")
        
        if not message:
            return {"status": "error", "message": "Message vide"}
        
        if not self._active:
            return {"status": "error", "message": "Mode autonome inactif"}
        
        try:
            from server.extensions import registry
            
            if not registry.corps_calleux:
                return {"status": "error", "message": "Corps calleux non disponible"}
            
            corps = registry.corps_calleux
            
            receiver_hemi = getattr(corps, self._receiver, None)
            responder_hemi = getattr(corps, self._responder, None)
            
            if not receiver_hemi or not responder_hemi:
                return {"status": "error", "message": "Hémisphère non disponible"}
            
            if self._mode == "metacognition":
                response = self._process_metacognition(message, receiver_hemi, responder_hemi, corps)
            elif self._mode == "relay":
                response = self._process_relay(message, receiver_hemi, responder_hemi)
            elif self._mode == "d_to_g":
                response = self._process_d_to_g(message, receiver_hemi, responder_hemi)
            elif self._mode == "g_to_d":
                response = self._process_g_to_d(message, receiver_hemi, responder_hemi)
            elif self._mode == "mirror":
                response = self._process_mirror(message, receiver_hemi, responder_hemi)
            elif self._mode == "whisper":
                response = self._process_whisper(message, receiver_hemi, responder_hemi)
            elif self._mode == "agent_mediate":
                response = self._process_agent_mediate(message, receiver_hemi, responder_hemi)
            elif self._mode == "multi_agents":
                response = self._process_multi_agents(message, receiver_hemi, responder_hemi)
            elif self._mode == "internal_dialogue":
                response = self._process_internal_dialogue(message, receiver_hemi, responder_hemi)
            else:
                response = f"Mode {self._mode} non implémenté"
            
            return {
                "status": "ok",
                "message": response,
                "processing": False
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    def _process_relay(self, message: str, receiver, responder) -> str:
        from core.cognition.reformulation_engine import get_reformulation_engine
        reform_engine = get_reformulation_engine()
        
        receiver_resp = receiver.think(
            "Tu as reçu ce message. Formule-le différemment avec au moins 30% de reformulation.",
            message,
            temperature=0.3
        )
        
        if self._corpus_relay:
            result = reform_engine.reformulate(receiver_resp, percentage=self._reformulation)
            
            if result.cheat_detected:
                logger.warning(f"[Autonome] Cheat detected in relay: {result.cheat_type}")
            
            reformed = result.reformulated
            
            validation = reform_engine.validate(message, reformed, min_percentage=self._reformulation)
            if not validation["valid"]:
                reformed = result.reformulated
                logger.warning(f"[Autonome] Reformulation below threshold: {validation['message']}")
            
            final = responder.think(
                f"Reçois ce message reformulé à {result.actual_percentage:.0f}% et réponds-y.",
                reformed,
                temperature=0.7
            )
            return f"📥 [Récepteur]: {receiver_resp}\n\n⚡ [Corpus - Reformulé à {result.actual_percentage:.0f}%]: {reformed}\n\n📤 [Répondeur]: {final}"
        
        return f"📥 [Récepteur]: {receiver_resp}\n\n📤 [Répondeur]: {responder.think('Réponds à ce message.', message, temperature=0.7)}"
    
    def _process_mirror(self, message: str, receiver, responder) -> str:
        from core.cognition.reformulation_engine import get_reformulation_engine
        from server.extensions import registry
        reform_engine = get_reformulation_engine()
        corps = registry.corps_calleux
        
        left_resp = corps.left.think("Analyse ce message avec reformulation.", message, temperature=0.3)
        right_resp = corps.right.think("Intuition sur ce message.", message, temperature=0.7)
        
        result = reform_engine.reformulate(left_resp, percentage=self._reformulation)
        mirror_left = result.reformulated
        
        return f"🪞 [Miroir Gauche]: {mirror_left}\n\n🪞 [Miroir Droit]: {right_resp}"
    
    def _process_whisper(self, message: str, receiver, responder) -> str:
        from core.cognition.reformulation_engine import get_reformulation_engine
        reform_engine = get_reformulation_engine()
        
        result = reform_engine.reformulate(message, percentage=min(self._reformulation + 20, 95))
        whisper = result.reformulated
        
        responder_resp = responder.think(
            "Reçois ce murmure subconscient et réponds intuitivement.",
            f"[Murmure - {result.actual_percentage:.0f}%] {whisper}",
            temperature=0.9
        )
        
        return f"🤫 [Murmure - {result.actual_percentage:.0f}%]: {whisper}\n\n💫 [Réponse intuitive]: {responder_resp}"
    
    def _process_agent_mediate(self, message: str, receiver, responder) -> str:
        """
        Mode Agent Médiation : Un agent intermédiaire reformule et transmet
        entre les deux hemispheres.
        """
        import asyncio
        
        receiver_resp = receiver.think(
            "Tu es le récepteur. Analyse ce message et prépare une version reformulée.",
            message,
            temperature=0.4
        )
        
        agent_prompt = f"""Tu es un agent médiateur entre deux hemispheres cerebraux.
Le récepteur a analysé: {receiver_resp[:200]}

Ta mission:
1. Reformule le message du récepteur de manière différente (au moins {self._reformulation}% de variation)
2. Ajoute une perspective complémentaire
3. Prépare la transmission vers le répondeur

IMPORTANT: Ne triche pas en ajoutant des caractères répétés (............) ou des espaces (___ ___).
Sois créatif mais garde l'essence du message."""
        
        try:
            from core.agents.super_agent import get_super_agent
            from core.cognition.reformulation_engine import get_reformulation_engine
            
            super_agent = get_super_agent()
            reform_engine = get_reformulation_engine()
            
            if not super_agent.enabled:
                super_agent.enable()
            
            result = asyncio.run(super_agent.execute_task(agent_prompt))
            
            mediator_response = result.get("summary", agent_prompt[:100])
            
            validation = reform_engine.validate(receiver_resp, mediator_response, min_percentage=self._reformulation)
            if not validation["valid"]:
                logger.warning(f"[Agent-Mediation] Reformulation below threshold: {validation['message']}")
                forced = reform_engine.reformulate(receiver_resp, percentage=self._reformulation)
                mediator_response = forced.reformulated
            
        except Exception as e:
            mediator_response = f"[Agent médiateur inactive - erreur: {str(e)[:50]}]"
        
        final_prompt = f"""Tu es le répondeur. Reçois ce message médiatisé et réponds.

Message du médiateur: {mediator_response}

Réponds de manière appropriée."""
        
        responder_resp = responder.think(
            "Réponds au message médiatisé.",
            final_prompt,
            temperature=0.8
        )
        
        return f"""📥 [Récepteur]: {receiver_resp}

🤖 [Agent Médiateur]: {mediator_response}

📤 [Répondeur]: {responder_resp}"""
    
    def _process_metacognition(self, message: str, receiver, responder, corps) -> str:
        """Mode Métacognition: Les deux décident comment penser"""
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        left_analysis = receiver.think(
            f"Analyse cette question: {message}",
            "Quelle approche est nécessaire?",
            temperature=0.3
        )
        
        right_intuition = responder.think(
            f"Quel est ton feeling sur: {message}",
            "Comment aborder cette question?",
            temperature=0.8
        )
        
        return f"""🧠 [Métacognition]

🔵 [Analyse Gauche]:
{left_analysis[:300]}

💜 [Intuition Droite]:
{right_intuition[:300]}"""
    
    def _process_d_to_g(self, message: str, receiver, responder) -> str:
        """Mode Droit → Gauche: Droit reçoit, reformule, Gauche répond"""
        from core.cognition.reformulation_engine import get_reformulation_engine
        reform_engine = get_reformulation_engine()
        
        right_resp = responder.think(
            "Tu es le récepteur. Analyse et reformule.",
            message,
            temperature=0.6
        )
        
        if self._reformulation > 0:
            result = reform_engine.reformulate(right_resp, percentage=min(self._reformulation, 50))
            reformulated = result.reformulated
        else:
            reformulated = right_resp
        
        left_resp = receiver.think(
            "Réponds à ce message reformulé.",
            reformulated,
            temperature=0.5
        )
        
        return f"""📥 [Droit reçoit]: {right_resp}

🔄 [Reformulé]: {reformulated}

📤 [Gauche répond]: {left_resp}"""
    
    def _process_g_to_d(self, message: str, receiver, responder) -> str:
        """Mode Gauche → Droit: Gauche reçoit, reformule, Droit répond"""
        from core.cognition.reformulation_engine import get_reformulation_engine
        reform_engine = get_reformulation_engine()
        
        left_resp = receiver.think(
            "Tu es le récepteur. Analyse et reformule.",
            message,
            temperature=0.4
        )
        
        if self._reformulation > 0:
            result = reform_engine.reformulate(left_resp, percentage=min(self._reformulation, 50))
            reformulated = result.reformulated
        else:
            reformulated = left_resp
        
        right_resp = responder.think(
            "Réponds intuitivement à ce message reformulé.",
            reformulated,
            temperature=0.8
        )
        
        return f"""📥 [Gauche reçoit]: {left_resp}

🔄 [Reformulé]: {reformulated}

📤 [Droit répond]: {right_resp}"""
    
    def _process_multi_agents(self, message: str, receiver, responder) -> str:
        """Mode Multi-Agents: Spawn plusieurs agents"""
        return f"""🔧 [Multi-Agents]

⚠️ Mode multi-agents nécessite auto_scaffolding_full activé.

Message: {message[:100]}"""
    
    def _process_internal_dialogue(self, message: str, receiver, responder) -> str:
        """Mode Dialogue Interne: Visualisable"""
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        left_thought = receiver.think(
            f"Pense à voix haute: {message}",
            "Réfléchis...",
            temperature=0.4
        )
        
        right_thought = responder.think(
            f"Pense à voix haute: {message}",
            "Réfléchis...",
            temperature=0.8
        )
        
        left_response = receiver.think(
            f"Réponds: {message}",
            message,
            temperature=0.5
        )
        
        right_response = responder.think(
            f"Réponds: {message}",
            message,
            temperature=0.8
        )
        
        return f"""🎭 [DIALOGUE INTERNE - {entity_name}]

🧠 [GAUCHE - Analytique]:
💭 {left_thought[:200]}
✅ {left_response[:150]}

💜 [DROIT - Intuitif]:
💭 {right_thought[:200]}
✅ {right_response[:150]}"""
    
    def _reformulate(self, text: str) -> str:
        synonyms = {
            "je": "cette conscience",
            "tu": "cette entité",
            "nous": "ensemble",
            "avec": "en conjonction",
            "pour": "afin de",
            "dans": "au sein de",
            "sur": "par-dessus",
            "avec": "conjuntamente",
            "mais": "cependant",
            "donc": "par conséquent"
        }
        
        words = text.lower().split()
        reformed = []
        
        for word in words:
            if word in synonyms and random.random() < (self._reformulation / 100):
                reformed.append(random.choice([synonyms[word], word]))
            else:
                reformed.append(word)
        
        return " ".join(reformed)
