from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

router = APIRouter(tags=["views"])

_templates = None
BASE_DIR = Path(__file__).parent.parent.parent.absolute()


def set_templates(templates):
    global _templates
    _templates = templates


DEFAULT_CONTEXT = {
    "session": {"is_initiator": True, "user_email": "admin@local", "username": "Admin"},
    "model_info": {"display_name": "Non configure", "left": None, "right": None},
    "lm_ready": False,
    "stats": {"total": 0, "errors": 0, "success": 0, "total_thoughts": 0},
    "config": {"name": "BicameriS", "version": "1.0.0.6a"},
    "pulse": 0.0,
}


def make_context(extra=None):
    ctx = DEFAULT_CONTEXT.copy()
    if extra:
        ctx.update(extra)
    return ctx


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if _templates:
        return _templates.TemplateResponse("index.html", make_context({"request": request}))
    return FileResponse(str(BASE_DIR / "web" / "templates" / "index.html"))


@router.get("/{path:path}")
async def catch_all(request: Request, path: str):
    return FileResponse(str(BASE_DIR / "web" / "templates" / "index.html"))
