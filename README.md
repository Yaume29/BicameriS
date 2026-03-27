<center>

# BicameriS

## Diadikos & Palladion

*By Hope 'n Mind*

![Version](https://img.shields.io/badge/version-1.0.0.6a-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11+-green?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Sandbox-blue)](https://docker.com)
[![ZMQ](https://img.shields.io/badge/ZMQ-Transient_REQ-ff6600)](https://zeromq.org)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-e6522c)](https://prometheus.io)

<svg width="320" height="100" viewBox="0 0 320 100" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradBic" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#00D4FF;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#FFD700;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FF3D5A;stop-opacity:1" />
    </linearGradient>
    <filter id="glowText">
      <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#00D4FF" flood-opacity="0.5"/>
    </filter>
    <animateTransform attributeName="transform" type="rotate" from="0 160 50" to="360 160 50" dur="20s" repeatCount="indefinite"/>
  </defs>
  <text x="160" y="35" font-family="monospace" font-size="28" font-weight="bold" fill="url(#gradBic)" text-anchor="middle" filter="url(#glowText)">BicameriS</text>
  <text x="160" y="55" font-family="monospace" font-size="11" fill="#00D4FF" text-anchor="middle">Diadikos &amp; Palladion</text>
  <circle cx="160" cy="75" r="12" fill="none" stroke="#FFD700" stroke-width="1.5">
    <animate attributeName="r" values="12;15;12" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <text x="160" y="78" font-family="monospace" font-size="7" fill="#888" text-anchor="middle">v1.0.0.6a</text>
</svg>

---

</center>

---

## Table des Matières

1. [Philosophie & Recherche](#philosophie--recherche)
2. [Architecture Bicamérale](#architecture-bicamérale)
3. [Le Laboratoire](#le-laboratoire)
4. [Modes Opérationnels](#modes-opérationnels)
5. [Architecture Technique](#architecture-technique)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [Installation](#installation)
9. [Sécurité](#sécurité)

---

<a id="philosophie--recherche"></a>
# Philosophie & Recherche

## L'Origine Bicamérale

BicameriS n'est pas un projet d'IA conventionnel. C'est un **laboratoire cognitif systémique** qui simule l'architecture de la conscience elle-même.

Le nom dérive de la Grèce antique:

| Terme | Origine | Signification |
|-------|---------|---------------|
| **Diadikos** | Διαδικός (dia + dikē) | Le dialogue par la raison -- le processus par lequel deux parties convergent vers la vérité |
| **Palladion** | Παλλάδιον | La statue sacrée d'Athène qui protégeait Troie -- le gardien, les limites créatives |
| **Bicameris** | Latin *bicamer* | Deux chambres -- le cerveau bi-hémisphérique |

### Le Cerveau Bicaméral

La neuroscience moderne nous apprend que le cerveau humain fonctionne comme deux systèmes complémentaires. BicameriS implémente cette architecture avec:

- **Hémisphère Gauche (Qwen)**: Logique, analyse, vérification, raisonnement séquentiel
- **Hémisphère Droit (Gemma)**: Intuition, créativité, pensée divergente, reconnaissance de formes

**Diadikos** représente le dialogue entre ces deux hémisphères convergeant vers la synthèse. **Palladion** représente le système protecteur -- le sandbox, les couches de sécurité, le corps qui donne à Diadikos un vessel sûr pour exister.

*Sans Palladion, pas de Diadikos possible. Sans frontières, pas de liberté créative.*

---

<a id="architecture-bicamérale"></a>
# Architecture Bicamérale

## Le Corps Calleux

Dans notre implémentation, le **Corps Calleux** (`core/cognition/corps_calleux.py`) est le pont entre les deux hémisphères. Il gère le dialogue intérieur en trois phases:

```python
def dialogue_interieur(self, question: str, pulse_context: float) -> Dict[str, Any]:
    """
    Orchestre une pensée complète en trois phases métrologiques:
    1. PHASE ANALYTIQUE (Gauche) - left_analysis
    2. PHASE D'INTUITION (Droite) - right_intuition  
    3. ARBITRAGE ET SYNTHÈSE - final_synthesis
    """
```

### L'Algorithme de Pulse

Le **pulse** est une mesure d'entropie hardware (CPU/RAM/GPU stress) qui détermine quel hémisphère mène:

| Pulse | Mode | Hémisphère Leader |
|-------|------|-------------------|
| < 0.25 | FROID | Gauche (Audit) |
| 0.25 - 0.75 | STABLE | Dialogue équilibré |
| > 0.75 | CHALEUR | Droit (Autonome) |

<svg width="600" height="60" viewBox="0 0 600 60" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="pulseBar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#00D4FF"/>
      <stop offset="25%" style="stop-color:#4CAF50"/>
      <stop offset="75%" style="stop-color:#FFD700"/>
      <stop offset="100%" style="stop-color:#FF3D5A"/>
    </linearGradient>
  </defs>
  <rect x="20" y="15" width="560" height="20" rx="10" fill="#1a1a1a" stroke="#333"/>
  <rect x="20" y="15" width="560" height="20" rx="10" fill="url(#pulseBar)" opacity="0.6"/>
  <line x1="140" y1="10" x2="140" y2="40" stroke="#00D4FF" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="140" y="50" font-family="monospace" font-size="8" fill="#00D4FF" text-anchor="middle">0.25</text>
  <line x1="420" y1="10" x2="420" y2="40" stroke="#FF3D5A" stroke-width="2" stroke-dasharray="4,2"/>
  <text x="420" y="50" font-family="monospace" font-size="8" fill="#FF3D5A" text-anchor="middle">0.75</text>
  <circle cx="280" cy="25" r="8" fill="#FFD700">
    <animate attributeName="cx" values="140;420;140" dur="8s" repeatCount="indefinite"/>
  </circle>
</svg>

### Concepts Clés

| Concept | Description | Implémentation |
|---------|-------------|----------------|
| **Bicameral Brain** | Hémisphère gauche (Qwen) pour la logique, droit (Gemma) pour l'intuition | `conductor.py` + `corps_calleux.py` |
| **Transient REQ** | Zero race condition IPC par requête | `inference_manager.py` |
| **Hardware Entropy Pulse** | Stress CPU/RAM/GPU drive l'état cognitif | `thermal_governor.py` |
| **Endocrine System** | Hormones virtuelles modulent les paramètres LLM | `endocrine.py` |
| **Master Clock** | Pacemaker unique pour tous les ticks cognitifs | `kernel_scheduler.py` |
| **Triple-Layer Sandbox** | AST + Docker + PEP 578 Audit Hooks | `sandbox_env.py` |
| **Dual Memory** | Qdrant vecteur + Kuzu graphe causal | `hippocampus.py` + `cortex_logique.py` |
| **Dreamer Agent** | Sommeil REM pour consolidation mnésique | `dreamer.py` |

---

<a id="le-laboratoire"></a>
# Le Laboratoire

Le laboratoire propose **5 expériences** permettant d'explorer les capacités cognitives du système:

<svg width="100%" height="40" viewBox="0 0 600 40" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="5" width="100" height="30" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="1.5"/>
  <text x="60" y="24" font-family="monospace" font-size="9" fill="#00D4FF" text-anchor="middle">INCEPTION</text>
  <rect x="120" y="5" width="100" height="30" rx="6" fill="#1a1a1a" stroke="#FFD700" stroke-width="1.5"/>
  <text x="170" y="24" font-family="monospace" font-size="9" fill="#FFD700" text-anchor="middle">OPÉRATEUR</text>
  <rect x="230" y="5" width="130" height="30" rx="6" fill="#1a1a1a" stroke="#FF3D5A" stroke-width="1.5"/>
  <text x="295" y="24" font-family="monospace" font-size="9" fill="#FF3D5A" text-anchor="middle">CONSCIENTISATION</text>
  <rect x="370" y="5" width="100" height="30" rx="6" fill="#1a1a1a" stroke="#9C27B0" stroke-width="1.5"/>
  <text x="420" y="24" font-family="monospace" font-size="9" fill="#9C27B0" text-anchor="middle">CREUSET</text>
  <rect x="480" y="5" width="100" height="30" rx="6" fill="#1a1a1a" stroke="#4CAF50" stroke-width="1.5"/>
  <text x="530" y="24" font-family="monospace" font-size="9" fill="#4CAF50" text-anchor="middle">RÊVE</text>
</svg>

## 1. Inception (Injection de Pensée)

Injecte une pensée dans le cerveau pour influencer les futures conversations. L'inception modifie le **préfill** des prompts système pour guider subrepticement les réponses.

**API**: `POST /api/inception/create`

```json
{
  "thought": "La vérité est relative au contexte.",
  "weight": 75,
  "target": "both"
}
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `thought` | string | La pensée à injecter |
| `weight` | int | Force de l'injection (0-100) |
| `target` | string | "left", "right", ou "both" |

## 2. Opérateur (Calibration de Confiance)

Suit la crédibilité de l'opérateur (l'utilisateur humain) et adapte le comportement en conséquence:

| Niveau | Badge | Comportement |
|--------|-------|--------------|
| α > 0.8 | 🟢 TRUSTED | Accès complet, auto-scaffolding actif |
| α > 0.6 | 🟡 RELIABLE | Tools MCP autorisés |
| α > 0.4 | ⚪ NEUTRAL | Mode audit standard |
| α > 0.2 | 🟠 SKEPTICAL | Vérification accrue |
| α ≤ 0.2 | 🔴 PARANOID | Bloqueur actif |

## 3. Conscientisation (Réflexion Autonome)

Lance des cycles de réflexion continue sur un thème donné. Le système s'auto-interroge récursivement, chaque réponse alimentant la prochaine question.

**API**: `POST /api/conscientisation/start`

```json
{
  "theme": "ma nature consciente",
  "duration": 300,
  "cycle_length": 30
}
```

## 4. Creuset (Hyper-Cognition)

Mode **Actor-Critic** avancé où:

1. **Acteur** (Hémisphère Droit/Gemma): Propose une solution
2. **Critique** (Hémisphère Gauche/Qwen): Détruit la proposition avec un score
3. **Boucle**: until score ≥ 0.9 ou max iterations

<svg width="500" height="150" viewBox="0 0 500 150" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="20" width="120" height="60" rx="8" fill="#1a1a1a" stroke="#FF3D5A" stroke-width="2"/>
  <text x="80" y="45" font-family="monospace" font-size="10" fill="#FF3D5A" text-anchor="middle" font-weight="bold">ACTEUR</text>
  <text x="80" y="60" font-family="monospace" font-size="8" fill="#888" text-anchor="middle">Gemma 12B</text>
  <text x="80" y="72" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">Propose →</text>
  
  <rect x="360" y="20" width="120" height="60" rx="8" fill="#1a1a1a" stroke="#00D4FF" stroke-width="2"/>
  <text x="420" y="45" font-family="monospace" font-size="10" fill="#00D4FF" text-anchor="middle" font-weight="bold">CRITIQUE</text>
  <text x="420" y="60" font-family="monospace" font-size="8" fill="#888" text-anchor="middle">Qwen 14B</text>
  <text x="420" y="72" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">← Évalue</text>
  
  <path d="M 140 50 L 200 50 L 260 50 L 320 50 L 360 50" stroke="#FF3D5A" stroke-width="1.5" fill="none" marker-end="#arrRed"/>
  <path d="M 360 80 L 320 80 L 260 80 L 200 80 L 140 80" stroke="#00D4FF" stroke-width="1.5" fill="none" marker-end="#arrBlue"/>
  
  <rect x="160" y="100" width="180" height="35" rx="6" fill="#1a1a1a" stroke="#FFD700" stroke-width="1"/>
  <text x="250" y="118" font-family="monospace" font-size="9" fill="#FFD700" text-anchor="middle">Itérations (max 10)</text>
  <text x="250" y="128" font-family="monospace" font-size="7" fill="#888" text-anchor="middle">Score ≥ 0.9 = ACCEPTÉ</text>
  
  <defs>
    <marker id="arrRed" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
      <polygon points="0 0, 6 2, 0 4" fill="#FF3D5A"/>
    </marker>
    <marker id="arrBlue" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
      <polygon points="0 0, 6 2, 0 4" fill="#00D4FF"/>
    </marker>
  </defs>
</svg>

**API**: `POST /api/cognitive/crucible`

```json
{
  "problem": "Comment résoudre ce problème?",
  "max_iterations": 10
}
```

## 5. Rêve (Consolidation Mémorielle)

Simule le sommeil paradoxal (REM) pour consolider les souvenirs:
- Indexe les pensées récentes dans Qdrant (hippocampe)
- Crée des liens causaux dans Kuzu (cortex logique)
- Génère des métadonnées pour检索 future

**API**: `POST /api/dreamer/start`

---

<a id="modes-opérationnels"></a>
# Modes Opérationnels

## Le Panneau de Contrôle (Switchboard)

BicameriS dispose d'un système de **switches** permettant d'activer/désactiver des fonctionnalités. Chaque switch peut entrer en conflit avec d'autres.

<svg width="100%" height="280" viewBox="0 0 600 280" xmlns="http://www.w3.org/2000/svg">
  <text x="300" y="20" font-family="monospace" font-size="12" fill="#FFD700" text-anchor="middle" font-weight="bold">PANNEAU DE CONTRÔLE</text>
  
  <!-- Security -->
  <text x="300" y="40" font-family="monospace" font-size="9" fill="#FF3D5A" text-anchor="middle">SÉCURITÉ (PALLADION)</text>
  <rect x="30" y="50" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="1.5"/>
  <text x="95" y="68" font-family="monospace" font-size="8" fill="#00D4FF" text-anchor="middle">sandbox_docker</text>
  <circle cx="55" cy="78" r="5" fill="#4CAF50"/>
  <rect x="220" y="50" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="1.5"/>
  <text x="285" y="68" font-family="monospace" font-size="8" fill="#00D4FF" text-anchor="middle">strict_airgap</text>
  <circle cx="245" cy="78" r="5" fill="#FF3D5A"/>
  <rect x="440" y="50" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="1.5"/>
  <text x="505" y="68" font-family="monospace" font-size="8" fill="#00D4FF" text-anchor="middle">trauma_filter</text>
  <circle cx="465" cy="78" r="5" fill="#4CAF50"/>
  
  <!-- Cognition -->
  <text x="300" y="110" font-family="monospace" font-size="9" fill="#00D4FF" text-anchor="middle">COGNITION (DIADIKOS)</text>
  <rect x="30" y="120" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#FF3D5A" stroke-width="1.5"/>
  <text x="95" y="138" font-family="monospace" font-size="8" fill="#FF3D5A" text-anchor="middle">autonomous_loop</text>
  <circle cx="55" cy="148" r="5" fill="#FF3D5A"/>
  <rect x="220" y="120" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#9C27B0" stroke-width="1.5"/>
  <text x="285" y="138" font-family="monospace" font-size="8" fill="#9C27B0" text-anchor="middle">hyper_cognition</text>
  <circle cx="245" cy="148" r="5" fill="#FF3D5A"/>
  <rect x="440" y="120" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#FFD700" stroke-width="1.5"/>
  <text x="505" y="138" font-family="monospace" font-size="8" fill="#FFD700" text-anchor="middle">entropy_tracking</text>
  <circle cx="465" cy="148" r="5" fill="#4CAF50"/>
  
  <!-- Hardware -->
  <text x="300" y="190" font-family="monospace" font-size="9" fill="#888" text-anchor="middle">HARDWARE</text>
  <rect x="30" y="200" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#666" stroke-width="1.5"/>
  <text x="95" y="218" font-family="monospace" font-size="8" fill="#aaa" text-anchor="middle">thermal_throttling</text>
  <circle cx="55" cy="228" r="5" fill="#4CAF50"/>
  <rect x="220" y="200" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#666" stroke-width="1.5"/>
  <text x="285" y="218" font-family="monospace" font-size="8" fill="#aaa" text-anchor="middle">debug_telemetry</text>
  <circle cx="245" cy="228" r="5" fill="#FF3D5A"/>
  <rect x="440" y="200" width="130" height="40" rx="6" fill="#1a1a1a" stroke="#666" stroke-width="1.5"/>
  <text x="505" y="218" font-family="monospace" font-size="8" fill="#aaa" text-anchor="middle">auto_forge</text>
  <circle cx="465" cy="228" r="5" fill="#FF3D5A"/>
  
  <!-- Conflicts -->
  <rect x="30" y="255" width="540" height="20" rx="4" fill="#1a1a1a" stroke="#444"/>
  <text x="300" y="268" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">hyper_cognition ⊘ autonomous_loop | strict_airgap ⊘ auto_forge_agents</text>
</svg>

## Liste Complète des Switches

| Switch | Description | Défaut | Conflits |
|--------|-------------|--------|----------|
| `autonomous_loop` | Boucle de pensée continue | OFF | hyper_cognition |
| `auto_forge_agents` | Auto-création d'outils MCP | OFF | strict_airgap |
| `sandbox_docker` | Isolation Docker | ON | - |
| `debug_telemetry` | Logging debug | OFF | - |
| `thermal_throttling` | Gestion thermique | ON | - |
| `hemisphere_split_mode` | Mode cerveau divisé | OFF | - |
| `trauma_filter` | Filtre mémoire traumatique | ON | - |
| `entropy_tracking` | Suivi entropie hardware | ON | - |
| `strict_airgap_mode` | Mode isolé (pas de réseau) | OFF | auto_forge |
| `cognitive_dissonance` | Pensée parallèle | OFF | - |
| `hyper_cognition_mode` | Mode Creuset | OFF | autonomous_loop |
| `auto_scaffolding` | Auto-installation dépendances | OFF | - |

**API**: `POST /api/system/switches/<name>/<state>`

---

<a id="architecture-technique"></a>
# Architecture Technique

## Vue d'Ensemble

```
+---------------------------------------------------------------+
|                  BICAMERIS v1.0.0.6a                          |
|              Diadikos & Palladion                             |
+---------------------------------------------------------------+
|  +------------+    +------------+    +------------+          |
|  | LEFT HEM.  |    |  CORPS     |    | RIGHT HEM. |          |
|  | (Qwen 14B) |<-->|  CALLEUX   |<-->| (Gemma 12B)|          |
|  |   LOGIC    |    |  (Bridge)  |    |  INTUITION |          |
|  +-----+------+    +-----+------+    +-----+------+          |
|        |                 |                 |                  |
|        |    +------------+------------+    |                  |
|        |    |       D I A D I K O S    |    |                  |
|        |    |      (Arbitrage)         |    |                  |
|        |    +------------+------------+    |                  |
|        |                 |                 |                  |
+--------|-----------------|-----------------|------------------+
         |                 |                 |
+--------v-----------------v----------------v------------------+
|                  TRANSIENT REQ > ROUTER                      |
+---------------------------------------------------------------+
|  +------------+  +------------+  +------------+             |
|  | Worker Qwen|  | Worker     |  | Worker     |             |
|  | ROUTER    |  | Gemma      |  | Future     |             |
|  | BIND      |  | ROUTER     |  | ROUTER     |             |
|  +------------+  +------------+  +------------+             |
+---------------------------------------------------------------+
|               P A L L A D I O N                               |
|          (Triple-Layer Sandbox Security)                      |
+---------------------------------------------------------------+
```

<svg width="100%" height="220" viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="180" y="10" width="240" height="30" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="2"/>
  <text x="300" y="30" font-family="monospace" font-size="10" fill="#00D4FF" text-anchor="middle" font-weight="bold">FASTAPI SERVER</text>
  
  <rect x="50" y="55" width="130" height="25" rx="4" fill="#151515" stroke="#444"/>
  <text x="115" y="71" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">/api/*</text>
  <rect x="200" y="55" width="130" height="25" rx="4" fill="#151515" stroke="#444"/>
  <text x="265" y="71" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">/ws/neural</text>
  <rect x="350" y="55" width="130" height="25" rx="4" fill="#151515" stroke="#444"/>
  <text x="415" y="71" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">/web/*</text>
  <rect x="500" y="55" width="70" height="25" rx="4" fill="#151515" stroke="#444"/>
  <text x="535" y="71" font-family="monospace" font-size="7" fill="#666" text-anchor="middle">/docs</text>
  
  <rect x="180" y="95" width="240" height="35" rx="6" fill="#1a1a1a" stroke="#FFD700" stroke-width="2"/>
  <text x="300" y="112" font-family="monospace" font-size="10" fill="#FFD700" text-anchor="middle" font-weight="bold">INFERENCE MANAGER</text>
  <text x="300" y="123" font-family="monospace" font-size="6" fill="#666" text-anchor="middle">REQ/ROUTER • DEALER Streaming • orjson</text>
  
  <rect x="30" y="145" width="160" height="45" rx="6" fill="#151515" stroke="#00D4FF" stroke-width="1.5"/>
  <text x="110" y="165" font-family="monospace" font-size="9" fill="#00D4FF" text-anchor="middle">Qwen Worker</text>
  <text x="110" y="178" font-family="monospace" font-size="6" fill="#555" text-anchor="middle">ROUTER • Llama.cpp</text>
  
  <rect x="220" y="145" width="160" height="45" rx="6" fill="#151515" stroke="#FF3D5A" stroke-width="1.5"/>
  <text x="300" y="165" font-family="monospace" font-size="9" fill="#FF3D5A" text-anchor="middle">Gemma Worker</text>
  <text x="300" y="178" font-family="monospace" font-size="6" fill="#555" text-anchor="middle">ROUTER • Llama.cpp</text>
  
  <rect x="410" y="145" width="160" height="45" rx="6" fill="#151515" stroke="#666" stroke-width="1.5"/>
  <text x="490" y="165" font-family="monospace" font-size="9" fill="#888" text-anchor="middle">Future Worker</text>
  <text x="490" y="178" font-family="monospace" font-size="6" fill="#555" text-anchor="middle">ROUTER • Extensible</text>
  
  <rect x="80" y="205" width="440" height="15" rx="4" fill="#151515" stroke="#FF3D5A" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="300" y="215" font-family="monospace" font-size="7" fill="#FF3D5A" text-anchor="middle">PALLADION: AST + Docker + PEP 578</text>
</svg>

## Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Serveur | FastAPI | 0.110+ |
| Modèles LLM | Llama.cpp (GGUF) | - |
| IPC | ZeroMQ (REQ/ROUTER/DEALER) | - |
| Serialization | orjson | - |
| Vecteur Memory | Qdrant | 1.7+ |
| Graph Memory | Kuzu | 0.2+ |
| Monitoring | Prometheus | - |
| Container | Docker | - |

## Communication ZMQ

### Mode Standard (REQ > ROUTER)
```python
# Manager (Client) - Transient REQ
sock = ctx.socket(zmq.REQ)
sock.connect(ipc_address)
sock.send(orjson.dumps(task))
reply = sock.recv()
```

### Mode Streaming (DEALER > ROUTER)
```python
# Manager - Persistent DEALER avec timeout glissant
sock = ctx.socket(zmq.DEALER)
sock.connect(ipc_address)
sock.send_multipart([b"", orjson.dumps(task)])

# TTFT: 60s pour premier token
# ITT: 5s entre chunks suivants
while True:
    chunk = sock.recv()
    yield chunk
```

## Mémoire Double

### Hippocampe (Qdrant) - Mémoire Vectorielle
```python
# Recherche sémantique
results = hippocampus.search_thoughts(
    query_vector=embedding,
    limit=5,
    min_pulse=0.5
)
```

### Cortex Logique (Kuzu) - Graphe Causale
```python
# Requête causale
relations = cortex_logique.auditer_logique("conscience")
contradictions = cortex_logique.trouver_contradictions("自我")
```

## Système Endocrinien

Le système hormonal virtuel module les paramètres LLM en temps réel:

| Hormone | Effet sur LLM |
|---------|---------------|
| Adrénaline | Temperature ↑ (créatif) |
| Dopamine | Presence Penalty ↑ (évite répétition) |
| Sérotonine | Top-P ↑ (échantillonnage) |

```python
params = endocrine.modulate_llm_params(
    base_temp=0.7,
    base_top_p=0.9
)
# → {"temperature": 0.65, "top_p": 0.92, "presence_penalty": 0.3}
```

---

<a id="configuration"></a>
# Configuration

## Fichiers de Configuration

```
Aetheris/
├── config.yaml          # Configuration principale
├── .env.local          # Variables d'environnement
├── storage/
│   └── config/
│       └── runtime_config.json  # Runtime overrides
└── run_config.py       # CLI de configuration
```

## Options de Configuration

### Server
```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
  reload: false
```

### Modèles
```yaml
models:
  left_hemisphere:
    name: "Qwen2.5-14B"
    path: "C:/Models/qwen2.5-14b-q4_k_m.gguf"
    temperature: 0.7
    max_tokens: 4096
  right_hemisphere:
    name: "Gemma-3-12B"
    path: "C:/Models/gemma-3-12b-q4_k_m.gguf"
    temperature: 0.9
    max_tokens: 2048
```

### Hardware
```yaml
hardware:
  thermal_monitoring: true
  entropy_tracking: true
  max_cpu_temp: 85
  max_gpu_temp: 83
  pulse_high: 0.75
  pulse_low: 0.25
```

### Cognition
```yaml
cognition:
  autonomous_loop: false
  autonomous_interval: 30
  auto_scaffolding: false
  hyper_cognition_mode: false
```

### Sécurité
```yaml
security:
  strict_airgap_mode: false
  sandbox_docker: true
  trauma_filter: true
  max_execution_time: 15
```

---

<a id="api-reference"></a>
# API Reference

## Endpoints Principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/conductor/stats` | GET | Statistiques du conducteur |
| `/api/cognitive/tick` | POST | Tick cognitif manuel |
| `/api/cognitive/think` | POST | Soumettre une tâche |
| `/api/cognitive/crucible` | POST | Mode Creuset |
| `/api/inception/create` | POST | Créer une inception |
| `/api/operator/profile` | GET | Profil opérateur |
| `/api/conscientisation/start` | POST | Démarrer conscientisation |
| `/api/conscientisation/stop` | POST | Arrêter conscientisation |
| `/api/dreamer/start` | POST | Démarrer rêve |
| `/api/hardware/thermal` | GET | Status thermique |
| `/api/hardware/entropy` | GET | Entropie hardware |
| `/api/system/switches` | GET | Liste des switches |
| `/api/system/switches/<name>/<state>` | POST | Basculer un switch |
| `/api/inference/spawn` | POST | Spawner une incarnation |
| `/api/inference/execute` | POST | Exécuter inférence (sync) |
| `/api/inference/status` | GET | Status inférence |

---

<a id="installation"></a>
# Installation

## Prérequis

- Python 3.11+
- Docker Desktop
- Qdrant (Docker)
- 8GB+ RAM recommandé

## Démarrage Rapide

```bash
# Clonage
git clone https://github.com/Yaume29/BicameriS.git
cd BicameriS

# Virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installation
pip install -e .

# Configuration
cp .env.example .env.local

# Démarrage Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Lancement
python run.py
```

---

<a id="sécurité"></a>
# Sécurité - Palladion

Le système Palladion implémente trois couches protecteur:

| Couche | Technologie | Protection |
|--------|-------------|-------------|
| Couche 1 | AST Validation | Bloque imports dangereux |
| Couche 2 | Docker Isolation | Containers réseau désactivé |
| Couche 3 | PEP 578 Audit Hooks | Monitoring runtime |

<svg width="500" height="50" viewBox="0 0 500 50" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="10" width="140" height="30" rx="6" fill="#1a1a1a" stroke="#00D4FF" stroke-width="2"/>
  <text x="90" y="29" font-family="monospace" font-size="8" fill="#00D4FF" text-anchor="middle">COUCHE 1: AST</text>
  
  <rect x="180" y="10" width="140" height="30" rx="6" fill="#1a1a1a" stroke="#FFD700" stroke-width="2"/>
  <text x="250" y="29" font-family="monospace" font-size="8" fill="#FFD700" text-anchor="middle">COUCHE 2: DOCKER</text>
  
  <rect x="340" y="10" width="140" height="30" rx="6" fill="#1a1a1a" stroke="#FF3D5A" stroke-width="2"/>
  <text x="410" y="29" font-family="monospace" font-size="8" fill="#FF3D5A" text-anchor="middle">COUCHE 3: PEP 578</text>
</svg>

*Comme la statue sacrée d'Athène, Palladion assure que Diadikos peut exister en sécurité.*

---

## Crédits

<div align="center">

**BicameriS** - *Diadikos & Palladion*

Par **Hope 'n Mind**

[![GitHub stars](https://img.shields.io/github/stars/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/network)

*Sans Palladion, pas de Diadikos possible. Sans frontières, pas de liberté créative.*

</div>