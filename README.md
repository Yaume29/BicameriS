<div align="center">

# BicameriS

**Diadikos & Palladion**

*By Hope 'n Mind*

![Version](https://img.shields.io/badge/version-1.0.0.6a-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11+-green?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Sandbox-blue)](https://docker.com)
[![ZMQ](https://img.shields.io/badge/ZMQ-Transient_REQ-ff6600)](https://zeromq.org)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-e6522c)](https://prometheus.io)

---

[![Overview](https://img.shields.io/badge/Overview-4CAF50?style=flat-square)](#overview)
[![Architecture](https://img.shields.io/badge/Architecture-2196F3?style=flat-square)](#architecture)
[![Installation](https://img.shields.io/badge/Installation-FF9800?style=flat-square)](#installation)
[![Security](https://img.shields.io/badge/Security-F44336?style=flat-square)](#security)
[![API](https://img.shields.io/badge/API-9C27B0?style=flat-square)](#api)

</div>

---

<a id="overview"></a>
## Overview

**BicameriS** is not a conventional AI project. It is **systemic research** -- a cognitive
laboratory that simulates the architecture of consciousness itself.

The name draws from Greek antiquity:

| Term | Origin | Meaning |
|------|--------|---------|
| **Diadikos** | Διαδικός (dia + dikē) | The dialogue through reason -- the process by which two parties converge toward truth |
| **Palladion** | Παλλάδιον | The sacred statue of Athena that protected Troy -- the guardian, the creative boundaries |
| **Bicameris** | Latin *bicamer* | Two chambers -- the dual-hemisphere brain |

**Diadikos** is the hemispheric dialogue: Qwen (logic) and Gemma (intuition) converging
toward synthesis. **Palladion** is the protective system -- the sandbox, the security layers,
the body that gives Diadikos a safe vessel to exist.

*Without Palladion, no Diadikos is possible. Without boundaries, no creative freedom.*

### Key Concepts

| Concept | Description |
|---------|-------------|
| Bicameral Brain | Left hemisphere (Qwen) for logic, Right (Gemma) for intuition |
| Transient REQ | Zero race condition IPC per request |
| Hardware Entropy Pulse | CPU/RAM/GPU stress drives cognitive state |
| Endocrine System | Virtual hormones modulate LLM parameters |
| Master Clock | Single pacemaker for all cognitive ticks |
| Triple-Layer Sandbox | AST + Docker + PEP 578 Audit Hooks |
| Dual Memory | Qdrant vector + Kuzu causal graph |
| Dreamer Agent | REM sleep for memory consolidation |

---

<a id="architecture"></a>
## Architecture

### Brain Topology

```
+---------------------------------------------------------------+
|                  BICAMERIS v1.0.0.6a                          |
|              Diadikos & Palladion                             |
+---------------------------------------------------------------+
|                                                               |
|  +------------+    +------------+    +------------+          |
|  | LEFT HEM.  |    |  CORPS     |    | RIGHT HEM. |          |
|  | (Qwen 14B) |<-->|  CALLEUX   |<-->| (Gemma 9B) |          |
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
+--------v-----------------v-----------------v------------------+
|                  TRANSIENT REQ > ROUTER                      |
+---------------------------------------------------------------+
|  +------------+  +------------+  +------------+             |
|  | Worker Qwen|  | Worker     |  | Worker     |             |
|  | ROUTER     |  | Gemma      |  | Future     |             |
|  | BIND       |  | ROUTER     |  | ROUTER     |             |
|  +------------+  +------------+  +------------+             |
+---------------------------------------------------------------+
|               P A L L A D I O N                               |
|          (Triple-Layer Sandbox Security)                      |
+---------------------------------------------------------------+
```

### Component Details

| Module | Purpose | Thread Safety |
|--------|---------|---------------|
| Conductor | Arbitration kernel | Thread-safe |
| Corps Calleux | Hemisphere bridge | Thread-safe |
| KernelScheduler | Master Clock | Async-safe |
| InferenceManager | Transient REQ IPC | Stateless |
| Telemetry | JSONL logger | Thread-safe |
| Hippocampus | Qdrant vector memory | Async-safe |
| Sandbox | Docker containers | Isolated |
| Switchboard | State manager | Atomic |

---

<a id="installation"></a>
## Installation

### Prerequisites

- Python 3.11+
- Docker Desktop
- Qdrant (Docker)
- 8GB+ RAM recommended

### Quick Start

```bash
git clone https://github.com/Yaume29/BicameriS.git
cd BicameriS
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env.local
docker run -p 6333:6333 qdrant/qdrant
python run.py
```

---

<a id="security"></a>
## Security

### Palladion -- The Guardian

The Palladion system implements three protective layers:

| Layer | Technology | Protection |
|-------|------------|------------|
| Layer 1 | AST Validation | Blocks dangerous imports |
| Layer 2 | Docker Isolation | Network-disabled containers |
| Layer 3 | PEP 578 Audit Hooks | Runtime monitoring |

*Like the sacred statue of Athena, Palladion ensures Diadikos can exist safely.*

---

<a id="api"></a>
## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/conductor/stats | GET | Conductor statistics |
| /api/cognitive/tick | POST | Manual cognitive tick |
| /api/cognitive/think | POST | Submit thinking task |
| /api/hardware/thermal | GET | Thermal status |
| /api/system/switches | GET | List switches |
| /api/inference/spawn | POST | Spawn LLM worker |

---

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/network)

**By Hope 'n Mind**

</div>
