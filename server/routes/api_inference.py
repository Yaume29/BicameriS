"""
Inference API Routes
===================
Endpoints for inference management
FastAPI with async delegation
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import orjson

from server.extensions import registry

router = APIRouter(prefix="/api/inference", tags=["inference"])


# ==============================================================================
# DEPENDENCY INJECTOR
# ==============================================================================


def get_inference():
    if not registry.inference_manager:
        raise HTTPException(status_code=501, detail="Inference Subsystem Offline")
    return registry.inference_manager


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================


class SpawnRequest(BaseModel):
    name: str
    model_path: str
    n_ctx: int = 8192
    n_gpu_layers: int = 32


class ExecuteRequest(BaseModel):
    name: str
    prompt: str
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    stream: bool = False


# ==============================================================================
# ENDPOINTS - All blocking calls delegated to threadpool
# ==============================================================================


@router.get("/status")
async def inference_status(inference=Depends(get_inference)):
    """Get inference status"""
    return await asyncio.to_thread(inference.get_status)


@router.post("/spawn")
async def spawn_incarnation(req: SpawnRequest, inference=Depends(get_inference)):
    """Spawn inference incarnation"""
    success = await asyncio.to_thread(
        inference.spawn_incarnation,
        req.name,
        req.model_path,
        n_ctx=req.n_ctx,
        n_gpu_layers=req.n_gpu_layers,
    )
    return {"status": "success" if success else "failed", "name": req.name}


@router.post("/execute")
async def execute_inference(req: ExecuteRequest, inference=Depends(get_inference)):
    """Execute inference - Sync mode or Streaming SSE"""
    
    if req.stream:
        def chunk_generator():
            try:
                for chunk in inference.execute_stream(
                    name=req.name,
                    prompt=req.prompt,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                ):
                    yield f"data: {orjson.dumps(chunk).decode('utf-8')}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_chunk = orjson.dumps({"error": str(e), "is_final": True}).decode('utf-8')
                yield f"data: {error_chunk}\n\n"

        return StreamingResponse(chunk_generator(), media_type="text/event-stream")
    
    result = await asyncio.to_thread(
        inference.execute,
        req.name,
        req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return result


@router.post("/guillotine/{name}")
async def guillotine_incarnation(name: str, inference=Depends(get_inference)):
    """Guillotine an incarnation"""
    success = await asyncio.to_thread(inference.guillotine, name)
    return {"status": "success" if success else "failed", "name": name}


@router.post("/guillotine_all")
async def guillotine_all(inference=Depends(get_inference)):
    """Guillotine all incarnations"""
    await asyncio.to_thread(inference.guillotine_all)
    return {"status": "success"}
