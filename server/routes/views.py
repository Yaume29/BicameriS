"""
Views Routes
============
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


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Home page"""
    if _templates:
        return _templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<h1>Diadikos & Palladion v1.0.0.6a</h1>")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    if _templates:
        return _templates.TemplateResponse("dashboard.html", {"request": request})
    return HTMLResponse("<h1>Dashboard</h1>")


@router.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    """Chat page"""
    if _templates:
        return _templates.TemplateResponse("chat.html", {"request": request})
    return HTMLResponse("<h1>Chat</h1>")


@router.get("/laboratoire", response_class=HTMLResponse)
async def laboratoire(request: Request):
    """Laboratory page"""
    if _templates:
        return _templates.TemplateResponse("laboratoire.html", {"request": request})
    return HTMLResponse("<h1>Laboratoire</h1>")


@router.get("/models", response_class=HTMLResponse)
async def models(request: Request):
    """Models management page"""
    if _templates:
        return _templates.TemplateResponse("models.html", {"request": request})
    return HTMLResponse("<h1>Models</h1>")


@router.get("/think", response_class=HTMLResponse)
async def think(request: Request):
    """Think page"""
    if _templates:
        return _templates.TemplateResponse("think.html", {"request": request})
    return HTMLResponse("<h1>Think</h1>")


@router.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    """Tasks page"""
    if _templates:
        return _templates.TemplateResponse("tasks.html", {"request": request})
    return HTMLResponse("<h1>Tasks</h1>")


@router.get("/files", response_class=HTMLResponse)
async def files(request: Request):
    """Files page"""
    if _templates:
        return _templates.TemplateResponse("files.html", {"request": request})
    return HTMLResponse("<h1>Files</h1>")


@router.get("/launcher", response_class=HTMLResponse)
async def launcher(request: Request):
    """Launcher page"""
    if _templates:
        return _templates.TemplateResponse("launcher.html", {"request": request})
    return HTMLResponse("<h1>Launcher</h1>")
