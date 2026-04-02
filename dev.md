# Document de Développement - Intégration Sherlock OSINT

## Table des Matières

1. [Architecture Générale du Core](#architecture-générale-du-core)
2. [Spécifications Techniques Frontend](#spécifications-techniques-frontend)
3. [Modules Actifs Frontend](#modules-actifs-frontend)
4. [État de Connexion Core-Frontend](#état-de-connexion-core-frontend)
5. [Priorités de Développement](#priorités-de-développement)
6. [Rapport d'Intégration Sherlock OSINT](#rapport-dintégration-sherlock-osint)

---

## 1. Architecture Générale du Core

### 1.1 Structure des Agents

```
core/
├── agents/                    # Gestion des agents
│   ├── specialized/          # Agents spécialisés
│   │   ├── specialist_editor.py    ← Agent principal pour le mode éditeur
│   │   ├── research_agent.py       # Agent de recherche web/sources
│   │   ├── coder_agent.py          # Agent de codage
│   │   ├── writer_agent.py         # Agent d'écriture
│   │   ├── thinking_modes.py        # Modes de pensée (ToT, ReAct, etc.)
│   │   ├── falsification_engine.py # Moteur de falsification
│   │   └── memory_sleep.py          # Gestion veille mémoire
│   ├── web_tools.py          # Outils web (search, fetch, browser)
│   ├── tool_registry.py      # Registre des outils
│   └── tool_permission.py   # Permissions par mode
│
├── cognition/                # Système cognitif bicaméral
│   ├── corps_calleux.py     # Pont entre les deux hemispheres
│   ├── left_hemisphere.py   # Analyse logique
│   ├── right_hemisphere.py  # Intuition créative
│   ├── cognitive_hooks.py   # Hooks cognitifs
│   └── reasoning_kernel.py # Noyau de raisonnement
│
├── lab/                     # Module laboratoire
│   ├── lab_engine.py       # Moteur du lab
│   └── modules/            # Modules du lab (20 modules)
│       └── 2_EditeurSpecialiste/
│           ├── module.py          # Module principal
│           ├── executor.py       # Exécuteur de code
│           ├── workspace.py      # Gestion workspace
│           └── themes.py         # Thèmes spécialisés
│
├── system/                  # Systemes peripheriques
│   ├── web_search.py       # Recherche web
│   ├── knowledge_base.py   # Base de connaissances
│   └── ...
│
└── execution/              # Execution et inference
    ├── inference_manager.py  # Gestionnaire d'inférence LLM
    └── ...
```

### 1.2 SpecialistEditorAgent - Agent Central

**Fichier:** `core/agents/specialized/specialist_editor.py`

```python
class EditorMode(Enum):
    CHAT = "chat"               # Dialogue simple
    RESEARCH = "research"       # Recherche récursive
    CODE = "code"               # Auto-expérimentation
    FALSIFICATION = "falsification"  # Boucle de falsification
```

**Méthodes principales:**
- `activate(mode, capabilities)` - Active l'éditeur dans un mode
- `deactivate()` - Désactive et restaure la mémoire
- `process(input_text, context)` - Traite selon le mode actuel
- `set_mode(mode)` - Change de mode dynamiquement

### 1.3 Web Tools Existants

**Fichier:** `core/agents/web_tools.py`

```python
class WebTools:
    - search: WebSearchTool (SearX, DuckDuckGo)
    - fetch: WebFetchTool (texte, markdown, html)
    - browser: BrowserTool (Playwright)
```

---

## 2. Spécifications Techniques Frontend

### 2.1 Stack Technique

- **Framework:** React 18+ avec Vite
- **Langage:** TypeScript
- **Styling:** Tailwind CSS
- **Build:** Vite avec hot module replacement

### 2.2 Structure des Composants

```
frontend/
├── src/
│   ├── App.tsx                    # Routeur principal (mode switching)
│   ├── main.tsx                   # Point d'entrée
│   ├── index.css                  # Styles globaux
│   └── components/
│       ├── ChatPage.tsx          # Mode Chat bicaméral
│       ├── CodePage.tsx          # Mode Code avec exécut
│       └── ResearchPage.tsx      # Mode Research académique
```

### 2.3 Architecture de Navigation

**App.tsx** - Gestion des modes:
```typescript
type AppMode = 'chat' | 'research' | 'code';

const [mode, setMode] = useState<AppMode>('chat');

const renderPage = () => {
  switch (mode) {
    case 'chat': return <ChatPage />;
    case 'research': return <ResearchPage />;
    case 'code': return <CodePage />;
  }
};
```

### 2.4 Design System

- **Sidebar:** 64px width, icônes emoji
- **Colors:**
  - Chat: Cyan/Purple (bicaméral)
  - Research: Purple/Pink (académique)
  - Code: Green/Yellow (développement)
- **Typography:** Tailwind utilities, text-xs/sm
- **Messages:** Rounded cards avec roles (user, assistant-left, assistant-right, corpus)

---

## 3. Modules Actifs Frontend

### 3.1 ChatPage - Mode Bicaméral

**Fonctionnalités:**
- Messages avec roles multiples (user, assistant-left, assistant-right, corpus, system)
- Indicateurs de frappe par hemisphere
- Envoi de messages avec Enter
- Auto-scroll vers le bas

**Structure de données:**
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system';
  content: string;
  timestamp: Date;
}
```

** État actuel:** Simulation (pas de connexion API réelle)

### 3.2 CodePage - Mode Développement

**Fonctionnalités:**
- Panneau gauche: Liste des fichiers générés
- Panneau central: Chat + input
- Panneau droit: Hooks & Quality metrics
- Sélecteur de Thinking Mode (critic_refine, plan_execute, react, reflexion, tot)
- Exécution de code (simulée)

**Panneau Droite - Hooks:**
- Security Audit (priorité haute)
- Memory Reconcile (priorité moyenne)
- Style Check (priorité basse)
- Telemetry

**Panneau Droite - Quality Metrics:**
- Couverture de tests
- Documentation
- Standards

**État actuel:** Simulation (pas de connexion API réelle)

### 3.3 ResearchPage - Mode Recherche

**Fonctionnalités:**
- Panneau gauche: Sources + Template + Thinking Mode
- Panneau central: Chat + input
- Panneau droit: Logs de recherche
- Templates: academic, research, analysis, report
- Thinking Modes: plan_execute, react, reflexion, tot, critic_refine

**Structure:**
- Sources (arXiv, Semantic Scholar, Web)
- Logs de recherche avec status

**État actuel:** Simulation (pas de connexion API réelle)

---

## 4. État de Connexion Core-Frontend

### 4.1 Ce Qui Est Connecté

| Composant | Frontend | Backend | Status |
|-----------|----------|---------|--------|
| SpecialistEditorAgent | ❌ | ✅ | API existante mais non utilisée |
| EditorMode switching | ❌ | ✅ | API existante |
| WebSearch (SearX/DuckDuckGo) | ❌ | ✅ | Développé mais non intégré |
| Thinking Modes (ToT, ReAct) | ❌ | ✅ | Développé mais non intégré |
| Lab Module (EditeurSpecialiste) | ❌ | ✅ | API complète existante |

### 4.2 Ce Qui N'Est Pas Connecté

1. **API Specialist Editor** → Non utilisée par le frontend React
   - `POST /specialist/activate`
   - `POST /specialist/deactivate`
   - `POST /specialist/process`
   - `POST /specialist/mode`
   - `GET /specialist/status`

2. **Web Tools** → Non exposés au frontend
   - Recherche username (Sherlock) non implémentée
   - Fetch web non utilisé

3. **Cognitive Hooks** → Non visualisés
   - Memory reconciliation
   - Security audit
   - Style check

4. **Code Execution** → Non fonctionnel
   - Workspace manager non connecté
   - Code executor non exposé

### 4.3 API Routes Existantes (Non Connectées)

```
server/routes/
├── api_specialist_editor.py   # 8 endpoints
├── api_research.py            # Recherche
├── api_chat.py                # Chat bicaméral
├── api_lab.py                  # Lab module
├── api_skills.py              # Skills bicaméraux
└── api_agents.py               # Gestion agents
```

---

## 5. Priorités de Développement

### 5.1 Priorité HAUTE (Phase 1)

1. **Connecter le React Frontend au Backend**
   - Créer une couche API client (fetch/axios)
   - Mapper les pages React aux endpoints existants
   - Gérer les états de chargement

2. **Intégrer Sherlock OSINT**
   - Créer l'agent OSINT
   - L'intégrer comme mode dans SpecialistEditor
   - Créer la page OsintPage

3. **Implémenter la Exécution Réelle de Code**
   - Connecter CodePage au CodeExecutor du lab
   - Gérer le workspace

### 5.2 Priorité MOYENNE (Phase 2)

1. **Dashboard Métriques**
   - Visualiser les cognitive hooks
   - Afficher les quality metrics réels

2. **Research Mode Réel**
   - Connecter à ResearchAgent
   - Implémenter la recherche web réelle

3. **Gestion des Sessions**
   - Sauvegarder l'historique
   - Reprendre les conversations

### 5.3 Priorité BASSE (Phase 3)

1. **Thèmes et Personnalisation**
2. **Mode Hors-ligne**
3. **Export/Import de projets**

---

## 6. Rapport d'Intégration Sherlock OSINT

### 6.1 Présentation de Sherlock

**Sherlock** est un outil OSINT (Open Source Intelligence) qui permet de rechercher un username sur plus de **400 réseaux sociaux** simultanément.

**Caractéristiques:**
- 77,200+ stars GitHub
- 9,100+ forks
- CLI et API disponibles
- Recherche par username sur plusieurs plateformes
- Export JSON, CSV, XLSX
- Support Proxy/Tor

### 6.2 Cas d'Usage dans BicameriS

L'intégration de Sherlock comme outil OSINT permettrait:

1. **Mode OSINT dans l'Éditeur Spécialiste**
   - Recherche d'informations sur une personne par son username
   - Investigation de sécurité
   - Reconnaissance passive

2. **Intégration au Chat Bicaméral**
   - L'hémisphère gauche analyse les résultats
   - L'hémisphère droit propose des angles d'investigation

3. **Rapports OSINT**
   - Génération de rapports structurés
   - Export des résultats

### 6.3 Architecture d'Intégration Proposed

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ChatPage  │ │Research  │ │ CodePage │ │OsintPage │  │
│  │          │ │  Page    │ │          │ │ (NEW)    │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │         │
│       └────────────┴─────┬──────┴────────────┘         │
│                          │                              │
│                    App.tsx                              │
│              (mode switching)                           │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │          api_specialist_editor.py                  │  │
│  │   - activate, deactivate, process, set_mode       │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                                │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │        SpecialistEditorAgent                     │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  EditorMode Enum                            │  │  │
│  │  │  - CHAT, RESEARCH, CODE, FALSIFICATION      │  │  │
│  │  │  - OSINT (NOUVEAU)                          │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────┬───────────────────────────┘  │
│                         │                                │
│              ┌──────────┴──────────┐                     │
│              │                     │                     │
│              ▼                     ▼                     │
│  ┌──────────────────┐    ┌──────────────────┐         │
│  │ WebTools existant│    │ Sherlock OSINT   │         │
│  │ (search/fetch)   │    │ (NEW - adapter)  │         │
│  └──────────────────┘    └──────────────────┘         │
└──────────────────────────────────────────────────────────┘
```

### 6.4 Implémentation Détallée

#### 6.4.1 Création de l'Agent OSINT

**Fichier:** `core/agents/specialized/osint_agent.py`

```python
"""
OSINT Agent
==========
Agent de recherche d'informations open source.
Intègre les capacités de Sherlock pour la recherche de usernames.
"""

import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess

logger = logging.getLogger("agents.osint")

@dataclass
class OsintResult:
    username: str
    site: str
    url: str
    status: str  # found, not_found, error
    response_time: float

class OsintAgent:
    """
    Agent OSINT pour la recherche de usernames.
    Utilise Sherlock comme backend de recherche.
    """
    
    def __init__(self, sherlock_path: str = None):
        self.sherlock_path = sherlock_path or "sherlock"
        self.results: List[OsintResult] = []
        self._session_history: List[Dict] = []
        
        # Charger la liste des sites supportés
        self._supported_sites = self._load_sites_list()
    
    def _load_sites_list(self) -> List[str]:
        """Charge la liste des sites supportés par Sherlock"""
        # Retourner les sites principaux
        return [
            "twitter.com",
            "instagram.com",
            "facebook.com",
            "github.com",
            "reddit.com",
            "youtube.com",
            "tiktok.com",
            "linkedin.com",
            "pinterest.com",
            "snapchat.com",
            # ... (400+ sites)
        ]
    
    async def search_username(self, username: str, sites: List[str] = None) -> Dict:
        """
        Recherche un username sur les réseaux sociaux.
        
        Args:
            username: Le username à rechercher
            sites: Liste optionnelle de sites spécifiques
        
        Returns:
            Dict avec les résultats de recherche
        """
        if not username:
            return {"status": "error", "message": "Username requis"}
        
        target_sites = sites or self._supported_sites[:50]  # Limiter par défaut
        
        results = {
            "username": username,
            "searched_sites": len(target_sites),
            "found": [],
            "not_found": [],
            "errors": []
        }
        
        # Exécuter Sherlock
        try:
            cmd = [
                "python", "-m", "sherlock",
                username,
                "--json",
                "--timeout", "60"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                data = json.loads(stdout.decode())
                
                for site, info in data.items():
                    if info.get("status") == "claimed":
                        results["found"].append({
                            "site": site,
                            "url": info.get("url", ""),
                            "status": "found"
                        })
                    else:
                        results["not_found"].append({
                            "site": site,
                            "status": "not_found"
                        })
            else:
                results["errors"].append(stderr.decode())
                
        except FileNotFoundError:
            # Sherlock non installé, utiliser approche alternative
            return await self._search_alternative(username, target_sites)
        except Exception as e:
            logger.error(f"[OsintAgent] Search error: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def _search_alternative(self, username: str, sites: List[str]) -> Dict:
        """
        Approche alternative si Sherlock n'est pas disponible.
        Utilise les web tools existants.
        """
        from ..web_tools import get_web_tools
        
        web_tools = get_web_tools()
        
        results = {
            "username": username,
            "searched_sites": len(sites),
            "found": [],
            "not_found": [],
            "errors": [],
            "method": "web_tools"
        }
        
        for site in sites[:20]:  # Limiter pour éviter timeout
            query = f"site:{site} {username}"
            
            try:
                search_results = await web_tools.search.search(query, num_results=3)
                
                for r in search_results:
                    if username.lower() in r.url.lower():
                        results["found"].append({
                            "site": site,
                            "url": r.url,
                            "title": r.title,
                            "status": "found"
                        })
            except Exception as e:
                results["errors"].append(f"{site}: {e}")
        
        return results
    
    def get_status(self) -> Dict:
        """Retourne le statut de l'agent OSINT"""
        return {
            "supported_sites": len(self._supported_sites),
            "total_searches": len(self._session_history),
            "last_search": self._session_history[-1] if self._session_history else None
        }


# Instance globale
_osint_agent: Optional[OsintAgent] = None

def get_osint_agent() -> OsintAgent:
    """Récupère l'instance globale de l'agent OSINT"""
    global _osint_agent
    if _osint_agent is None:
        _osint_agent = OsintAgent()
    return _osint_agent
```

#### 6.4.2 Extension du SpecialistEditorAgent

**Modification:** `core/agents/specialized/specialist_editor.py`

```python
class EditorMode(Enum):
    CHAT = "chat"
    RESEARCH = "research"
    CODE = "code"
    FALSIFICATION = "falsification"
    OSINT = "osint"  # NOUVEAU MODE
```

```python
def _process_osint(self, input_text: str, context: Dict) -> Dict:
    """Mode OSINT - Recherche de username"""
    osint_agent = self._get_osint_agent()
    
    username = context.get("username", input_text)
    sites = context.get("sites", None)
    
    result = await osint_agent.search_username(username, sites)
    
    return {
        "status": "ok",
        "mode": "osint",
        "result": result
    }
```

#### 6.4.3 Création de la Page OsintPage

**Fichier:** `frontend/src/components/OsintPage.tsx`

```typescript
import { useState, useRef, useEffect } from 'react';

interface OsintResult {
  site: string;
  url: string;
  status: 'found' | 'not_found' | 'error';
}

interface OsintMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'osint';
  content: string;
  timestamp: Date;
  results?: OsintResult[];
}

export default function OsintPage() {
  const [messages, setMessages] = useState<OsintMessage[]>([
    {
      id: '1',
      role: 'system',
      content: 'Mode OSINT activé. Entrez un username pour rechercher sa présence sur les réseaux sociaux.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const searchUsername = async () => {
    if (!input.trim()) return;

    const username = input.trim();
    const userMsg: OsintMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: `Rechercher le username: ${username}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsSearching(true);

    try {
      const response = await fetch('/api/specialist/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: username,
          context: { mode: 'osint' }
        })
      });

      const data = await response.json();
      
      const resultsMsg: OsintMessage = {
        id: `result-${Date.now()}`,
        role: 'osint',
        content: `Résultats pour "${username}":\n\n` +
          `Trouvés: ${data.result?.found?.length || 0}\n` +
          `Non trouvés: ${data.result?.not_found?.length || 0}`,
        timestamp: new Date(),
        results: data.result?.found || []
      };
      setMessages((prev) => [...prev, resultsMsg]);

    } catch (error) {
      const errorMsg: OsintMessage = {
        id: `error-${Date.now()}`,
        role: 'system',
        content: `Erreur lors de la recherche: ${error}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSearching(false);
    }
  };

  const getRoleStyle = (role: string) => {
    switch (role) {
      case 'user':
        return { bg: 'bg-blue-500/15', border: 'border-blue-500/20', align: 'justify-end', label: 'Vous', labelColor: 'text-blue-400' };
      case 'assistant':
        return { bg: 'bg-cyan-500/10', border: 'border-cyan-500/15', align: 'justify-start', label: 'Assistant', labelColor: 'text-cyan-400' };
      case 'osint':
        return { bg: 'bg-red-500/10', border: 'border-red-500/15', align: 'justify-start', label: 'OSINT', labelColor: 'text-red-400' };
      case 'system':
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-center', label: 'Système', labelColor: 'text-gray-400' };
      default:
        return { bg: 'bg-gray-500/10', border: 'border-gray-500/15', align: 'justify-start', label: '', labelColor: 'text-gray-400' };
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Panel - Sites */}
      <div className="w-64 bg-gray-800/50 border-r border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">🎯 Targets</h3>
        <div className="space-y-2 text-[10px] text-gray-400">
          <div className="p-2 rounded bg-gray-700/50">Twitter</div>
          <div className="p-2 rounded bg-gray-700/50">Instagram</div>
          <div className="p-2 rounded bg-gray-700/50">GitHub</div>
          <div className="p-2 rounded bg-gray-700/50">Facebook</div>
          <div className="p-2 rounded bg-gray-700/50">Reddit</div>
          <div className="p-2 rounded bg-gray-700/50 text-gray-500">+ 395 autres...</div>
        </div>
      </div>

      {/* Center - Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800/80">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-500/30 to-orange-500/30 border border-gray-600 flex items-center justify-center">
              <span className="text-lg">🕵️</span>
            </div>
            <div>
              <div className="text-sm font-semibold">OSINT Mode</div>
              <div className="text-[10px] text-gray-500">Recherche de usernames</div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((msg) => {
            const style = getRoleStyle(msg.role);
            return (
              <div key={msg.id} className={`flex ${style.align}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${style.bg} ${style.border} border shadow-sm`}>
                  <div className={`text-[9px] font-semibold mb-1 ${style.labelColor}`}>{style.label}</div>
                  <div className="text-xs text-gray-200 leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                  {msg.results && msg.results.length > 0 && (
                    <div className="mt-3 p-2 rounded bg-gray-800/50">
                      <div className="text-[9px] text-gray-400 mb-1">Résultats trouvés:</div>
                      {msg.results.map((r, i) => (
                        <a key={i} href={r.url} target="_blank" rel="noopener" className="block text-[9px] text-red-400 hover:underline">
                          {r.site}: {r.url}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isSearching && (
            <div className="flex items-center gap-2">
              <div className="px-4 py-2 rounded-2xl bg-gray-800 border border-gray-700">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
              <span className="text-[9px] text-gray-500">Recherche en cours...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-700 bg-gray-800/80 p-3">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  searchUsername();
                }
              }}
              placeholder="Entrez un username à rechercher..."
              rows={1}
              className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-red-500/40 resize-none"
            />
            <button
              onClick={searchUsername}
              disabled={!input.trim() || isSearching}
              className="p-2.5 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 text-white border border-red-500/30 hover:from-red-500/30 hover:to-orange-500/30 transition-all disabled:opacity-50"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" fill="none" />
                <path d="M9 6V9M9 12H9.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - History */}
      <div className="w-64 bg-gray-800/50 border-l border-gray-700 p-4 overflow-y-auto">
        <h3 className="text-xs font-semibold text-gray-300 mb-4">📜 Historique</h3>
        <div className="space-y-2">
          <div className="p-2 rounded-lg bg-gray-700/50 border border-gray-600">
            <div className="text-[9px] text-gray-400">Derniere recherche: maintenant</div>
            <div className="text-[9px] text-gray-500 mt-1">Statut: {isSearching ? 'En cours' : 'Terminé'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### 6.4.4 Mise à Jour du App.tsx

```typescript
import { useState } from 'react';
import ChatPage from './components/ChatPage';
import ResearchPage from './components/ResearchPage';
import CodePage from './components/CodePage';
import OsintPage from './components/OsintPage';  // NOUVEAU

type AppMode = 'chat' | 'research' | 'code' | 'osint';  // AJOUTER osint

export default function App() {
  const [mode, setMode] = useState<AppMode>('chat');

  const renderPage = () => {
    switch (mode) {
      case 'chat':
        return <ChatPage />;
      case 'research':
        return <ResearchPage />;
      case 'code':
        return <CodePage />;
      case 'osint':
        return <OsintPage />;  // NOUVEAU
      default:
        return <ChatPage />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-gray-900 text-white overflow-hidden">
      {/* Mode Selector */}
      <div className="flex flex-col w-16 bg-gray-800 border-r border-gray-700">
        {/* ... boutons existants ... */}
        
        {/* NOUVEAU BOUTON OSINT */}
        <button
          onClick={() => setMode('osint')}
          className={`flex-1 flex items-center justify-center text-2xl transition-all ${
            mode === 'osint'
              ? 'bg-red-600 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-white'
          }`}
          title="OSINT"
        >
          🕵️
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderPage()}
      </div>
    </div>
  );
}
```

#### 6.4.5 Ajout de l'API Endpoint

**Fichier:** `server/routes/api_specialist_editor.py` (déjà existant, ajouter endpoint OSINT)

```python
@router.post("/osint/search")
async def osint_search(request: Request):
    """Recherche un username via OSINT"""
    try:
        data = await request.json()
        username = data.get("username", "")
        sites = data.get("sites", None)
        
        from core.agents.specialized.osint_agent import get_osint_agent
        agent = get_osint_agent()
        
        result = await agent.search_username(username, sites)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/osint/status")
async def osint_status():
    """Retourne le statut de l'agent OSINT"""
    from core.agents.specialized.osint_agent import get_osint_agent
    agent = get_osint_agent()
    return agent.get_status()
```

### 6.5 Dépendances Requises

```bash
# Requirements.txt
sherlock-project  # Ou installation via pip
aiohttp            # Pour les requêtes async
playwright         # Pour browser automation (optionnel)
```

### 6.6 Considérations de Sécurité

1. **Rate Limiting**
   - Limiter les requêtes pour éviter le blocage
   - Implémenter un délai entre chaque site

2. **Proxy/Tor**
   - Offrir l'option d'utiliser Tor pour anonymiser les requêtes
   - Configurable via paramètres

3. **Stockage des Résultats**
   - Les résultats peuvent être sensibles
   - Chiffrer les données stockées
   - Option de suppression

4. **Licence et Usage**
   - Sherlock utilise la licence MIT
   - Respecter les Terms of Service des plateformes ciblées
   - Usage仅限于研究和安全测试

### 6.7 Résumé de l'Intégration

| Composant | Fichier | Action |
|-----------|---------|--------|
| Agent OSINT | `core/agents/specialized/osint_agent.py` | CRÉER |
| SpecialistEditor | `core/agents/specialized/specialist_editor.py` | MODIFIER (ajouter OSINT mode) |
| API Routes | `server/routes/api_specialist_editor.py` | MODIFIER (ajouter endpoints) |
| OsintPage | `frontend/src/components/OsintPage.tsx` | CRÉER |
| App.tsx | `frontend/src/App.tsx` | MODIFIER (ajouter mode + bouton) |

### 6.8 Phases d'Implémentation Recommandées

**Phase 1 (Immédiate):**
1. Créer `osint_agent.py` minimal
2. Ajouter le mode OSINT à SpecialistEditor
3. Créer OsintPage avec UI de base
4. Connecter au backend (simulation)

**Phase 2 (Court terme):**
1. Implémenter la recherche Sherlock réelle
2. Ajouter la gestion des erreurs
3. Implémenter le rate limiting
4. Ajouter les exports (JSON, CSV)

**Phase 3 (Medium terme):**
1. Ajouter support Proxy/Tor
2. Implémenter la recherche récursive
3. Ajouter la génération de rapports
4. Intégrer au système bicaméral (analyse + intuition)

---

## Annexe: Chemins des Fichiers Clés

```
quick-moon/
├── core/
│   └── agents/
│       └── specialized/
│           ├── specialist_editor.py    # Agent principal
│           ├── osint_agent.py          # [À CRÉER]
│           ├── research_agent.py       # Agent de recherche
│           └── web_tools.py            # Outils web
├── server/
│   └── routes/
│       └── api_specialist_editor.py    # Endpoints API
├── frontend/
│   └── src/
│       ├── App.tsx                     # [À MODIFIER]
│       └── components/
│           ├── ChatPage.tsx
│           ├── CodePage.tsx
│           ├── ResearchPage.tsx
│           └── OsintPage.tsx           # [À CRÉER]
└── dev.md                              # Ce document
```

---

*Document généré le 3 Avril 2026*
*Projet: BicameriS - Système d'IA Bicaméral*
