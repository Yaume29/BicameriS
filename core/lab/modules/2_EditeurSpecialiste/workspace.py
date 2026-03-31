"""
Workspace Manager - Éditeur Spécialiste
===================================
Gestion du répertoire de travail.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("editeur.workspace")

BASE_DIR = Path(__file__).parent.parent.parent.parent.absolute()
DEFAULT_WORKSPACE = BASE_DIR / "storage" / "lab" / "workspaces"


class WorkspaceManager:
    """
    Gestionnaire de workspace pour l'Editeur Spécialiste.
    """
    
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        self.workspace_path = None
        self.project_type = None
        
        if workspace_id:
            self.workspace_path = DEFAULT_WORKSPACE / workspace_id
    
    def create_workspace(self, name: str, base_path: str = None) -> Dict:
        """
        Crée un nouveau workspace.
        """
        import uuid
        
        workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
        
        if base_path and Path(base_path).exists():
            workspace_path = Path(base_path)
        else:
            workspace_path = DEFAULT_WORKSPACE / workspace_id
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            readme = workspace_path / "README.md"
            readme.write_text(f"# {name}\n\nProjet créé avec l'Editeur Spécialiste.\n")
        
        self.workspace_id = workspace_id
        self.workspace_path = workspace_path
        self._detect_project_type()
        
        return {
            "id": workspace_id,
            "name": name,
            "path": str(workspace_path),
            "project_type": self.project_type,
            "created": True
        }
    
    def open_workspace(self, path: str) -> Dict:
        """
        Ouvre un workspace existant.
        """
        workspace_path = Path(path)
        
        if not workspace_path.exists():
            return {"status": "error", "message": "Chemin inexistant"}
        
        if not workspace_path.is_dir():
            return {"status": "error", "message": "Doit être un dossier"}
        
        self.workspace_path = workspace_path
        self.workspace_id = workspace_path.name
        self._detect_project_type()
        
        return {
            "id": self.workspace_id,
            "name": workspace_path.name,
            "path": str(workspace_path),
            "project_type": self.project_type,
            "files": self.list_files()
        }
    
    def _detect_project_type(self):
        """Détecte le type de projet."""
        if not self.workspace_path:
            return
        
        files = list(self.workspace_path.glob("*"))
        filenames = [f.name for f in files]
        
        if "pyproject.toml" in filenames or "setup.py" in filenames or "requirements.txt" in filenames:
            self.project_type = "python"
        elif "package.json" in filenames:
            self.project_type = "javascript"
        elif "Cargo.toml" in filenames:
            self.project_type = "rust"
        elif "go.mod" in filenames:
            self.project_type = "go"
        elif "main.tex" in filenames or "paper.tex" in filenames:
            self.project_type = "latex"
        elif any(f.suffix == ".md" for f in files if f.is_file()):
            self.project_type = "documentation"
        else:
            self.project_type = "generic"
    
    def list_files(self, pattern: str = "**/*") -> List[Dict]:
        """Liste les fichiers du workspace."""
        if not self.workspace_path:
            return []
        
        files = []
        for f in self.workspace_path.glob(pattern):
            if f.is_file():
                rel_path = f.relative_to(self.workspace_path)
                try:
                    stat = f.stat()
                    files.append({
                        "name": str(rel_path),
                        "path": str(f),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
                except:
                    pass
        
        return sorted(files, key=lambda x: x["name"])
    
    def read_file(self, filename: str) -> Dict:
        """Lit un fichier."""
        if not self.workspace_path:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        file_path = self.workspace_path / filename
        
        if not file_path.exists():
            return {"status": "error", "message": f"Fichier non trouvé: {filename}"}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            return {
                "status": "ok",
                "filename": filename,
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def write_file(self, filename: str, content: str) -> Dict:
        """Écrit un fichier."""
        if not self.workspace_path:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        file_path = self.workspace_path / filename
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return {
                "status": "ok",
                "filename": filename,
                "path": str(file_path)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_file(self, filename: str) -> Dict:
        """Supprime un fichier."""
        if not self.workspace_path:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        file_path = self.workspace_path / filename
        
        if not file_path.exists():
            return {"status": "error", "message": f"Fichier non trouvé: {filename}"}
        
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            return {"status": "ok", "filename": filename}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_directory(self, dirname: str) -> Dict:
        """Crée un répertoire."""
        if not self.workspace_path:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        dir_path = self.workspace_path / dirname
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"status": "ok", "dirname": dirname}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_file_tree(self, max_depth: int = 3) -> Dict:
        """Retourne l'arborescence complète."""
        if not self.workspace_path:
            return {"status": "error", "message": "Aucun workspace ouvert"}
        
        def build_tree(path: Path, depth: int = 0):
            if depth > max_depth:
                return None
            
            items = []
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith("."):
                        continue
                    if item.is_dir():
                        children = build_tree(item, depth + 1)
                        if children:
                            items.append({
                                "name": item.name,
                                "type": "directory",
                                "children": children
                            })
                    else:
                        items.append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                pass
            
            return items
        
        return {
            "status": "ok",
            "tree": build_tree(self.workspace_path),
            "project_type": self.project_type
        }
    
    def search_files(self, query: str, extensions: List[str] = None) -> List[Dict]:
        """Recherche dans les fichiers."""
        if not self.workspace_path:
            return []
        
        results = []
        query_lower = query.lower()
        
        for f in self.workspace_path.rglob("*"):
            if not f.is_file():
                continue
            if f.name.startswith("."):
                continue
            if extensions and f.suffix not in extensions:
                continue
            
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if query_lower in content.lower():
                    rel_path = f.relative_to(self.workspace_path)
                    lines = content.split("\n")
                    matches = []
                    for i, line in enumerate(lines, 1):
                        if query_lower in line.lower():
                            matches.append({
                                "line": i,
                                "content": line[:100]
                            })
                    results.append({
                        "file": str(rel_path),
                        "matches": matches[:5]
                    })
            except:
                pass
        
        return results


_workspace_manager = None


def get_workspace_manager(workspace_id: str = None) -> WorkspaceManager:
    """Singleton du workspace manager."""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager(workspace_id)
    return _workspace_manager


def set_workspace(workspace_id: str):
    """Définit le workspace actif."""
    global _workspace_manager
    _workspace_manager = WorkspaceManager(workspace_id)
