<div align="center">

# BICAMERIS v4.0

**Cognitive Bicameral Kernel - Where Logic Meets Intuition**

![Version](https://img.shields.io/badge/version-4.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.11+-green?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)

[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-red)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Sandbox-blue)](https://docker.com)
[![ZMQ](https://img.shields.io/badge/ZMQ-IPC-orange)](https://zeromq.org)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-e6522c)](https://prometheus.io)

---

[![Overview](https://img.shields.io/badge/Overview-4CAF50?style=flat-square)](#overview)
[![Architecture](https://img.shields.io/badge/Architecture-2196F3?style=flat-square)](#architecture)
[![Installation](https://img.shields.io/badge/Installation-FF9800?style=flat-square)](#installation)
[![Security](https://img.shields.io/badge/Security-F44336?style=flat-square)](#security)
[![API](https://img.shields.io/badge/API-9C27B0?style=flat-square)](#api)
[![Monitoring](https://img.shields.io/badge/Monitoring-00BCD4?style=flat-square)](#monitoring)

</div>

---

<a id="overview"></a>
## Overview

**Bicameris** is a cognitive bicameral kernel that simulates a dual-hemisphere AI brain.

### Key Concepts

| Concept | Description |
|---------|-------------|
| Bicameral Brain | Two AI hemispheres - Left (logic), Right (intuition) |
| Hardware Entropy Pulse | Real CPU/RAM/GPU stress readings influence cognitive state |
| Endocrine System | Virtual hormones modulate LLM parameters |
| Master Clock | Single pacemaker orchestrating all cognitive ticks |
| Triple-Layer Sandbox | AST + Docker + PEP 578 Audit Hooks |
| Dual Memory | Qdrant (vector) + Kuzu graph (causal) |
| Dreamer Agent | REM sleep cycles consolidate memory |
| Sensory Buffer | External data injection prevents cognitive collapse |

---

<a id="architecture"></a>
## Architecture

### Component Details

| Module | Purpose | Thread Safety |
|--------|---------|---------------|
| **Conductor** | Arbitration kernel; decides hemisphere leader | Thread-safe |
| **Corps Calleux** | Bridge between hemispheres | Thread-safe |
| **KernelScheduler** | Master Clock; pacemaker for all ticks | Async-safe |
| **InferenceManager** | ZMQ IPC for Llama.cpp workers | Mutex-protected |
| **Telemetry** | Async JSONL logger with Ring Buffer | Thread-safe |
| **Hippocampus** | Qdrant vector memory | Async-safe |
| **Sandbox** | Docker containers with security | Isolated |
| **Switchboard** | Thread-safe state manager | Atomic |

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
| **Layer 1** | AST Validation | Blocks dangerous imports |
| **Layer 2** | Docker Isolation | Network-disabled containers |
| **Layer 3** | PEP 578 Audit Hooks | Runtime monitoring |

---

<a id="api"></a>
## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conductor/stats` | GET | Conductor statistics |
| `/api/cognitive/tick` | POST | Manual cognitive tick |
| `/api/cognitive/think` | POST | Submit thinking task |
| `/api/hardware/thermal` | GET | Hardware thermal status |
| `/api/system/switches` | GET | List lab switches |
| `/api/inference/spawn` | POST | Spawn LLM incarnation |

---

<a id="monitoring"></a>
## Monitoring

| Endpoint | Type | Description |
|----------|------|-------------|
| `/ws/neural` | PUSH | Real-time neural state |
| `/ws/thermal` | PUSH | Hardware monitoring |

---

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/Yaume29/BicameriS?style=social)](https://github.com/Yaume29/BicameriS/stargazers)

**Made with love by the Bicameris Team**

</div>
