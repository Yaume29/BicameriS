import asyncio
import json
import queue
from typing import AsyncGenerator, Any, Dict, Optional

from .base import CognitiveTopology


class DialogueStreaming(CognitiveTopology):
    name = "Dialogue Streaming"
    description = "Flux streaming: Tokens un par un"
    
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
        
        token_queue = queue.Queue()
        
        def on_chunk(chunk):
            token_queue.put(chunk)
        
        await asyncio.to_thread(
            left.think_stream,
            "You are the ANALYTICAL hemisphere. Analyze this question precisely.",
            prompt,
            on_chunk
        )
        
        while True:
            try:
                token = token_queue.get_nowait()
                yield f"data: {json.dumps({'phase': 'left', 'token': token, 'status': 'streaming'})}\n\n"
            except queue.Empty:
                break
        
        yield f"data: {json.dumps({'phase': 'left', 'status': 'complete'})}\n\n"
        
        yield f"data: {json.dumps({'phase': 'right', 'status': 'start'})}\n\n"
        
        token_queue = queue.Queue()
        
        def on_chunk_right(chunk):
            token_queue.put(chunk)
        
        await asyncio.to_thread(
            right.think,
            "You are the INTUITIVE hemisphere. Respond creatively.",
            prompt,
            temperature=temperature + 0.2
        )
        
        while True:
            try:
                token = token_queue.get_nowait()
                yield f"data: {json.dumps({'phase': 'right', 'token': token, 'status': 'streaming'})}\n\n"
            except queue.Empty:
                break
        
        yield f"data: {json.dumps({'phase': 'right', 'status': 'complete'})}\n\n"
        yield f"data: {json.dumps({'phase': 'complete', 'status': 'done'})}\n\n"
