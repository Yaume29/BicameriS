"""
Auto-Scaffolding Extensions System
Permet à Aetheris de créer ses propres outils dynamiquement.
"""

import os
import sys
import importlib
import importlib.util
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable


class ExtensionLoader:
    """
    Système d'auto-scaffolding.

    Quand l'entité se heurte à une limite, elle peut:
    1. Écrire un nouveau module Python dans extensions/
    2. Le tester via la Sandbox
    3. L'importer dynamiquement si succès
    4. L'enregistrer comme nouvel outil
    """

    def __init__(self, extensions_dir: str = "ZONE_AETHERIS/extensions"):
        self.extensions_dir = Path(extensions_dir)
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_extensions: Dict[str, Any] = {}
        self._registry: Dict[str, Callable] = {}
        self._load_existing()

    def _load_existing(self):
        """Charge les extensions existantes au démarrage"""
        for f in self.extensions_dir.glob("*.py"):
            if f.stem != "__init__":
                self._dynamic_import(f.stem)

    def _dynamic_import(self, module_name: str) -> bool:
        """Importe dynamiquement un module"""
        try:
            module_path = self.extensions_dir / f"{module_name}.py"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                self.loaded_extensions[module_name] = module
                return True
        except Exception as e:
            print(f"[EXTENSIONS] Erreur import {module_name}: {e}")
        return False

    def create_extension(
        self, name: str, code: str, description: str = ""
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle extension.
        """
        filename = f"{name}.py"
        filepath = self.extensions_dir / filename

        header = f'''"""
Extension auto-générée: {name}
{description}
Créé: {datetime.now().isoformat()}
"""

'''

        filepath.write_text(header + code, encoding="utf-8")

        return {"status": "created", "name": name, "path": str(filepath)}

    def test_extension(
        self, name: str, test_code: str = None, timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Teste une extension via la sandbox.
        """
        from core_reserved.conductor import get_conductor

        conductor = get_conductor()

        if test_code:
            result = conductor.execute_sandbox(
                test_code, filename=f"test_{name}.py", timeout=timeout
            )
        else:
            test_default = f"import {name}; print('OK')"
            result = conductor.execute_sandbox(
                test_default, filename=f"test_{name}.py", timeout=timeout
            )

        return result

    def register_function(self, name: str, func: Callable):
        """Enregistre une fonction comme outil"""
        self._registry[name] = func

    def execute_extension(self, func_name: str, **kwargs) -> Any:
        """Exécute une fonction d'extension"""
        if func_name in self._registry:
            return self._registry[func_name](**kwargs)
        return {"error": f"Fonction {func_name} non trouvée"}

    def get_available_extensions(self) -> List[Dict]:
        """Liste les extensions disponibles"""
        extensions = []

        for f in self.extensions_dir.glob("*.py"):
            if f.stem != "__init__":
                extensions.append(
                    {
                        "name": f.stem,
                        "path": str(f),
                        "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(
                            f.stat().st_mtime
                        ).isoformat(),
                    }
                )

        return extensions

    def get_registered_functions(self) -> List[str]:
        """Liste les fonctions enregistrées"""
        return list(self._registry.keys())

    def delete_extension(self, name: str) -> Dict[str, Any]:
        """Supprime une extension"""
        filepath = self.extensions_dir / f"{name}.py"

        if filepath.exists():
            filepath.unlink()
            if name in self.loaded_extensions:
                del self.loaded_extensions[name]
            return {"status": "deleted", "name": name}

        return {"error": "Extension non trouvée"}

    def get_stats(self) -> Dict:
        """Statistiques des extensions"""
        return {
            "extensions_loaded": len(self.loaded_extensions),
            "functions_registered": len(self._registry),
            "total_extensions": len(list(self.extensions_dir.glob("*.py"))) - 1,
            "registry": list(self._registry.keys()),
        }


# Instance globale
_extension_loader = None


def get_extension_loader() -> ExtensionLoader:
    global _extension_loader
    if _extension_loader is None:
        _extension_loader = ExtensionLoader()
    return _extension_loader
