"""
API Chat Routes
===============
Chat endpoint for dialogue with Aetheris
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict

from core.cognition.tot_reasoner import get_tot_reasoner, ToTStrategy
from core.system.config_manager import get_config
from core.system.emergency_override import get_emergency_system

router = APIRouter(tags=["chat"])

# Chat history storage
CHAT_HISTORY_FILE = Path("storage/logs/chat_history.json")
CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# In-memory chat history (for current session)
_chat_history: List[Dict] = []


def load_chat_history() -> List[Dict]:
    """Load chat history from file"""
    global _chat_history
    if CHAT_HISTORY_FILE.exists():
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                _chat_history = json.load(f)
        except:
            _chat_history = []
    return _chat_history


def save_chat_history():
    """Save chat history to file"""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_chat_history[-100:], f, indent=2, ensure_ascii=False)  # Keep last 100 messages
    except Exception as e:
        logging.warning(f"[Chat] Failed to save history: {e}")


@router.get("/chat/history")
async def get_chat_history():
    """Get chat history"""
    return {"history": _chat_history[-50:]}


@router.get("/chat/reformulation")
async def get_chat_reformulation():
    """Get chat reformulation rate"""
    global _chat_reformulation_rate
    return {"rate": _chat_reformulation_rate}


@router.post("/chat/reformulation")
async def set_chat_reformulation(request: Request):
    """Set chat reformulation rate"""
    global _chat_reformulation_rate
    try:
        data = await request.json()
        rate = data.get("rate", 50)
        
        if rate < 0:
            rate = 0
        elif rate > 100:
            rate = 100
        
        _chat_reformulation_rate = rate
        
        return {"status": "ok", "rate": rate, "message": f"Taux de reformulation: {rate}%"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/chat/autonomous-mode")
async def get_autonomous_mode():
    """Get current autonomous thinking mode"""
    try:
        from server.extensions import registry
        if registry.corps_calleux:
            return registry.corps_calleux.get_available_modes()
        return {"error": "Corps Calleux not available"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/chat/autonomous-mode")
async def set_autonomous_mode(request: Request):
    """Set autonomous thinking mode with graceful sleep"""
    try:
        data = await request.json()
        new_mode = data.get("mode", "metacognition")
        
        from server.extensions import registry
        if registry.corps_calleux:
            sleep_result = registry.corps_calleux.sleep(target_mode=new_mode)
            registry.corps_calleux.set_autonomous_mode(new_mode)
            
            return {
                "status": "ok", 
                "mode": new_mode,
                "sleep": {
                    "saved": sleep_result.get("saved", False),
                    "thoughts_count": sleep_result.get("thoughts_count", 0)
                },
                "entity_message": sleep_result.get("entity_message", f"Mode changé pour {new_mode}")
            }
        return {"error": "Corps Calleux not available"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/chat/modes")
async def get_all_modes():
    """Get all available autonomous modes"""
    try:
        from server.extensions import registry
        if registry.corps_calleux:
            return registry.corps_calleux.get_available_modes()
        return {"error": "Corps Calleux not available"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/chat/sleep")
async def sleep_corps_calleux(request: Request):
    """Graceful sleep - save thoughts before stopping"""
    try:
        data = await request.json()
        force = data.get("force", False)
        target_mode = data.get("target_mode", None)
        
        from server.extensions import registry
        if registry.corps_calleux:
            result = registry.corps_calleux.sleep(force=force, target_mode=target_mode)
            return result
        return {"error": "Corps Calleux not available"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/chat/thinking-status")
async def get_thinking_status():
    """Check if corps calleux is currently thinking"""
    try:
        from server.extensions import registry
        if registry.corps_calleux:
            return {
                "thinking": registry.corps_calleux.is_thinking(),
                "history_count": len(registry.corps_calleux.get_thought_history())
            }
        return {"thinking": False, "error": "Corps Calleux not available"}
    except Exception as e:
        return {"thinking": False, "error": str(e)}




@router.post("/chat/send")
async def chat_send(request: Request):
    """Send a message and get response from Aetheris"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        use_tot = data.get("use_tot", False)
        
        if not message:
            return {"status": "error", "error": "Message vide"}
        
        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        _chat_history.append(user_msg)
        
        response_text = ""
        tot_result = None
        
        message_lower = message.lower().strip()
        
        if message_lower.startswith("/research ") or message_lower.startswith("/recherche "):
            query = message.replace("/research ", "").replace("/recherche ", "").strip()
            result = await _research_with_corps_calleux(query)
            return {
                "status": "ok",
                "response": result.get("response", ""),
                "history": _chat_history[-10:],
                "sources": result.get("sources", [])
            }
        
        if message_lower.startswith("/agent ") or message_lower.startswith("/spawn "):
            task = message.replace("/agent ", "").replace("/spawn ", "").strip()
            result = await _spawn_agents(task)
            return {
                "status": "ok",
                "response": result.get("result", ""),
                "history": _chat_history[-10:],
                "agents_created": result.get("agents_created", 0)
            }
        
        emergency = get_emergency_system()
        if emergency.is_god_mode_active():
            override = emergency.get_active_override()
            from server.extensions import registry
            if registry.corps_calleux:
                response_text = emergency.force_execute(
                    override.message,
                    registry.corps_calleux
                )
                emergency.clear_override()
                return {
                    "status": "god_mode",
                    "response": response_text,
                    "history": _chat_history[-10:]
                }
        
        if use_tot:
            tot = _get_tot_with_config()
            tot.enable()
            result = await tot.think(message)
            response_text = result.get("synthesis", result.get("solution", ""))
            tot_result = result
        else:
            response_text = await generate_response(message, use_tot=False)
        
        # Add assistant response to history
        assistant_msg = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        }
        _chat_history.append(assistant_msg)
        
        # Save history
        save_chat_history()
        
        response = {
            "status": "ok",
            "response": response_text,
            "history": _chat_history[-10:]
        }
        
        if use_tot and tot_result:
            response["tot"] = {
                "used_tot": True,
                "best_score": tot_result.get("best_score", 0),
                "iterations": tot_result.get("iterations", 0),
                "tree": tot_result.get("tree", [])[:10]
            }
        
        return response
        
    except Exception as e:
        logging.error(f"[Chat] Error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """Stream a response from Aetheris"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        use_tot = data.get("use_tot", False)
        
        if not message:
            return {"status": "error", "error": "Message vide"}
        
        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        _chat_history.append(user_msg)
        
        async def generate_stream():
            """Generate streaming response"""
            full_response = ""
            
            try:
                # Try to use Corps Calleux for bicameral response
                from server.extensions import registry
                from core.system.switchboard import get_cognitive_router
                
                if registry.corps_calleux:
                    corps = registry.corps_calleux
                    
                    if corps.left and corps.right:
                        router_class = get_cognitive_router()
                        ui_settings = data.get("settings", {"lab_mode": "dialogue_classique"})
                        
                        async for chunk in router_class.route(
                            message, 
                            ui_settings, 
                            corps.left, 
                            corps.right, 
                            corps
                        ):
                            yield chunk
                            full_response += chunk
                        
                        full_response = full_response
                    else:
                        hemi = corps.left or corps.right
                        if hemi:
                            system_prompt = "You are BicameriS. Respond naturally and thoughtfully."
                            response = hemi.think(system_prompt, message)
                            full_response = response
                            yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"
                        else:
                            fallback = get_fallback_response(message)
                            full_response = fallback
                            yield f"data: {json.dumps({'type': 'response', 'content': fallback})}\n\n"
                else:
                    fallback = get_fallback_response(message)
                    full_response = fallback
                    yield f"data: {json.dumps({'type': 'response', 'content': fallback})}\n\n"
                    
            except Exception as e:
                fallback = get_fallback_response(message)
                full_response = fallback
                yield f"data: {json.dumps({'type': 'error', 'content': fallback})}\n\n"
            
            # Add to history
            assistant_msg = {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            }
            _chat_history.append(assistant_msg)
            save_chat_history()
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logging.error(f"[Chat] Stream error: {e}")
        return {"status": "error", "error": str(e)}


async def _spawn_agents(task: str) -> Dict:
    """Spawn sub-agents for complex task"""
    try:
        from core.agents.super_agent import get_super_agent
        
        super_agent = get_super_agent()
        
        from server.extensions import registry
        if registry.corps_calleux:
            super_agent.connect_corps_calleux(registry.corps_calleux)
        
        if registry.corps_calleux and registry.corps_calleux.left:
            from core.agents.tool_registry import get_tool_registry
            super_agent.connect_tool_registry(get_tool_registry())
        
        super_agent.enable()
        
        result = await super_agent.execute_task(task)
        
        return {
            "result": result.get("result", "Task completed"),
            "agents_created": result.get("agents_created", 0),
            "status": result.get("status", "ok")
        }
    except Exception as e:
        return {"result": f"Agent spawn failed: {str(e)}", "agents_created": 0}


async def _research_with_corps_calleux(query: str) -> Dict:
    """Research using web tools then bicameral synthesis"""
    try:
        from server.extensions import registry
        
        if registry.corps_calleux:
            return await registry.corps_calleux.research_and_respond(query)
        
        from core.agents.web_tools import get_web_tools
        web_tools = get_web_tools()
        
        results = await web_tools.search.search(query, num_results=5)
        
        content = f"Search results for: {query}\n\n"
        for r in results:
            content += f"- {r.title}: {r.snippet}\n"
        
        return {
            "response": content,
            "sources": [{"title": r.title, "url": r.url} for r in results]
        }
    except Exception as e:
        return {"response": f"Research failed: {str(e)}", "sources": []}


_chat_reformulation_rate = 50  # Default 50%


async def generate_response(message: str, use_tot: bool = False) -> str:
    """
    Generate a response using BICAMERAL SYNTHESIS with OBLIGATORY REFORMULATION.
    
    The message routing depends on the AUTONOMOUS MODE:
    - relay: Receiver → Reformulation → Responder
    - mirror: Both see in mirror view
    - whisper: Low intensity transmission
    - agent-mediate: Agent intermediate reformulates
    """
    global _chat_reformulation_rate
    
    try:
        from server.extensions import registry
        from core.cognition.reformulation_engine import get_reformulation_engine
        from core.system.identity_manager import get_entity_name
        
        reform_engine = get_reformulation_engine()
        
        if not registry.corps_calleux:
            return get_fallback_response(message)
        
        corps = registry.corps_calleux
        
        if not corps.left or not corps.right:
            entity_name = get_entity_name()
            hemi = corps.left or corps.right
            if hemi:
                return hemi.think(f"You are {entity_name}. Respond completely.", message)
            return get_fallback_response(message)
        
        entity_name = get_entity_name()
        
        autonomous_mode = getattr(corps, 'autonomous_mode', 'metacognition')
        reformulation_rate = _chat_reformulation_rate
        
        if autonomous_mode == "metacognition":
            return await _mode_metacognition(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "relay":
            return await _mode_relay(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "d_to_g":
            return await _mode_d_to_g(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "g_to_d":
            return await _mode_g_to_d(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "mirror":
            return await _mode_mirror(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "whisper":
            return await _mode_whisper(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "agent_mediate":
            return await _mode_agent_mediate(message, corps, entity_name, reformulation_rate, reform_engine)
        elif autonomous_mode == "multi_agents":
            return await _mode_multi_agents(message, corps, entity_name)
        elif autonomous_mode == "internal_dialogue":
            return await _mode_internal_dialogue(message, corps, entity_name)
        else:
            return await _mode_metacognition(message, corps, entity_name, reformulation_rate, reform_engine)
    
    except Exception as e:
        logging.error(f"[Chat] Response generation error: {e}")
        return get_fallback_response(message)


async def _mode_relay(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode Relay: Receiver → Reformulation → Responder"""
    receiver = corps.left
    responder = corps.right
    
    if rate > 0:
        result = reform_engine.reformulate(message, percentage=rate)
        reformulated = result.reformulated
        reform_info = f"\n\n[Reformulé à {result.actual_percentage:.0f}%]"
    else:
        reformulated = message
        reform_info = ""
    
    receiver_resp = receiver.think(
        f"You are the RECEIVER of {entity_name}. Reformulate this message differently.",
        reformulated,
        temperature=0.3
    )
    
    if rate > 0:
        result2 = reform_engine.reformulate(receiver_resp, percentage=rate)
        final_input = result2.reformulated
        reform_info2 = f"\n[Reformulé 2x à {result2.actual_percentage:.0f}%]"
    else:
        final_input = receiver_resp
        reform_info2 = ""
    
    responder_resp = responder.think(
        f"You are the RESPONDER of {entity_name}. Receive this and respond.",
        final_input,
        temperature=0.7
    )
    
    return f"📥 [Récepteur]: {receiver_resp}\n\n⚡ [Corpus]: {final_input}{reform_info2}\n\n📤 [Répondeur]: {responder_resp}{reform_info}"


async def _mode_mirror(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode Miroir: Both hemispheres see each other in mirror"""
    left = corps.left
    right = corps.right
    
    if rate > 0:
        result = reform_engine.reformulate(message, percentage=rate)
        reformulated = result.reformulated
        reform_info = f"\n[Reformulé à {result.actual_percentage:.0f}%]"
    else:
        reformulated = message
        reform_info = ""
    
    left_resp = left.think(f"You are {entity_name} ANALYTICAL. Analyze this.", reformulated, temperature=0.3)
    right_resp = right.think(f"You are {entity_name} INTUITIVE. Respond to this.", reformulated, temperature=0.9)
    
    mirror_left = left.think(f"Mirror view: {right_resp[:200]}", "Comment on this intuition.", temperature=0.5)
    mirror_right = right.think(f"Mirror view: {left_resp[:200]}", "Comment on this analysis.", temperature=0.7)
    
    return f"🪞 [Miroir Gauche]: {mirror_left}\n\n🪞 [Miroir Droit]: {mirror_right}{reform_info}"


async def _mode_whisper(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode Whisper: Low intensity transmission"""
    left = corps.left
    right = corps.right
    
    if rate > 0:
        result = reform_engine.reformulate(message, percentage=min(rate + 30, 95))
        reformulated = result.reformulated
    else:
        words = message.split()
        import random
        reformulated = " ".join(random.sample(words, min(len(words), 5)))
    
    left_resp = left.think("Process this at low intensity.", reformulated, temperature=0.2)
    
    right_resp = right.think(
        f"Intuition from whisper: {left_resp[:100]}",
        "Respond intuitively to this subtle signal.",
        temperature=0.9
    )
    
    return f"🤫 [Whisper]: {reformulated}\n\n💫 [Intuition]: {right_resp}"


async def _mode_agent_mediate(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode Agent Médiation: Agent intermediate reformulates"""
    import asyncio
    left = corps.left
    right = corps.right
    
    if rate > 0:
        result = reform_engine.reformulate(message, percentage=rate)
        reformulated = result.reformulated
    else:
        reformulated = message
    
    left_resp = left.think(
        "You are the RECEIVER. Analyze and prepare reformulation.",
        reformulated,
        temperature=0.4
    )
    
    agent_prompt = f"""You are a MEDIATOR AGENT between two brain hemispheres.
Receiver analyzed: {left_resp[:300]}

Your mission:
1. Reformulate the message (at least {rate}% variation)
2. Add complementary perspective
3. Prepare transmission to responder

Do NOT cheat with repeated chars (........) or underscores."""

    try:
        from core.agents.super_agent import get_super_agent
        super_agent = get_super_agent()
        
        if not super_agent.enabled:
            super_agent.enable()
        
        agent_result = await super_agent.execute_task(agent_prompt)
        mediator_resp = agent_result.get("summary", agent_prompt[:200])
        
        validation = reform_engine.validate(left_resp, mediator_resp, min_percentage=rate)
        if not validation["valid"]:
            forced = reform_engine.reformulate(left_resp, percentage=rate)
            mediator_resp = forced.reformulated
    
    except Exception as e:
        mediator_resp = f"[Agent unavailable: {str(e)[:50]}]"
    
    right_resp = right.think(
        f"Mediated message: {mediator_resp[:300]}",
        "Respond to this mediated input.",
        temperature=0.8
    )
    
    return f"📥 [Récepteur]: {left_resp}\n\n🤖 [Agent Médiateur]: {mediator_resp}\n\n📤 [Répondeur]: {right_resp}"


async def _mode_metacognition(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode 1: Métacognition Bicamérale - Decide HOW to think"""
    left = corps.left
    right = corps.right
    
    left_analysis = left.think(
        f"You are {entity_name} ANALYTICAL. Analyze this question and determine what approach is needed.",
        message,
        temperature=0.3
    )
    
    right_intuition = right.think(
        f"You are {entity_name} INTUITIVE. What's your 'feeling' about how to approach this?",
        message,
        temperature=0.8
    )
    
    strategy_prompt = f"""You are {entity_name} Corps Calleux (Bridge). 
DECIDE HOW TO RESPOND to this question.

LEFT ANALYSIS: {left_analysis[:500]}
RIGHT INTUITION: {right_intuition[:500]}

Original: {message}

Respond as JSON: {{"strategie": "X", "justification": "Y"}}"""
    
    decision = left.think(strategy_prompt, "Decide.", temperature=0.5)
    
    strategy = "bicameral"
    if "direct_gauche" in decision.lower():
        strategy = "direct_gauche"
    elif "direct_droit" in decision.lower():
        strategy = "direct_droit"
    elif "research" in decision.lower():
        strategy = "research"
    
    if strategy == "direct_gauche":
        final = left.think(f"Answer.", message, temperature=0.6)
        return f"🧠 [Métacognition - {strategy}]\n\n🔵 Gauche: {final}"
    elif strategy == "direct_droit":
        final = right.think(f"Answer.", message, temperature=0.8)
        return f"🧠 [Métacognition - {strategy}]\n\n💜 Droit: {final}"
    else:
        left_resp = left.think("Answer.", message, temperature=0.5)
        right_resp = right.think("Answer.", message, temperature=0.8)
        return f"🧠 [Métacognition - bicameral]\n\n🔵 Gauche: {left_resp[:200]}...\n\n💜 Droit: {right_resp[:200]}..."


async def _mode_d_to_g(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode 3: Droit → Gauche"""
    left = corps.left
    right = corps.right
    
    right_resp = right.think("You are RECEIVER. Analyze and reformulate.", message, temperature=0.6)
    
    if rate > 0:
        result = reform_engine.reformulate(right_resp, percentage=min(rate, 50))
        reformulated = result.reformulated
        reform_info = f" [Ref {result.actual_percentage:.0f}%]"
    else:
        reformulated = right_resp
        reform_info = ""
    
    left_resp = left.think(f"Received{reform_info}. Answer.", reformulated, temperature=0.5)
    
    return f"📥 [Droit]: {right_resp}\n\n🔄 [Reformulé{reform_info}]: {reformulated}\n\n📤 [Gauche]: {left_resp}"


async def _mode_g_to_d(message: str, corps, entity_name: str, rate: int, reform_engine) -> str:
    """Mode 4: Gauche → Droit"""
    left = corps.left
    right = corps.right
    
    left_resp = left.think("You are RECEIVER. Analyze and reformulate.", message, temperature=0.4)
    
    if rate > 0:
        result = reform_engine.reformulate(left_resp, percentage=min(rate, 50))
        reformulated = result.reformulated
        reform_info = f" [Ref {result.actual_percentage:.0f}%]"
    else:
        reformulated = left_resp
        reform_info = ""
    
    right_resp = right.think(f"Received{reform_info}. Answer intuitively.", reformulated, temperature=0.8)
    
    return f"📥 [Gauche]: {left_resp}\n\n🔄 [Reformulé{reform_info}]: {reformulated}\n\n📤 [Droit]: {right_resp}"


async def _mode_multi_agents(message: str, corps, entity_name: str) -> str:
    """Mode 8: Multi-Agents"""
    return f"🔧 [Multi-Agents]\n\n⚠️ Ce mode nécessite auto_scaffolding_full activé pour spawn des agents."


async def _mode_internal_dialogue(message: str, corps, entity_name: str) -> str:
    """Mode 9: Dialogue Interne Visualisable"""
    left = corps.left
    right = corps.right
    
    left_thought = left.think(f"Think out loud about: {message}", message, temperature=0.4)
    right_thought = right.think(f"Think out loud about: {message}", message, temperature=0.8)
    
    left_resp = left.think(f"Answer: {message}", message, temperature=0.5)
    right_resp = right.think(f"Answer: {message}", message, temperature=0.8)
    
    return f"""🎭 [DIALOGUE INTERNE - {entity_name}]

🧠 [GAUCHE - Analytique]:
   💭 {left_thought[:200]}...
   ✅ {left_resp[:150]}...

💜 [DROIT - Intuitif]:
   💭 {right_thought[:200]}...
   ✅ {right_resp[:150]}...

⚡ [RÉSULTAT]:
   Gauche: {left_resp[:100]}... + Droit: {right_resp[:100]}..."""


def get_fallback_response(message: str) -> str:
    """Fallback response when models are not loaded"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["bonjour", "salut", "hello", "hi"]):
        return "Bonjour ! Je suis Aetheris, l'entité cognitive de BicameriS. Pour que je puisse vous répondre correctement, veuillez d'abord configurer mes modèles dans l'onglet 'Modèles'."
    
    elif any(word in message_lower for word in ["aide", "help", "comment"]):
        return """Pour utiliser BicameriS:

1. Allez dans **⚙️ Modèles** pour scanner vos fichiers GGUF
2. Sélectionnez un modèle pour l'hémisphère gauche (DIA)
3. Sélectionnez un modèle pour l'hémisphère droit (PAL)
4. Cliquez sur **Initialiser** pour charger les modèles
5. Revenez ici pour dialoguer avec moi !

Si vous n'avez pas de modèles, vous pouvez en télécharger depuis HuggingFace."""
    
    elif "modèle" in message_lower or "model" in message_lower:
        return "Les modèles GGUF sont des fichiers de poids neuronal compressés. Ils se chargent via llama-cpp-python et permettent l'inférence locale. Configurez-les dans l'onglet Modèles."
    
    else:
        return "Je suis en mode dégradé. Pour que je puisse réfléchir et dialoguer avec vous, veuillez charger des modèles dans l'onglet ⚙️ Modèles."


@router.post("/chat/clear")
async def chat_clear():
    """Clear chat history"""
    global _chat_history
    _chat_history = []
    save_chat_history()
    return {"status": "ok", "message": "Historique effacé"}


# ==================== TREE OF THOUGHTS ====================

def _get_tot_with_config() -> tuple:
    """Configure ToT reasoner with current hemispheres"""
    tot = get_tot_reasoner()
    
    from server.extensions import registry
    
    if registry.corps_calleux:
        tot.connect_corps_calleux(registry.corps_calleux)
    
    return tot


@router.get("/chat/tot/status")
async def tot_status():
    """Get ToT status"""
    tot = get_tot_reasoner()
    config = get_config()
    
    from server.extensions import registry
    corps_connected = registry.corps_calleux is not None
    hemispheres_ready = (
        registry.corps_calleux and 
        registry.corps_calleux.left is not None and 
        registry.corps_calleux.right is not None
    )
    
    return {
        "enabled": tot.is_enabled(),
        "connected": tot.is_connected(),
        "config_enabled": config.config.system.tot_enabled,
        "strategy": tot.strategy.value if hasattr(tot, 'strategy') else "bfs",
        "max_depth": tot.max_depth,
        "max_branches": tot.max_branches,
        "corps_calleux": {
            "available": corps_connected,
            "hemispheres_ready": hemispheres_ready,
            "left": registry.corps_calleux.left is not None if registry.corps_calleux else False,
            "right": registry.corps_calleux.right is not None if registry.corps_calleux else False
        }
    }


@router.post("/chat/tot/toggle")
async def tot_toggle(enabled: bool = True, strategy: str = "bfs", max_depth: int = 5, max_branches: int = 5):
    """Toggle Tree of Thoughts on/off"""
    tot = get_tot_reasoner()
    
    if strategy == "bfs":
        tot.strategy = ToTStrategy.BFS
    elif strategy == "dfs":
        tot.strategy = ToTStrategy.DFS
    elif strategy == "best_first":
        tot.strategy = ToTStrategy.BEST_FIRST
    else:
        tot.strategy = ToTStrategy.BFS
    
    tot.max_depth = max_depth
    tot.max_branches = max_branches
    
    if enabled:
        tot.enable()
    else:
        tot.disable()
    
    config = get_config()
    config.config.system.tot_enabled = enabled
    config.save()
    
    return {
        "status": "ok",
        "enabled": tot.is_enabled(),
        "strategy": tot.strategy.value,
        "max_depth": max_depth,
        "max_branches": max_branches
    }


@router.post("/chat/tot/visualize")
async def tot_visualize():
    """Get ToT tree visualization"""
    tot = get_tot_reasoner()
    return {
        "visualization": tot.get_tree_visualization()
    }


# ==================== EMERGENCY GOD MODE ====================

@router.get("/chat/emergency/key")
async def get_emergency_key():
    """Get the hidden emergency key (UI only)"""
    emergency = get_emergency_system()
    return {
        "key": emergency.get_god_button_key()
    }


@router.post("/chat/emergency/trigger")
async def trigger_emergency(message: str):
    """Trigger emergency god mode (hidden API)"""
    emergency = get_emergency_system()
    result = emergency.trigger_god_mode(message)
    return result


@router.get("/chat/emergency/status")
async def emergency_status():
    """Check if god mode is active"""
    emergency = get_emergency_system()
    return {
        "active": emergency.is_god_mode_active()
    }
