import asyncio
import json
from typing import AsyncGenerator, Any, Dict, Optional

from .base import CognitiveTopology


class RelaisAsymetrique(CognitiveTopology):
    name = "Relais Asymétrique"
    description = "Flux asymétrique: Droit hallucine, Gauche audite, Crucible arbitre"
    
    async def run(
        self,
        prompt: str,
        left: Any,
        right: Any,
        cc: Any,
        memory: Optional[Any] = None,
        ui_settings: Optional[Dict] = None
    ) -> AsyncGenerator[str, None]:
        temperature_right = ui_settings.get("temperature_right", 1.2) if ui_settings else 1.2
        temperature_left = ui_settings.get("temperature_left", 0.3) if ui_settings else 0.3
        
        yield f"data: {json.dumps({'phase': 'hypotheses', 'status': 'start'})}\n\n"
        
        right_response = await asyncio.to_thread(
            right.think,
            "You are the CREATIVE hemisphere. Generate wild, creative hypotheses. Don't check facts - IMAGINE.",
            prompt,
            temperature=temperature_right
        )
        
        yield f"data: {json.dumps({'phase': 'hypotheses', 'token': right_response, 'status': 'complete'})}\n\n"
        
        yield f"data: {json.dumps({'phase': 'audit', 'status': 'start'})}\n\n"
        
        left_response = await asyncio.to_thread(
            left.think,
            "You are the LOGICAL auditor. VERIFY facts and DESTROY false hypotheses.",
            f"Question: {prompt}\nCreative Hypotheses:\n{right_response}\n\nCritical audit:",
            temperature=temperature_left
        )
        
        yield f"data: {json.dumps({'phase': 'audit', 'token': left_response, 'status': 'complete'})}\n\n"
        
        yield f"data: {json.dumps({'phase': 'crucible', 'status': 'start'})}\n\n"
        
        crucible_prompt = f"""You are the CRUCIBLE - FINAL ARBITER.
Don't compromise - CHOOSE the truth.

Question: {prompt}
Creative Voice:\n{right_response}\n
Logical Voice:\n{left_response}\n

Final decision:"""
        
        synthesis = await asyncio.to_thread(
            left.think,
            "You are the arbiter. Make the final decision.",
            crucible_prompt,
            temperature=0.5
        )
        
        yield f"data: {json.dumps({'phase': 'crucible', 'token': synthesis, 'status': 'complete'})}\n\n"
        yield f"data: {json.dumps({'phase': 'complete', 'status': 'done'})}\n\n"
