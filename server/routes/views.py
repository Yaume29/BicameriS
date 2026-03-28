"""
Views Routes
===========
HTML page routes
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["views"])

# Templates will be injected by main.py
_templates = None


def set_templates(templates):
    global _templates
    _templates = templates


# Default session with is_initiator=True to show all menus
DEFAULT_SESSION = {
    "is_initiator": True,
    "user_email": "admin@local",
    "username": "Admin"
}


def get_session():
    """Get session with full access"""
    return DEFAULT_SESSION.copy()


# Default context variables for all templates
DEFAULT_CONTEXT = {
    # Session
    "session": DEFAULT_SESSION,
    
    # Model info
    "model_info": {"display_name": "Non configuré", "left": None, "right": None},
    "lm_ready": False,
    
    # Stats
    "stats": {"total": 0, "errors": 0, "success": 0, "total_thoughts": 0},
    "task_stats": {"total": 0, "running": 0, "pending": 0},
    "inception_stats": {"pending": 0, "total": 0, "acknowledged": False},
    "thinker_stats": {"active": False, "thoughts": 0},
    "pulse": 0.0,
    
    # Config
    "config": {"name": "Aetheris", "version": "1.0.0.6a", "auto_scaffolding": False, "sandbox_docker": True},
    
    # Operator
    "operator": {"sensitivity": 0.5, "impact": 0.5, "active": False},
    
    # Conscientisation
    "conscientisation": {"active": False, "level": 0},
    
    # Research
    "research_results": [],
    
    # Identity
    "identity": {"name": "Aetheris", "email": "admin@local"},
    
    # Categories for templates
    "categories": {
        "logic": "Logique",
        "creativity": "Créativité", 
        "analysis": "Analyse",
        "intuition": "Intuition",
        "memory": "Mémoire"
    },
    
    # Lab features
    "features": {
        "sandbox": True,
        "auto_scaffolding": False,
        "mcp": False,
        "trauma": True
    }
}


def make_context(extra=None):
    """Create context with defaults + extras"""
    ctx = DEFAULT_CONTEXT.copy()
    if extra:
        ctx.update(extra)
    return ctx


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Home page"""
    if _templates:
        return _templates.TemplateResponse("index.html", make_context({"request": request}))
    return HTMLResponse("<h1>Diadikos & Palladion v1.0.0.6a</h1>")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    if _templates:
        return _templates.TemplateResponse("dashboard.html", make_context({"request": request}))
    return HTMLResponse("<h1>Dashboard</h1>")


@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    """Chat page"""
    if _templates:
        return _templates.TemplateResponse("chat.html", make_context({"request": request}))
    return HTMLResponse("<h1>Chat</h1>")


@router.get("/laboratoire", response_class=HTMLResponse)
async def laboratoire(request: Request):
    """Laboratory page"""
    if _templates:
        return _templates.TemplateResponse("laboratoire.html", make_context({"request": request}))
    return HTMLResponse("<h1>Laboratoire</h1>")


@router.get("/inception", response_class=HTMLResponse)
async def inception(request: Request):
    """Inception page"""
    if _templates:
        return _templates.TemplateResponse("inception.html", make_context({"request": request}))
    return HTMLResponse("<h1>Inception</h1>")


@router.get("/models", response_class=HTMLResponse)
async def models(request: Request):
    """Models management page"""
    if _templates:
        return _templates.TemplateResponse("models.html", make_context({"request": request}))
    return HTMLResponse("<h1>Models</h1>")


@router.get("/think", response_class=HTMLResponse)
async def think(request: Request):
    """Think page"""
    if _templates:
        return _templates.TemplateResponse("think.html", make_context({"request": request}))
    return HTMLResponse("<h1>Think</h1>")


@router.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    """Tasks page"""
    if _templates:
        return _templates.TemplateResponse("tasks.html", make_context({"request": request}))
    return HTMLResponse("<h1>Tasks</h1>")


@router.get("/files", response_class=HTMLResponse)
async def files(request: Request):
    """Files page"""
    if _templates:
        return _templates.TemplateResponse("files.html", make_context({"request": request}))
    return HTMLResponse("<h1>Files</h1>")


@router.get("/launcher", response_class=HTMLResponse)
async def launcher(request: Request):
    """Launcher page"""
    if _templates:
        return _templates.TemplateResponse("launcher.html", make_context({"request": request}))
    return HTMLResponse("<h1>Launcher</h1>")


@router.get("/research", response_class=HTMLResponse)
async def research(request: Request):
    """Research panel page"""
    if _templates:
        return _templates.TemplateResponse("research_panel.html", make_context({"request": request}))
    return HTMLResponse("<h1>Research</h1>")


@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page"""
    if _templates:
        return _templates.TemplateResponse("settings.html", make_context({"request": request}))
    return HTMLResponse("<h1>Settings</h1>")
