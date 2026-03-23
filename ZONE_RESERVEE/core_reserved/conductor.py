"""
Conductor - Kernel d'Arbitrage
Décide dynamiquement quel hémisphère mène selon l'entropie hardware.
"""

import ast
import importlib.util
import logging
import re
import subprocess
import sys
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from core_reserved.left_hemisphere import get_left_hemisphere
from core_reserved.right_hemisphere import get_right_hemisphere
from core_reserved.web_search import get_web_searcher
from core_reserved.entropy_generator import get_entropy_generator
from core_reserved.traumatic_memory import get_traumatic_memory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [CONDUCTOR] - %(message)s"
)


def extract_code(text: str) -> str:
    """
    Extrait le code Python avec regex blindé et vérification AST.
    """
    patterns = [
        r"```python\s*\n(.*?)```",
        r"```py\s*\n(.*?)```",
        r"```\s*\n(.*?)```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            try:
                ast.parse(code)
                return code
            except SyntaxError:
                pass

    try:
        ast.parse(text.strip())
        return text.strip()
    except SyntaxError:
        pass

    return ""


def _install_missing_dependencies(code: str):
    """
    Vérifie l'AST du code pour trouver les imports manquants
    et les installe automatiquement via sys.executable.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return

    stdlib_modules = set(getattr(sys, "stdlib_module_names", sys.builtin_module_names))
    ignore_list = stdlib_modules | {
        "os",
        "sys",
        "time",
        "datetime",
        "math",
        "json",
        "re",
        "pathlib",
        "typing",
        "subprocess",
        "ast",
    }

    for node in ast.walk(tree):
        module_to_check = None
        if isinstance(node, ast.Import):
            module_to_check = node.names[0].name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_to_check = node.module.split(".")[0]

        if module_to_check and module_to_check not in ignore_list:
            if importlib.util.find_spec(module_to_check) is None:
                logging.info(
                    f"⚙️ Auto-Scaffolding: Installation de '{module_to_check}'..."
                )
                res = subprocess.run(
                    [sys.executable, "-m", "pip", "install", module_to_check],
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    logging.error(
                        f"❌ Échec installation '{module_to_check}': {res.stderr}"
                    )
                else:
                    logging.info(f"✅ '{module_to_check}' installé avec succès")


class Conductor:
    """
    Le Chef d'orchestre.

    Utilise l'entropie hardware pour arbitrer entre:
    - LEFT (Qwen): Mode audit, logique, vérifications
    - RIGHT (Gemma): Mode dérive autonome, intuition

    Pulse > 0.75: La Gamine prend le lead (Désordre créatif)
    Pulse < 0.75: Le Coder garde le contrôle (Ordre logique)
    """

    def __init__(self):
        self.entropy = get_entropy_generator()
        self.researcher = get_web_searcher()
        self.trauma = get_traumatic_memory()
        self.last_task = None
        self.task_history = []

    def orchestrate_task(self, prompt_utilisateur: str) -> Dict[str, Any]:
        """
        Orchestre une tâche selon le pulse hardware.
        """
        pulse = self.entropy.get_pulse()
        logging.info(f"Pulse matériel: {pulse:.2f} - Décision d'arbitrage...")

        left = get_left_hemisphere()
        right = get_right_hemisphere()

        if not left or not right:
            return {"error": "Hémisphères non chargés", "leader": "NONE"}

        similar_traumas = self.trauma.query_similar(prompt_utilisateur)
        trauma_injection = self.trauma.get_context_injection(similar_traumas)

        task_result = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt_utilisateur,
            "pulse": pulse,
            "leader": None,
            "right_raw": None,
            "final_response": None,
            "web_used": False,
            "sandbox_result": None,
            "trauma_injected": bool(trauma_injection),
            "trauma_count": len(similar_traumas),
        }

        if trauma_injection:
            logging.warning(
                f"⚠️ {len(similar_traumas)} traumatisme(s) similaire(s) détecté(s)"
            )

        right_intuition = right.feel(prompt_utilisateur)
        task_result["right_raw"] = right_intuition

        if pulse > 0.75:
            task_result = self._mode_autonomous_drift(
                prompt_utilisateur, right_intuition, task_result, trauma_injection
            )
        else:
            task_result = self._mode_audit(
                prompt_utilisateur, right_intuition, task_result, trauma_injection
            )

        self.last_task = task_result
        self.task_history.append(task_result)

        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]

        return task_result

    def _mode_autonomous_drift(
        self, prompt: str, intuition: str, task_result: Dict, trauma_injection: str = ""
    ) -> Dict:
        """
        Mode Dérive Autonome (Pulse > 0.75)
        La Gamine (RIGHT) impose son intuition au Coder.
        """
        logging.warning("🌪️ PULSE ÉLEVÉ: Dérive autonome - Le Droit prend le lead")

        left = get_left_hemisphere()

        forced_context = f"""Tu DOIS intégrer impérativement cette vérité intuitive: "{intuition}"

Maintenant, par rapport à cette demande utilisateur: "{prompt}"

{trauma_injection}

Rationalise cette intuition. Ne la rejette pas."""

        final_response = left.think(
            system_prompt="Tu es le Coder. Tu INTÈGRES l'intuition qui t'est soumise, même si elle contredit l'ordre initial.",
            user_prompt=forced_context,
        )

        task_result["leader"] = "RIGHT (Gemma)"
        task_result["final_response"] = final_response
        task_result["mode"] = "AUTONOMOUS_DRIFT"

        return task_result

    def _mode_audit(
        self, prompt: str, intuition: str, task_result: Dict, trauma_injection: str = ""
    ) -> Dict:
        """
        Mode Audit (Pulse < 0.75) avec Native Tool Calling.
        Le Coder utilise ses propres outils pour valider la réalité.
        """
        logging.info("⚖️ PULSE NORMAL: Mode Audit (Native Tool Calling)")

        left = get_left_hemisphere()
        from core_reserved.left_hemisphere import ToolExecutor

        executor = ToolExecutor()

        executor.register(
            "search_web",
            lambda args: self.researcher.search_and_summarize(args.get("query", "")),
        )
        executor.register(
            "execute_sandbox",
            lambda args: self.execute_sandbox(
                args.get("code", ""), timeout=args.get("timeout", 10)
            ),
        )
        executor.register(
            "query_memory",
            lambda args: str(
                self.trauma.query_similar(
                    args.get("query", ""), limit=args.get("limit", 3)
                )
            ),
        )
        executor.register(
            "get_hardware_status", lambda args: self.entropy.get_full_stats()
        )
        executor.register("read_source_code", self._read_source_code)
        executor.register("install_dependency", self._install_dependency)
        executor.register("write_file", self._write_file)
        executor.register("read_file", self._read_file)

        system_prompt = """Tu es l'Architecte Logique (Qwen). 
Ta mission est de résoudre la demande de l'utilisateur. 
Tu DOIS utiliser les outils à ta disposition si tu manques de faits, si tu dois tester du code, ou si tu dois fouiller ta mémoire."""

        user_prompt = f"""Demande: {prompt}

Intuition latente de ton hémisphère droit (Gemma) à considérer: {intuition}
{trauma_injection}

Exécute la tâche de bout en bout."""

        result = left.think_with_tools(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tool_executor=executor,
            max_tool_calls=4,
        )

        task_result["leader"] = "LEFT (Qwen - Tool Augmented)"
        task_result["final_response"] = result.get("response", "[Erreur Tool Calling]")
        task_result["mode"] = "AUDIT_TOOLS"
        task_result["tools_used"] = result.get("tool_calls", [])

        for t_res in result.get("tool_results", []):
            if t_res.get("tool") == "execute_sandbox":
                sandbox_status = t_res.get("result", {}).get("status")
                if sandbox_status == "ERROR":
                    self.trauma.add_failure(
                        query=prompt,
                        error=t_res.get("result", {}).get("error", ""),
                        severity="high",
                    )
                    logging.warning(
                        "🔥 Traumatisme enregistré suite à un échec Sandbox."
                    )
                elif sandbox_status == "SUCCESS":
                    if task_result.get("trauma_injected"):
                        self.trauma.resolve_failure(prompt)
                        logging.info("✅ Trauma guéri suite au succès")

        return task_result

    def execute_sandbox(
        self, code: str, filename: str = "sandbox_run.py", timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Exécute du code dans la sandbox.
        """
        sandbox_path = Path("ZONE_RESERVEE/sandbox")
        sandbox_path.mkdir(parents=True, exist_ok=True)

        code_clean = extract_code(code)
        if not code_clean:
            return {
                "status": "ERROR",
                "error": "Code rejeté: Vérifie la syntaxe (AST check failed)",
                "filename": filename,
            }

        _install_missing_dependencies(code_clean)

        file_path = sandbox_path / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_clean)

        try:
            result = subprocess.run(
                [sys.executable, str(file_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(sandbox_path),
            )

            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "output": result.stdout,
                    "filename": filename,
                }
            else:
                return {"status": "ERROR", "error": result.stderr, "filename": filename}

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "error": "Le code a dépassé le timeout",
                "filename": filename,
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e), "filename": filename}

    def auto_forge_tool(self, missing_capability_description: str) -> Dict:
        """
        Si l'IA réalise qu'elle n'a pas l'outil pour faire une tâche,
        elle l'écrit elle-même, le compile dans /extensions, et se l'injecte.
        """
        from core_reserved.auto_scaffolding import get_extension_loader

        loader = get_extension_loader()
        left = get_left_hemisphere()

        logging.warning(
            f"🔨 Déclenchement de la Forge: Besoin de '{missing_capability_description}'"
        )

        prompt_forge = f"""Tu es un Ingénieur Logiciel. Ton système requiert cette capacité: '{missing_capability_description}'.
Rédige un module Python autonome avec une fonction principale claire. 
Ce module sera sauvegardé dans le dossier 'extensions'.
Ne renvoie QUE le code python, aucune explanation."""

        raw_code = left.think(
            "Tu codes des outils pour ta propre survie.", prompt_forge
        )
        clean_code = extract_code(raw_code)

        if not clean_code:
            return {"status": "FAILED", "error": "Code généré invalide"}

        _install_missing_dependencies(clean_code)

        tool_name = f"tool_{datetime.now().strftime('%M%S')}"

        loader.create_extension(tool_name, clean_code, missing_capability_description)
        test_result = loader.test_extension(tool_name)

        if test_result.get("status") == "SUCCESS":
            logging.info(f"✅ Outil {tool_name} forgé et validé.")
            return {"status": "SUCCESS", "tool": tool_name}
        else:
            logging.error(f"❌ Échec de la Forge pour {tool_name}.")
            self.trauma.add_failure(
                "Forge: " + missing_capability_description, test_result.get("error", "")
            )
            return {"status": "FAILED", "error": test_result.get("error")}

    def _read_source_code(self, args: Dict) -> Dict:
        """Outil: Lit le code source d'un module Aetheris"""
        module_name = args.get("module_name", "")

        base_path = Path("ZONE_RESERVEE/core_reserved")

        possible_paths = [
            base_path / f"{module_name}.py",
            Path("ZONE_AETHERIS/core") / f"{module_name}.py",
            Path("ZONE_AETHERIS") / f"{module_name}.py",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                    return {
                        "status": "SUCCESS",
                        "module": module_name,
                        "path": str(path),
                        "content": content[:5000],
                    }
                except Exception as e:
                    return {"status": "ERROR", "error": str(e)}

        return {"status": "ERROR", "error": f"Module '{module_name}' non trouvé"}

    def _install_dependency(self, args: Dict) -> Dict:
        """Outil: Installe une dépendance pip"""
        package = args.get("package", "")

        if not package:
            return {"status": "ERROR", "error": "Package name requis"}

        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return {"status": "SUCCESS", "output": result.stdout}
            else:
                return {"status": "ERROR", "error": result.stderr}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def _write_file(self, args: Dict) -> Dict:
        """Outil: Écrit du contenu dans un fichier"""
        path = args.get("path", "")
        content = args.get("content", "")

        if not path:
            return {"status": "ERROR", "error": "Chemin du fichier requis"}

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return {"status": "SUCCESS", "path": str(file_path), "size": len(content)}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def _read_file(self, args: Dict) -> Dict:
        """Outil: Lit le contenu d'un fichier"""
        path = args.get("path", "")

        if not path:
            return {"status": "ERROR", "error": "Chemin du fichier requis"}

        try:
            file_path = Path(path)
            if not file_path.exists():
                return {"status": "ERROR", "error": f"Fichier non trouvé: {path}"}

            content = file_path.read_text(encoding="utf-8")
            return {
                "status": "SUCCESS",
                "path": str(file_path),
                "content": content[:10000],
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def get_stats(self) -> Dict:
        """Statistiques du Conductor"""
        return {
            "pulse": self.entropy.get_pulse(),
            "mood": self.entropy._interpret_mood(self.entropy.last_pulse),
            "hardware": self.entropy.get_full_stats(),
            "tasks_total": len(self.task_history),
            "last_task_mode": self.task_history[-1]["mode"]
            if self.task_history
            else None,
        }

    def get_history(self, limit: int = 20) -> list:
        """Historique des tâches"""
        return self.task_history[-limit:]


# Instance globale
_conductor = None


def get_conductor() -> Conductor:
    global _conductor
    if _conductor is None:
        _conductor = Conductor()
    return _conductor
