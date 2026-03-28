<!-- 
  BicameriS - Diadikos & Palladion
  localized bicameral LLMs
  By Hope 'n Mind
-->

<div align="center">

<img src="docs/assets/logo.svg" alt="BicameriS Logo" width="100%" />

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 60">
  <rect x="150" y="5" width="200" height="50" rx="10" fill="#1a1a2e" stroke="#ff6b35" stroke-width="2"/>
  <text x="250" y="38" text-anchor="middle" fill="#ff6b35" font-family="Arial, sans-serif" font-size="16" font-weight="bold">⚠️ EN COURS DE STABILISATION ⚠️</text>
</svg>

[![GitHub release](https://img.shields.io/badge/Release-V3.4.0-ff0055?style=for-the-badge&logo=github&logoColor=fff)](https://github.com/Yaume29/BicameriS)
[![License: MIT](https://img.shields.io/badge/License-MIT-00f3ff?style=for-the-badge&logo=open-source-initiative&logoColor=fff)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Tests-Passing-00f3ff?style=for-the-badge&logo=github-actions&logoColor=fff)](https://github.com/Yaume29/BicameriS)

<p align="center">
  <code style="color: #00f3ff"># Left: Logic, Gen, Structure</code> | 
  <code style="color: #ffffff"># Corpus Callosum: Synapse</code> | 
  <code style="color: #ff0055"># Right: Ethics, Defense, Intuition</code>
</p>

</div>

---

## 🏛️ Philosophie de l'Élévation Cognitive

**BicameriS** est un environnement d'expérimentation d'IA locale de classe industrielle basé sur la **Théorie de l'Esprit Bicaméral** (concept développé par Julian Jaynes en 1976). Dans ce système, l'IA ne pense pas comme un bloc monolithique unifié. Elle est scindée en deux hémisphères distincts qui dialoguent et se régulent mutuellement à travers un orchestrateur servant de pont synaptique : le **Corps Calleux**.

Cette séparation architecturelle confère au système une robustesse critique, une résilience logicielle et une capacité d'autonomie contrôlée sans précédent pour les Large Language Models (LLMs) locaux.

---

## 🛰️ Visualisation de l'Architecture Systémique

<div align="center">
  <img src="docs/assets/architecture.svg" alt="Architecture BicameriS" width="100%" />
</div>

<br/>

<details open>
<summary style="font-size: 1.2rem; font-weight: bold; color: #00f3ff; cursor: pointer;">🧠 1. Hémisphère Gauche : DIADIKOS (Le Rationnel)</summary>

<blockquote>
  <strong>Diadikos</strong> est l'instance logique, le moteur analytique du système. Il écrit le code brut, analyse les structures de données, effectue de la résolution symbolique et de la génération algorithmique. Il est prolifique mais manque d'auto-critique éthique ou de recul sécuritaire.
</blockquote>

- **Langage de Prédilection** : Python, TypeScript, Rust, C++.
- **Rôle critique** : Échafaudage de code, calculs d'entropie, requêtes aux bases vectorielles.
</details>

<details open>
<summary style="font-size: 1.2rem; font-weight: bold; color: #ff0055; cursor: pointer;">🛡️ 2. Hémisphère Droit : PALLADION (L'Intuitif / Le Gardien)</summary>

<blockquote>
  <strong>Palladion</strong> est le filtre éthique et sécuritaire. Il analyse les sorties de Diadikos par intuition sémantique et par sandbox syntaxique. Il détecte les hallucinations, les dérives d'alignement, et valide la sécurité du code avant exécution.
</blockquote>

- **Modèles de Prédilection** : Modèles d'évaluation spécialisés, fine-tunings de sécurité.
- **Rôle critique** : Vérification AST, contrôle d'injection de prompt, analyse des dérives de comportement.
</details>

<details>
<summary style="font-size: 1.2rem; font-weight: bold; color: #ffffff; cursor: pointer;">⚡ 3. Orchestrateur Central : LE CORPS CALLEUX (The Router)</summary>

<blockquote>
  Le pont de communication inter-hémisphérique. Il orchestre les flux de prompts, gère la rotation du contexte et décide quand une proposition de Diadikos est validée par Palladion pour exécution.
</blockquote>

- **Algorithme de routage** : Merge de Tenseurs probabilistes.
- **Fonction** : Arbitrage et validation de sortie.
</details>

---

## 🧪 Le Laboratoire d'Expérimentation & Modes (The Lab)

L'intérêt principal du repository réside dans son **Lab interactif**, un ensemble de protocoles d'exécution avancés.

<div align="center">
  <img src="docs/assets/lab.svg" alt="Laboratoire BicameriS" width="100%" />
</div>

<br/>

### ⚙️ Les Modes d'Expériences Clés :

#### 🧬 01 - Auto-Scaffolding Contrôlé
L'échafaudage de code automatique itératif. Diadikos écrit un bout de script. Palladion l'analyse. S'il est validé, il est exécuté. Les logs d'erreurs d'exécution nourrissent la boucle suivante de Diadikos pour auto-correction.
- **Contrôle** : Limite de profondeur du graphe (Depth-limit) et temps d'exécution maximum.

#### 🛡️ 02 - AST Secure Sandbox
Analyse de l'Arbre Syntaxique Abstrait (AST) avant exécution. Aucune commande système (`rm -rf`, requêtes curl externes non-autorisées) ne peut s'échapper. L'exécution se fait dans une enclave hermétique.

#### ♻️ 03 - Cognitive Rollover (Rotation de Contexte)
Pour surmonter la limite de contexte des LLM locaux, le système effectue un "sliding context". La mémoire de travail est compressée et réinjectée sous forme de résumé sémantique.

#### 💤 04 - Paradoxical Sleep (REM Cycle)
Une tâche de fond qui simule le sommeil paradoxal biologique. Le système nettoie la base de données vectorielle, élimine les redondances de mémoire à court terme et consolide les poids des connexions synaptiques logicielles (RAG pruning).

---

## 📉 Équations, Métriques & Évaluation Objective

BicameriS ne repose pas sur de la pure heuristique ; il s'appuie sur une formalisation mathématique rigoureuse de la fusion des deux modèles LLM locaux.

### 📐 Déviation de Kullback-Leibler (KL Divergence)
Le Corps Calleux évalue la distance entre la distribution de probabilités de Diadikos ($P$) et Palladion ($Q$). Si la divergence dépasse un certain seuil ($\tau$), le cycle est rejeté.

$$D_{KL}(P \parallel Q) = \sum_{x \in X} P(x) \log \left( \frac{P(x)}{Q(x)} \right)$$

### 📊 Tableau de bord des Inférences de Vitesse et VRAM (In-Situ metrics)

<div align="center">

| Modèle Utilisé (Backend local) | Rôle | VRAM Allouée | Tokens/sec | Température |
| :--- | :--- | :--- | :--- | :--- |
| **Llama-3-8B-Instruct** | Diadikos | 6.5 Go | 42.5 | 0.7 |
| **Phi-3-Mini-4k** | Palladion | 2.8 Go | 68.1 | 0.2 |
| **BGE-M3 (Embedding)** | Synapse/RAG | 1.1 Go | N/A | 0.0 |

</div>

---

## 🎛️ Configuration et Toggles (Drapeaux d'exécution)

Chaque option du Lab est modifiable dynamiquement dans le fichier `.env` ou via l'interface CLI :

```bash
# Activation des modules
AUTO_SCAFFOLDING_ENABLED=true
AST_SANDBOX_STRICT=true
COGNITIVE_ROLLOVER_THRESHOLD=0.85
REM_SLEEP_COMPRESSION=true

# Configuration Matérielle
DIADIKOS_GPU_LAYERS=35
PALLADION_GPU_LAYERS=25
```

---

## 🚀 Prise en main rapide et Déploiement

```bash
# Cloner le repository
git clone https://github.com/Yaume29/BicameriS.git
cd BicameriS

# Installer les dépendances
npm install

# Lancer le Lab de test avec l'UI
npm run dev
```

---

<div align="center">
  <p>Projet expérimental issu du laboratoire Hope 'n Mind. Contribuez en ouvrant des Issues sur GitHub et rejoignez notre discussion de recherche pour la sécurité de l'alignement local !</p>
  <img src="https://img.shields.io/badge/Made_With-❤️-0f0055?style=for-the-badge" alt="Made with love" />
  <p><img src="docs/assets/logo.png" alt="Hope 'n Mind Sasu Holding" width="77%" /></p>
</div>
