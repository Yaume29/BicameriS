<div align="center">

# BICAMERIS v6.0

**Cognitive Bicameral Kernel - Where Logic Meets Intuition**

![Version](https://img.shields.io/badge/version-6.0.0-blue?style=for-the-badge)
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

**Bicameris** is an autonomous cognitive architecture featuring a dual-hemisphere brain
powered by local LLM inference. It arbitrates between logic (Qwen) and intuition (Gemma)
using hardware entropy as a dynamic cognitive driver.

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
|                    BICAMERIS v6.0 KERNEL                      |
+---------------------------------------------------------------+
|                                                               |
|  +------------+    +------------+    +------------+          |
|  | LEFT HEM.  |    |  CORPS     |    | RIGHT HEM. |          |
|  | (Qwen 14B) |<-->|  CALLEUX   |<-->| (Gemma 9B) |          |
|  | Logic      |    |  (Bridge)  |    | Intuition  |          |
|  +-----+------+    +-----+------+    +-----+------+          |
|        |                 |                 |                  |
|        |    +------------+------------+    |                  |
|        |    |        CONDUCTOR        |    |                  |
|        |    |      (Arbitrage)        |    |                  |
|        |    +------------+------------+    |                  |
|        |                 |                 |                  |
+--------|-----------------|-----------------|------------------+
         |                 |                 |
+--------v-----------------v-----------------v------------------+
|                    TRANSIENT REQ > ROUTER                    |
+---------------------------------------------------------------+
|  +------------+  +------------+  +------------+             |
|  | Worker Qwen|  | Worker     |  | Worker     |             |
|  | ROUTER     |  | Gemma      |  | Future     |             |
|  | BIND       |  | ROUTER     |  | ROUTER     |             |
|  +------------+  +------------+  +------------+             |
+---------------------------------------------------------------+
```

### IPC Architecture (v6.0)

```
+-------------------+         ipc://          +------------------+
| InferenceManager  | ---- TRANSIENT REQ ---> | Worker Process   |
| (FastAPI Thread)  |                         | (LLM Inference)  |
|                   | <--- [reply] ---------- |                  |
|  socket = ctx.    |                         | ROUTER BIND      |
|    socket(REQ)    |                         | [id, msg] ->     |
|  connect()        |                         | process_task()   |
|  send(task)       |                         | send([id,reply]) |
|  recv()           |                         |                  |
|  close()          |                         |                  |
+-------------------+                         +------------------+

Benefits vs PAIR persistent:
- Zero race conditions (stateless client)
- Crash-resilient (fresh socket per request)
- No lock contention
- Automatic reconnection
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

### Triple-Layer Sandbox

| Layer | Technology | Protection |
|-------|------------|------------|
| Layer 1 | AST Validation | Blocks dangerous imports |
| Layer 2 | Docker Isolation | Network-disabled containers |
| Layer 3 | PEP 578 Audit Hooks | Runtime monitoring |

### Features

- Airgap Mode for sensitive operations
- Auto-scaffolding with dependency verification
- Trauma filter against injection attacks
- SAL classifier for sensitive content
- Switchboard controls for all features

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

### WebSocket

| Endpoint | Type | Description |
|----------|------|-------------|
| /ws/neural | PUSH | Neural state updates |
| /ws/thermal | PUSH | Thermal monitoring |

---

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/network)

Made with love by the Bicameris Team

</div>
