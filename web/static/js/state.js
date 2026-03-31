class BicamerisState {
    constructor() {
        this.state = { 
            mode: 'dialogue_classique', 
            inferenceState: 'idle',
            telemetry: { pulse: 0, vram: 0 } 
        };
        this.listeners = new Map();
    }

    subscribe(key, callback) {
        if (!this.listeners.has(key)) this.listeners.set(key, []);
        this.listeners.get(key).push(callback);
    }

    update(key, value) {
        this.state[key] = value;
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(cb => cb(value));
        }
    }
}
window.Bicameris = new BicamerisState();
