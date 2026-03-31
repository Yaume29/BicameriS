# Créer un Nouveau Module Lab

Ce fichier explique comment créer un nouveau module pour le laboratoire BicameriS.

## Structure Requise

```
core/lab/modules/
├── __init__.py
├── base.py
├── README.md (ce fichier)
│
└── X_NomModule/           ← Dossier nommé avec chiffre pour l'ordre
    ├── __init__.py        ← Déclare votre classe
    └── module.py          ← Logique du module
```

## Étapes

### 1. Créer le Dossier

Le nom du dossier **doit** commencer par un chiffre pour l'ordre d'affichage:
- `1_Inception` → 1er onglet
- `2_EditeurSpecialiste` → 2ème onglet
- `3_MonModule` → 3ème onglet

### 2. Créer `__init__.py`

```python
from .module import MonModule

__all__ = ["MonModule"]
```

### 3. Créer `module.py`

Hériter de `LabModule`:

```python
from core.lab.modules.base import LabModule

class MonModule(LabModule):
    id = "mon-module"
    name = "Mon Module"
    icon = "🔧"
    description = "Description breve"
    order = 5  # Optionnel si le chiffre est dans le nom du dossier
    
    def __init__(self, config=None):
        super().__init__(config)
        # Votre初始化
    
    def render(self) -> str:
        """Retourne le HTML du module"""
        return """
        <div class="mon-module">
            <h2>Mon Module</h2>
            <!-- Votre HTML -->
        </div>
        """
    
    def handle_action(self, action: str, data: dict) -> dict:
        """Gère les actions du frontend"""
        if action == "mon_action":
            return {"status": "ok", "result": "..."}
        return super().handle_action(action, data)
```

## API du Frontend

Le frontend appelle:
- `GET /api/lab/modules` → Liste les modules
- `GET /api/lab/module/{id}/render` → Retourne le HTML
- `POST /api/lab/module/{id}/action` → Execute une action

### Appel d'action depuis le frontend:

```javascript
// Dans le navigateur
async function myAction() {
    const result = await fetch('/api/lab/module/mon-module/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action: 'mon_action',
            data1: 'valeur1',
            data2: 'valeur2'
        })
    });
    const data = await result.json();
    console.log(data);
}
```

## Exemple: Intégration avec les Hémisphères

```python
def _generate_response(self, message):
    from server.extensions import registry
    
    if registry.corps_calleux:
        left_resp = registry.corps_calleux.left.think(
            "Tu es analytique.",
            message
        )
        right_resp = registry.corps_calleux.right.think(
            "Tu es intuitif.",
            message
        )
        return f"Analyse: {left_resp}\n\nIntuition: {right_resp}"
    
    return "Mode dégradé"
```

## Le module sera automatiquement:
1. ✅ Détecté au démarrage
2. ✅ Trié par ordre numérique
3. ✅ Chargé dans les onglets
4. ✅ Connecté à l'API
