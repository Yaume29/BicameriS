/**
 * BICAMERIS Brain State Manager
 * Diadikos & Palladion - By Hope 'n Mind
 * 
 * Real-time brain activity visualization with:
 * - Left hemisphere (Diadikos) = Cyan/Blue glow
 * - Right hemisphere (Palladion) = Red glow
 * - Corpus Callosum (Bridge) = White/Green glow
 * - Fade effects and real pulse based on thinking activity
 */

class BicamerisBrain {
    constructor() {
        // Brain state
        this.state = {
            left: {
                status: 'empty',      // empty, loaded, thinking
                intensity: 0,         // 0-1 pulse intensity
                lastThought: null,
                pulseRate: 2,         // seconds
                thoughts: 0
            },
            right: {
                status: 'empty',
                intensity: 0,
                lastThought: null,
                pulseRate: 2,
                thoughts: 0
            },
            bridge: {
                active: false,
                intensity: 0,
                cycles: 0,
                lastCycle: null
            },
            overall: {
                status: 'STANDBY',
                mood: 'CALM',         // CALM, ACTIVE, THINKING, FUSED
                pulse: 2,
                thinking: false
            }
        };
        
        // WebSocket connection
        this.ws = null;
        this.wsRetryCount = 0;
        this.maxRetries = 5;
        
        // Polling fallback
        this.pollInterval = null;
        this.pollRate = 2000; // ms
        
        // Animation frame
        this.animationFrame = null;
        
        // DOM elements cache
        this.elements = {};
        
        // Initialize
        this.init();
    }
    
    init() {
        // Cache DOM elements
        this.cacheElements();
        
        // Start WebSocket connection
        this.connectWebSocket();
        
        // Start polling as fallback
        this.startPolling();
        
        // Start animation loop
        this.startAnimation();
        
        // Apply initial state
        this.applyState();
        
        console.log('[BicamerisBrain] Initialized');
    }
    
    cacheElements() {
        this.elements = {
            body: document.body,
            sidebar: document.querySelector('.sidebar'),
            brainLeft: document.getElementById('brain-left'),
            brainRight: document.getElementById('brain-right'),
            corpus: document.getElementById('corpus-callosum'),
            statusMain: document.getElementById('brain-status-main'),
            statusMeta: document.getElementById('brain-status-meta'),
            modelStatus: document.getElementById('model-status'),
            pulseValue: document.getElementById('pulse-value'),
            cyclesValue: document.getElementById('cycles-value'),
            activityDots: document.querySelectorAll('.activity-dot'),
            cards: document.querySelectorAll('.card, .info-card, .step-card')
        };
    }
    
    // ============================================
    // WEBSOCKET CONNECTION
    // ============================================
    
    connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/neural`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('[BicamerisBrain] WebSocket connected');
                this.wsRetryCount = 0;
                this.stopPolling(); // WebSocket connected, stop polling
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleUpdate(data);
                } catch (e) {
                    console.error('[BicamerisBrain] Parse error:', e);
                }
            };
            
            this.ws.onclose = () => {
                console.log('[BicamerisBrain] WebSocket disconnected');
                this.ws = null;
                
                // Try to reconnect
                if (this.wsRetryCount < this.maxRetries) {
                    this.wsRetryCount++;
                    setTimeout(() => this.connectWebSocket(), 2000);
                } else {
                    // Fall back to polling
                    this.startPolling();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('[BicamerisBrain] WebSocket error:', error);
            };
            
        } catch (e) {
            console.error('[BicamerisBrain] WebSocket creation failed:', e);
            this.startPolling();
        }
    }
    
    // ============================================
    // POLLING FALLBACK
    // ============================================
    
    startPolling() {
        if (this.pollInterval) return;
        
        this.pollInterval = setInterval(() => {
            this.pollStatus();
        }, this.pollRate);
        
        // Initial poll
        this.pollStatus();
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    async pollStatus() {
        try {
            // Get model status
            const modelResp = await fetch('/api/models/status');
            const modelData = await modelResp.json();
            
            // Get inference status
            let inferenceData = { incarnations: [] };
            try {
                const inferenceResp = await fetch('/api/inference/status');
                inferenceData = await inferenceResp.json();
            } catch (e) {
                // Inference might not be available
            }
            
            // Get cognition status
            let cognitionData = { cycles: 0 };
            try {
                const cognitionResp = await fetch('/api/cognitive/stats');
                cognitionData = await cognitionResp.json();
            } catch (e) {
                // Cognition might not be available
            }
            
            // Build state
            const state = {
                left: {
                    status: modelData.left?.loaded ? 'loaded' : 'empty',
                    thinking: inferenceData.incarnations?.some(i => i.name?.includes('left') && i.alive) || false
                },
                right: {
                    status: modelData.right?.loaded ? 'loaded' : 'empty',
                    thinking: inferenceData.incarnations?.some(i => i.name?.includes('right') && i.alive) || false
                },
                bridge: {
                    active: modelData.is_split_mode || false,
                    cycles: cognitionData.corps_calleux?.cycles || modelData.corps_calleux?.total_cycles || 0
                }
            };
            
            this.handleUpdate(state);
            
        } catch (e) {
            // Silent fail for polling
        }
    }
    
    // ============================================
    // STATE HANDLING
    // ============================================
    
    handleUpdate(data) {
        // Update left hemisphere
        if (data.left) {
            if (data.left.thinking) {
                this.state.left.status = 'thinking';
                this.state.left.intensity = 1;
                this.state.left.thoughts++;
            } else if (data.left.status === 'loaded' || data.left.loaded) {
                this.state.left.status = 'loaded';
                this.state.left.intensity = 0.5;
            } else {
                this.state.left.status = 'empty';
                this.state.left.intensity = 0;
            }
        }
        
        // Update right hemisphere
        if (data.right) {
            if (data.right.thinking) {
                this.state.right.status = 'thinking';
                this.state.right.intensity = 1;
                this.state.right.thoughts++;
            } else if (data.right.status === 'loaded' || data.right.loaded) {
                this.state.right.status = 'loaded';
                this.state.right.intensity = 0.5;
            } else {
                this.state.right.status = 'empty';
                this.state.right.intensity = 0;
            }
        }
        
        // Update bridge
        if (data.bridge) {
            if (typeof data.bridge === 'object') {
                this.state.bridge.active = data.bridge.active || false;
                this.state.bridge.cycles = data.bridge.cycles || 0;
            } else {
                this.state.bridge.active = data.bridge;
            }
            
            if (this.state.bridge.active) {
                this.state.bridge.intensity = 0.8;
                this.state.bridge.cycles++;
                this.state.bridge.lastCycle = new Date();
            }
        }
        
        // Update overall state
        this.updateOverallState();
        
        // Apply state to DOM
        this.applyState();
    }
    
    updateOverallState() {
        const leftThinking = this.state.left.status === 'thinking';
        const rightThinking = this.state.right.status === 'thinking';
        const bothLoaded = this.state.left.status === 'loaded' && this.state.right.status === 'loaded';
        
        if (leftThinking && rightThinking) {
            this.state.overall.status = 'THINKING';
            this.state.overall.mood = 'THINKING';
            this.state.overall.pulse = 0.8;
            this.state.overall.thinking = true;
        } else if (leftThinking) {
            this.state.overall.status = 'THINKING_LEFT';
            this.state.overall.mood = 'ACTIVE';
            this.state.overall.pulse = 1;
            this.state.overall.thinking = true;
        } else if (rightThinking) {
            this.state.overall.status = 'THINKING_RIGHT';
            this.state.overall.mood = 'ACTIVE';
            this.state.overall.pulse = 1;
            this.state.overall.thinking = true;
        } else if (bothLoaded && this.state.bridge.active) {
            this.state.overall.status = 'BICAMERAL';
            this.state.overall.mood = 'FUSED';
            this.state.overall.pulse = 2;
            this.state.overall.thinking = false;
        } else if (this.state.left.status === 'loaded' || this.state.right.status === 'loaded') {
            this.state.overall.status = 'ACTIVE';
            this.state.overall.mood = 'CALM';
            this.state.overall.pulse = 2;
            this.state.overall.thinking = false;
        } else {
            this.state.overall.status = 'STANDBY';
            this.state.overall.mood = 'CALM';
            this.state.overall.pulse = 3;
            this.state.overall.thinking = false;
        }
    }
    
    // ============================================
    // DOM UPDATES
    // ============================================
    
    applyState() {
        const { body, sidebar, brainLeft, brainRight, corpus } = this.elements;
        
        // Update body data attributes for CSS
        body.setAttribute('data-left', this.state.left.status);
        body.setAttribute('data-right', this.state.right.status);
        body.setAttribute('data-bridge', this.state.bridge.active);
        body.setAttribute('data-mood', this.state.overall.mood);
        
        // Toggle body classes
        body.classList.toggle('brain-active', this.state.overall.thinking);
        
        // Update sidebar classes
        if (sidebar) {
            sidebar.classList.remove('brain-thinking-left', 'brain-thinking-right', 'brain-thinking-both');
            
            if (this.state.left.status === 'thinking' && this.state.right.status === 'thinking') {
                sidebar.classList.add('brain-thinking-both');
            } else if (this.state.left.status === 'thinking') {
                sidebar.classList.add('brain-thinking-left');
            } else if (this.state.right.status === 'thinking') {
                sidebar.classList.add('brain-thinking-right');
            }
        }
        
        // Update brain SVG elements
        if (brainLeft) {
            brainLeft.classList.remove('active', 'thinking');
            if (this.state.left.status === 'thinking') {
                brainLeft.classList.add('thinking');
            } else if (this.state.left.status === 'loaded') {
                brainLeft.classList.add('active');
            }
        }
        
        if (brainRight) {
            brainRight.classList.remove('active', 'thinking');
            if (this.state.right.status === 'thinking') {
                brainRight.classList.add('thinking');
            } else if (this.state.right.status === 'loaded') {
                brainRight.classList.add('active');
            }
        }
        
        if (corpus) {
            corpus.classList.toggle('active', this.state.bridge.active);
        }
        
        // Update CSS variables for animations
        document.documentElement.style.setProperty('--pulse-left', `${this.state.left.pulseRate}s`);
        document.documentElement.style.setProperty('--pulse-right', `${this.state.right.pulseRate}s`);
        document.documentElement.style.setProperty('--overall-pulse', `${this.state.overall.pulse}s`);
        document.documentElement.style.setProperty('--brain-left-intensity', this.state.left.intensity);
        document.documentElement.style.setProperty('--brain-right-intensity', this.state.right.intensity);
        document.documentElement.style.setProperty('--bridge-intensity', this.state.bridge.intensity);
        
        // Update status display
        this.updateStatusDisplay();
        
        // Update activity dots
        this.updateActivityDots();
        
        // Update metrics
        this.updateMetrics();
    }
    
    updateStatusDisplay() {
        const { statusMain, statusMeta } = this.elements;
        
        if (statusMain) {
            statusMain.textContent = this.state.overall.status;
            statusMain.className = 'brain-status-main';
            
            if (this.state.overall.status === 'BICAMERAL') {
                statusMain.classList.add('bicameral');
            } else if (this.state.overall.thinking) {
                statusMain.classList.add('active');
            } else {
                statusMain.classList.add('standby');
            }
        }
        
        if (statusMeta) {
            statusMeta.textContent = `DIA: ${this.state.left.thoughts} | PAL: ${this.state.right.thoughts}`;
        }
    }
    
    updateActivityDots() {
        const dots = this.elements.activityDots;
        
        dots.forEach((dot, index) => {
            dot.classList.remove('active', 'thinking-left', 'thinking-right');
            
            if (index === 0 && this.state.left.status === 'thinking') {
                dot.classList.add('thinking-left');
            } else if (index === 1 && this.state.bridge.active) {
                dot.classList.add('active');
            } else if (index === 2 && this.state.right.status === 'thinking') {
                dot.classList.add('thinking-right');
            }
        });
    }
    
    updateMetrics() {
        const { modelStatus, pulseValue, cyclesValue } = this.elements;
        
        if (modelStatus) {
            if (this.state.bridge.active) {
                modelStatus.textContent = 'Bicaméral';
                modelStatus.style.color = 'var(--synapse)';
            } else if (this.state.left.status === 'loaded') {
                modelStatus.textContent = 'DIA actif';
                modelStatus.style.color = 'var(--diadikos)';
            } else if (this.state.right.status === 'loaded') {
                modelStatus.textContent = 'PAL actif';
                modelStatus.style.color = 'var(--palladion)';
            } else {
                modelStatus.textContent = 'Non configuré';
                modelStatus.style.color = 'var(--text-dim)';
            }
        }
        
        if (pulseValue) {
            pulseValue.textContent = this.state.overall.pulse.toFixed(2);
            pulseValue.classList.toggle('highlight', this.state.overall.thinking);
        }
        
        if (cyclesValue) {
            cyclesValue.textContent = this.state.bridge.cycles;
        }
    }
    
    // ============================================
    // ANIMATION LOOP
    // ============================================
    
    startAnimation() {
        const animate = () => {
            // Update pulse intensities based on time
            const time = Date.now() / 1000;
            
            if (this.state.left.status === 'loaded') {
                this.state.left.intensity = 0.3 + Math.sin(time * Math.PI / this.state.left.pulseRate) * 0.2;
            }
            
            if (this.state.right.status === 'loaded') {
                this.state.right.intensity = 0.3 + Math.sin(time * Math.PI / this.state.right.pulseRate + 0.5) * 0.2;
            }
            
            if (this.state.bridge.active) {
                this.state.bridge.intensity = 0.5 + Math.sin(time * Math.PI / 1.5) * 0.3;
            }
            
            // Update CSS variables for smooth animation
            document.documentElement.style.setProperty('--brain-left-intensity', this.state.left.intensity);
            document.documentElement.style.setProperty('--brain-right-intensity', this.state.right.intensity);
            document.documentElement.style.setProperty('--bridge-intensity', this.state.bridge.intensity);
            
            this.animationFrame = requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    stopAnimation() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }
    
    // ============================================
    // PUBLIC API
    // ============================================
    
    getState() {
        return { ...this.state };
    }
    
    triggerThinking(hemisphere = 'both') {
        if (hemisphere === 'left' || hemisphere === 'both') {
            this.state.left.status = 'thinking';
            this.state.left.intensity = 1;
            this.state.left.thoughts++;
        }
        
        if (hemisphere === 'right' || hemisphere === 'both') {
            this.state.right.status = 'thinking';
            this.state.right.intensity = 1;
            this.state.right.thoughts++;
        }
        
        this.updateOverallState();
        this.applyState();
        
        // Reset after 2 seconds
        setTimeout(() => {
            if (hemisphere === 'left' || hemisphere === 'both') {
                if (this.state.left.status === 'thinking') {
                    this.state.left.status = 'loaded';
                    this.state.left.intensity = 0.5;
                }
            }
            
            if (hemisphere === 'right' || hemisphere === 'both') {
                if (this.state.right.status === 'thinking') {
                    this.state.right.status = 'loaded';
                    this.state.right.intensity = 0.5;
                }
            }
            
            this.updateOverallState();
            this.applyState();
        }, 2000);
    }
    
    setBridgeActive(active) {
        this.state.bridge.active = active;
        this.applyState();
    }
    
    destroy() {
        this.stopAnimation();
        this.stopPolling();
        
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize on DOM ready
let bicamerisBrain = null;

document.addEventListener('DOMContentLoaded', () => {
    bicamerisBrain = new BicamerisBrain();
    
    // Expose to global scope
    window.bicamerisBrain = bicamerisBrain;
    
    // Click on main content to trigger thinking
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.addEventListener('click', (e) => {
            if (!e.target.closest('a, button, input, textarea, select')) {
                bicamerisBrain.triggerThinking('both');
            }
        });
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (bicamerisBrain) {
        bicamerisBrain.destroy();
    }
});
