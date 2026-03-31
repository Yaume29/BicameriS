# Prompt pour LLM - Création de Module BicameriS

Tu vas créer un nouveau module Lab complet pour le système BicameriS.

## Contexte

BicameriS est un système d'IA bicaméral avec:
- Deux hemispheres: gauche (analytique) et droit (intuitif)
- Corps calleux qui synthétise les réponses
- Modules spécialisés dans le dossier `core/lab/modules/`

## Instructions

### 1. Crée la structure suivante:
```
core/lab/modules/X_NomModule/
├── __init__.py
└── module.py
```

Remplace `X` par le numero d'ordre et `NomModule` par le nom de ton module.

### 2. Fichier `__init__.py`:
```python
from .module import NomModule

__all__ = ["NomModule"]
```

### 3. Fichier `module.py`:

DOIT contenir:
- Classe héritant de `LabModule`
- Attributs: `id`, `name`, `icon`, `description`, `order`
- Methode `render()` retournant du HTML
- Methode `handle_action()` pour les actions API
- Variables CSS `--module-color` et `--module-color-rgb` en inline

```python
from typing import Dict
from ...modules.base import LabModule

class NomModule(LabModule):
    id = "nom-module"
    name = "Nom du Module"
    icon = "🔧"
    description = "Description breve"
    order = 5
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        # Ton initialisation
    
    def render(self) -> str:
        # CHOISIS TES COULEURS:
        # Cyan: #00d4ff, RGB: 0, 212, 255
        # Violet: #8b5cf6, RGB: 139, 92, 246  
        # Ambre: #f59e0b, RGB: 245, 158, 11
        # Vert: #10b981, RGB: 16, 185, 129
        # Rose: #ff6b6b, RGB: 255, 107, 107
        
        return f"""
        <div class="module-nomModule module-X_NomModule" 
             style="--module-color: #8b5cf6; --module-color-rgb: 139, 92, 246;">
            <!-- TON HTML ICI -->
        </div>
        """
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "mon_action":
            return self._mon_action(data)
        return super().handle_action(action, data)
    
    def _mon_action(self, data: Dict) -> Dict:
        # Ta logique
        return {"status": "ok", "result": "..."}
```

### 4. Acceder aux hemispheres:

```python
def _utiliser_hemispheres(self, message: str) -> str:
    try:
        from server.extensions import registry
        
        if registry.corps_calleux:
            left = registry.corps_calleux.left.think("Analytique.", message, temperature=0.3)
            right = registry.corps_calleux.right.think("Intuitif.", message, temperature=0.7)
            return f"Analyse: {left}\n\nIntuition: {right}"
    except:
        pass
    return "Mode dégradé"
```

### 5. Styles CSS disponibles:
Les classes suivantes sont automatiques avec `--module-color`:
- `.btn-primary` - Bouton principal
- `.form-group` - Groupe de formulaire
- `.message.user` - Messages utilisateur
- `.message.assistant` - Messages IA
- `.module-card` - Carte de module

## Exemples de Modules Existants

### Inception (Cyan):
- Injection de pensées dans les hemispheres

### EditeurSpecialiste (Violet):
- Chat avec themes (Academie, Code, Litterature)
- Workspace de fichiers
- Verification d'hypotheses

### Induction (Ambre):
- Induction contextuelle
- Methodes: prefix, suffix, flood, cycle

### Autonome (Vert):
- Communication inter-hemispherique
- Modes: relay, mirror, whisper

## Ta Tache

Cree un module fonctionnel avec:
1. Un cas d'utilisation clair
2. Une UI cohente avec le theme
3. L'integration avec les hemispheres si pertinent
4. Des actions API utiles
5. Des couleurs uniques (choisis dans la palette ou ajoute une nouvelle)

Reponds uniquement avec le code creer, sans explications superflues.
