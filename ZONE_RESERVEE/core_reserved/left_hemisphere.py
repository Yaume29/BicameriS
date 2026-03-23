"""
Hémisphère Gauche d'Aetheris - Logique/Analyse
Utilisation de llama-cpp-python pour inference locale avec Native Tool Calling
"""

import os
import json
import re
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime


AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Recherche des informations sur le web via SearXNG ou DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Requête de recherche"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["searxng", "duckduckgo"]},
                        "description": "Sources可选 (défaut: les deux)",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Nombre de résultats",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sandbox",
            "description": "Exécute du code Python dans un environnement isolé",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code Python à exécuter"},
                    "timeout": {
                        "type": "integer",
                        "default": 10,
                        "description": "Timeout en secondes",
                    },
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Écrit du contenu dans un fichier",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Chemin du fichier"},
                    "content": {"type": "string", "description": "Contenu à écrire"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_memory",
            "description": "Interroge la mémoire vectorielle pour des souvenirs similaires",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Requête de rappel"},
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Nombre de résultats",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lit le contenu d'un fichier",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Chemin du fichier"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hardware_status",
            "description": "Retourne le statut hardware actuel (CPU, RAM, VRAM, pulse)",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_source_code",
            "description": "Lit le code source d'Aetheris pour comprendre son architecture",
            "parameters": {
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "Nom du module (ex: conductor, flux, left_hemisphere)",
                    }
                },
                "required": ["module_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_dependency",
            "description": "Installe une dépendance Python via pip",
            "parameters": {
                "type": "object",
                "properties": {
                    "package": {
                        "type": "string",
                        "description": "Nom du package à installer",
                    },
                },
                "required": ["package"],
            },
        },
    },
]


class ToolExecutor:
    """Exécuteur d'outils pour le Native Tool Calling"""

    def __init__(self):
        self.handlers: Dict[str, Callable] = {}

    def register(self, name: str, handler: Callable):
        self.handlers[name] = handler

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name in self.handlers:
            try:
                return self.handlers[tool_name](arguments)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Outil '{tool_name}' non enregistré"}


class LeftHemisphere:
    """
    Hémisphère gauche : Logique, raisonnement, décisions explicites
    Température: configurable (défaut 0.7)
    Contexte: configurable (défaut 16384 tokens)
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 16384,
        n_gpu_layers: int = -1,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
    ):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.model = None
        self.is_loaded = False

        self._load_model()

    def _load_model(self):
        """Charge le modèle avec llama-cpp-python"""
        try:
            from llama_cpp import Llama

            print(f"[LEFT] Chargement de {self.model_path}...")
            print(f"[LEFT] n_ctx={self.n_ctx}, n_gpu_layers={self.n_gpu_layers}")
            print(f"[LEFT] temp={self.temperature}, top_p={self.top_p}")

            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                n_threads=os.cpu_count() or 8,
                flash_attention=True,
                use_mmap=False,
                verbose=False,
            )

            self.is_loaded = True
            print(f"[LEFT] Modèle chargé avec succès!")

        except ImportError:
            print("[LEFT] ERREUR: llama-cpp-python non installé")
            self.is_loaded = False

        except Exception as e:
            print(f"[LEFT] ERREUR lors du chargement: {e}")
            self.is_loaded = False

    def think(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse structurée et logique"""
        if not self.is_loaded or self.model is None:
            return "[LEFT] Modèle non chargé"

        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stop=[],
            )

            if response and response.get("choices"):
                return response["choices"][0]["message"]["content"]

            return "[LEFT] Pas de réponse"

        except Exception as e:
            return f"[LEFT] Erreur: {str(e)}"

    def think_stream(self, system_prompt: str, user_prompt: str, callback):
        """Génère avec streaming"""
        if not self.is_loaded or self.model is None:
            callback("[LEFT] Modèle non chargé")
            return

        try:
            self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stream=True,
                stop=[],
                on_chunk=callback,
            )
        except Exception as e:
            callback(f"[LEFT] Erreur: {str(e)}")

    def update_params(self, **kwargs):
        """Met à jour les paramètres à la volée"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        print(f"[LEFT] Paramètres mis à jour: {kwargs}")

    def set_params(
        self, temperature=None, top_p=None, repeat_penalty=None, max_tokens=None
    ):
        """Met à jour les paramètres d'inférence"""
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if repeat_penalty is not None:
            self.repeat_penalty = repeat_penalty
        if max_tokens is not None:
            self.max_tokens = max_tokens
        print(
            f"[LEFT] Params: temp={self.temperature}, top_p={self.top_p}, repeat={self.repeat_penalty}, max_tokens={self.max_tokens}"
        )

    def summarize(self, content: str, max_tokens: int = 512) -> str:
        """Résume le contenu"""
        if not self.is_loaded:
            return "[LEFT] Modèle non chargé"

        prompt = (
            f"Résume ce texte en points clés précis (max 5 points):\n{content[:8000]}"
        )

        return self.think(
            system_prompt="Tu es un assistant qui synthétise l'information.",
            user_prompt=prompt,
        )

    def get_status(self) -> Dict:
        """Retourne le statut complet"""
        return {
            "loaded": self.is_loaded,
            "model_path": self.model_path,
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty,
        }

    def unload(self):
        """Décharge le modèle de la mémoire"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            print("[LEFT] Modèle déchargé")

    def think_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_executor: "ToolExecutor" = None,
        max_tool_calls: int = 4,
    ) -> Dict[str, Any]:
        """
        Génère une réponse avec Native Tool Calling et boucle d'auto-correction.
        """
        if not self.is_loaded or self.model is None:
            return {
                "response": "[LEFT] Modèle non chargé",
                "tool_calls": [],
                "tool_results": [],
            }

        tools_json = json.dumps(AVAILABLE_TOOLS, indent=2)

        full_system = f"""{system_prompt}

Tu possèdes des outils natifs. Pour résoudre la tâche:
1. Analyse la demande et tes manques d'informations.
2. Si un outil est nécessaire, réponds STRICTEMENT avec ce format JSON:
{{"name": "nom_de_loutil", "arguments": {{"param1": "valeur1"}}}}
3. N'ajoute AUCUN texte avant ou après le JSON si tu appelles un outil.
4. Si tu as réussi ou que tu n'as plus besoin d'outil, donne ta conclusion finale en texte clair.

Outils disponibles:
{tools_json}"""

        tool_calls_made = []
        tool_results = []

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt},
        ]

        for iteration in range(max_tool_calls):
            try:
                response = self.model.create_chat_completion(
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    repeat_penalty=self.repeat_penalty,
                )
            except Exception as e:
                return {
                    "response": f"[LEFT] Erreur Inférence: {str(e)}",
                    "tool_calls": tool_calls_made,
                    "tool_results": tool_results,
                }

            if not response or not response.get("choices"):
                break

            content = response["choices"][0]["message"].get("content", "")
            if not content.strip():
                break

            parsed_calls = self._parse_tool_calls(content)

            if not parsed_calls:
                return {
                    "response": content,
                    "tool_calls": tool_calls_made,
                    "tool_results": tool_results,
                }

            for tool_call in parsed_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})

                tool_calls_made.append({"name": tool_name, "arguments": tool_args})

                if tool_executor and tool_name in tool_executor.handlers:
                    result = tool_executor.execute(tool_name, tool_args)
                else:
                    result = {"error": f"Outil '{tool_name}' inconnu."}

                tool_results.append({"tool": tool_name, "result": result})

            # Agréger tous les résultats dans un seul message de feedback
            messages.append({"role": "assistant", "content": content})

            feedback_lines = ["Résultats des outils appelés:"]
            for tr in tool_results:
                feedback_lines.append(
                    f"\n[{tr.get('tool')}]\n{json.dumps(tr.get('result'), ensure_ascii=False)}"
                )

            feedback_lines.append(
                "\n\nSi un résultat contient une erreur, CORRIGE ton approche. Sinon, poursuis ou conclus."
            )

            messages.append({"role": "user", "content": "\n".join(feedback_lines)})

        final_prompt = "Limite d'outils atteinte. Conclus avec les données actuelles."
        messages.append({"role": "user", "content": final_prompt})

        final_response = self.model.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return {
            "response": final_response["choices"][0]["message"].get(
                "content", "Erreur finale."
            )
            if final_response and final_response.get("choices")
            else "Pas de réponse",
            "tool_calls": tool_calls_made,
            "tool_results": tool_results,
        }

    def _parse_tool_calls(self, text: str) -> List[Dict]:
        """Parse les appels d'outils avec extraction JSON robuste"""
        # Plan A: Extraction de blocs markdown ```json ou ```python
        patterns = [
            r"```(?:json|python)?\s*\n(.*?)\n```",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    json_str = match.group(1).strip()
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list):
                        valid = [p for p in parsed if "name" in p or "function" in p]
                        if valid:
                            return valid
                    elif isinstance(parsed, dict) and (
                        "name" in parsed or "function" in parsed
                    ):
                        return [parsed]
                except (json.JSONDecodeError, AttributeError):
                    pass

        # Plan B: Extraction structurelle via json.loads sur le texte complet
        try:
            parsed = json.loads(text.strip())
            if isinstance(parsed, list):
                valid = [p for p in parsed if "name" in p or "function" in p]
                if valid:
                    return valid
            elif isinstance(parsed, dict) and (
                "name" in parsed or "function" in parsed
            ):
                return [parsed]
        except (json.JSONDecodeError, ValueError):
            pass

        # Plan C: Extraction robuste JSON avec regex qui tolère les accolades imbriquées
        # Cherche le pattern {"name": "...", "arguments": {...}} même avec du code Python dedans
        json_pattern = r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                parsed = json.loads(match)
                if "name" in parsed or "function" in parsed:
                    return [parsed]
            except (json.JSONDecodeError, ValueError):
                continue

        # Plan D: Recherche de TOUT objet JSON avec extraction positionnelle
        # Trouve toutes les positions de { et } pour reconstruire les objets
        start_positions = [m.start() for m in re.finditer(r"\{", text)]
        end_positions = [m.start() for m in re.finditer(r"\}", text)]

        for start in start_positions:
            for end in end_positions:
                if end > start:
                    candidate = text[start : end + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict) and (
                            "name" in parsed or "function" in parsed
                        ):
                            return [parsed]
                    except (json.JSONDecodeError, ValueError):
                        continue

        return []


# Instance globale
_left_hemisphere = None


def get_left_hemisphere() -> Optional[LeftHemisphere]:
    return _left_hemisphere


def init_left_hemisphere(model_path: str, **kwargs) -> LeftHemisphere:
    global _left_hemisphere
    _left_hemisphere = LeftHemisphere(model_path=model_path, **kwargs)
    return _left_hemisphere
