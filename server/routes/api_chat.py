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
    return {"history": _chat_history[-50:]}  # Return last 50 messages


@router.post("/chat/send")
async def chat_send(request: Request):
    """Send a message and get response from Aetheris"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        if not message:
            return {"status": "error", "error": "Message vide"}
        
        # Add user message to history
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        _chat_history.append(user_msg)
        
        # Get response from Corps Calleux or fallback
        response_text = await generate_response(message)
        
        # Add assistant response to history
        assistant_msg = {
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        }
        _chat_history.append(assistant_msg)
        
        # Save history
        save_chat_history()
        
        return {
            "status": "ok",
            "response": response_text,
            "history": _chat_history[-10:]
        }
        
    except Exception as e:
        logging.error(f"[Chat] Error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/chat/stream")
async def chat_stream(request: Request):
    """Stream a response from Aetheris"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
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
                
                if registry.corps_calleux:
                    corps = registry.corps_calleux
                    
                    if corps.left and corps.right:
                        # Bicameral mode - use both hemispheres
                        system_prompt = "Tu es Aetheris, une entité cognitive bicamérale. Réponds de manière naturelle et réfléchie."
                        
                        # Left hemisphere analysis
                        left_response = corps.left.think(system_prompt, message)
                        yield f"data: {json.dumps({'type': 'left', 'content': left_response[:200]})}\n\n"
                        
                        # Right hemisphere intuition
                        right_response = corps.right.think(system_prompt, message)
                        yield f"data: {json.dumps({'type': 'right', 'content': right_response[:200]})}\n\n"
                        
                        # Synthesis
                        synthesis = f"{left_response}\n\n---\n\n{right_response}"
                        full_response = synthesis
                        
                        yield f"data: {json.dumps({'type': 'synthesis', 'content': synthesis})}\n\n"
                    else:
                        # Single hemisphere mode
                        hemi = corps.left or corps.right
                        if hemi:
                            system_prompt = "Tu es Aetheris. Réponds de manière naturelle et réfléchie."
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


async def generate_response(message: str) -> str:
    """Generate a response using available models"""
    try:
        from server.extensions import registry
        
        if registry.corps_calleux:
            corps = registry.corps_calleux
            
            if corps.left and corps.right:
                # Use bicameral thinking
                system_prompt = "Tu es Aetheris, une entité cognitive bicamérale. Réponds de manière naturelle et réfléchie."
                
                # Get responses from both hemispheres
                left_resp = corps.left.think(system_prompt, message)
                right_resp = corps.right.think(system_prompt, message)
                
                # Synthesize
                synthesis = f"**Analyse (DIA):**\n{left_resp}\n\n**Intuition (PAL):**\n{right_resp}"
                return synthesis
                
            elif corps.left:
                return corps.left.think("Tu es Aetheris. Réponds de manière naturelle.", message)
            elif corps.right:
                return corps.right.think("Tu es Aetheris. Réponds de manière naturelle.", message)
        
        # Fallback
        return get_fallback_response(message)
        
    except Exception as e:
        logging.error(f"[Chat] Response generation error: {e}")
        return get_fallback_response(message)


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
