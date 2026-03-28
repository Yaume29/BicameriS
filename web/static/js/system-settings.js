/**
 * SYSTEM SETTINGS PANEL - BIOMETRIC EDITION
 * Panneau d'options rétractable pour Thermal, Inference & VRAM
 * Includes Switchboard toggles for laboratory features
 */

const SystemSettings = {
    thermalEnabled: false,
    thermalInterval: null,
    undervoltProfile: 'AGGRESSIVE',
    guillotineEnabled: true,
    
    init() {
        this.createPanel();
        this.bindEvents();
        this.loadSwitches();
    },
    
    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'system-settings-panel';
        panel.className = 'settings-panel collapsed';
        panel.innerHTML = `
            <div class="settings-toggle" onclick="SystemSettings.toggle()">
                <span class="toggle-icon">⚙️</span>
                <span class="toggle-text">SYSTEM</span>
                <span class="toggle-arrow">▼</span>
            </div>
            <div class="settings-content">
                <div class="settings-section">
                    <h4>🌡️ THERMAL GOVERNOR</h4>
                    <div class="setting-row">
                        <label class="toggle-label">
                            <input type="checkbox" id="thermal-enable" onchange="SystemSettings.toggleThermal(this.checked)">
                            <span>Monitoring actif</span>
                        </label>
                    </div>
                    <div class="setting-row">
                        <label>Profil Undervolting</label>
                        <select id="undervolt-profile" onchange="SystemSettings.setUndervolt(this.value)">
                            <option value="DEFAULT">DEFAULT (Aucun)</option>
                            <option value="MODERATE">MODERATE (-50mV)</option>
                            <option value="AGGRESSIVE" selected>AGGRESSIVE (-100mV)</option>
                            <option value="OMEGA">OMEGA (-150mV)</option>
                        </select>
                    </div>
                    <div class="thermal-status">
                        <div class="status-row">
                            <span class="label">CPU:</span>
                            <span class="value" id="thermal-cpu">--°C</span>
                        </div>
                        <div class="status-row">
                            <span class="label">GPU:</span>
                            <span class="value" id="thermal-gpu">--°C</span>
                        </div>
                        <div class="status-row">
                            <span class="label">Impact:</span>
                            <span class="value" id="thermal-impact">--</span>
                        </div>
                        <div class="status-row">
                            <span class="label">Mood:</span>
                            <span class="value" id="thermal-mood">--</span>
                        </div>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>🗡️ VRAM GUILLOTINE</h4>
                    <div class="setting-row">
                        <label class="toggle-label">
                            <input type="checkbox" id="guillotine-enable" checked onchange="SystemSettings.toggleGuillotine(this.checked)">
                            <span>Guillotine après inférence</span>
                        </label>
                    </div>
                    <div class="setting-row">
                        <button class="btn-danger" onclick="SystemSettings.guillotineAll()">⚡ TUER TOUTES LES INCARNATIONS</button>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>🧠 INFERENCE INCARNATIONS</h4>
                    <div class="incarnations-list" id="incarnations-list">
                        <p class="empty">Aucune incarnation active</p>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>🔬 LABORATOIRE COGNITIF</h4>
                    <div class="switchboard-controls" id="switchboard-controls">
                        <p class="empty">Chargement...</p>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>🧬 MODULATEUR ENDOCRINIEN</h4>
                    <div class="setting-row">
                        <label class="toggle-label">
                            <input type="checkbox" id="endocrine-enable" onchange="SystemSettings.toggleEndocrine(this.checked)">
                            <span>Liaison Soma-Psyché</span>
                        </label>
                    </div>
                    <div class="endocrine-sliders" id="endocrine-sliders">
                        <div class="setting-row">
                            <label>Réceptivité au Pulse:</label>
                            <span class="slider-value" id="val-sens">0.50</span>
                        </div>
                        <input type="range" id="slider-sens" min="0" max="1" step="0.05" value="0.5" 
                               oninput="SystemSettings.updateSliderDisplay('sens', this.value)">
                        <div class="setting-row">
                            <label>Impact Température:</label>
                            <span class="slider-value" id="val-imp">0.50</span>
                        </div>
                        <input type="range" id="slider-imp" min="0" max="1" step="0.05" value="0.5"
                               oninput="SystemSettings.updateSliderDisplay('imp', this.value)">
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(panel);
        
        const style = document.createElement('style');
        style.textContent = `
            .settings-panel {
                position: fixed;
                bottom: 0;
                right: 20px;
                width: 320px;
                background: var(--bg-card, #12121a);
                border: 1px solid #333;
                border-radius: 12px 12px 0 0;
                z-index: 1000;
                font-family: 'Segoe UI', sans-serif;
                transition: transform 0.3s ease;
            }
            
            .settings-panel.collapsed .settings-content {
                display: none;
            }
            
            .settings-toggle {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 12px 16px;
                cursor: pointer;
                background: linear-gradient(90deg, #1a1a24, #12121a);
                border-radius: 12px 12px 0 0;
                border-bottom: 1px solid #333;
            }
            
            .settings-toggle:hover {
                background: linear-gradient(90deg, #252530, #1a1a24);
            }
            
            .toggle-icon { font-size: 1.2rem; }
            .toggle-text { font-weight: 600; color: var(--primary, #00ff95); flex: 1; }
            .toggle-arrow { color: var(--text-dim, #666); transition: transform 0.3s; }
            
            .settings-panel.collapsed .toggle-arrow { transform: rotate(-90deg); }
            
            .settings-content {
                max-height: 400px;
                overflow-y: auto;
                padding: 12px;
            }
            
            .settings-section {
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #222;
            }
            
            .settings-section h4 {
                margin: 0 0 10px 0;
                font-size: 0.85rem;
                color: var(--secondary, #7b2ff7);
            }
            
            .setting-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            
            .setting-row label {
                font-size: 0.85rem;
                color: var(--text, #e0e0e0);
            }
            
            .setting-row select {
                background: #1a1a24;
                border: 1px solid #333;
                color: var(--text, #e0e0e0);
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
            }
            
            .toggle-label {
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            }
            
            .toggle-label input[type="checkbox"] {
                width: 16px;
                height: 16px;
                accent-color: var(--primary, #00ff95);
            }
            
            .thermal-status {
                background: #0a0a0f;
                border-radius: 6px;
                padding: 8px;
                margin-top: 8px;
            }
            
            .status-row {
                display: flex;
                justify-content: space-between;
                font-size: 0.8rem;
                margin-bottom: 4px;
            }
            
            .status-row .label { color: var(--text-dim, #666); }
            .status-row .value { color: var(--primary, #00ff95); font-weight: 600; }
            
            .btn-danger {
                width: 100%;
                padding: 8px;
                background: #2a1a1a;
                border: 1px solid #ff6b6b;
                color: #ff6b6b;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.8rem;
                transition: all 0.2s;
            }
            
            .btn-danger:hover {
                background: #ff6b6b;
                color: #0a0a0f;
            }
            
            .incarnations-list {
                max-height: 120px;
                overflow-y: auto;
            }
            
            .incarnations-list .empty {
                color: var(--text-dim, #666);
                font-size: 0.8rem;
                text-align: center;
                padding: 10px;
            }
            
            .incarnation-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 8px;
                background: #1a1a24;
                border-radius: 4px;
                margin-bottom: 4px;
                font-size: 0.75rem;
            }
            
            .incarnation-item .name { color: var(--accent, #00e5ff); }
            .incarnation-item .status { 
                color: #00ff95; 
            }
            .incarnation-item .status.dead { color: #ff6b6b; }
            
            .switchboard-controls {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .switchboard-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 8px 10px;
                background: #1a1a24;
                border-radius: 6px;
                font-size: 0.8rem;
            }
            
            .switchboard-item .name {
                color: var(--text, #e0e0e0);
                flex: 1;
            }
            
            .switchboard-item input[type="checkbox"] {
                width: 18px;
                height: 18px;
                accent-color: var(--primary, #00ff95);
            }
            
            .endocrine-sliders {
                margin-top: 8px;
                padding: 8px;
                background: #0a0a0f;
                border-radius: 6px;
                opacity: 1;
                pointer-events: auto;
                transition: opacity 0.2s;
            }
            
            .endocrine-sliders.disabled {
                opacity: 0.4;
                pointer-events: none;
            }
            
            .slider-value {
                color: var(--primary, #00ff95);
                font-weight: 600;
                font-size: 0.85rem;
            }
            
            .endocrine-sliders input[type="range"] {
                width: 100%;
                margin: 4px 0 12px 0;
                accent-color: var(--secondary, #7b2ff7);
            }
        `;
        document.head.appendChild(style);
    },
    
    toggle() {
        const panel = document.getElementById('system-settings-panel');
        panel.classList.toggle('collapsed');
    },
    
    bindEvents() {
        this.loadThermalStatus();
        this.loadIncarnations();
        this.loadEndocrineConfig();
    },
    
    async toggleThermal(enabled) {
        this.thermalEnabled = enabled;
        
        if (enabled) {
            this.startThermalMonitoring();
        } else {
            this.stopThermalMonitoring();
        }
        
        this.updateThermalUI();
    },
    
    startThermalMonitoring() {
        if (this.thermalInterval) return;
        
        this.thermalInterval = setInterval(async () => {
            await this.loadThermalStatus();
        }, 2000);
    },
    
    stopThermalMonitoring() {
        if (this.thermalInterval) {
            clearInterval(this.thermalInterval);
            this.thermalInterval = null;
        }
    },
    
    async loadThermalStatus() {
        try {
            const res = await fetch('/api/hardware/thermal/status');
            const data = await res.json();
            
            document.getElementById('thermal-cpu').textContent = (data.current_temp || '--') + '°C';
            document.getElementById('thermal-gpu').textContent = (data.gpu_temp || '--') + '°C';
            document.getElementById('thermal-impact').textContent = (data.entropic_impact || '--');
            document.getElementById('thermal-mood').textContent = data.thermal_mood || '--';
            
            // Color based on mood (COLD, STABLE, AGITATED, FEVER)
            const mood = data.thermal_mood;
            const moodEl = document.getElementById('thermal-mood');
            if (mood === 'FEVER') moodEl.style.color = '#ff6b6b';
            else if (mood === 'AGITATED') moodEl.style.color = '#feca57';
            else if (mood === 'COLD') moodEl.style.color = '#00e5ff';
            else moodEl.style.color = '#00ff95';
            
        } catch(e) {
            console.error('Thermal status error:', e);
        }
    },
    
    updateThermalUI() {
        const status = document.getElementById('thermal-enable');
        if (this.thermalEnabled) {
            document.querySelector('.thermal-status').style.opacity = '1';
        } else {
            document.querySelector('.thermal-status').style.opacity = '0.5';
        }
    },
    
    async setUndervolt(profile) {
        this.undervoltProfile = profile;
        
        if (profile === 'DEFAULT') {
            console.log('Undervolting disabled');
            return;
        }
        
        try {
            const res = await fetch('/api/thermal/undervolt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({profile})
            });
            const data = await res.json();
            console.log('Undervolt applied:', data);
        } catch(e) {
            console.error('Undervolt error:', e);
        }
    },
    
    toggleGuillotine(enabled) {
        this.guillotineEnabled = enabled;
        console.log('Guillotine:', enabled ? 'enabled' : 'disabled');
    },
    
    async guillotineAll() {
        if (!confirm('⚠️ VRAM HARD-RESET: Détruire toutes les incarnations?')) return;
        
        try {
            const res = await fetch('/api/inference/guillotine_all', {method: 'POST'});
            const data = await res.json();
            console.log('Guillotine result:', data);
            this.loadIncarnations();
        } catch(e) {
            console.error('Guillotine error:', e);
        }
    },
    
    async loadIncarnations() {
        try {
            const res = await fetch('/api/inference/status');
            const data = await res.json();
            
            const container = document.getElementById('incarnations-list');
            
            if (!data.incarnations || data.incarnations.length === 0) {
                container.innerHTML = '<p class="empty">Aucune incarnation active</p>';
                return;
            }
            
            container.innerHTML = data.incarnations.map(inc => `
                <div class="incarnation-item">
                    <span class="name">${inc.name}</span>
                    <span class="status ${inc.alive ? '' : 'dead'}">${inc.alive ? '●' : '○'}</span>
                </div>
            `).join('');
            
        } catch(e) {
            console.error('Incarnations error:', e);
        }
    },
    
    // ============ SWITCHBOARD METHODS ============
    
    async loadSwitches() {
        try {
            const res = await fetch('/api/system/switches');
            const switches = await res.json();
            
            const container = document.getElementById('switchboard-controls');
            if (!container) return;
            
            const switchLabels = {
                autonomous_loop: '🔄 Boucle Autonome',
                auto_forge_agents: '🛠️ Auto-Forge Agents',
                sandbox_docker: '🐳 Sandbox Docker',
                debug_telemetry: '📊 Debug Telemetry',
                thermal_throttling: '🌡️ Thermal Throttling',
                hemisphere_split_mode: '🧠 Mode Split Hémisphères',
                trauma_filter: '💜 Filtre Trauma',
                entropy_tracking: '🎲 Suivi Entropie'
            };
            
            container.innerHTML = Object.entries(switches).map(([key, value]) => `
                <div class="switchboard-item">
                    <span class="name">${switchLabels[key] || key}</span>
                    <input type="checkbox" 
                           id="switch-${key}" 
                           ${value ? 'checked' : ''}
                           onchange="SystemSettings.toggleSwitch('${key}', this.checked)">
                </div>
            `).join('');
            
        } catch(e) {
            console.error('Switchboard error:', e);
            const container = document.getElementById('switchboard-controls');
            if (container) container.innerHTML = '<p class="empty">Erreur chargement</p>';
        }
    },
    
    async toggleSwitch(feature, state) {
        try {
            const res = await fetch(`/api/system/switches/${feature}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({state})
            });
            const data = await res.json();
            
            if (data.conflicts && data.conflicts.length > 0) {
                let conflictMsg = `⚠️ Conflits détectés en activant "${feature}":\n\n`;
                for (const conflict of data.conflicts) {
                    conflictMsg += `• "${conflict.feature}" sera désactivé\n  Raison: ${conflict.reason}\n\n`;
                }
                conflictMsg += "Continuer ?";
                
                if (!confirm(conflictMsg)) {
                    const checkbox = document.querySelector(`input[data-feature="${feature}"]`);
                    if (checkbox) checkbox.checked = !state;
                    return;
                }
                
                for (const conflict of data.conflicts) {
                    const checkbox = document.querySelector(`input[data-feature="${conflict.feature}"]`);
                    if (checkbox) {
                        checkbox.checked = false;
                        this.showToast(`${conflict.feature} désactivé (conflit avec ${feature})`, 'warning');
                    }
                }
            }
            
            this.showToast(`${feature}: ${state ? 'ON' : 'OFF'}`, state ? 'success' : 'info');
            console.log(`[Switchboard] ${feature}: ${state ? 'ON' : 'OFF'}`, data);
        } catch(e) {
            console.error('Toggle switch error:', e);
            this.showToast(`Erreur: ${e.message}`, 'error');
        }
    },
    
    // ============ ENDOCRINE METHODS ============
    
    endocrineTimeout: null,
    
    async loadEndocrineConfig() {
        try {
            const res = await fetch('/api/system/status');
            const data = await res.json();
            const endocrine = data.endocrine || {enabled: true, sensitivity: 0.5, impact: 0.5};
            
            const toggle = document.getElementById('endocrine-enable');
            const slidersDiv = document.getElementById('endocrine-sliders');
            const sensSlider = document.getElementById('slider-sens');
            const impSlider = document.getElementById('slider-imp');
            
            if (toggle) toggle.checked = endocrine.enabled;
            if (slidersDiv) {
                slidersDiv.classList.toggle('disabled', !endocrine.enabled);
            }
            if (sensSlider) sensSlider.value = endocrine.sensitivity;
            if (impSlider) impSlider.value = endocrine.impact;
            
            document.getElementById('val-sens').textContent = endocrine.sensitivity.toFixed(2);
            document.getElementById('val-imp').textContent = endocrine.impact.toFixed(2);
            
        } catch(e) {
            console.error('Load endocrine error:', e);
        }
    },
    
    async toggleEndocrine(enabled) {
        const slidersDiv = document.getElementById('endocrine-sliders');
        if (slidersDiv) {
            slidersDiv.classList.toggle('disabled', !enabled);
        }
        this.sendEndocrineConfig();
    },
    
    updateSliderDisplay(type, value) {
        document.getElementById(`val-${type}`).textContent = parseFloat(value).toFixed(2);
        this.sendEndocrineConfig();
    },
    
    sendEndocrineConfig() {
        clearTimeout(this.endocrineTimeout);
        this.endocrineTimeout = setTimeout(async () => {
            const enabled = document.getElementById('endocrine-enable')?.checked ?? true;
            const sensitivity = parseFloat(document.getElementById('slider-sens')?.value ?? 0.5);
            const impact = parseFloat(document.getElementById('slider-imp')?.value ?? 0.5);
            
            try {
                const res = await fetch('/api/system/endocrine', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        enabled: enabled,
                        sensitivity: sensitivity,
                        impact: impact
                    })
                });
                if (!res.ok) {
                    const err = await res.json();
                    console.error('Endocrine config error:', err);
                }
            } catch(e) {
                console.error('Endocrine API error:', e);
            }
        }, 250);
    },
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? '#4CAF50' : type === 'warning' ? '#FF9800' : type === 'error' ? '#f44336' : '#2196F3'};
        `;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    SystemSettings.init();
});
