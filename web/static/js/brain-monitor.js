// Brain Monitor Opératif - Diadikos-Palladion
// Real-time neural state visualization with WebSocket + Polling

class BrainMonitor {
    constructor() {
        this.socket = null;
        this.pollingFallback = null;
        this.currentState = {
            left: 'empty',
            right: 'empty',
            thinking: 'none',
            bridge: false,
            agents: [],
            status_text: 'INITIALISATION',
            sub_text: 'AWAITING_INSTRUCTION'
        };
        this.init();
    }

    init() {
        this.createWidget();
        this.connectWebSocket();
        this.startPollingFallback();
    }

    createWidget() {
        const existing = document.querySelector('.brain-monitor-container');
        if (existing) return;

        const widget = document.createElement('div');
        widget.className = 'brain-monitor-container';
        widget.innerHTML = `
            <div class="monitor-frame">
                <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <filter id="glow-green-monitor">
                            <feGaussianBlur stdDeviation="2.5" result="blur"/>
                            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                        </filter>
                        <filter id="glow-cyan-monitor">
                            <feGaussianBlur stdDeviation="3" result="blur"/>
                            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                        </filter>
                    </defs>
                    
                    <circle cx="100" cy="100" r="95" fill="none" stroke="#080808" stroke-width="1" />
                    <circle cx="100" cy="100" r="85" fill="none" stroke="#080808" stroke-width="0.5" stroke-dasharray="2,10" />
                    
                    <circle id="agent-critic" class="agent-node" cx="100" cy="15" r="3" />
                    <circle id="agent-research" class="agent-node" cx="185" cy="100" r="3" />
                    <circle id="agent-coder" class="agent-node" cx="15" cy="100" r="3" />
                    
                    <g id="grp-left">
                        <path id="hem-l" class="hemisphere state-empty" d="M90,40 C70,35 40,45 35,85 C30,125 50,165 80,175 C85,178 90,165 90,145 L90,40" />
                        <path class="neural-lines" d="M45,80 Q60,85 85,75" stroke="currentColor"/>
                        <path class="neural-lines" d="M45,110 Q65,100 85,120" stroke="currentColor"/>
                    </g>
                    
                    <g id="grp-right">
                        <path id="hem-r" class="hemisphere state-empty" d="M110,40 C130,35 160,45 165,85 C170,125 150,165 120,175 C115,178 110,165 110,145 L110,40" />
                        <path class="neural-lines" d="M155,80 Q140,85 115,75" stroke="currentColor"/>
                        <path class="neural-lines" d="M155,110 Q135,100 115,120" stroke="currentColor"/>
                    </g>
                    
                    <g id="bridge-monitor">
                        <line class="bridge-line" x1="94" y1="70" x2="106" y2="70" />
                        <line class="bridge-line" x1="94" y1="100" x2="106" y2="100" />
                        <line class="bridge-line" x1="94" y1="130" x2="106" y2="130" />
                    </g>
                </svg>
                
                <div class="label-container">
                    <div class="log-text" id="ui-meta">KERNEL_METROLOGY_ACTIVE</div>
                    <div class="log-text" id="ui-sub">AWAITING_INSTRUCTION</div>
                    <div class="status-badge" id="status-main">INITIALISATION</div>
                </div>
            </div>
        `;
        
        const header = document.querySelector('header') || document.body;
        header.insertBefore(widget, header.firstChild);
        
        this.injectStyles();
    }

    injectStyles() {
        if (document.getElementById('brain-monitor-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'brain-monitor-styles';
        styles.textContent = `
            .brain-monitor-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
            }
            .monitor-frame {
                position: relative;
                width: 120px;
                height: 120px;
                border: 1px solid #111;
                border-radius: 50%;
                background: #020406;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .monitor-frame svg {
                width: 100%;
                height: 100%;
            }
            .hemisphere {
                fill: rgba(0,0,0,0.6);
                stroke-width: 2;
                transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                stroke-linecap: round;
            }
            .neural-lines {
                fill: none;
                stroke-width: 0.5;
                opacity: 0.15;
            }
            .state-empty { stroke: #441111; filter: drop-shadow(0 0 2px #ff0000); opacity: 0.5; }
            .state-loaded { stroke: #00ff95; filter: url(#glow-green-monitor); opacity: 1; }
            .state-fused { stroke: #00e5ff; filter: url(#glow-cyan-monitor); opacity: 1; }
            .thinking-pulse {
                animation: breathe 1.5s infinite ease-in-out;
                stroke-width: 3 !important;
            }
            @keyframes breathe {
                0%, 100% { opacity: 0.7; stroke-width: 2; }
                50% { opacity: 1; stroke-width: 4; filter: brightness(1.3) drop-shadow(0 0 10px currentColor); }
            }
            .bridge-line {
                stroke: #222;
                stroke-width: 1.5;
                stroke-dasharray: 4,4;
                transition: all 0.5s ease;
            }
            .bridge-active {
                stroke: #00ff95;
                filter: drop-shadow(0 0 5px #00ff95);
                stroke-dasharray: 100;
                stroke-dashoffset: 100;
                animation: bridge-flow 2s infinite linear;
            }
            @keyframes bridge-flow {
                from { stroke-dashoffset: 20; }
                to { stroke-dashoffset: 0; }
            }
            .agent-node {
                fill: #111;
                stroke: #333;
                stroke-width: 1;
                transition: all 0.3s;
            }
            .agent-active {
                fill: #00ff95;
                stroke: white;
                filter: drop-shadow(0 0 5px #00ff95);
            }
            .label-container {
                position: absolute;
                bottom: -25px;
                text-align: center;
                width: 100%;
                font-family: 'Orbitron', monospace;
            }
            .log-text {
                font-size: 7px;
                color: #444;
                letter-spacing: 1px;
                margin: 1px 0;
            }
            .status-badge {
                font-size: 8px;
                padding: 2px 6px;
                border: 1px solid #222;
                display: inline-block;
                margin-top: 3px;
                color: #666;
            }
        `;
        document.head.appendChild(styles);
    }

    connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/neural`;
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('[BrainMonitor] WebSocket connected');
                this.stopPollingFallback();
            };
            
            this.socket.onclose = () => {
                console.log('[BrainMonitor] WebSocket disconnected, using polling');
                this.startPollingFallback();
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.updateMonitor(data);
                } catch (e) {
                    console.log('[BrainMonitor] Parse error:', e);
                }
            };
            
        } catch (e) {
            console.log('[BrainMonitor] WebSocket error:', e);
        }
    }

    startPollingFallback() {
        if (this.pollingFallback) return;
        this.pollingFallback = setInterval(() => this.pollStatus(), 3000);
    }

    stopPollingFallback() {
        if (this.pollingFallback) {
            clearInterval(this.pollingFallback);
            this.pollingFallback = null;
        }
    }

    async pollStatus() {
        try {
            const response = await fetch('/api/models/status');
            const data = await response.json();
            
            const state = {
                left: data.left?.loaded ? 'loaded' : 'empty',
                right: data.right?.loaded ? 'loaded' : 'empty',
                thinking: 'none',
                bridge: false,
                agents: [],
                status_text: data.is_split_mode ? 'BICAMERAL_MODE' : 'STANDBY',
                sub_text: data.is_split_mode ? 'DUAL_MODEL_ACTIVE' : 'SYSTEM_READY'
            };
            
            if (data.is_split_mode) {
                state.left = 'loaded';
                state.right = 'loaded';
                state.bridge = true;
            }
            
            this.updateMonitor(state);
        } catch (e) {
            // Silently fail
        }
    }

    updateMonitor(data) {
        this.currentState = data;
        
        const hL = document.getElementById('hem-l');
        const hR = document.getElementById('hem-r');
        const bridgeLines = document.getElementById('bridge-monitor')?.querySelectorAll('line') || [];
        const statusMain = document.getElementById('status-main');
        const uiSub = document.getElementById('ui-sub');

        if (!hL || !hR) return;

        // Remove thinking pulses first
        hL.classList.remove('thinking-pulse');
        hR.classList.remove('thinking-pulse');

        // 1. Gestion des Hémisphères
        hL.className = 'hemisphere ' + (data.left === 'loaded' ? 'state-loaded' : (data.left === 'fused' ? 'state-fused' : 'state-empty'));
        hR.className = 'hemisphere ' + (data.right === 'loaded' ? 'state-loaded' : (data.right === 'fused' ? 'state-fused' : 'state-empty'));

        // 2. Gestion de la pensée (Pulsation indépendante)
        if (data.thinking === 'left') hL.classList.add('thinking-pulse');
        if (data.thinking === 'right') hR.classList.add('thinking-pulse');
        if (data.thinking === 'both') { hL.classList.add('thinking-pulse'); hR.classList.add('thinking-pulse'); }

        // 3. Gestion du Pont
        bridgeLines.forEach(l => {
            if (data.bridge) {
                l.classList.add('bridge-active');
                l.style.stroke = (data.left === 'fused') ? '#00e5ff' : '#00ff95';
            } else {
                l.classList.remove('bridge-active');
                l.style.stroke = '#222';
            }
        });

        // 4. Gestion des Agents
        const agents = data.agents || [];
        const critic = document.getElementById('agent-critic');
        const research = document.getElementById('agent-research');
        const coder = document.getElementById('agent-coder');
        
        if (critic) critic.className = 'agent-node' + (agents.includes('critic') ? ' agent-active' : '');
        if (research) research.className = 'agent-node' + (agents.includes('research') ? ' agent-active' : '');
        if (coder) coder.className = 'agent-node' + (agents.includes('coder') ? ' agent-active' : '');

        // 5. Labels UI
        if (statusMain) {
            statusMain.innerText = data.status_text || 'IDLE';
            statusMain.style.color = (data.left === 'fused') ? '#00e5ff' : (data.left === 'loaded' ? '#00ff95' : '#441111');
        }
        if (uiSub) uiSub.innerText = data.sub_text || 'SYSTEM_READY';
    }
}

// Expose broadcast function for backend
window.brainMonitorState = {
    update: (data) => {
        const widget = document.querySelector('.brain-monitor-container');
        if (widget && window._brainMonitorInstance) {
            window._brainMonitorInstance.updateMonitor(data);
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window._brainMonitorInstance = new BrainMonitor();
});
