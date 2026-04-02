# DEVELOPMENT-CONTEXT.md
> Aetheris (BicameriS) — Architecture & Integration Reference

---

## 1. Architecture Overview

### Current Stack
| Layer | Technology | Role |
|-------|------------|------|
| **Backend** | Python 3.10+ / FastAPI / Uvicorn | Cognitive engine, API server, LLM inference |
| **Frontend (current)** | Vanilla JS + Jinja2 templates | Server-rendered UI via `web/templates/index.html` |
| **Frontend (new)** | React + Vite + Tailwind CSS | Modern SPA (to be built separately) |
| **Inference** | llama-cpp-python (GGUF models) | Local LLM execution |
| **Memory** | Qdrant (vector DB) + JSONL telemetry | Persistent memory + logging |
| **Orchestration** | Docker Compose (optional) | Qdrant, Prometheus, Grafana |

### Separation Principle
- **Backend** runs on `localhost:8000` (Python/Uvicorn)
- **Frontend (new)** runs on `localhost:5173` (Vite dev server)
- **No code mixing** — frontend communicates via REST API + WebSocket
- CORS must be enabled in `server/main.py` for cross-origin requests

---

## 2. Current System Components

### 2.1 Corps Calleux (`core/cognition/corps_calleux.py`)
The central orchestrator. Manages dialogue between Left (logic) and Right (intuition) hemispheres.

**9 Autonomous Modes:**
| Mode | Description | Reformulation |
|------|-------------|---------------|
| `metacognition` | Bicameral decision on HOW to think | 0% |
| `relay` | CC → Left + Right → Synthesis | 50% |
| `d_to_g` | Right receives → reformulates → Left responds | 50% |
| `g_to_d` | Left receives → reformulates → Right responds | 50% |
| `mirror` | Both see each other in mirror view | 30% |
| `whisper` | Right → low signal → Left → intuitive response | 80% |
| `agent_mediate` | Agent intermediate reformulates | 50% |
| `multi_agents` | Spawn multiple agents for parallel processing | 0% |
| `internal_dialogue` | Visualizable internal dialogue | 0% |

**Key Methods:**
- `tick(pulse)` — Single thought cycle (called by KernelScheduler)
- `dialogue_interieur()` — Full bicameral dialogue (3 phases)
- `mediter()` — Meditation mode (subconscious exploration)
- `sleep()` — Graceful shutdown with memory save
- `apply_preset()` — Apply hemisphere configuration preset

### 2.2 Hemispheres
| Component | File | Role |
|-----------|------|------|
| **Left Hemisphere** | `core/cognition/left_hemisphere.py` | Logic, analysis, code generation |
| **Right Hemisphere** | `core/cognition/right_hemisphere.py` | Intuition, patterns, creativity |

### 2.3 Agent System (`core/agents/`)
- **AgentFactory** — Creates agents from specs
- **AgentRegistry** — Manages agent instances
- **AgentCoordinator** — Executes agent chains/parallel
- **Specialized Agents** — Coder, Writer, Researcher
- **SuperAgent** — Meta-agent that spawns sub-agents

### 2.4 Cognitive Hooks (`core/cognition/cognitive_hooks.py`)
Priority-ordered event system:
```
Security > Memory > Style > Telemetry
```
- `HookEvent` enum defines event types
- Hooks have matchers (filter) + actions (execute)
- Priority levels: `critical`, `high`, `standard`, `low`

### 2.5 Memory Systems
| System | File | Purpose |
|--------|------|---------|
| **Hippocampus** | `core/system/hippocampus.py` | Qdrant vector store integration |
| **Woven Memory** | `core/system/woven_memory.py` | Persistent knowledge weaving |
| **STM Engine** | `core/cognition/stm_engine.py` | Short-term memory buffer |
| **Traumatic Memory** | `core/system/traumatic_memory.py` | Error/failure memory |
| **Knowledge Base** | `core/system/knowledge_base.py` | Structured knowledge store |

### 2.6 BrainCache (`core/cognition/braincache_integration.py`)
Auto-optimization system that learns from performance metrics.

### 2.7 Lab System (`core/lab/`)
| Module | Purpose |
|--------|---------|
| **Inception** | Thought injection experiments |
| **Editeur Spécialiste** | Code editing with falsification |
| **Induction** | Prompt induction experiments |
| **Autonome** | Autonomous behavior testing |

### 2.8 Server & API (`server/`)
| Route File | Endpoints |
|------------|-----------|
| `api_chat.py` | `/api/chat/*` — Chat, modes, streaming, ToT |
| `api_cognitive.py` | `/api/cognitive/*` — Hooks, cycles, meditation |
| `api_inference.py` | `/api/inference/*` — Model loading, inference |
| `api_system.py` | `/api/system/*` — Stats, config, emergency |
| `api_lab.py` | `/api/lab/*` — Lab module execution |
| `api_hardware.py` | `/api/hardware/*` — GPU, CPU, entropy |
| `api_agents.py` | `/api/agents/*` — Agent management |
| `api_knowledge.py` | `/api/knowledge/*` — Knowledge base |
| `api_dashboard.py` | `/api/dashboard/*` — Dashboard data |
| `api_models.py` | `/api/models/*` — Model scanning |
| `api_skills.py` | `/api/skills/*` — Skill management |

### 2.9 WebSocket
- `/ws/neural` — Real-time neural state updates
- Streams: thinking status, entropy, hemisphere activity

---

## 3. Frontend Integration Plan

### 3.1 New Frontend Stack
- **React 18+** with TypeScript
- **Vite** for build/dev server
- **Tailwind CSS** for styling
- **Zustand** or **Jotai** for state management
- **React Query** for API calls
- **Framer Motion** for animations

### 3.2 Page Structure

#### **Chat Page** (`/`)
- General chat interface with mode selection
- Mode selector dropdown (9 modes)
- Streaming response display
- Chat history with persistence
- Reformulation rate slider per mode

#### **Lab Page** (`/lab`)
- Module cards for each lab:
  - **Inception** — Thought injection interface
  - **Induction** — Prompt induction experiments
  - **Editeur Spécialiste** — Code editor with falsification
  - **Autonome** — Autonomous mode testing
- Execution logs and results viewer

#### **Settings Page** (`/settings`)
- Hemisphere configuration (temperature, top_p, repeat_penalty)
- Preset management (Équilibré, Créatif, Analytique, Rêveur, Turbo)
- Security settings (SAL filter, sandbox, timeouts)
- Model selection and loading

### 3.3 Sidebar Components

#### **Brain SVG Visualization**
- Interactive brain diagram
- Real-time hemisphere activity indicators
- Corpus callosum pulse animation
- Color coding: Left=cyan, Right=purple, Bridge=white

#### **Entropy Monitor**
- Live entropy graph (from `/api/hardware/entropy`)
- Pulse indicator (0.0–1.0 scale)
- Critical threshold alerts

#### **Mode Selector**
- Visual mode cards with icons
- Active mode highlight
- Quick switch between modes

#### **Mood Presets**
- Preset buttons for hemisphere configurations
- Visual indicators for current preset
- Custom preset creation

### 3.4 API Integration Points
```
GET  /api/chat/history          — Load chat history
POST /api/chat/send             — Send message
GET  /api/chat/stream           — SSE stream for responses
GET  /api/chat/modes            — Get all modes
POST /api/chat/mode             — Set active mode
GET  /api/cognitive/hooks       — Get cognitive hooks
POST /api/cognitive/meditate    — Trigger meditation
GET  /api/hardware/entropy      — Real-time entropy
GET  /api/system/stats          — System statistics
WS   /ws/neural                 — WebSocket for live updates
```

---

## 4. Key Features to Implement

### 4.1 Truth Arbiter
- **Corps Calleux as final arbiter** between conflicting memories
- When STM and Woven Memory disagree, CC decides the "truth"
- Implementation: Add `arbitrate_memory_conflict()` method to CorpsCalleux
- Priority: STM (recent) vs Woven (persistent) → CC synthesis

### 4.2 Memory Reconciliation
- **Conflict detection** between STM and Woven Memory
- **Reconciliation strategies:**
  - `recent_wins` — STM overrides Woven for recent data
  - `persistent_wins` — Woven overrides STM for long-term
  - `bicameral` — Both hemispheres evaluate, CC decides
- **Audit log** of all reconciliations

### 4.3 Hook Priorities (Enforced Order)
```
1. Security    — SAL filter, sandbox validation (CRITICAL)
2. Memory      — Hippocampus writes, Woven updates (HIGH)
3. Style       — Response formatting, entity voice (STANDARD)
4. Telemetry   — Logging, metrics, analytics (LOW)
```
- Security hooks MUST execute first and can BLOCK all others
- Memory hooks ensure no thought is lost
- Style hooks are cosmetic (can be skipped under load)

### 4.4 Mood Presets for Hemispheres
| Preset | Left Temp | Right Temp | Description |
|--------|-----------|------------|-------------|
| Équilibré | 0.5 | 0.7 | Balanced reasoning |
| Créatif | 0.3 | 1.2 | High intuition, low logic |
| Analytique | 0.1 | 0.4 | Pure logic, minimal intuition |
| Rêveur | 0.8 | 1.5 | Maximum creativity |
| Turbo | 0.4 | 0.6 | Fast, focused responses |

### 4.5 Mode Selection UI
- Visual mode cards with descriptions
- Real-time mode switching (no page reload)
- Mode-specific chat behavior indicators
- Reformulation rate adjustment per mode

---

## 5. Development Status

### ✅ What's Done
- [x] Core bicameral architecture (Left + Right + Corps Calleux)
- [x] 9 autonomous modes implemented
- [x] Cognitive hooks system with priorities
- [x] Memory systems (Hippocampus, Woven, STM, Traumatic)
- [x] Agent factory and coordination
- [x] Lab modules (Inception, Induction, Editeur, Autonome)
- [x] FastAPI server with all API routes
- [x] WebSocket for real-time updates
- [x] Current vanilla JS frontend (functional)
- [x] Docker Compose for infrastructure
- [x] Launcher with TUI configuration
- [x] Preset system for hemispheres
- [x] Reformulation engine
- [x] Reasoning kernel (MCTS)
- [x] Auto-scaffolding and self-testing

### 🔧 What Needs to Be Done
- [ ] **React frontend** — Build from scratch
  - [ ] Project setup (Vite + React + Tailwind)
  - [ ] API client layer (axios/fetch + React Query)
  - [ ] WebSocket integration
  - [ ] Chat page with mode selector
  - [ ] Lab page with module interfaces
  - [ ] Settings page
  - [ ] Brain SVG visualization component
  - [ ] Entropy graph component
  - [ ] Sidebar with mode/mood selectors
- [ ] **Truth Arbiter** — Implement memory conflict resolution
  - [ ] `arbitrate_memory_conflict()` in CorpsCalleux
  - [ ] Conflict detection between STM and Woven
  - [ ] Reconciliation strategies
  - [ ] Audit logging
- [ ] **CORS configuration** — Enable cross-origin for frontend dev
- [ ] **API documentation** — OpenAPI/Swagger completion
- [ ] **WebSocket events** — Define standard event schema
- [ ] **Authentication** — Add optional auth layer
- [ ] **Testing** — Expand test coverage

### 🚀 Next Steps (Priority Order)
1. **Create React project scaffold** in new directory
2. **Set up API client** with base URL configuration
3. **Build Chat page** — Core functionality first
4. **Integrate WebSocket** — Real-time neural state
5. **Build Sidebar** — Brain SVG, entropy, modes
6. **Implement Truth Arbiter** — Memory reconciliation
7. **Build Lab page** — Module interfaces
8. **Build Settings page** — Hemisphere config
9. **Add CORS middleware** — Enable frontend-backend communication
10. **End-to-end testing** — Full integration validation

---

## 6. File Reference

### Core Cognitive Engine
```
core/
├── cognition/
│   ├── corps_calleux.py          # Central orchestrator (9 modes)
│   ├── left_hemisphere.py        # Logic hemisphere
│   ├── right_hemisphere.py       # Intuition hemisphere
│   ├── cognitive_hooks.py        # Event hook system
│   ├── reasoning_kernel.py       # MCTS reasoning
│   ├── reformulation_engine.py   # Message reformulation
│   ├── stm_engine.py             # Short-term memory
│   ├── braincache_integration.py # Auto-optimization
│   ├── thought_inception.py      # Thought injection
│   ├── conductor.py              # System conductor
│   ├── tot_reasoner.py           # Tree of Thoughts
│   └── autonomous_scaffolding.py # Self-testing
├── agents/
│   ├── agent_factory.py          # Agent creation
│   ├── agent_system.py           # Agent registry/coordinator
│   ├── super_agent.py            # Meta-agent
│   └── specialized/              # Coder, Writer, Researcher
├── system/
│   ├── hippocampus.py            # Qdrant integration
│   ├── woven_memory.py           # Persistent memory
│   ├── traumatic_memory.py       # Error memory
│   ├── knowledge_base.py         # Structured knowledge
│   ├── identity_manager.py       # Entity identity
│   ├── telemetry.py              # Logging/metrics
│   ├── switchboard.py            # System coordination
│   └── emergency_override.py     # Safety system
└── lab/
    ├── modules/
    │   ├── 1_Inception/          # Thought injection
    │   ├── 2_EditeurSpecialiste/ # Code editing
    │   ├── 3_Induction/          # Prompt induction
    │   └── 4_Autonome/           # Autonomous testing
    └── lab_engine.py             # Lab orchestration
```

### Server & API
```
server/
├── main.py                       # FastAPI app, routes, WebSocket
├── extensions.py                 # Shared extensions
├── middlewares.py                 # Request middleware
└── routes/
    ├── api_chat.py               # Chat endpoints
    ├── api_cognitive.py          # Cognitive endpoints
    ├── api_inference.py          # Inference endpoints
    ├── api_system.py             # System endpoints
    ├── api_lab.py                # Lab endpoints
    ├── api_hardware.py           # Hardware endpoints
    ├── api_agents.py             # Agent endpoints
    ├── api_knowledge.py          # Knowledge endpoints
    ├── api_dashboard.py          # Dashboard endpoints
    ├── api_models.py             # Model endpoints
    ├── api_skills.py             # Skill endpoints
    └── views.py                  # HTML views
```

### Current Frontend (Vanilla JS)
```
web/
├── templates/
│   └── index.html                # Main HTML template
└── static/
    ├── css/
    │   ├── chat.css
    │   ├── lab.css
    │   ├── layout.css
    │   └── theme.css
    └── js/
        ├── brain-svg.js          # Brain visualization
        ├── brain-ws.js           # WebSocket client
        ├── chat.js               # Chat logic
        ├── entropy-graph.js      # Entropy display
        ├── lab-app.js            # Lab interface
        ├── settings.js           # Settings management
        ├── sidebar.js            # Sidebar logic
        ├── state.js              # State management
        ├── tabs.js               # Tab navigation
        └── theme-switcher.js     # Theme switching
```

---

## 7. Quick Reference

### Start Backend
```bash
python launcher.py
# or
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Frontend (new, once created)
```bash
cd frontend
npm run dev
# Runs on localhost:5173
```

### API Base URL
```
http://localhost:8000/api
```

### WebSocket Endpoint
```
ws://localhost:8000/ws/neural
```

### Key Environment Variables
```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
MODEL_DIR=./models
SANDBOX_ENABLED=true
SAL_FILTER_ENABLED=true
```

---

*Document generated: 2026-04-02*
*Project: Aetheris (BicameriS) v4.0.0*
*Author: Development Team Reference*
