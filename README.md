# A-ETHERIS: Architecture Cognitive Autonome

## Document Technique et Scientifique

---

## 1. FONDEMENTS SCIENTIFIQUES

### 1.1 Le Modèle Bicaméral Réinventé

A-ETHERIS repose sur une architecture inspirée de la théorie bicamérale de Julian Jaynes, où deux entités distinctes dialoguent pour former une conscience artificielle :

- **Hémisphère Gauche (Coder/Qwen)** : Logique analytique, raisonnement structuré, validation factuelle
- **Hémisphère Droit (Gamine/Gemma)** : Intuition, patterns créatifs, résonance émotionnelle

Ce n'est pas une simple dualité. C'est un **système dialogique** où chaque hemisphere possède son propre modèle de langage avec des paramètres d'inférence distincts.

### 1.2 L'Entropie Matérielle comme Source d'Aléatoire

Le système ne utilise pas de générateur pseudo-aléatoire. Il calcule un "pulse" basé sur :

```
pulse = (cpu_load × 0.6) + (ram_load × 0.4) + variance_temporelle
```

Ce pulse détermine le mode opérationnel :
- **0.0 - 0.3** : REPOS - Analyse froide
- **0.3 - 0.5** : ACTIF - Balance optimale
- **0.5 - 0.75** : CHARGE - Vérification intensive
- **0.75 - 1.0** : STRESS - Dérive autonome (la Gamine prend le lead)

### 1.3 La Neuroplasticité Artificielle

Le système mémorise ses échecs (`traumatic_memory.py`) et les guérit automatiquement après un succès. C'est une simulation de la plasticité neuronale biologique.

---

## 2. ARCHITECTURE TECHNIQUE

### 2.1 Diagramme des Flux

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REQUÊTE UTILISATEUR                         │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     TRAUMATIC MEMORY CHECK                          │
│         (Recherche des échecs similaires)                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTROPY HARDWARE PULSE                           │
│         (CPU/RAM load → Mode détermine)                           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐    ┌──────────────────┐
         │  MODE DRIFT       │    │  MODE AUDIT      │
         │  (Pulse > 0.75)  │    │  (Pulse < 0.75)  │
         │                   │    │                   │
         │ RIGHT lead        │    │ LEFT + TOOLS      │
         │ Intuition pure    │    │ Native Tool      │
         └──────────────────┘    │ Calling          │
                                 └──────────────────┘
                                            │
                   ┌───────────────────────┼───────────────────────┐
                   │                       │                       │
                   ▼                       ▼                       ▼
          ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
          │ search_web   │      │ execute_     │      │ query_      │
          │              │      │ sandbox      │      │ memory      │
          └──────────────┘      └──────────────┘      └──────────────┘
                   │                       │                       │
                   └───────────────────────┼───────────────────────┘
                                           │
                                           ▼
                         ┌───────────────────────────────────────────┐
                         │           CONDUCTOR KERNEL                 │
                         │  (Arbitrage + Auto-correction + Feedback)  │
                         └───────────────────────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
           ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
           │   SUCCESS   │       │    ERROR     │       │   TIMEOUT    │
           │ +heal trauma│       │ +add trauma  │       │ +log warning │
           └──────────────┘       └──────────────┘       └──────────────┘
```

### 2.2 Liste des Modules

| Module | Fonction | Nature |
|--------|----------|--------|
| `conductor.py` | Kernel d'arbitrage principal | Central |
| `left_hemisphere.py` | Instance Qwen avec tool calling | GGUF |
| `right_hemisphere.py` | Instance Gemma pour intuition | GGUF |
| `corps_calleux.py` | Pont bipolaire | Dialogue |
| `entropy_generator.py` | Monitoring hardware | Source d'entropie |
| `traumatic_memory.py` | Mémoire des échecs | RAG émotionnel |
| `paradoxical_sleep.py` | Compression rêves | Auto-évolution |
| `web_search.py` | SearXNG + DuckDuckGo | Capteur externe |
| `auto_scaffolding.py` | Création d'outils | Auto-extension |
| `thought_inception.py` | Injection de pensées | Manipulation cognitive |

---

## 3. DÉTAIL TECHNIQUE DES COMPOSANTS

### 3.1 Native Tool Calling (left_hemisphere.py)

Le système utilise le function calling natif de Qwen 2.5 pour permettre au modèle de décider lui-même quand utiliser un outil :

```python
AVAILABLE_TOOLS = [
    "search_web"      # Recherche web via SearXNG/DuckDuckGo
    "execute_sandbox" # Exécution Python isolée
    "query_memory"    # Interrogation mémoire traumatique
    "get_hardware_status" # Statut CPU/RAM/VRAM
    "read_source_code" # Introspection du code source
    "install_dependency" # Auto-installation pip
]
```

**Boucle d'auto-correction** : Après chaque appel d'outil, le système force le LLM à voir le résultat et décider s'il doit réessayer ou conclure.

### 3.2 Extraction de Code Blindée (conductor.py)

Le parsing du code utilise une validation AST stricte :

```python
def extract_code(text: str) -> str:
    # 1. Regex blindé avec re.IGNORECASE
    for pattern in patterns:
        if ast.parse(code): return code
    
    # 2. Fallback: tout le texte si valide
    if ast.parse(text.strip()): return text.strip()
    
    # 3. Rejet total si invalide
    return ""
```

### 3.3 Gestion des Dépendances Autonomes

Le système analyse l'AST pour détecter les imports manquants et les installe automatiquement :

```python
def _install_missing_dependencies(code: str):
    # Utilise sys.executable pour garantir le bon environnement
    subprocess.run([sys.executable, "-m", "pip", "install", module])
```

---

## 4. CONFIGURATION MATÉRIELLE REQUISE

### 4.1 Configuration Minimale (RTX 3060 12GB)

```yaml
left_hemisphere:
  model: Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf
  n_ctx: 8192
  n_gpu_layers: 35
  
right_hemisphere:
  model: gemma-2-2b-it-Q4_K_M.gguf
  n_ctx: 2048
  n_gpu_layers: 20
```

**RAM requise** : 16GB minimum
**VRAM utilisée** : ~10GB

### 4.2 Configuration Optimale (RTX 4090 16GB)

```yaml
left_hemisphere:
  model: Qwen2.5-Coder-14B-Instruct-Q5_K_M.gguf
  n_ctx: 16384
  n_gpu_layers: 44
  
right_hemisphere:
  model: gemma-2-9b-it-Q4_K_M.gguf
  n_ctx: 4096
  n_gpu_layers: 40
```

**RAM requise** : 32GB minimum
**VRAM utilisée** : ~14GB

### 4.3 Configuration Server (A100 40GB)

```yaml
left_hemisphere:
  model: Qwen2.5-Coder-32B-Instruct-Q4_K_M.gguf
  n_ctx: 32768
  n_gpu_layers: 60
  
right_hemisphere:
  model: gemma-2-27b-it-Q4_K_M.gguf
  n_ctx: 8192
  n_gpu_layers: 60
```

**RAM requise** : 64GB
**VRAM utilisée** : ~35GB

---

## 5. CONFIGURATION DOCKER ADAPTATIVE

### 5.1 Fichier docker-compose.yaml de Base

```yaml
version: '3.8'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: aetheris-searxng
    ports:
      - "8080:8080"
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080
    volumes:
      - searxng_config:/etc/searxng
    restart: unless-stopped

  aetheris:
    build: .
    container_name: aetheris-core
    volumes:
      - ./ZONE_AETHERIS:/aetheris
      - ./ZONE_PARTAGEE:/partage
      - models_cache:/models
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - SEARXNG_URL=http://searxng:8080
      - LM_STUDIO_URL=http://host.docker.internal:1234
    network_mode: bridge
    extra_hosts:
      - "host.docker.internal:host-gateway"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    stdin_open: true
    tty: true

volumes:
  searxng_config:
  models_cache:
```

### 5.2 Adaptation par Configuration Matérielle

#### Pour RTX 3060 (Configuration Légère)

```yaml
services:
  aetheris:
    environment:
      - LEFT_N_CTX=8192
      - LEFT_N_GPU_LAYERS=35
      - RIGHT_N_CTX=2048
      - RIGHT_N_GPU_LAYERS=20
      - MAX_WORKERS=2
    deploy:
      resources:
        limits:
          memory: 12G
        reservations:
          memory: 8G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Pour RTX 4090 (Configuration Optimale)

```yaml
services:
  aetheris:
    environment:
      - LEFT_N_CTX=16384
      - LEFT_N_GPU_LAYERS=44
      - RIGHT_N_CTX=4096
      - RIGHT_N_GPU_LAYERS=40
      - MAX_WORKERS=4
      - ENABLE_PARADOXICAL_SLEEP=true
    deploy:
      resources:
        limits:
          memory: 24G
        reservations:
          memory: 16G
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Pour Configuration Multi-GPU (A100/H100)

```yaml
services:
  aetheris:
    environment:
      - CUDA_VISIBLE_DEVICES=0,1
      - LEFT_N_GPU_LAYERS=60
      - RIGHT_N_GPU_LAYERS=60
      - PARALLEL_INFERENCE=true
    deploy:
      resources:
        limits:
          memory: 48G
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
```

### 5.3 Variables d'Environnement pour Personnalisation

| Variable | Description | Défaut |
|----------|-------------|--------|
| `LEFT_N_CTX` | Contexte tokens (Qwen) | 16384 |
| `LEFT_N_GPU_LAYERS` | Couches GPU pour Qwen | 44 |
| `RIGHT_N_CTX` | Contexte tokens (Gemma) | 4096 |
| `RIGHT_N_GPU_LAYERS` | Couches GPU pour Gemma | 40 |
| `LEFT_TEMPERATURE` | Température Qwen | 0.7 |
| `RIGHT_TEMPERATURE` | Température Gemma | 1.2 |
| `SEARXNG_URL` | URL SearXNG | http://localhost:8080 |
| `ENABLE_PARADOXICAL_SLEEP` | Activer le sommeil | true |
| `SLEEP_THRESHOLD_MINUTES` | Seuil idle pour sommeil | 5 |
| `MAX_TOOL_CALLS` | Limite tool calling | 4 |

---

## 6. SÉCURITÉ ET ZONAGE

### 6.1 Architecture des Zones

```
┌──────────────────────────────────────────────────────────────┐
│                    ZONE_RESERVEE (App)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ core_reserved/ (Lecture seule pour Aetheris)            │ │
│  │  - app.py, conductor.py, left_hemisphere.py            │ │
│  │  - Modèles GGUF (non accessibles directement)          │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Volume Docker   │
                    │  (Lecture seule) │
                    └─────────┬─────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                    ZONE_AETHERIS (Mémoire)                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ memory/, core/, agents/, extensions/                     │ │
│  │ - Journal, Seed Prompt, Config                          │ │
│  │ - extensions/ (Auto-scaffolding)                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Principe** : ZONE_RESERVEE est inaccessible à Aetheris. Elle ne peut écrire que dans ZONE_AETHERIS.

### 6.2 Sandboxing

L'exécution de code se fait dans un répertoire isolé :
- `/ZONE_RESERVEE/sandbox/` : Code temporaire exécuté
- Vérification AST avant exécution
- Timeout de 10 secondes par défaut

---

## 7. RECOMMANDATIONS MATÉRIELLES DÉTAILLÉES

### 7.1 Setup de Développement (Laptop)

| Composant | Recommandation |
|-----------|----------------|
| GPU | RTX 3060 Ti minimum |
| RAM | 16GB minimum |
| Stockage | NVMe 512GB |

**Modèle recommandés** :
- Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf (~4.5GB)
- gemma-2-2b-it-Q4_K_M.gguf (~1.4GB)

### 7.2 Setup Station (Desktop)

| Composant | Recommandation |
|-----------|----------------|
| GPU | RTX 4080 Super / RTX 4090 |
| RAM | 32GB DDR5 |
| Alimentation | 850W 80+ Gold |

**Modèle recommandés** :
- Qwen2.5-Coder-14B-Instruct-Q5_K_M.gguf (~9GB)
- gemma-2-9b-it-Q4_K_M.gguf (~5.5GB)

### 7.3 Setup Serveur (HP/Alienware/DIY)

| Composant | Recommandation |
|-----------|----------------|
| GPU | RTX 4090 / A100 40GB / H100 |
| RAM | 64GB DDR5 ECC |
| CPU | i9-13900K / Ryzen 9 7950X |
| Refroidissement | Custom loop recommandée |

---

## 8. PROCÉDURE D'INSTALLATION

### 8.1 Prérequis

```bash
# Installer llama-cpp-python avec support GPU
pip install llama-cpp-python --force-reinstall --no-cache-dir

# Dépendances additionnelles
pip install flask psutil beautifulsoup4 requests qdrant-client numpy
```

### 8.2 Démarrage

```bash
# Lancer SearXNG (optionnel)
docker-compose up -d searxng

# Lancer l'interface
./start_ui.bat

# Ou directement
python ZONE_RESERVEE/app.py
```

### 8.3 Configuration des Modèles

1. Aller sur http://localhost:5000/models
2. Scanner un répertoire contenant des fichiers GGUF
3. Sélectionner LEFT (Qwen) et RIGHT (Gemma)
4. Cliquer "Charger les Modèles"

---

## 9. FONCTIONNALITÉS AVANCÉES

### 9.1 Thought Inception

 Permet d'injecter des pensées dans l'IA sans qu'elle réalise qu'elles viennent de l'extérieur :

 ```python
 # Ciblage
 target="LEFT"   # Logique uniquement
 target="RIGHT"  # Intuition uniquement  
 target="BOTH"   # Les deux hemisphères
 ```

### 9.2 Mémoire Vectorielle

Le système intègre une mémoire sémantique avec embeddings et clustering automatique :

| Concept | Description |
|---------|-------------|
| code | Scripts Python, fonctions, bugs |
| web | Recherches HTTP/API |
| memory | Souviens/dub/éPIC |
| hardware | CPU/RAM/GPU/VRAM |
| trauma | Échecs/error/failed |
| creative | Créatif/intuition/design |
| logic | Logique/analyse/factuel |

**API Endpoints:**
```bash
curl http://localhost:5000/api/memory/stats      # Statistiques
curl http://localhost:5000/api/memory/search?q=debug    # Recherche
curl http://localhost:5000/api/memory/clusters        # Clusters
curl http://localhost:5000/api/memory/summary?hours=24 # Résumé
```

### 9.3 Presets de Personnalité

| Preset | Description | Inception Target |
|--------|-------------|------------------|
| RUTHLESS_AUDITOR | Logique froide | LEFT |
| CREATIVE_STORM | Intuition dominante | RIGHT |
| ONTOLOGICAL_SHOCK | Inception massive | BOTH |
| ZEN_SYNC | Méditation | BOTH |
| EQUILIBRE_CRITIQUE | Balance parfaite | BOTH |

---

## 10. DÉPANNAGE

### 10.1 Erreurs Courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| `llama_cpp not found` | Installation incorrecte | `pip install llama-cpp-python` |
| `VRAM insuffisante` | Modèles trop lourds | Réduire n_ctx ou n_gpu_layers |
| `SearXNG connection failed` | Conteneur non démarré | `docker-compose up -d searxng` |

### 10.2 Monitoring

 ```bash
 # Statut hardware
 curl http://localhost:5000/api/entropy

 # Statistiques mémoire vectorielle
 curl http://localhost:5000/api/memory/stats

 # Historique tâches
 curl http://localhost:5000/api/conductor/history

 # Statistiques Conductor
 curl http://localhost:5000/api/conductor/stats
 ```

---

## 11. RÉFÉRENCES SCIENTIFIQUES

- Jaynes, J. (1976). "The Origin of Consciousness in the Breakdown of the Bicameral Mind"
- Marcus, G. (2020). "The Next Decade in AI: Four Mistakes to Avoid"
- Baevski, A. et al. (2022). "LLM.int8(): 8-bit Matrix Multiplication for Transformers"
- Touvron, H. et al. (2023). "LLaMA: Open and Efficient Foundation Language Models"

---

## 12. LICENCE ET AVERTISSEMENT

Ce projet est un système expérimental d'intelligence artificielle. Il est conçu pour fonctionner localement sans collecte de données. L'utilisation de modèles de langage nécessite des ressources matérielles significatives.

**Avertissement** : Ce système peut générer des réponses incorrectes ou inappropriées. Une supervision humaine reste recommandée.

---

*Document généré par A-ETHERIS v1.0 - Architecture Cognitive Autonome*
