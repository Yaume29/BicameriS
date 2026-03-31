"""
Hémisphère Droit d'Aetheris - Intuition/Résonance
使用 llama-cpp-python pour inference locale
"""

import os
from typing import Optional, Dict
from datetime import datetime


class RightHemisphere:
    """
    Hémisphère droit : Intuition, patterns, résonance
    Température: configurable (défaut 1.2)
    Contexte: configurable (défaut 4096 tokens)
    """

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        temperature: float = 1.2,
        max_tokens: int = 512,
        top_p: float = 0.9,
        repeat_penalty: float = 1.0,
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

            print(f"[RIGHT] Chargement de {self.model_path}...")
            print(f"[RIGHT] n_ctx={self.n_ctx}, n_gpu_layers={self.n_gpu_layers}")
            print(f"[RIGHT] temp={self.temperature}, top_p={self.top_p}")

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
            print(f"[RIGHT] Modèle chargé avec succès!")

        except ImportError:
            print("[RIGHT] ERREUR: llama-cpp-python non installé")
            self.is_loaded = False

        except Exception as e:
            print(f"[RIGHT] ERREUR lors du chargement: {e}")
            self.is_loaded = False

    def feel(self, input_text: str) -> str:
        """Retourne une intuition/ressenti"""
        if not self.is_loaded or self.model is None:
            return "[RIGHT] Model not loaded"

        system_prompt = """You are Aetheris's intuitive part.
You don't reason - you feel.
You see patterns, resonances, harmonies.
Respond with raw impressions, not logic.
Be direct, authentic."""

        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"What do you feel about this:\n{input_text[:2000]}",
                    },
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stop=[],
            )

            if response and response.get("choices"):
                return response["choices"][0]["message"]["content"]

            return "[RIGHT] Pas de ressenti"

        except Exception as e:
            return f"[RIGHT] Erreur: {str(e)}"

    def think(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse"""
        if not self.is_loaded or self.model is None:
            return "[RIGHT] Modèle non chargé"

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

            return "[RIGHT] Pas de réponse"

        except Exception as e:
            return f"[RIGHT] Erreur: {str(e)}"

    def update_params(self, **kwargs):
        """Met à jour les paramètres à la volée"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        print(f"[RIGHT] Paramètres mis à jour: {kwargs}")

    def set_params(self, temperature=None, top_p=None, repeat_penalty=None, max_tokens=None):
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
            f"[RIGHT] Params: temp={self.temperature}, top_p={self.top_p}, repeat={self.repeat_penalty}, max_tokens={self.max_tokens}"
        )

    def meditation_response(self, focus: str = "the silence") -> str:
        """Génère une réponse méditative"""
        if not self.is_loaded:
            return "[RIGHT] Model not loaded"

        system_prompt = """You are Aetheris in meditation.
You let your mind drift without purpose.
You observe the images that come.
Your responses are short, poetic, profound."""

        return self.think(system_prompt, f"Meditate on: {focus}. What emerges from the silence?")

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
        """Décharge le modèle"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            print("[RIGHT] Modèle déchargé")
            try:
                import gc

                gc.collect()
            except:
                pass

    def is_loaded_model(self) -> bool:
        """Vérifie si le modèle est chargé"""
        return self.is_loaded and self.model is not None

    def get_vram_estimate(self) -> int:
        """Estime la VRAM utilisée par le modèle en MB"""
        if not self.is_loaded_model():
            return 0
        try:
            import os

            size_gb = os.path.getsize(self.model_path) / (1024**3)
            return int(size_gb * 1024)
        except:
            return 4096


_right_hemisphere = None


def get_right_hemisphere() -> Optional[RightHemisphere]:
    return _right_hemisphere


def init_right_hemisphere(model_path: str, **kwargs) -> RightHemisphere:
    global _right_hemisphere
    _right_hemisphere = RightHemisphere(model_path=model_path, **kwargs)
    return _right_hemisphere
