// Brain Hemisphere Status Loader
// Updates the brain logo based on loaded models

class BrainStatusWidget {
    constructor() {
        this.updateInterval = 5000;
        this.init();
    }

    init() {
        this.createWidget();
        this.updateStatus();
        setInterval(() => this.updateStatus(), this.updateInterval);
    }

    createWidget() {
        const existing = document.querySelector('.brain-logo-container');
        if (existing) return;

        const widget = document.createElement('div');
        widget.className = 'brain-logo-container';
        widget.id = 'brain-status-widget';
        widget.innerHTML = `
            <div class="brain-hemisphere left" id="brain-left">
                <div class="brain-texture"></div>
            </div>
            <div class="brain-connector"></div>
            <div class="brain-hemisphere right" id="brain-right">
                <div class="brain-texture"></div>
            </div>
            <div class="brain-tooltip" id="brain-tooltip">
                <div class="tooltip-title">🧠 État des Hémisphères</div>
                <div class="tooltip-section" id="left-info">
                    <h4>⚡ Gauche (Logique)</h4>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Modèle:</span>
                        <span class="tooltip-value" id="left-model">Aucun</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Temp:</span>
                        <span class="tooltip-value" id="left-temp">-</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Ctx:</span>
                        <span class="tooltip-value" id="left-ctx">-</span>
                    </div>
                </div>
                <div class="tooltip-section" id="right-info">
                    <h4>✨ Droit (Intuitif)</h4>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Modèle:</span>
                        <span class="tooltip-value" id="right-model">Aucun</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Temp:</span>
                        <span class="tooltip-value" id="right-temp">-</span>
                    </div>
                    <div class="tooltip-row">
                        <span class="tooltip-label">Ctx:</span>
                        <span class="tooltip-value" id="right-ctx">-</span>
                    </div>
                </div>
                <div class="brain-status" id="brain-status-text">En attente...</div>
            </div>
        `;
        document.body.appendChild(widget);
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/models/status');
            const data = await response.json();

            const leftPath = document.getElementById('brain-left');
            const rightPath = document.getElementById('brain-right');

            if (!leftPath || !rightPath) return;

            // Left hemisphere
            const left = data.left || {};
            const leftLoaded = left.loaded === true;
            
            if (leftLoaded) {
                leftPath.classList.remove('status-red');
                leftPath.classList.add('status-green');
            } else {
                leftPath.classList.remove('status-green');
                leftPath.classList.add('status-red');
            }

            // Right hemisphere
            const right = data.right || {};
            const rightLoaded = right.loaded === true;
            
            if (rightLoaded) {
                rightPath.classList.remove('status-red');
                rightPath.classList.add('status-green');
            } else {
                rightPath.classList.remove('status-green');
                rightPath.classList.add('status-red');
            }

            // Handle Split Mode (both green if split mode is active and at least one is loaded)
            if (data.is_split_mode && (leftLoaded || rightLoaded)) {
                leftPath.classList.remove('status-red');
                leftPath.classList.add('status-green');
                rightPath.classList.remove('status-red');
                rightPath.classList.add('status-green');
            }

        } catch (error) {
            // console.log('Brain status: API not available');
        }
    }

    truncate(str, len) {
        if (!str) return 'Aucun';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    new BrainStatusWidget();
});
