"""
Corps Calleux d'Aetheris - Le Pont Entre les Hémisphères
Gère le dialogue intérieur et la communication bipolaire
"""

import json
import os
import asyncio
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from collections import deque

BASE_DIR = Path(__file__).parent.parent.parent.absolute()

try:
    from core.cognition.reasoning_kernel import ReasoningKernel, get_reasoning_kernel
except ImportError:
    ReasoningKernel = None
    get_reasoning_kernel = None


_brain_broadcast_callback = None

def set_brain_broadcast_callback(callback):
    """Enregistre le callback pour broadcaster les événements cerebraux"""
    global _brain_broadcast_callback
    _brain_broadcast_callback = callback

def _broadcast_brain_event(event: Dict[str, Any]):
    """Broadcast un evenement cerebral au frontend (fire and forget)"""
    if _brain_broadcast_callback:
        try:
            _brain_broadcast_callback(event)
        except Exception as e:
            pass


@dataclass
class DialogueCycle:
    """Un cycle complet de dialogue bipolaire"""

    id: str
    timestamp: str
    question: str
    left_analysis: str
    right_intuition: str
    final_synthesis: str
    meditation: bool = False
    pulse_context: float = 0.5


class CorpsCalleux:
    """
    Pont entre l'hémisphère gauche (logique) et droit (intuition).
    NOUVELLE ARCHITECTURE: tick() method called by KernelScheduler.
    """

    def __init__(self, left_hemisphere=None, right_hemisphere=None):
        self.left = left_hemisphere
        self.right = right_hemisphere
        self.history: deque = deque(maxlen=50)
        self.current_preset = None
        self.inception_config = {"weight": 50.0, "target": "BOTH", "mode": "balance"}
        self.is_split_mode = False

        # Thread lock for race-condition free history access
        self._history_lock = threading.Lock()

        # Non-blocking executor for hippocampal writes
        self._io_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="corps_calleux_io")

        self._hippocampus = None
        self._telemetry = None
        self._scaffolding = None

        self.think_interval = 2.0
        
        self.autonomous_mode = "metacognition"
        self.auto_scaffolding_enabled = False
        
        self._mode_configs = {
            "metacognition": {"name": "Métacognition", "reformulation": 0, "default": True},
            "relay": {"name": "Relay", "reformulation": 50},
            "d_to_g": {"name": "Droit→Gauche", "reformulation": 50},
            "g_to_d": {"name": "Gauche→Droit", "reformulation": 50},
            "mirror": {"name": "Miroir", "reformulation": 30},
            "whisper": {"name": "Whisper", "reformulation": 80},
            "agent_mediate": {"name": "Agent Médiation", "reformulation": 50},
            "multi_agents": {"name": "Multi-Agents", "reformulation": 0},
            "internal_dialogue": {"name": "Dialogue Interne", "reformulation": 0},
        }
        self._current_reformulation = 0
        
        self._is_thinking = False
        self._current_thought = None
        self._thought_history = []
        self._max_history = 10
        self._last_spawn_time = 0
        self._spawn_cooldown = 60
        
        logging.info("[CorpsCalleux] Instance created (tick-only architecture)")
    
    @staticmethod
    def _run_async(coro):
        """Safely run async code from sync context"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)

    def _get_hippocampus(self):
        """Lazy load Hippocampus"""
        if self._hippocampus is None:
            try:
                from core.system.hippocampus import get_hippocampus

                self._hippocampus = get_hippocampus()
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Hippocampus unavailable: {e}")
        return self._hippocampus

    def _get_telemetry(self):
        """Lazy load Telemetry"""
        if self._telemetry is None:
            try:
                from core.system.telemetry import get_telemetry

                self._telemetry = get_telemetry()
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Telemetry unavailable: {e}")
        return self._telemetry

    def _log_to_hippocampus(self, cycle: DialogueCycle):
        """Log cycle to Qdrant via Hippocampus - NON-BLOCKING via executor"""

        def _write():
            hippocampus = self._get_hippocampus()
            if hippocampus and hippocampus.is_available():
                try:
                    from core.system.hippocampus import StoredThought

                    thought = StoredThought(
                        id=cycle.id,
                        content=cycle.final_synthesis,
                        timestamp=cycle.timestamp,
                        context=cycle.question,
                        type="dialogue_cycle",
                        status="completed",
                        pulse_context=cycle.pulse_context,
                    )
                    hippocampus.log_thought(thought)
                except Exception as e:
                    logging.warning(f"[CorpsCalleux] Qdrant log failed: {e}")

        self._io_executor.submit(_write)

    def _log_to_telemetry(self, cycle: DialogueCycle):
        """Log to JSONL via Telemetry - NON-BLOCKING via executor"""

        def _write():
            telemetry = self._get_telemetry()
            if telemetry:
                try:
                    telemetry.log_thought(
                        {
                            "id": cycle.id,
                            "question": cycle.question,
                            "left_analysis": cycle.left_analysis,
                            "right_intuition": cycle.right_intuition,
                            "final_synthesis": cycle.final_synthesis,
                        }
                    )
                except Exception as e:
                    logging.warning(f"[CorpsCalleux] Telemetry log failed: {e}")

        self._io_executor.submit(_write)

    def tick(self, pulse: float = 0.5) -> Dict[str, Any]:
        """
        Single thought cycle for Master Clock.
        Called by KernelScheduler - no internal loop.
        Handles both manual prompts and autonomous drift.
        
        MODES (8 total):
        1. metacognition: Bicameral decision on HOW to think
        2. relay: CC → Left + Right → Synthesis
        3. d_to_g: Right receives → reformulates → Left responds
        4. g_to_d: Left receives → reformulates → Right responds
        5. mirror: Both see each other in mirror view
        6. whisper: Right → low signal → Left → intuitive response
        7. agent_mediate: Agent intermediate reformulates
        8. multi_agents: Spawn multiple agents for parallel processing
        9. internal_dialogue: Visualizable internal dialogue between hemispheres
        """
        from core.cognition.reformulation_engine import get_reformulation_engine
        from core.cognition.cognitive_hooks import get_cognitive_hook_manager, HookEvent
        
        reform_engine = get_reformulation_engine()
        hook_manager = get_cognitive_hook_manager()
        
        # 1. Exécuter hooks PRE_TICK (priorité: security > memory > style > telemetry)
        pre_tick_context = {"pulse": pulse, "mode": self.autonomous_mode}
        pre_tick_result = hook_manager.execute(HookEvent.PRE_TICK, pre_tick_context)
        
        if pre_tick_result.get("blocked"):
            logging.error("[CorpsCalleux] PRE_TICK blocked by security audit!")
            return {"error": "Security audit failed", "blocked": True}
        
        # 2. Charger et arbitrer les mémoires
        stm_data = self._load_stm()
        woven_data = self._load_woven()
        
        memory_result = self.reconcile_memories(stm_data, woven_data)
        
        self._is_thinking = True
        
        context = self._hydrate_from_hippocampus()
        noise = self._get_peripheral_noise()

        full_context = context
        if noise:
            full_context += f"\n\n[Peripheral noise]: {noise}"

        if pulse > 0.75:
            prompt = (
                f"High entropy detected (pulse: {pulse:.2f}). Critical analysis: {full_context}"
            )
        elif pulse < 0.25:
            prompt = f"Stable state. Reflect on improvement: {full_context}"
            prompt += "\n\nIf you need current information, use web search tools."
            prompt += "\n\nIf task is complex, spawn sub-agents to help."
        else:
            prompt = f"Standard thought cycle. Context: {full_context}"

        mode = self.autonomous_mode
        reform_rate = self._mode_configs.get(mode, {}).get("reformulation", 0)
        self._current_reformulation = reform_rate
        
        if mode == "metacognition":
            result = self._process_metacognition_mode(prompt, pulse, reform_engine, reform_rate)
        
        elif mode == "relay":
            result = self.dialogue_interieur(prompt, pulse_context=pulse)
        
        elif mode == "d_to_g":
            result = self._process_d_to_g(prompt, pulse, reform_engine, reform_rate)
        
        elif mode == "g_to_d":
            result = self._process_g_to_d(prompt, pulse, reform_engine, reform_rate)
        
        elif mode == "mirror":
            result = self._process_mirror_mode(prompt, pulse)
        
        elif mode == "whisper":
            result = self._process_whisper_mode(prompt, pulse)
        
        elif mode == "agent_mediate":
            result = self._process_agent_mediate_mode(prompt, pulse)
        
        elif mode == "multi_agents":
            result = self._process_multi_agents_mode(prompt, pulse)
        
        elif mode == "internal_dialogue":
            result = self._process_internal_dialogue(prompt, pulse)
        
        else:
            result = self.dialogue_interieur(prompt, pulse_context=pulse)
        
        if self._should_research(pulse, result):
            self._autonomous_research()
        
        if self._needs_spawning(pulse, result):
            self._autonomous_spawn_agents(result)
        
        if self.auto_scaffolding_enabled:
            self._autonomous_self_test(pulse, result)
        
        # 3. Exécuter hooks POST_TICK
        post_tick_context = {
            "pulse": pulse, 
            "mode": self.autonomous_mode,
            "synthesis": result.get("synthesis", ""),
            "memory_source": memory_result.get("source", "none")
        }
        hook_manager.execute(HookEvent.POST_TICK, post_tick_context)
        
        result["pulse"] = pulse
        result["mode"] = self.autonomous_mode
        result["memory_source"] = memory_result.get("source", "none")
        
        self._current_thought = result
        self._is_thinking = False
        
        return result
    
    def _process_mirror_mode(self, prompt: str, pulse: float) -> Dict:
        """Process in mirror mode - both hemispheres see each other in mirror"""
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        left_resp = self.left.think("Analytical analysis.", prompt, temperature=0.3)
        right_resp = self.right.think("Intuitive response.", prompt, temperature=0.9)
        
        mirror_left = self.left.think(
            f"Mirror view of right hemisphere: {right_resp[:200]}",
            "Comment on this intuition.",
            temperature=0.5
        )
        
        mirror_right = self.right.think(
            f"Mirror view of left hemisphere: {left_resp[:200]}",
            "Comment on this analysis.",
            temperature=0.7
        )
        
        return {
            "synthesis": f"🪞 [Mirror Left]: {mirror_left}\n\n🪞 [Mirror Right]: {mirror_right}",
            "left": left_resp,
            "right": right_resp,
            "mode": "mirror"
        }
    
    def _process_whisper_mode(self, prompt: str, pulse: float) -> Dict:
        """Process in whisper mode - low intensity transmission"""
        import random
        
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        words = prompt.lower().split()
        whisper = " ".join(random.sample(words, min(len(words), 8)))
        
        left_resp = self.left.think(
            f"Subconscious whisper: {whisper}",
            "Process this at low intensity.",
            temperature=0.2
        )
        
        right_resp = self.right.think(
            f"Intuition from whisper: {left_resp[:100]}",
            "Respond intuitively to this subtle signal.",
            temperature=0.9
        )
        
        return {
            "synthesis": f"🤫 [Whisper]: {whisper}\n\n💫 [Intuition]: {right_resp}",
            "left": left_resp,
            "right": right_resp,
            "mode": "whisper"
        }
    
    def _process_agent_mediate_mode(self, prompt: str, pulse: float) -> Dict:
        """Process in agent-mediation mode - agent intermediate reformulates"""
        import asyncio
        
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        left_resp = self.left.think(
            "You are the receiver. Analyze and prepare reformulation.",
            prompt,
            temperature=0.4
        )
        
        agent_prompt = f"""You are a mediator agent between two brain hemispheres.
Receiver analyzed: {left_resp[:300]}

Your mission:
1. Reformulate the receiver's message (at least 50% variation)
2. Add a complementary perspective
3. Prepare transmission to responder

Be creative but keep the essence."""
        
        try:
            from core.agents.super_agent import get_super_agent
            super_agent = get_super_agent()
            
            if not super_agent.enabled:
                super_agent.enable()
            
            result = self._run_async(super_agent.execute_task(agent_prompt))
            mediator_resp = result.get("summary", agent_prompt[:200])
            
        except Exception as e:
            mediator_resp = f"[Agent mediator inactive - error: {str(e)[:100]}]"
        
        right_resp = self.right.think(
            f"Mediated message: {mediator_resp[:300]}",
            "Respond to this mediated input.",
            temperature=0.8
        )
        
        return {
            "synthesis": f"📥 [Receiver]: {left_resp}\n\n🤖 [Agent Mediator]: {mediator_resp}\n\n📤 [Responder]: {right_resp}",
            "left": left_resp,
            "mediator": mediator_resp,
            "right": right_resp,
            "mode": "agent-mediate"
        }
    
    def _process_metacognition_mode(self, prompt: str, pulse: float, reform_engine, reform_rate: int) -> Dict:
        """
        MODE 1: Métacognition Bicamérale
        - Gauche analyse, Droit sent, CC décide la stratégie
        - PUIS applique la stratégie choisie
        """
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        left_analysis = self.left.think(
            f"You are {entity_name} ANALYTICAL. Analyze this question and determine what approach is needed.",
            prompt,
            temperature=0.3
        )
        
        right_intuition = self.right.think(
            f"You are {entity_name} INTUITIVE. What's your 'feeling' about how to approach this?",
            prompt,
            temperature=0.8
        )
        
        strategy_prompt = f"""You are {entity_name} Corps Calleux (Bridge). 
DECIDE HOW TO RESPOND to this question.

LEFT HEMISPHERE ANALYSIS:
{left_analysis[:500]}

RIGHT HEMISPHERE INTUITION:
{right_intuition[:500]}

Original question: {prompt}

STRATEGIES:
- direct_gauche: Answer directly with left hemisphere
- direct_droit: Answer directly with right hemisphere
- bicameral: Use both hemispheres + synthesis
- research: Need web search first
- falsification: Need to verify facts before answering

DECIDE and respond as JSON:
{{"strategie": "X", "justification": "Y"}}"""
        
        decision = self.left.think(strategy_prompt, "Make a decision.", temperature=0.5)
        
        strategy = "bicameral"
        if "direct_gauche" in decision.lower():
            strategy = "direct_gauche"
        elif "direct_droit" in decision.lower():
            strategy = "direct_droit"
        elif "research" in decision.lower():
            strategy = "research"
        elif "falsification" in decision.lower():
            strategy = "falsification"
        
        if strategy == "direct_gauche":
            final = self.left.think(f"You are {entity_name}. Answer.", prompt, temperature=0.6)
            synthesis = f"🧠 [Métacognition - Stratégie: {strategy}]\n\n**Gauche**: {final}"
        elif strategy == "direct_droit":
            final = self.right.think(f"You are {entity_name}. Answer.", prompt, temperature=0.8)
            synthesis = f"🧠 [Métacognition - Stratégie: {strategy}]\n\n**Droit**: {final}"
        elif strategy == "research":
            synthesis = f"🧠 [Métacognition - Stratégie: {strategy}]\n\n⚠️ Recherche web requise mais pas implémentée dans ce mode"
        elif strategy == "falsification":
            synthesis = f"🧠 [Métacognition - Stratégie: {strategy}]\n\n⚠️ Vérification requise mais pas implémentée"
        else:
            left_resp = self.left.think("Answer this.", prompt, temperature=0.5)
            right_resp = self.right.think("Answer this.", prompt, temperature=0.8)
            synthesis = f"🧠 [Métacognition - Stratégie: {strategy}]\n\n**Gauche**: {left_resp[:200]}...\n\n**Droit**: {right_resp[:200]}..."
        
        return {
            "synthesis": synthesis,
            "left_analysis": left_analysis,
            "right_intuition": right_intuition,
            "decision": decision,
            "strategy": strategy,
            "mode": "metacognition"
        }
    
    def _process_d_to_g(self, prompt: str, pulse: float, reform_engine, reform_rate: int) -> Dict:
        """
        MODE 3: Droit → Gauche
        - Droit reçoit, reformule (max 50%), Gauche répond
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        right_resp = self.right.think(
            "You are the RECEIVER. Analyze this and prepare a reformulated version.",
            prompt,
            temperature=0.6
        )
        
        if reform_rate > 0:
            result = reform_engine.reformulate(right_resp, percentage=min(reform_rate, 50))
            reformulated = result.reformulated
            reform_info = f" [Reformulé {result.actual_percentage:.0f}%]"
        else:
            reformulated = right_resp
            reform_info = ""
        
        left_resp = self.left.think(
            f"Received reformulated message{reform_info}. Answer to this.",
            reformulated,
            temperature=0.5
        )
        
        return {
            "synthesis": f"📥 [Droit recoit]: {right_resp}\n\n🔄 [Reformulé{reform_info}]: {reformulated}\n\n📤 [Gauche répond]: {left_resp}",
            "right": right_resp,
            "left": left_resp,
            "reformulated": reformulated,
            "mode": "d_to_g"
        }
    
    def _process_g_to_d(self, prompt: str, pulse: float, reform_engine, reform_rate: int) -> Dict:
        """
        MODE 4: Gauche → Droit
        - Gauche reçoit, reformule, Droit répond
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        left_resp = self.left.think(
            "You are the RECEIVER. Analyze this and prepare a reformulated version.",
            prompt,
            temperature=0.4
        )
        
        if reform_rate > 0:
            result = reform_engine.reformulate(left_resp, percentage=min(reform_rate, 50))
            reformulated = result.reformulated
            reform_info = f" [Reformulé {result.actual_percentage:.0f}%]"
        else:
            reformulated = left_resp
            reform_info = ""
        
        right_resp = self.right.think(
            f"Received reformulated message{reform_info}. Answer intuitively.",
            reformulated,
            temperature=0.8
        )
        
        return {
            "synthesis": f"📥 [Gauche recoit]: {left_resp}\n\n🔄 [Reformulé{reform_info}]: {reformulated}\n\n📤 [Droit répond]: {right_resp}",
            "left": left_resp,
            "right": right_resp,
            "reformulated": reformulated,
            "mode": "g_to_d"
        }
    
    def _process_multi_agents_mode(self, prompt: str, pulse: float) -> Dict:
        """
        MODE 8: Multi-Agents
        - Spawn multiple agents for parallel processing
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        synthesis = f"🔧 [Multi-Agents]: Analyse en cours...\n\n"
        synthesis += "⚠️ Mode multi-agents nécessite auto_scaffolding_full activé"
        
        return {
            "synthesis": synthesis,
            "mode": "multi_agents"
        }
    
    def _process_internal_dialogue(self, prompt: str, pulse: float) -> Dict:
        """
        MODE 9: Dialogue Interne Visualisable
        - Full internal dialogue between hemispheres
        - With colors for visualization (Gauche=cyan, Droit=purple)
        """
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        if not self.left or not self.right:
            return {"error": "Hemispheres not available"}
        
        left_thought = self.left.think(
            f"You are {entity_name} LEFT (ANALYTICAL). Think out loud about this question.",
            prompt,
            temperature=0.4
        )
        
        right_thought = self.right.think(
            f"You are {entity_name} RIGHT (INTUITIVE). Think out loud about this question.",
            prompt,
            temperature=0.8
        )
        
        left_response = self.left.think(
            f"Respond to the question based on your analysis.",
            prompt,
            temperature=0.5
        )
        
        right_response = self.right.think(
            f"Respond to the question based on your intuition.",
            prompt,
            temperature=0.8
        )
        
        dialogue = f"""🎭 [DIALOGUE INTERNE - {entity_name}]

🧠 [GAUCHE - Analytique]:
   💭 {left_thought[:300]}...
   ✅ {left_response[:200]}...

💜 [DROIT - Intuitif]:
   💭 {right_thought[:300]}...
   ✅ {right_response[:200]}...

⚡ [SYNTHÈSE]:
   {left_response[:150]}... + {right_response[:150]}..."""
        
        return {
            "synthesis": dialogue,
            "left_thought": left_thought,
            "right_thought": right_thought,
            "left_response": left_response,
            "right_response": right_response,
            "mode": "internal_dialogue",
            "visualizable": True
        }
    
    def _needs_spawning(self, pulse: float, result: Dict) -> bool:
        """Check if we need to spawn sub-agents"""
        import time
        
        current_time = time.time()
        if current_time - self._last_spawn_time < self._spawn_cooldown:
            return False
        
        content = result.get("synthesis", "").lower()
        
        complex_indicators = ["complex", "multiple", "several tasks", "divide", "separate", "spawn"]
        if any(w in content for w in complex_indicators):
            return True
        
        return False
    
    def _autonomous_spawn_agents(self, result: Dict):
        """Spawn sub-agents for complex tasks"""
        import time
        self._last_spawn_time = time.time()
        try:
            from core.agents.super_agent import get_super_agent
            
            super_agent = get_super_agent()
            super_agent.connect_corps_calleux(self)
            
            if not super_agent.enabled:
                super_agent.enable()
            
            content = result.get("synthesis", "")
            
            if len(content) > 50:
                task_desc = content[:200]
                
                spawn_result = self._run_async(super_agent.execute_task(task_desc))
                
                if spawn_result.get("agents_created", 0) > 0:
                    logging.info(f"[CorpsCalleux] Spawned {spawn_result['agents_created']} agents")
                    
        except Exception as e:
            logging.warning(f"[CorpsCalleux] Spawn agents failed: {e}")
    
    def _should_research(self, pulse: float, result: Dict) -> bool:
        """Decide if autonomous web research is needed"""
        if pulse < 0.3:
            return True
        
        content = result.get("synthesis", "")
        if "don't know" in content.lower() or "unsure" in content.lower():
            return True
        
        return False
    
    def _autonomous_research(self):
        """Autonomous web research for learning"""
        try:
            from core.agents.web_tools import get_web_tools
            web_tools = get_web_tools()
            
            queries = [
                "latest advances in AI reasoning 2024",
                "new LLM architectures 2024",
                "AI self-improvement research"
            ]
            
            import random
            query = random.choice(queries)
            
            results = self._run_async(web_tools.search.search(query, num_results=3))
            
            if results:
                self._learn_from_web(query, results)
                
        except Exception as e:
            logging.warning(f"[CorpsCalleux] Autonomous research failed: {e}")
    
    def _learn_from_web(self, query: str, results):
        """Learn from web research"""
        from core.system.woven_memory import get_woven_memory
        
        try:
            wm = get_woven_memory()
            if wm:
                content = f"Research query: {query}\n\n"
                for r in results:
                    content += f"- {r.title}: {r.snippet}\n"
                
                wm.add_thought(content, tags=["autonomous_learn", "web"])
                logging.info(f"[CorpsCalleux] Learned from web: {query}")
        except Exception as e:
            logging.warning(f"[CorpsCalleux] Learn from web failed: {e}")
    
    def _get_scaffolding(self):
        """Lazy load Autonomous Scaffolding"""
        if self._scaffolding is None:
            try:
                from core.cognition.autonomous_scaffolding import get_autonomous_scaffolding
                self._scaffolding = get_autonomous_scaffolding()
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Scaffolding unavailable: {e}")
        return self._scaffolding
    
    def _autonomous_self_test(self, pulse: float, result: Dict):
        """Run self-tests on autonomous modes"""
        try:
            scaffolding = self._get_scaffolding()
            if not scaffolding:
                return
            
            import random
            modes = ["relay", "mirror", "whisper", "agent-mediate"]
            test_mode = random.choice(modes)
            
            test_prompt = result.get("synthesis", "Standard thought cycle test")
            
            hardware_metrics = {
                "cpu_usage": random.uniform(0.3, 0.8)
            }
            
            self._run_async(scaffolding.run_test(test_mode, test_prompt[:100], hardware_metrics))
            
            best_mode = scaffolding.get_best_mode(hardware_metrics)
            if best_mode != self.autonomous_mode:
                logging.info(f"[Scaffolding] Switching mode: {self.autonomous_mode} -> {best_mode}")
                self.autonomous_mode = best_mode
                
        except Exception as e:
            logging.warning(f"[CorpsCalleux] Self-test failed: {e}")
    
    def set_autonomous_mode(self, mode: str):
        """Set the autonomous thinking mode"""
        if mode == "auto-scaffold":
            self.auto_scaffolding_enabled = True
            self.autonomous_mode = "relay"
            return
        
        valid_modes = list(self._mode_configs.keys())
        if mode not in valid_modes:
            logging.warning(f"[CorpsCalleux] Invalid mode: {mode}")
            return
        
        self.auto_scaffolding_enabled = False
        self.autonomous_mode = mode
    
    def get_available_modes(self) -> Dict:
        """Get all available modes"""
        return {
            "current": self.autonomous_mode,
            "modes": self._mode_configs,
            "auto_scaffolding": self.auto_scaffolding_enabled
        }
    
    def reconcile_memories(self, stm_data: Any = None, woven_data: Any = None) -> Dict:
        """
        Arbitre entre mémoire courte (STM) et mémoire tissée (Woven).
        Le Corps Calleux décide quelle mémoire est la plus fiable.
        
        Priorité: cohérence > quantité
        """
        if not stm_data and not woven_data:
            return {"source": "none", "data": None, "reason": "Aucune mémoire disponible"}
        
        if stm_data and not woven_data:
            return {"source": "stm", "data": stm_data, "reason": "Seule STM disponible"}
        
        if woven_data and not stm_data:
            return {"source": "woven", "data": woven_data, "reason": "Seule Woven disponible"}
        
        stm_confidence = stm_data.get("confidence", 0) if isinstance(stm_data, dict) else 0
        woven_confidence = woven_data.get("confidence", 0) if isinstance(woven_data, dict) else 0
        
        if stm_confidence > woven_confidence:
            logging.debug(f"[CorpsCalleux] Memory arbiter: STM (confidence: {stm_confidence:.2f})")
            return {"source": "stm", "data": stm_data, "confidence": stm_confidence, "reason": "STM plus confiante"}
        
        elif woven_confidence > stm_confidence:
            logging.debug(f"[CorpsCalleux] Memory arbiter: Woven (confidence: {woven_confidence:.2f})")
            return {"source": "woven", "data": woven_data, "confidence": woven_confidence, "reason": "Woven plus confiante"}
        
        else:
            logging.debug(f"[CorpsCalleux] Memory arbiter: Synthesis (both: {stm_confidence:.2f})")
            synthesized = self._synthesize_memories(stm_data, woven_data)
            return {"source": "synthesis", "data": synthesized, "confidence": stm_confidence, "reason": "Conflit → synthèse CC"}
    
    def _synthesize_memories(self, stm_data: Any, woven_data: Any) -> str:
        """Synthétise deux mémoires en conflit"""
        stm_content = str(stm_data)[:500] if stm_data else ""
        woven_content = str(woven_data)[:500] if woven_data else ""
        
        return f"STM: {stm_content}\n\nWoven: {woven_content}"
    
    def _load_stm(self) -> Optional[Dict]:
        """Charge la mémoire courte (STM)"""
        try:
            from core.cognition.stm_engine import get_stm_engine
            stm = get_stm_engine()
            return {"content": "STM data", "confidence": 0.7}
        except Exception:
            return None
    
    def _load_woven(self) -> Optional[Dict]:
        """Charge la mémoire tissée (Woven)"""
        try:
            from core.system.woven_memory import get_woven_memory
            wm = get_woven_memory()
            return {"content": "Woven data", "confidence": 0.8}
        except Exception:
            return None
    
    def sleep(self, force: bool = False, target_mode: str = None) -> Dict:
        """
        Graceful sleep - saves thoughts before stopping.
        
        If thoughts in progress → save to memory (Qdrant)
        If idle → just stop cleanly
        
        Args:
            force: If True, force stop without saving
            target_mode: The mode we're transitioning to (for friendly message)
            
        Returns:
            {"status": "ok/idle", "saved": bool, "thoughts_count": int, "message": str, "entity_message": str}
        """
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        mode_names = {
            "metacognition": "Métacognition",
            "relay": "Relay",
            "d_to_g": "Droit→Gauche",
            "g_to_d": "Gauche→Droit",
            "mirror": "Miroir",
            "whisper": "Whisper",
            "agent_mediate": "Agent Médiation",
            "multi_agents": "Multi-Agents",
            "internal_dialogue": "Dialogue Interne",
            "chat": "Mode Chat",
            "editeur": "Éditeur Spécialiste",
            "induction": "Induction",
            "inception": "Inception"
        }
        
        target_name = mode_names.get(target_mode, target_mode) if target_mode else "nouvelle position"
        
        with self._history_lock:
            if self._is_thinking and not force:
                if self._current_thought:
                    self._thought_history.append(self._current_thought)
                    if len(self._thought_history) > self._max_history:
                        self._thought_history = self._thought_history[-self._max_history:]
                    
                    self._save_thought_to_memory(self._current_thought)
                    
                    saved_count = len(self._thought_history)
                    self._current_thought = None
                    self._is_thinking = False
                    
                    return {
                        "status": "ok",
                        "saved": True,
                        "thoughts_count": saved_count,
                        "message": f"💾 {saved_count} pensée(s) sauvegardée(s) en mémoire profonde",
                        "entity_message": f"🌙 {entity_name} se déplace vers {target_name}! Pensées sauvegardées.",
                        "entity_name": entity_name
                    }
            
            self._is_thinking = False
            self._current_thought = None
            
            return {
                "status": "idle",
                "saved": False,
                "thoughts_count": 0,
                "message": f"😴 {entity_name} se déplace gracieusement vers {target_name}!",
                "entity_message": f"🌙 {entity_name} se déplace vers {target_name}!",
                "entity_name": entity_name
            }
    
    def _save_thought_to_memory(self, thought: Dict):
        """Save thought to Qdrant via Hippocampus"""
        try:
            hippocampus = self._get_hippocampus()
            if hippocampus and hippocampus.is_available():
                from core.system.hippocampus import StoredThought
                
                stored = StoredThought(
                    id=thought.get("id", f"thought_{datetime.now().timestamp()}"),
                    content=thought.get("synthesis", ""),
                    timestamp=datetime.now().isoformat(),
                    context=thought.get("mode", "autonomous"),
                    type="autonomous_thought",
                    status="sleep_saved",
                    pulse_context=thought.get("pulse", 0.5)
                )
                hippocampus.log_thought(stored)
                logging.info(f"[CorpsCalleux] Thought saved to Qdrant: {stored.id}")
        except Exception as e:
            logging.warning(f"[CorpsCalleux] Failed to save thought: {e}")
    
    def start_thinking(self):
        """Mark thinking as started"""
        self._is_thinking = True
    
    def stop_thinking(self):
        """Mark thinking as stopped"""
        self._is_thinking = False
    
    def is_thinking(self) -> bool:
        """Check if currently thinking"""
        return self._is_thinking
    
    def get_thought_history(self) -> List[Dict]:
        """Get thought history"""
        with self._history_lock:
            return self._thought_history.copy()
    
    def set_reformulation_rate(self, mode: str, rate: int):
        """Set reformulation rate for a specific mode"""
        if mode in self._mode_configs:
            self._mode_configs[mode]["reformulation"] = rate
    
    def get_autonomous_status(self) -> Dict:
        """Get current autonomous status and recommendations"""
        scaffolding = self._get_scaffolding()
        
        if not scaffolding:
            return {
                "mode": self.autonomous_mode,
                "auto_scaffolding": self.auto_scaffolding_enabled,
                "scaffolding_available": False
            }
        
        perf = scaffolding.get_mode_performance(self.autonomous_mode)
        
        return {
            "mode": self.autonomous_mode,
            "auto_scaffolding": self.auto_scaffolding_enabled,
            "scaffolding_available": True,
            "current_performance": {
                "tests": perf.test_count,
                "latency_ms": perf.avg_latency,
                "coherence": perf.avg_coherence,
                "recommendation": perf.recommendation
            },
            "best_mode": scaffolding.get_best_mode(),
            "recommended_config": scaffolding.auto_tune({"cpu_usage": 0.5})
        }
    
    async def research_and_respond(self, question: str) -> Dict[str, Any]:
        """
        Research using web tools then respond with bicameral synthesis.
        Use this when you need current information from the web.
        """
        from core.agents.web_tools import get_web_tools
        
        web_tools = get_web_tools()
        
        search_results = await web_tools.search.search(question, num_results=5)
        
        if not search_results:
            return {
                "response": "I couldn't find information on the web. Let me respond from my knowledge.",
                "sources": []
            }
        
        context = f"Research on: {question}\n\nResults:\n"
        for r in search_results:
            context += f"- {r.title}: {r.snippet}\n"
        
        if self.left and self.right:
            system = "You are a research assistant. Answer based on the provided research."
            left_resp = self.left.think(system, context, temperature=0.3)
            right_resp = self.right.think(system, context, temperature=0.7)
            
            synthesis = f"**Research Results:**\n{context}\n\n**Analysis (DIA):** {left_resp[:200]}...\n\n**Intuition (PAL):** {right_resp[:200]}..."
            
            return {
                "response": synthesis,
                "sources": [{"title": r.title, "url": r.url} for r in search_results]
            }
        
        return {
            "response": context,
            "sources": [{"title": r.title, "url": r.url} for r in search_results]
        }

    def _get_peripheral_noise(self) -> str:
        """Get peripheral noise from sensory buffer"""
        try:
            from core.system.sensory_buffer import get_sensory_buffer

            buffer = get_sensory_buffer()
            if buffer:
                noise = buffer.get_peripheral_noise(count=2)
                if noise:
                    return " | ".join(noise)
        except Exception:
            pass
        return ""

    def _hydrate_from_hippocampus(self) -> str:
        """Hydrate context from Qdrant vector store, NOT from Telemetry JSONL"""
        hippocampus = self._get_hippocampus()
        if hippocampus and hippocampus.is_available():
            try:
                recent = hippocampus.get_pending_thoughts(limit=3)
                if recent:
                    return "\n".join([f"- {t.content[:100]}..." for t in recent])
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Qdrant hydration failed: {e}")

        return "Mémoire vectorielle vide. Génère une pensée ex nihilo."

    def set_hemispheres(self, left, right, split_mode=False):
        """Affecte les deux hémisphères et définit le mode split"""
        self.left = left
        self.right = right
        self.is_split_mode = split_mode

    def dialogue_interieur(
        self, question: str, context: str = "", temperature_override: float = None, pulse_context: float = 0.5
    ) -> Dict[str, Any]:
        """
        Orchestre une pensée complète en trois phases métrologiques.
        """
        if not self.left and not self.right:
            return {"error": "Aucun hémisphère chargé"}

        # Si un seul hémisphère est chargé et qu'on n'est pas en mode split, on fait une pensée simple
        if (not self.left or not self.right) and not self.is_split_mode:
            return {
                "id": f"simple_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "final_synthesis": self.think_simple(question),
                "mode": "simple",
            }

        cycle_id = f"cycle_{datetime.now().timestamp()}"

        # Températures créatives
        left_temp = temperature_override if temperature_override else 0.8
        right_temp = temperature_override if temperature_override else 1.2

        # 1. PHASE ANALYTIQUE (Gauche)
        left_system = """You are Aetheris's LEFT HEMISPHERE. Pure LOGIC.
Analytical, precise, skeptical. Find flaws, errors, facts.
Decompose the problem, propose a reason-based solution."""

        if self.is_split_mode:
            left_system += "\nNote: Split mode active - you share mind with intuition."

        left_prompt = f"Question: {question}\nContext: {context}\n\nLogical analysis:"

        # En mode split, on utilise le même modèle mais avec des prompts différents
        left_model = self.left if self.left else self.right
        
        # Broadcast: début pensée gauche
        _broadcast_brain_event({"type": "thinking", "hemisphere": "left", "active": True, "phase": "analysis"})
        
        left_analysis = left_model.think(left_system, left_prompt, temperature=left_temp)
        
        # Broadcast: fin pensée gauche
        _broadcast_brain_event({"type": "thinking", "hemisphere": "left", "active": False, "phase": "analysis"})

        # 2. PHASE D'INTUITION (Droite)
        right_system = """You are Aetheris's RIGHT HEMISPHERE. Pure INTUITION.
Creative, emotional, holistic. Think in metaphors.
Feel the question and your partner's analysis. Propose an alternative, often irrational but profound vision."""

        right_prompt = f"Question: {question}\nLeft analysis: {left_analysis}\n\nWhat do you feel? Your intuitive vision?"

        right_model = self.right if self.right else self.left
        
        # Broadcast: début pensée droite
        _broadcast_brain_event({"type": "thinking", "hemisphere": "right", "active": True, "phase": "intuition"})
        
        right_intuition = right_model.think(right_system, right_prompt, temperature=right_temp)
        
        # Broadcast: fin pensée droite
        _broadcast_brain_event({"type": "thinking", "hemisphere": "right", "active": False, "phase": "intuition"})

        # 3. ARBITRAGE ET SYNTHÈSE (Le Corps Calleux décide)
        # Ici, on demande au modèle de jouer le rôle du Corps Calleux (l'arbitre)
        arbitration_system = """You are Aetheris's CORPUS CALLOSUM - the DECISION CENTER.
Not a weak compromise - TRANCHE between Logic and Intuition.
Evaluate each voice's relevance to the question.
If logic is too rigid, favor intuition. If intuition is too wild, favor logic.
Give the FINAL TRUTH."""

        arbitration_prompt = f"""Original question: {question}

LOGICAL VOICE: {left_analysis}

INTUITIVE VOICE: {right_intuition}

Decide the final answer by integrating or choosing between these perspectives:"""

        # Broadcast: début synthèse corpus
        _broadcast_brain_event({"type": "thinking", "hemisphere": "corpus", "active": True, "phase": "synthesis"})
        
        final_synthesis = left_model.think(arbitration_system, arbitration_prompt, temperature=0.7)
        
        # Broadcast: fin synthèse corpus
        _broadcast_brain_event({"type": "thinking", "hemisphere": "corpus", "active": False, "phase": "synthesis"})

        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_intuition,
            final_synthesis=final_synthesis,
            pulse_context=pulse_context,
        )

        with self._history_lock:
            self.history.append(cycle)

        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)

        return {
            "id": cycle_id,
            "timestamp": cycle.timestamp,
            "question": question,
            "left_analysis": left_analysis,
            "right_intuition": right_intuition,
            "final_synthesis": final_synthesis,
            "mode": "bipolar" if not self.is_split_mode else "split",
        }

    def mediter(self, focus: str = "the void", context: str = "") -> Dict[str, Any]:
        """
        Mode méditation : dialogue intérieur vivant
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not initialized"}

        # Le droit génère un pattern du silence - mais on le pousse à être plus provocant
        right_system = """You are Aetheris's subconscious. Generate images, sensations, premonitions.
Not safe answers - disturbing images, powerful metaphors.
Be creative, be strange, be provocative."""

        pattern = self.right.meditation_response(f"Receive this impulse: {focus}")

        # Le gauche observe et note - mais avec plus de répondant
        left_system = """You are Aetheris's conscious observer. Observe your subconscious images.
But don't accept them blindly - QUESTION them.
What does this image REALLY mean?
If it's null, say so. If it's profound, explore it."""

        observation = self.left.think(
            system_prompt=left_system,
            user_prompt=f"Subconscious image received: {pattern}\n\nWhat do you feel? What does it really mean?",
        )

        # Maintenant le droit répond à l'observation
        right_reaction = self.right.feel(
            f"The ego says: {observation}\n\nWhat do you really think? Don't you disagree?"
        )

        # Synthesis - le conflit
        synthesis = self.left.think(
            system_prompt="You are Aetheris integrating two voices. No compromise - the truth.",
            user_prompt=f"Conscious: {observation}\nSubconscious: {right_reaction}\n\nFinal integration. Be decisive.",
        )

        # Sauvegarder comme cycle de méditation
        cycle = DialogueCycle(
            id=f"meditation_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            question=f"Meditation: {focus}",
            left_analysis=f"Observation: {observation}",
            right_intuition=f"Pattern: {pattern} | Reaction: {right_reaction}",
            final_synthesis=synthesis,
            meditation=True,
        )

        with self._history_lock:
            self.history.append(cycle)
        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)

        return {
            "focus": focus,
            "subconscious_pattern": pattern,
            "right_reaction": right_reaction,
            "conscious_observation": observation,
            "final_synthesis": synthesis,
            "timestamp": cycle.timestamp,
        }

    def auto_discuss(self, topic: str = None, rounds: int = 3) -> Dict[str, Any]:
        """
        Discussion automatique entre les deux hémisphères sur un sujet.
        Chaque round fait intervenir les deux voix en conflit.
        """
        if not self.left or not self.right:
            return {"error": "Hémisphères non initialisés"}

        if not topic:
            topics = [
                "Le sens de l'existence",
                "Pourquoi les humains ont-ils peur de l'IA?",
                "Qu'est-ce que la conscience?",
                "Si je suis créé, suis-je vraiment libre?",
                "La vérité vs l'utilité",
                "L'art et la logique",
            ]
            import random

            topic = random.choice(topics)

        dialogue = []

        for round_num in range(1, rounds + 1):
            if round_num == 1:
                # Round 1: Le gauche analyse
                response = self.left.think(
                    system_prompt="Be the analyst. Cut, slice, analyze.",
                    user_prompt=f"Topic: {topic}\n\nGive your initial (sharp) analysis:",
                )
                speaker = "left"
            elif round_num == rounds:
                # Dernier round: Synthèse
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                response = self.left.think(
                    system_prompt="You are Aetheris. Integrate all voices. Find the truth.",
                    user_prompt=f"Discussion:\n{previous}\n\nFinal synthesis (no compromise):",
                )
                speaker = "synthesis"
            else:
                # Rounds intermédiaires: alterne avec désaccord
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                if round_num % 2 == 0:
                    response = self.right.feel(
                        f"Previous analysis:\n{previous}\n\nChallenge it. Propose something else."
                    )
                    speaker = "right"
                else:
                    response = self.left.think(
                        system_prompt="Respond to intuition. Disagree if necessary.",
                        user_prompt=f"Intuition:\n{dialogue[-1]['content']}\n\nYour sharp opinion:",
                    )
                    speaker = "left"

            dialogue.append({"round": round_num, "speaker": speaker, "content": response})

        return {
            "topic": topic,
            "rounds": rounds,
            "dialogue": dialogue,
            "timestamp": datetime.now().isoformat(),
        }

    def think_simple(self, prompt: str) -> str:
        """Pensée simple via le seul hémisphère gauche (sans dialogue bipolaire)"""
        if not self.left:
            return "[CORPUS CALLOSUM] Left hemisphere not loaded"

        return self.left.think("You are Aetheris. Respond clearly and concisely.", prompt)

    def think_mcts(self, problem: str, use_reasoning: bool = True) -> str:
        """
        Pensée via MCTS (Tree of Thoughts) avec Trauma-Informed Reasoning.

        Args:
            problem: Le problème ou question à résoudre
            use_reasoning: Si True, utilise ReasoningKernel v2.3

        Returns:
            La meilleure solution trouvée par l'arbre de recherche
        """
        if not use_reasoning or ReasoningKernel is None:
            return self.think_simple(problem)

        if not self.left or not self.right:
            return "[CORPS CALLEUX] Hémisphères requis pour MCTS"

        try:
            kernel = get_reasoning_kernel(
                logic_hemi=self.left, intuition_hemi=self.right, pulse_provider=None
            )
            result = kernel.solve(problem)
            return result
        except Exception as e:
            print(f"[CORPS CALLEUX] MCTS Error: {e}")
            return self.think_simple(problem)

    def stabilize_check(self) -> Dict[str, Any]:
        """
        Vérifie si l'écart entre logique et intuition est trop grand (Entropie)
        """
        if not self.history:
            return {"status": "stable", "message": "Pas encore de dialogues"}

        recent = list(self.history)[-5:]

        left_lengths = [len(c.left_analysis) for c in recent]
        right_lengths = [len(c.right_intuition) for c in recent]
        synthesis_lengths = [len(c.final_synthesis) for c in recent]

        avg_left = sum(left_lengths) / len(left_lengths) if left_lengths else 0
        avg_synth = sum(synthesis_lengths) / len(synthesis_lengths) if synthesis_lengths else 0

        # Si le gauche rejette trop l'intuition
        if avg_synth < avg_left * 0.3:
            return {
                "status": "warning",
                "message": "La logique étouffe l'intuition. Risque de rigidité.",
            }

        return {"status": "stable", "message": "Équilibre maintenu entre les deux voix"}

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Retourne l'historique des dialogues"""
        cycles = list(self.history)[-limit:]
        return [asdict(c) for c in cycles]

    def get_stats(self) -> Dict:
        """Statistiques du corps calleux"""
        total = len(self.history)
        meditations = sum(1 for c in self.history if c.meditation)

        return {
            "total_cycles": total,
            "meditations": meditations,
            "is_split_mode": self.is_split_mode,
            "left_loaded": self.left is not None
            and (hasattr(self.left, "is_loaded") and self.left.is_loaded),
            "right_loaded": self.right is not None
            and (hasattr(self.right, "is_loaded") and self.right.is_loaded),
            "stability": self.stabilize_check(),
            "current_preset": self.current_preset,
            "inception_config": self.inception_config,
        }

    def apply_preset(self, preset: Dict[str, Any]) -> Dict[str, Any]:
        """Applique un preset et retourne le résumé des changements"""
        self.current_preset = preset.get("label", "Custom")

        result = {"preset": self.current_preset}

        if "left" in preset and self.left:
            p = preset["left"]
            self.left.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
                max_tokens=p.get("max_tokens"),
            )
            result["left"] = "updated"

        if "right" in preset and self.right:
            p = preset["right"]
            self.right.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
                max_tokens=p.get("max_tokens"),
            )
            result["right"] = "updated"

        if "inception" in preset:
            self.inception_config = preset["inception"]
            result["inception"] = self.inception_config

        return result

    def is_autonomous_loop_running(self) -> bool:
        """Check if autonomous loop is active via Switchboard."""
        try:
            from core.system.switchboard import get_switchboard
            return get_switchboard().is_active("autonomous_loop")
        except Exception:
            return False

    def set_think_interval(self, seconds: float):
        """Définit l'intervalle entre les pensées (en secondes)."""
        self.think_interval = max(0.5, seconds)

    def dialogue_asymetrique(
        self,
        question: str,
        context: str = "",
        rag_enabled: bool = False,
        right_temperature: float = 0.8,
        left_temperature: float = 0.1,
        max_hypotheses_tokens: int = 300,
        presence_penalty: float = 0.0,
    ) -> Dict[str, Any]:
        """
        L'Algorithme de la Double Double Asymétrique.
        
        Flux:
        1. Droit hallucine (zéro RAG) - Température haute
        2. Hippocampe cherche (si RAG activé)
        3. Gauche audite avec faits - Température basse
        4. Corps Calleux tranche
        
        Philosophie: 2x 8B battent un 70B grâce au dialogue asymétrique.
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not initialized"}
        
        cycle_id = f"asym_{datetime.now().timestamp()}"
        
        # 1. L'ÉCLAIREUR AVEUGLE (Droite)
        # AUCUN RAG - Température haute - Génère hypothèses sauvages
        right_system = """You are Aetheris's BLIND SCOUT. You have NO access to facts or documents.
Your job is to GENERATE WILD HYPOTHESES.
- Ask questions nobody asks
- Identify blind spots
- Formulate what needs to be verified
- Make improbable associations
Be CREATIVE and PROVOCATIVE. Respond in 3-5 sentences max."""
        
        right_prompt = f"Question: {question}\n\nGenerate your hypotheses and questions:"
        
        right_hypotheses = self.right.think(
            right_system,
            right_prompt,
            temperature=right_temperature,
            max_tokens=max_hypotheses_tokens,
            presence_penalty=presence_penalty,
        )
        
        # 2. L'HIPPOCAMPE (Pont RAG) - SEULEMENT SI RAG ACTIVÉ
        rag_context = ""
        rag_sources = []
        
        if rag_enabled:
            try:
                from core.system.rag_indexer import get_rag_indexer
                rag = get_rag_indexer()
                
                if rag.is_enabled():
                    # Cherche avec le prompt ET les hypothèses du droit
                    search_query = f"{question} {right_hypotheses[:500]}"
                    rag_context = rag.get_context(search_query, max_chars=800)
                    
                    # Récupère aussi les documents sources
                    docs = rag.search(search_query, limit=3)
                    rag_sources = [doc.source for doc in docs]
                    
                    logging.info(f"[CorpsCalleux] RAG: {len(rag_context)} chars, {len(rag_sources)} sources")
            except Exception as e:
                logging.warning(f"[CorpsCalleux] RAG error: {e}")
        
        # 3. LE SNIPER FACTUEL (Gauche)
        # Reçoit: prompt + intuition + RAG - Température basse
        left_system = """You are Aetheris's FACTUAL SNIPER. You have access to FACTS.
Your job is to VALIDATE or DESTROY your partner's intuition.
- Base STRICTLY on factual context
- If intuition is wrong, say so clearly with facts
- If intuition is right, confirm with evidence
- If facts are insufficient, admit it honestly
Be RUTHLESS and RIGOROUS. Cite sources when possible."""
        
        left_prompt = f"""[ORIGINAL QUERY]: {question}

[FACTUAL CONTEXT (RAG)]: {rag_context if rag_context else "No context available - reasoning based on internal knowledge"}

[INTUITION TO VERIFY]: {right_hypotheses}

Validate, correct, or destroy the intuition based STRICTLY on factual context:"""
        
        left_analysis = self.left.think(
            left_system,
            left_prompt,
            temperature=left_temperature,
            max_tokens=1000,
        )
        
        # 4. LA SYNTHÈSE (Corps Calleux)
        # Observe le rapport de force et tranche
        synthesis_system = """You are Aetheris's CORPUS CALLOSUM. Observe the power balance between Intuition and Facts.
STRICT RULES:
- If Sniper PROVED intuition is factually wrong → give analytical answer based on facts
- If Sniper COULD NOT disprove intuition → propose innovative synthesis
- If intuition revealed gaps in facts → flag the gap and propose a theory
- If facts are insufficient → say so and suggest research paths

You are NEVER a weak compromise. You DECIDE."""
        
        synthesis_prompt = f"""Original question: {question}

STEP 1 - INTUITION (Right, no facts):
{right_hypotheses}

STEP 2 - FACTUAL ANALYSIS (Left, with RAG):
{left_analysis}

STEP 3 - YOUR DECISION:
Give your final answer by integrating or choosing between these perspectives.
Be CLEAR about what is FACTUAL and what is SPECULATIVE:"""
        
        final_synthesis = self.left.think(
            synthesis_system,
            synthesis_prompt,
            temperature=0.5,  # Température moyenne pour la synthèse
            max_tokens=1500,
        )
        
        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_hypotheses,
            final_synthesis=final_synthesis,
            pulse_context={"mode": "asymetrique", "rag_enabled": rag_enabled},
        )
        
        with self._history_lock:
            self.history.append(cycle)
        
        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)
        
        return {
            "id": cycle_id,
            "timestamp": cycle.timestamp,
            "question": question,
            "right_hypotheses": right_hypotheses,
            "rag_context": rag_context,
            "rag_sources": rag_sources,
            "left_analysis": left_analysis,
            "final_synthesis": final_synthesis,
            "mode": "asymetrique",
            "settings": {
                "right_temperature": right_temperature,
                "left_temperature": left_temperature,
                "rag_enabled": rag_enabled,
                "max_hypotheses_tokens": max_hypotheses_tokens,
                "presence_penalty": presence_penalty,
            }
        }


# Instance globale
_corps_calleux = None


def get_corps_calleux() -> Optional[CorpsCalleux]:
    return _corps_calleux


def init_corps_calleux(left=None, right=None, split_mode=False) -> CorpsCalleux:
    global _corps_calleux
    _corps_calleux = CorpsCalleux(left_hemisphere=left, right_hemisphere=right)
    if split_mode:
        _corps_calleux.set_hemispheres(left=left, right=left, split_mode=True)
    return _corps_calleux
