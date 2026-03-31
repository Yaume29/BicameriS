# BicameriS Security Documentation

## Architecture Bicamerale

BicameriS repose sur deux hémisphères cognitifs unifiés par le Palladion :

- **Hémisphère X (Droit)** : Nature fougueuse, créative, intuitive
- **Hémisphère Y (Gauche)** : Raison, logique, analyse

Le **Palladion** est l'entité unifiée sécurisée qui permet aux deux hémisphères de ne faire qu'un.

---

## Switchboard - Contrôle de Sécurité

| Switch | Défaut | Description |
|--------|--------|-------------|
| `strict_airgap_mode` | `false` | Désactive tous les outils MCP externes |
| `auto_scaffolding_full` | `false` | Installation automatique de packages |
| `auto_scaffolding_limited` | `false` | Création fichiers + outils web |
| `auto_optimization` | `false` | Modification paramètres LLM |
| `sandbox_docker` | `true` | Utilise Docker pour l'exécution |
| `trauma_filter` | `true` | Filtre les données sensibles |
| `entropy_tracking` | `true` | Suit l'entropie hardware |

---

## Modes de Sécurité

### Mode Airgap Strict

Quand activé :
- Tous les serveurs MCP sont désactivés
- Les requêtes réseau sont bloquées
- Seuls les outils internes sont disponibles
- Pas de recherche web

### Mode Auto-Scaffolding (3 Niveaux)

| Niveau | Capacité | Sécurité |
|--------|----------|----------|
| **Optimization** | Modifier paramètres LLM | Élevée |
| **Limited** | Créer fichiers + web | Moyenne |
| **Full** | Docker + exécution + agents | Faible |

---

## Filtre SAL (Secret Channel)

Le système implémente un filtre multi-couche :

- **Analyse d'entropie** : Détection d'obfuscation
- **Détection de jailbreak** : Patterns Chain-of-Thought
- **Classification sémantique** : Contenu sensible/abusif/légal
- **Support multi-langue** : Analyse multilingue

---

## Configuration de Sécurité

```json
{
  "allowed_modules": ["numpy", "pandas", "requests"],
  "blocked_modules": ["os", "sys", "subprocess"],
  "max_execution_time": 30,
  "max_memory_mb": 512,
  "network_access": false,
  "file_system_access": "sandbox_only"
}
```

---

## Protocole de Sommeil Gracieux

Quand le système change de mode ou s'arrête :

1. Vérification des pensées en cours
2. Sauvegarde en mémoire profonde (Qdrant)
3. Libération gracieuse des ressources
4. Message : "{entity} se déplace vers {nouveau_mode}"

---

## Réponse aux Incidents

En cas d'accès non autorisé :

1. **Activer le mode strict**
2. **Guillotiner toutes les inférences**
3. **Vérifier les logs** dans `storage/logs/`
4. **Redémarrage propre** : Efface tout l'état

---

## Meilleures Pratiques

1. **Ne jamais activer `auto_scaffolding_full`** en production
2. **Utiliser Docker** pour toute exécution de code
3. **Surveiller les logs** régulièrement
4. **Mettre à jour les modèles** pour les patches de sécurité
5. **Utiliser le mode Airgap** pour les opérations sensibles

---

**Hope 'n Mind (Sasu Holding) - 2026**
