from pathlib import Path
import os


class FileSystem:
    def __init__(self, workspace_path="./workspace"):
        self.workspace = Path(workspace_path)
        self.workspace.mkdir(exist_ok=True)

    def create_file(self, path, content):
        try:
            full_path = self.workspace / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return f"Fichier créé: {full_path}"
        except IOError as e:
            return f"Erreur création fichier: {e}"

    def read_file(self, path):
        try:
            full_path = self.workspace / path
            if full_path.exists():
                return full_path.read_text(encoding="utf-8")
            return f"Fichier non trouvé: {path}"
        except IOError as e:
            return f"Erreur lecture fichier: {e}"

    def list_files(self, path=""):
        try:
            target = self.workspace / path if path else self.workspace
            if target.exists():
                return [
                    str(p.relative_to(self.workspace))
                    for p in target.rglob("*")
                    if p.is_file()
                ]
            return []
        except IOError as e:
            print(f"[FILESYSTEM] Erreur list_files: {e}")
            return []
