# Guide de Création d'un Module Lab

## 1. Structure des Fichiers

```
core/lab/modules/
├── __init__.py
├── base.py
├── README.md
│
└── X_NomModule/              ← Dossier avec chiffre pour l'ordre
    ├── __init__.py            ← Déclare le module
    ├── module.py              ← Logique principale
    └── config.yaml            ← (optionnel) Configuration
```

**Nom du dossier:** Le chiffre détermine l'ordre d'affichage.
- `1_Inception` → 1er onglet
- `2_EditeurSpecialiste` → 2ème onglet
- `5_MonModule` → 5ème onglet

---

## 2. Fichiers Obligatoires

### `__init__.py`
```python
from .module import MonModule

__all__ = ["MonModule"]
```

### `module.py`
```python
from ...modules.base import LabModule
from typing import Dict

class MonModule(LabModule):
    id = "mon-module"
    name = "Mon Module"
    icon = "🔧"
    description = "Description breve"
    order = 5  # Optionnel si chiffre dans le nom du dossier
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        # Votre initialisation
    
    def render(self) -> str:
        """Retourne le HTML du module"""
        return """
        <div class="module-monModule module-5_MonModule" 
             style="--module-color: #ff6b6b; --module-color-rgb: 255, 107, 107;">
            <!-- Votre HTML ici -->
        </div>
        """
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        """Gère les actions du frontend"""
        if action == "mon_action":
            return self._mon_action(data)
        return super().handle_action(action, data)
    
    def _mon_action(self, data: Dict) -> Dict:
        # Votre logique
        return {"status": "ok", "result": "..."}
```

---

## 3. Variables CSS pour les Couleurs

Chaque module **DOIT** définir ses couleurs avec des variables CSS inline:

```html
<div class="module-monModule" 
     style="
        --module-color: #ff6b6b; 
        --module-color-rgb: 255, 107, 107;
     ">
```

### Couleurs par défaut disponibles:
| Module | Couleur | RGB |
|--------|---------|-----|
| Inception | Cyan | 0, 212, 255 |
| EditeurSpecialiste | Violet | 139, 92, 246 |
| Induction | Ambre | 245, 158, 11 |
| Autonome | Vert | 16, 185, 129 |

### Variables CSS utilisées automatiquement:
- `--module-color` - Couleur principale
- `--module-color-rgb` - RGB pour transparence (ex: `rgba(var(--module-color-rgb), 0.15)`)
- `--module-bg` - Background transparite
- `--module-border` - Bordure

---

## 4. API et Endpoints

### Endpoints principaux:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/lab/modules` | Liste tous les modules |
| GET | `/api/lab/module/{id}/render` | Retourne le HTML du module |
| POST | `/api/lab/module/{id}/action` | Exécute une action |

### Appel depuis le frontend:
```javascript
// Lister les modules
await fetch('/api/lab/modules')

// Obtenir le HTML d'un module
await fetch('/api/lab/module/mon-module/render')

// Exécuter une action
await fetch('/api/lab/module/mon-module/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        action: 'mon_action',
        param1: 'valeur1',
        param2: 'valeur2'
    })
})
```

---

## 5. Accès au Système Cognitif

### Se connecter aux hemispheres:
```python
def _generate_response(self, message: str) -> str:
    try:
        from server.extensions import registry
        
        if registry.corps_calleux:
            corps = registry.corps_calleux
            
            # Hémisphère gauche (analytique)
            left_resp = corps.left.think(
                "Tu es analytique.",
                message,
                temperature=0.3
            )
            
            # Hémisphère droit (intuitif)
            right_resp = corps.right.think(
                "Tu es intuitif.",
                message,
                temperature=0.7
            )
            
            return f"Analyse: {left_resp}\n\nIntuition: {right_resp}"
    
    except Exception as e:
        return f"Erreur: {str(e)}"
```

### Autres services disponibles:
```python
from server.extensions import registry

# Accéder aux autres composants
registry.corps_calleux     # Corps calleux (hémisphères)
registry.rag_indexer       # Indexeur RAG
registry.woven_memory       # Mémoire avancée
registry.task_queue         # File de tâches
```

---

## 6. Outils et Services Utiles

### WovenMemory (Mémoire):
```python
from core.system.woven_memory import get_woven_memory

wm = get_woven_memory()
wm.weave("Contenu à mémoriser", source="mon-module", category="general")
synapses = wm.recall("Requête", limit=5)
```

### Fichier de configuration:
```python
# Dans __init__ ou config
config = self.config.get('mon-module', {})
valeur = config.get('une_option', 'defaut')
```

---

## 7. Script de Découverte

Exécutez ce script pour découvrir les endpoints et services disponibles:

```bash
cd /chemin/vers/Aetheris
python -c "
import sys
sys.path.insert(0, '.')

print('=== SERVICES DISPONIBLES ===')
try:
    from server.extensions import registry
    print('Registry attributes:')
    for attr in dir(registry):
        if not attr.startswith('_'):
            print(f'  - {attr}')
except Exception as e:
    print(f'Erreur: {e}')

print()
print('=== ENDPOINTS API ===')
try:
    from server.routes import api_lab
    import inspect
    for name, func in inspect.getmembers(api_lab):
        if hasattr(func, 'endpoint'):
            print(f'  {func.endpoint.methods} {func.endpoint.path}')
except Exception as e:
    print(f'Erreur: {e}')

print()
print('=== MODULES LAB ===')
try:
    from core.lab.modules import list_lab_modules
    modules = list_lab_modules()
    for m in modules:
        print(f'  {m[\"order\"]}: {m[\"name\"]} ({m[\"id\"]})')
except Exception as e:
    print(f'Erreur: {e}')
"
```

---

## 8. Prompt pour LLM - Création de Module

Utilisez ce prompt pour qu'un LLM crée un module pour vous:

```
Tu es un développeur pour BicameriS, un système d'IA bicaméral.

Crée un nouveau module Lab complet dans le dossier core/lab/modules/X_NomModule/ où X est le numéro d'ordre.

### Requirements:
1. Crée un dossier core/lab/modules/X_NomModule/
2. Crée __init__.py qui exporte la classe principale
3. Crée module.py avec:
   - Classe héritant de LabModule
   - Méthode render() retournant du HTML
   - Méthode handle_action() pour les actions API
   - Styles CSS inline avec --module-color et --module-color-rgb

### Contexte du système:
- Les modules sont dans core/lab/modules/
- La classe de base est LabModule (core.lab.modules.base)
- Pour accéder aux hemispheres: from server.extensions import registry puis registry.corps_calleux.left/right
- Les actions API sont via handle_action(action, data)
- Couleurs via variables CSS: --module-color et --module-color-rgb

### Le module doit:
- Être autonome et fonctionnel
- Utiliser les styles CSS existants du laboratoire
- Se connecter au système cognitif si pertinent
- Retourner du HTML qui s'intègre au layout

Crée les fichiers nécessaires avec du code fonctionnel et complet.
```

---

## 9. Exemple: Module Simple Complet

### `core/lab/modules/5_Exemple/__init__.py`
```python
from .module import ExempleModule

__all__ = ["ExempleModule"]
```

### `core/lab/modules/5_Exemple/module.py`
```python
from typing import Dict
from ...modules.base import LabModule

class ExempleModule(LabModule):
    id = "exemple"
    name = "Exemple"
    icon = "📝"
    description = "Un module d'exemple"
    order = 5
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self._messages = []
    
    def render(self) -> str:
        return """
        <div class="module-exemple module-5_Exemple" 
             style="--module-color: #ff6b6b; --module-color-rgb: 255, 107, 107;">
            <div class="module-card">
                <h3>📝 Module Exemple</h3>
                
                <div class="form-group">
                    <label>Votre message</label>
                    <input type="text" id="exemple-input" placeholder="Tapez...">
                </div>
                
                <button class="btn btn-primary" onclick="sendExempleMessage()">
                    Envoyer
                </button>
                
                <div id="exemple-messages"></div>
            </div>
        </div>
        """
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        if action == "send":
            return self._send_message(data)
        return super().handle_action(action, data)
    
    def _send_message(self, data: Dict) -> Dict:
        msg = data.get("message", "")
        self._messages.append(msg)
        
        # Exemple d'utilisation des hemispheres
        try:
            from server.extensions import registry
            if registry.corps_calleux:
                response = registry.corps_calleux.left.think(
                    "Réponds de manière concise.",
                    msg
                )
                return {"status": "ok", "response": response}
        except:
            pass
        
        return {"status": "ok", "response": f"Reçu: {msg}"}
```

---

## Résumé Rapide

| Élément | Description |
|---------|-------------|
| Dossier | `X_NomModule/` (X = chiffre) |
| Classe | Hérite de `LabModule` |
| HTML | Retourne via `render()` |
| Actions | Via `handle_action()` |
| Couleurs | `--module-color` inline |
| API | `/api/lab/module/{id}/action` |
| Hémisphères | `registry.corps_calleux.left/right` |
