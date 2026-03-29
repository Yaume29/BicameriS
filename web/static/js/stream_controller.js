/**
 * BICAMERIS - Stream Controller
 * Unified WebSocket & SSE handler for real-time telemetry
 * 
 * Zero page reloads. Continuous stream of consciousness.
 */

class StreamController {
    constructor() {
        this.ws = null;
        this.wsRetryCount = 0;
        this.maxRetries = 10;
        this.listeners = new Map();
        this.isConnected = false;
        this.reconnectTimer = null;
        
        // Connection state
        this.state = {
            neural: false,
            telemetry: false,
            lastPulse: 0.5,
            lastUpdate: null
        };
    }
    
    /**
     * Initialize all connections
     */
    init() {
        this.connectNeural();
        this.startTelemetryPoll();
        console.log('[StreamController] Initialized');
    }
    
    /**
     * Connect to neural WebSocket
     */
    connectNeural() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/neural`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('[StreamController] Neural WebSocket connected');
                this.isConnected = true;
                this.wsRetryCount = 0;
                this.state.neural = true;
                this.emit('connected', { type: 'neural' });
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('[StreamController] Parse error:', e);
                }
            };
            
            this.ws.onclose = () => {
                console.log('[StreamController] Neural WebSocket disconnected');
                this.isConnected = false;
                this.state.neural = false;
                this.emit('disconnected', { type: 'neural' });
                this.scheduleReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('[StreamController] WebSocket error:', error);
            };
            
        } catch (e) {
            console.error('[StreamController] WebSocket creation failed:', e);
            this.scheduleReconnect();
        }
    }
    
    /**
     * Schedule reconnection with exponential backoff
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        
        if (this.wsRetryCount >= this.maxRetries) {
            console.log('[StreamController] Max retries reached, falling back to polling');
            return;
        }
        
        const delay = Math.min(1000 * Math.pow(2, this.wsRetryCount), 30000);
        this.wsRetryCount++;
        
        console.log(`[StreamController] Reconnecting in ${delay}ms (attempt ${this.wsRetryCount})`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connectNeural();
        }, delay);
    }
    
    /**
     * Handle incoming WebSocket message
     */
    handleMessage(data) {
        // Update internal state
        this.state.lastUpdate = new Date();
        
        // Emit to all listeners
        this.emit('message', data);
        
        // Route to specific handlers based on type
        switch (data.type) {
            case 'thermal':
                this.handleThermal(data);
                break;
                
            case 'pulse':
                this.handlePulse(data);
                break;
                
            case 'models':
                this.handleModels(data);
                break;
                
            case 'inference':
                this.handleInference(data);
                break;
                
            case 'corps_calleux':
                this.handleCorpsCalleux(data);
                break;
                
            default:
                // Emit as generic event
                this.emit(data.type, data);
        }
    }
    
    /**
     * Handle thermal data
     */
    handleThermal(data) {
        this.emit('thermal', data);
        
        // Update CSS variables for reactive animations
        if (data.cpu_temp) {
            document.body.style.setProperty('--cpu-temp', data.cpu_temp);
        }
        if (data.gpu_temp) {
            document.body.style.setProperty('--gpu-temp', data.gpu_temp);
        }
    }
    
    /**
     * Handle pulse data
     */
    handlePulse(data) {
        this.state.lastPulse = data.pulse || 0.5;
        
        // Update CSS variable for pulse-driven animations
        const pulseSpeed = 3 - (data.pulse * 2); // 0.5 pulse = 2s, 1.0 pulse = 1s
        document.body.style.setProperty('--pulse-speed', `${pulseSpeed}s`);
        document.body.style.setProperty('--pulse-intensity', data.pulse);
        
        this.emit('pulse', data);
    }
    
    /**
     * Handle models status
     */
    handleModels(data) {
        this.emit('models', data);
        
        // Update brain state based on models
        if (data.left?.loaded) {
            document.body.setAttribute('data-left', 'loaded');
        } else {
            document.body.setAttribute('data-left', 'empty');
        }
        
        if (data.right?.loaded) {
            document.body.setAttribute('data-right', 'loaded');
        } else {
            document.body.setAttribute('data-right', 'empty');
        }
        
        if (data.is_split_mode) {
            document.body.setAttribute('data-bridge', 'true');
        } else {
            document.body.setAttribute('data-bridge', 'false');
        }
    }
    
    /**
     * Handle inference events
     */
    handleInference(data) {
        this.emit('inference', data);
        
        // Update brain state for thinking animation
        if (data.thinking) {
            document.body.setAttribute('data-mood', 'THINKING');
        }
    }
    
    /**
     * Handle corps callosum events
     */
    handleCorpsCalleux(data) {
        this.emit('corps_calleux', data);
        
        if (data.cycles) {
            document.body.style.setProperty('--cc-cycles', data.cycles);
        }
    }
    
    /**
     * Start telemetry polling as fallback
     */
    startTelemetryPoll() {
        setInterval(async () => {
            try {
                // Poll pulse
                const pulseResp = await fetch('/api/dashboard/pulse');
                const pulseData = await pulseResp.json();
                this.handlePulse(pulseData);
                
                // Poll models status every 5 seconds
                if (Date.now() % 5000 < 1000) {
                    const modelsResp = await fetch('/api/models/status');
                    const modelsData = await modelsResp.json();
                    this.handleModels(modelsData);
                }
                
            } catch (e) {
                // Silent fail for polling
            }
        }, 1000);
    }
    
    /**
     * Register event listener
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            for (const callback of this.listeners.get(event)) {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`[StreamController] Listener error for ${event}:`, e);
                }
            }
        }
    }
    
    /**
     * Send message via WebSocket
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Cleanup
     */
    destroy() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        if (this.ws) {
            this.ws.close();
        }
        this.listeners.clear();
    }
}

// Global instance
window.streamController = new StreamController();
