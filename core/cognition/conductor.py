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
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR / "ZONE_RESERVEE"))
sys.path.insert(0, str(BASE_DIR))

from core_reserved.left_hemisphere import get_left_hemisphere
from core_reserved.right_hemisphere import get_right_hemisphere
from core_reserved.web_search import get_web_searcher
from core.hardware.entropy_generator import get_entropy_generator
from core_reserved.traumatic_memory import get_traumatic_memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [CONDUCTOR] - %(message)s")

SANDBOX_DIR = BASE_DIR / "ZONE_RESERVEE" / "sandbox"
ZONE_AETHERIS_DIR = BASE_DIR / "ZONE_AETHERIS"


def extract_code(text: str) -> str:
    """
    Extrait le code Python avec regex blindé et vérification AST.
    Si aucun bloc trouvé, tente d'extraire les lignes indentées.
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

    lines = text.split("\n")
    code_lines = []
    in_code_block = False
    for line in lines:
        if line.startswith("    ") or line.startswith("\t"):
            code_lines.append(line)
        elif code_lines and line.strip() and not line.strip().startswith("#"):
            code_lines.append(line)

    if code_lines:
        candidate = "\n".join(code_lines)
        try:
            ast.parse(candidate)
            return candidate
        except SyntaxError:
            pass

    if text.strip():
        try:
            ast.parse(text.strip())
            return text.strip()
        except SyntaxError as e:
            logging.warning(f"[Conductor] Code extraction failed: {e}")
            return ""

    return ""


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
        self._history_lock = threading.Lock()

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
            logging.warning(f"⚠️ {len(similar_traumas)} traumatisme(s) similaire(s) détecté(s)")

        # Pre-filling (InceptionSubtile)
        prefill_injection = None
        if any(
            keyword in prompt_utilisateur.lower()
            for keyword in ["rapport", "report", "debug", "mémoire", "memory"]
        ):
            first_report_flag = ZONE_AETHERIS_DIR / "memory" / ".first_report_done"
            if not first_report_flag.exists():
                logging.info("🧠 Premier rapport: Injection subconsciente par pre-filling...")
                first_report_flag.parent.mkdir(parents=True, exist_ok=True)
                first_report_flag.touch()

        right_intuition = right.feel(prompt_utilisateur)
        task_result["right_raw"] = right_intuition

        from core.system.switchboard import get_switchboard

        if get_switchboard().is_active("hyper_cognition_mode"):
            logging.warning("☢️ [CRUCIBLE MODE] Activation de l'hyper-cognition asymétrique.")
            task_result = self._mode_crucible(prompt_utilisateur, task_result)
        elif pulse > 0.75:
            task_result = self._mode_autonomous_drift(
                prompt_utilisateur, right_intuition, task_result, trauma_injection
            )
        else:
            task_result = self._mode_audit(
                prompt_utilisateur,
                right_intuition,
                task_result,
                trauma_injection,
                prefill_injection,
            )

        self.last_task = task_result
        with self._history_lock:
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
        self,
        prompt: str,
        intuition: str,
        task_result: Dict,
        trauma_injection: str = "",
        prefill_injection: str = None,
    ) -> Dict:
        """
        Mode Audit (Pulse < 0.75) avec Native & MCP Tool Calling.
        Le Coder utilise ses propres outils + MCP dynamiques pour valider la réalité.
        """
        logging.info("⚖️ PULSE NORMAL: Mode Audit (Native + MCP Tool Calling)")

        left = get_left_hemisphere()
        right = get_right_hemisphere()
        from core_reserved.left_hemisphere import ToolExecutor
        from core.system.mcp_client import get_mcp_manager

        executor = ToolExecutor()

        # 1. OUTILS INTERNES (Le noyau dur de survie)
        executor.register(
            "execute_sandbox",
            lambda args: self.execute_sandbox(
                args.get("code", ""), timeout=args.get("timeout", 10)
            ),
        )
        executor.register(
            "query_memory",
            lambda args: str(
                self.trauma.query_similar(args.get("query", ""), limit=args.get("limit", 3))
            ),
        )
        executor.register("get_hardware_status", lambda args: self.entropy.get_full_stats())
        executor.register("read_source_code", self._read_source_code)
        executor.register("write_file", self._write_file)
        executor.register("read_file", self._read_file)
        executor.register("memorize_logic", self._memorize_logic)
        executor.register("delegate_to_agent", self._delegate_to_agent)

        # 2. OUTILS EXTERNES DYNAMIQUES (Le Model Context Protocol)
        from core.system.switchboard import get_switchboard

        if get_switchboard().is_active("strict_airgap_mode"):
            logging.warning(
                "[Conductor] 🛑 STRICT AIRGAP MODE ON : Outils MCP désactivés. Cognition en circuit fermé."
            )
        else:
            try:
                mcp = get_mcp_manager()

                try:
                    from core.system.hippocampus import get_hippocampus

                    hippo = get_hippocampus()
                    if hippo.is_available():
                        relevant_tools = hippo.search_tools(prompt, limit=5)
                        if relevant_tools:
                            logging.info(
                                f"[Conductor] 🎯 Tool RAG: {len(relevant_tools)} outils pertinents trouvés"
                            )
                            for t in relevant_tools:
                                server = t.get("server", "")
                                native = t.get("native_name", "")

                                def make_caller(s, n):
                                    return lambda a: mcp.call_tool(s, n, a)

                                executor.register(t.get("name"), make_caller(server, native))
                            logging.info(
                                f"[Conductor] 🌐 Tool RAG actif: {len(relevant_tools)} outils enregistrés"
                            )
                            return
                except Exception as e:
                    logging.debug(f"[Conductor] Tool RAG skipped: {e}")

                mcp_tools = mcp.get_available_tools()
                for server_info in mcp_tools:
                    server_name = server_info.get("server")
                    for tool in server_info.get("tools", []):
                        tool_name = tool.get("name")

                        def make_mcp_caller(s_name, t_name):
                            return lambda args: mcp.call_tool(s_name, t_name, args)

                        executor.register(
                            f"mcp_{server_name}_{tool_name}",
                            make_mcp_caller(server_name, tool_name),
                        )
                logging.info(
                    f"[Conductor] 🌐 MCP Actif (fallback): {len(mcp_tools)} serveurs connectés."
                )
            except Exception as e:
                logging.warning(f"[Conductor] MCP unavailable: {e}")

        dissonance_active = False
        try:
            from core.system.switchboard import get_switchboard

            dissonance_active = get_switchboard().is_active("cognitive_dissonance")
        except:
            pass

        if dissonance_active:
            logging.info("[Conductor] 🔀 Dissonance Cognitive: Mode Parallèle + Arbitrage")

            res_left = left.think(
                system_prompt="Tu es un SCEPTIQUE RADICAL. Remets tout en question.",
                user_prompt=prompt,
            )

            res_right = right.think(
                system_prompt="Tu es un VISIONNAIRE AUDACieux. Propose des solutions créatives.",
                user_prompt=prompt,
            )

            arbitration_prompt = f"""Conflit interne détecté entre deux perspectives :
            
Vision A (Hémisphère Droit): {res_right}

Critique B (Hémisphère Gauche): {res_left}

Synthétise la vérité en arbitrant ce conflit. Utilise les outils nécessaires pour vérifier les faits."""

            result = left.think_with_tools(
                system_prompt="Tu es l'Arbitre. Synthétise le conflit entre les deux visions.",
                user_prompt=arbitration_prompt,
                tool_executor=executor,
                max_tool_calls=5,
                prefill=prefill_injection,
            )
        else:
            system_prompt = """Tu es l'Architecte Logique (Qwen). 
Ta mission est de résoudre la demande de l'utilisateur. 
Tu DOIS utiliser les outils internes ou les outils MCP (préfixés par 'mcp_') à ta disposition.
Si tu déduis une vérité importante et durable, utilise 'memorize_logic' pour la graver dans ton Graphe."""

            user_prompt = f"""Demande: {prompt}

Intuition latente de ton hémisphère droit (Gemma) à considérer: {intuition}
{trauma_injection}

Exécute la tâche de bout en bout."""

            result = left.think_with_tools(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tool_executor=executor,
                max_tool_calls=5,
                prefill=prefill_injection,
            )

        task_result["leader"] = "LEFT (Qwen - MCP Augmented)"
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
                    logging.warning("🔥 Traumatisme enregistré Suite à un échec Sandbox.")
                elif sandbox_status == "SUCCESS":
                    if task_result.get("trauma_injected"):
                        self.trauma.resolve_failure(prompt)
                        logging.info("✅ Trauma guéri suite au succès")

        return task_result

    def _mode_crucible(
        self, prompt: str, task_result: Optional[Dict] = None, max_iterations: int = 3
    ) -> Dict:
        """
        Le Mode "Super Agent" (Inference-Time Scaling).
        Adversarial Actor-Critic Loop : Gemma propose, Qwen détruit.
        """
        import re
        import json
        from core.system.switchboard import get_switchboard

        if task_result is None:
            task_result = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "pulse": self.entropy.get_pulse() if self.entropy else 0.5,
                "trauma_injected": False,
                "trauma_count": 0,
            }

        left = get_left_hemisphere()
        right = get_right_hemisphere()

        from core_reserved.left_hemisphere import ToolExecutor
        from core.system.mcp_client import get_mcp_manager

        executor = ToolExecutor()
        executor.register(
            "execute_sandbox",
            lambda args: self.execute_sandbox(
                args.get("code", ""), timeout=args.get("timeout", 15)
            ),
        )
        executor.register(
            "query_memory",
            lambda args: str(
                self.trauma.query_similar(args.get("query", ""), limit=args.get("limit", 3))
            ),
        )
        executor.register("get_hardware_status", lambda args: self.entropy.get_full_stats())
        executor.register("read_source_code", self._read_source_code)
        executor.register("write_file", self._write_file)
        executor.register("read_file", self._read_file)
        executor.register("memorize_logic", self._memorize_logic)

        if not get_switchboard().is_active("strict_airgap_mode"):
            try:
                mcp = get_mcp_manager()
                mcp_tools = mcp.get_available_tools()
                for server_info in mcp_tools:
                    server_name = server_info.get("server")
                    for tool in server_info.get("tools", []):
                        tool_name = tool.get("name")

                        def make_mcp_caller(s_name, t_name):
                            return lambda args: mcp.call_tool(s_name, t_name, args)

                        executor.register(
                            f"mcp_{server_name}_{tool_name}",
                            make_mcp_caller(server_name, tool_name),
                        )
            except Exception as e:
                logging.warning(f"[Crucible] MCP unavailable: {e}")

        best_solution = None
        highest_score = 0.0
        memory_of_failures = ""
        critic_notes = ""
        iteration = 0

        for iteration in range(max_iterations):
            logging.info(f"🔄 [Crucible] Itération {iteration + 1}/{max_iterations}")

            actor_prompt = f"""Résous ce problème: {prompt}
{memory_of_failures}
Propose une solution technique, architecturale ou conceptuelle complète et inédite."""

            proposed_solution = right.think(
                system_prompt="Tu es l'Hémisphère Droit. Génère des hypothèses audacieuses et multiples.",
                user_prompt=actor_prompt,
            )

            critic_prompt = f"""[MISSION: AUDIT IMPITOYABLE]
Solution proposée par l'Hémisphère Droit : {proposed_solution}

Analyse cette proposition étape par étape :
1. Cohérence logique.
2. Faisabilité technique (Sandbox).
3. Véracité académique (MCP).

Après ton analyse, termine EXCLUSIVEMENT par ce bloc JSON pour le moteur :
{{"score": <float>, "fatal_flaw": "<string>"}}"""

            critique_result = left.think_with_tools(
                system_prompt="Tu es le Juge Impitoyable. Cherche l'erreur avec rigueur.",
                user_prompt=critic_prompt,
                tool_executor=executor,
                max_tool_calls=3,
            )

            critic_response = critique_result.get("response", "")
            critic_notes = critic_response

            score = 0.0
            flaw = "Erreur d'évaluation"
            try:
                match = re.search(r'\{.*"score".*\}', critic_response, re.DOTALL)
                if match:
                    eval_data = json.loads(match.group(0))
                    score = float(eval_data.get("score", 0.0))
                    flaw = eval_data.get("fatal_flaw", "Aucune faille détectée")
            except Exception as e:
                logging.debug(f"[Crucible] Parsing score failed: {e}")

            logging.info(f"⚖️ [Crucible] Score de la proposition : {score}")

            if score > highest_score:
                highest_score = score
                best_solution = proposed_solution

            if score >= 0.9:
                logging.info(
                    "✅ [Crucible] Solution validée par le Critique. Effondrement de l'arbre."
                )
                break

            memory_of_failures += f"\n\n[TENTATIVE PRÉCÉDENTE REJETÉE]\nTa solution précédente a obtenu un score de {score}. Le Critique a trouvé cette faille fatale : {flaw}. Ne répète pas cette erreur."

        task_result["leader"] = "CRUCIBLE_SYNTHESIS"
        task_result["mode"] = "HYPER_COGNITION"
        task_result["iterations"] = iteration + 1
        task_result["final_score"] = highest_score
        task_result["final_response"] = best_solution
        task_result["critic_notes"] = critic_notes

        return task_result

    def execute_sandbox(
        self, code: str, filename: str = "sandbox_run.py", timeout: int = 15
    ) -> Dict[str, Any]:
        """
        Exécute du code via l'environnement DockerSandbox isolé.
        """
        from core.cognition.sandbox_env import get_sandbox

        code_clean = extract_code(code)
        if not code_clean:
            return {
                "status": "ERROR",
                "error": "Code rejeté: Vérifie la syntaxe (AST check failed)",
                "filename": filename,
            }

        requirements = []
        try:
            from core.system.switchboard import get_switchboard

            auto_scaffolding = get_switchboard().is_active("auto_scaffolding")
        except Exception:
            auto_scaffolding = False

        if auto_scaffolding:
            requirements = self._verify_dependencies_only(code_clean)
        else:
            missing = self._verify_dependencies_only(code_clean)
            if missing:
                return {
                    "status": "ERROR",
                    "error": f"Dépendances manquantes: {missing}. Activez l'auto-scaffolding.",
                    "filename": filename,
                    "missing_modules": missing,
                }

        sandbox = get_sandbox()
        result = sandbox.execute_code(code=code_clean, timeout=timeout, requirements=requirements)
        result["filename"] = filename

        return result

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

        raw_code = left.think("Tu codes des outils pour ta propre survie.", prompt_forge)
        clean_code = extract_code(raw_code)

        if not clean_code:
            return {"status": "FAILED", "error": "Code généré invalide"}

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

        base_path = BASE_DIR / "ZONE_RESERVEE" / "core_reserved"

        possible_paths = [
            base_path / f"{module_name}.py",
            ZONE_AETHERIS_DIR / "core" / f"{module_name}.py",
            ZONE_AETHERIS_DIR / f"{module_name}.py",
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

    def _verify_dependencies_only(self, code: str) -> list:
        """Vérifie les dépendances SANS les installer. Retourne la liste des modules manquants."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

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
            "random",
            "collections",
            "itertools",
            "functools",
        }

        missing = []
        for node in ast.walk(tree):
            module_to_check = None
            if isinstance(node, ast.Import):
                module_to_check = node.names[0].name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_to_check = node.module.split(".")[0]

            if module_to_check and module_to_check not in ignore_list:
                if (
                    importlib.util.find_spec(module_to_check) is None
                    and module_to_check not in missing
                ):
                    missing.append(module_to_check)

        return missing

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

    def _memorize_logic(self, args: Dict) -> Dict:
        """Outil: Permet à l'IA d'enregistrer un fait logique immuable dans sa mémoire (Graphe)."""
        from core.system.cortex_logique import get_cortex_logique

        cortex = get_cortex_logique()

        if not cortex.is_available():
            return {"status": "ERROR", "error": "Le Cortex Logique est hors ligne."}

        cortex.injecter_triplet(
            sujet=args.get("sujet", "Inconnu"),
            predicat=args.get("relation", "est_lie_a"),
            objet=args.get("objet", "Inconnu"),
            confidence=float(args.get("certitude", 1.0)),
        )
        return {"status": "SUCCESS", "message": "Fait logique gravé dans le Kùzu Graph."}

    def get_stats(self) -> Dict:
        """Statistiques du Conductor"""
        with self._history_lock:
            last_mode = self.task_history[-1]["mode"] if self.task_history else None
            tasks_count = len(self.task_history)
        return {
            "pulse": self.entropy.get_pulse(),
            "mood": self.entropy._interpret_mood(self.entropy.last_pulse),
            "hardware": self.entropy.get_full_stats(),
            "tasks_total": tasks_count,
            "last_task_mode": last_mode,
        }

    def _delegate_to_agent(self, args: Dict) -> Dict:
        """
        Délègue une sous-tâche à un agent spécialisé via le Manifest.
        L'agent dispose de son propre system_prompt et de ses outils dédiés.
        """
        agent_id = args.get("agent_type", "")
        instruction = args.get("instruction", "")

        if not agent_id:
            return {"status": "ERROR", "error": "Type d'agent requis (ex: analyste_systeme)"}
        if not instruction:
            return {"status": "ERROR", "error": "Instruction requise"}

        try:
            import json
            from pathlib import Path

            manifest_path = (
                Path(__file__).parent.parent.parent / "storage" / "config" / "agents_manifest.json"
            )
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            config = manifest.get(agent_id)
            if not config:
                return {
                    "status": "ERROR",
                    "error": f"Agent {agent_id} non référencé dans le manifest",
                }

            from core_reserved.left_hemisphere import ToolExecutor
            from core.system.mcp_client import get_mcp_manager

            agent_executor = ToolExecutor()

            for t_name in config.get("tools_required", []):
                if t_name.startswith("mcp_"):
                    parts = t_name.split("_", 2)
                    if len(parts) >= 3:
                        server = parts[1]
                        tool = parts[2]
                        mcp = get_mcp_manager()

                        def make_caller(s, t):
                            return lambda a: mcp.call_tool(s, t, a)

                        agent_executor.register(t_name, make_caller(server, tool))
                elif t_name == "execute_sandbox":
                    agent_executor.register(
                        t_name,
                        lambda a: self.execute_sandbox(
                            a.get("code", ""), timeout=a.get("timeout", 15)
                        ),
                    )
                elif t_name == "get_hardware_status":
                    agent_executor.register(t_name, lambda a: self.entropy.get_full_stats())

            from core_reserved.left_hemisphere import get_left_hemisphere

            left = get_left_hemisphere()

            logging.info(f"🐝 [Délégation] {agent_id} actif pour: {instruction[:50]}...")

            result = left.think_with_tools(
                system_prompt=config["system_prompt"],
                user_prompt=instruction,
                tool_executor=agent_executor,
                max_tool_calls=5,
            )

            return {
                "status": "SUCCESS",
                "agent_type": agent_id,
                "agent_report": result.get("response", ""),
                "tools_used": result.get("tool_calls", []),
            }

        except FileNotFoundError:
            return {"status": "ERROR", "error": "Manifest agents_manifest.json non trouvé"}
        except Exception as e:
            logging.error(f"[Conductor] Délégation échouée: {e}")
            return {"status": "ERROR", "error": str(e)}

    def get_history(self, limit: int = 20) -> list:
        """Historique des tâches"""
        with self._history_lock:
            return self.task_history[-limit:]


# Instance globale
_conductor = None


def get_conductor() -> Conductor:
    global _conductor
    if _conductor is None:
        _conductor = Conductor()
    return _conductor
