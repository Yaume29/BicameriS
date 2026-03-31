import asyncio
import json
from typing import AsyncGenerator, Any, Dict, Optional

from .base import CognitiveTopology


class DialogueClassique(CognitiveTopology):
    name = "Dialogue Classique"
    description = "Flux standard: Gauche analyse, Droit intuite, Synthèse"
    
    async def run(
        self,
        prompt: str,
        left: Any,
        right: Any,
        cc: Any,
        memory: Optional[Any] = None,
        ui_settings: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        temperature = ui_settings.get("temperature", 0.7) if ui_settings else 0.7
        
        yield f"data: {json.dumps({'phase': 'left', 'status': 'start'})}\n\n"
        
        left_response = await asyncio.to_thread(
            left.think,
            "You are the ANALYTICAL hemisphere. Analyze this question precisely.",
            prompt,
            temperature=temperature
        )
        
        yield f"data: {json.dumps({'phase': 'left', 'token': left_response, 'status': 'complete'})}\n\n"
        
        yield f"data: {json.dumps({'phase': 'right', 'status': 'start'})}\n\n"
        
        right_response = await asyncio.to_thread(
            right.think,
            "You are the INTUITIVE hemisphere. Respond creatively.",
            prompt,
            temperature=temperature + 0.2
        )
        
        yield f"data: {json.dumps({'phase': 'right', 'token': right_response, 'status': 'complete'})}\n\n"
        
        yield f"data: {json.dumps({'phase': 'synthesis', 'status': 'start'})}\n\n"
        
        synthesis_prompt = f"""Synthesize these two perspectives into a unified response.

ANALYTICAL: {left_response[:500]}

INTUITIVE: {right_response[:500]}

Original question: {prompt}

Produce a UNIFIED RESPONSE."""
        
        synthesis = await asyncio.to_thread(
            left.think,
            "You are the synthesis. Combine both perspectives.",
            synthesis_prompt,
            temperature=temperature
        )
        
        yield f"data: {json.dumps({'phase': 'synthesis', 'token': synthesis, 'status': 'complete'})}\n\n"
        yield f"data: {json.dumps({'phase': 'complete', 'status': 'done'})}\n\n"
