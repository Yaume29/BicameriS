class BicamerisState {
    constructor() {
        this.state = {
            mode: 'dialogue_classique',
            inferenceState: 'idle',
            telemetry: {
                pulse: 0,
                vram: 0,
                entropy: 0
            },
            currentView: 'chat',
            theme: 'dark-cyberpunk'
        };
        this.listeners = new Map();
    }
    
    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(callback);
    }
    
    update(key, value) {
        this.state[key] = value;
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(cb => cb(value));
        }
    }
    
    get(key) {
        return this.state[key];
    }
    
    setMode(mode) {
        this.update('mode', mode);
    }
    
    setInferenceState(phase) {
        this.update('inferenceState', phase);
    }
    
    setTelemetry(pulse, vram, entropy) {
        this.state.telemetry = { pulse, vram, entropy };
        if (this.listeners.has('telemetry')) {
            this.listeners.get('telemetry').forEach(cb => cb(this.state.telemetry));
        }
    }
    
    setView(view) {
        this.update('currentView', view);
    }
}

window.Bicameris = new BicamerisState();
