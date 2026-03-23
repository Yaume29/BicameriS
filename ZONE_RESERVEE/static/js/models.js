// Models configuration page

let scanInterval = null;

// Check models status on load
document.addEventListener('DOMContentLoaded', function() {
    checkModelsStatus();
    setInterval(checkModelsStatus, 5000);
});

function checkModelsStatus() {
    fetch('/api/models/status')
        .then(r => r.json())
        .then(data => {
            const statusDiv = document.getElementById('models-status');
            if (data.left && data.left.loaded) {
                statusDiv.innerHTML = `
                    <div class="status-ok">✓ Gauche chargé</div>
                    <div class="model-name">${data.left.model_path.split('\\').pop()}</div>
                `;
            } else {
                statusDiv.innerHTML = `<div class="status-wait">⏳ Gauche non chargé</div>`;
            }
            
            if (data.right && data.right.loaded) {
                statusDiv.innerHTML += `<div class="status-ok">✓ Droit chargé</div>`;
            } else {
                statusDiv.innerHTML += `<div class="status-wait">⏳ Droit non chargé</div>`;
            }
            
            if (data.corps_calleux && data.corps_calleux.total_cycles > 0) {
                statusDiv.innerHTML += `<div class="status-info">📊 ${data.corps_calleux.total_cycles} cycles</div>`;
            }
        });
}

// Scanner
document.getElementById('btn-scan').addEventListener('click', startModelScan);

function startModelScan() {
    const path = document.getElementById('scan-path').value || 'C:\\';
    const btn = document.getElementById('btn-scan');
    
    btn.disabled = true;
    btn.innerText = "Recherche en cours...";
    
    fetch('/api/models/scan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({path: path})
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'started') {
            // Start polling
            scanInterval = setInterval(pollScanResults, 1000);
        }
    });
}

function pollScanResults() {
    fetch('/api/models/results')
        .then(r => r.json())
        .then(data => {
            document.getElementById('scan-count').innerText = `${data.count} modèles trouvés`;
            
            if (!data.is_scanning) {
                clearInterval(scanInterval);
                document.getElementById('btn-scan').disabled = false;
                document.getElementById('btn-scan').innerText = "Scanner";
                
                // Populate dropdowns
                updateModelDropdowns(data.models);
            }
        });
}

function updateModelDropdowns(models) {
    const leftSelect = document.getElementById('left-model-select');
    const rightSelect = document.getElementById('right-model-select');
    
    const options = models.map(m => 
        `<option value="${m.path}">${m.name} (${m.size_gb} GB)</option>`
    ).join('');
    
    leftSelect.innerHTML = '<option value="">Sélectionner un modèle...</option>' + options;
    rightSelect.innerHTML = '<option value="">Sélectionner un modèle...</option>' + options;
    
    // Show models grid
    const grid = document.getElementById('models-list');
    grid.innerHTML = models.map(m => `
        <div class="model-card">
            <div class="model-name">${m.name}</div>
            <div class="model-size">${m.size_gb} GB</div>
            <div class="model-path">${m.path}</div>
        </div>
    `).join('');
}

// Load models
document.getElementById('load-models').addEventListener('click', loadModels);

function loadModels() {
    const leftPath = document.getElementById('left-model-select').value;
    const rightPath = document.getElementById('right-model-select').value;
    
    if (!leftPath || !rightPath) {
        alert('Sélectionner les deux modèles!');
        return;
    }
    
    const btn = document.getElementById('load-models');
    const status = document.getElementById('load-status');
    
    btn.disabled = true;
    btn.innerText = "Chargement en cours...";
    status.innerHTML = "<p>Chargement des modèles (peut prendre quelques minutes)...</p>";
    
    fetch('/api/models/load', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            left_path: leftPath,
            right_path: rightPath
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = "⚡ Charger les Modèles";
        
        if (data.corps_calleux) {
            status.innerHTML = `
                <div class="success">
                    ✓ Hémisphère gauche chargé
                    ✓ Hémisphère droit chargé
                    ✓ Corps calleux initialisé
                </div>
            `;
            checkModelsStatus();
        } else if (data.left && data.left.error) {
            status.innerHTML = `<div class="error">Erreur: ${data.left.error}</div>`;
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerText = "⚡ Charger les Modèles";
        status.innerHTML = `<div class="error">Erreur: ${err.message}</div>`;
    });
}

// Test bipolar thinking
document.getElementById('btn-test-bipolar').addEventListener('click', testBipolar);

function testBipolar() {
    const question = document.getElementById('test-question').value;
    if (!question) return;
    
    const btn = document.getElementById('btn-test-bipolar');
    const resultDiv = document.getElementById('test-result');
    
    btn.disabled = true;
    btn.innerText = "Réfléchit...";
    resultDiv.innerHTML = "<p>Génération en cours...</p>";
    
    fetch('/api/bipolar/think', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question: question})
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = "Tester";
        
        resultDiv.innerHTML = `
            <div class="bipolar-result">
                <div class="phase left">
                    <h5>💭 Analyse Logique (Gauche)</h5>
                    <p>${data.left_analysis}</p>
                </div>
                <div class="phase right">
                    <h5>💫 Intuition (Droit)</h5>
                    <p>${data.right_intuition}</p>
                </div>
                <div class="phase synthesis">
                    <h5>⚡ Synthèse Finale</h5>
                    <p>${data.final_synthesis}</p>
                </div>
            </div>
        `;
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerText = "Tester";
        resultDiv.innerHTML = `<div class="error">Erreur: ${err.message}</div>`;
    });
}

// Add CSS for models page
const style = document.createElement('style');
style.textContent = `
    .scanner-section, .config-section, .test-section, .presets-section {
        background: var(--bg-card);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .scanner-controls, .test-controls {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .scanner-controls input, .test-controls input {
        flex: 1;
        padding: 12px;
        border-radius: 8px;
        background: var(--bg-dark);
        border: 1px solid rgba(255,255,255,0.1);
        color: var(--text);
    }
    
    .models-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 10px;
        margin-top: 15px;
    }
    
    .model-card {
        background: var(--bg-dark);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .model-card .model-name {
        font-weight: bold;
        color: var(--accent);
    }
    
    .model-card .model-size {
        color: var(--text-dim);
        font-size: 12px;
    }
    
    .hemisphere-config {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .hemisphere {
        background: var(--bg-dark);
        padding: 20px;
        border-radius: 8px;
    }
    
    .hemisphere h4 {
        color: var(--accent);
        margin-bottom: 5px;
    }
    
    .hemisphere .desc {
        color: var(--text-dim);
        font-size: 12px;
        margin-bottom: 15px;
    }
    
    .model-select {
        width: 100%;
        padding: 10px;
        background: var(--bg-card);
        color: var(--text);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
    }
    
    .params {
        margin-top: 10px;
        font-size: 12px;
        color: var(--text-dim);
    }
    
    .load-btn {
        width: 100%;
        padding: 15px;
        font-size: 16px;
    }
    
    .load-status {
        margin-top: 15px;
    }
    
    .load-status .success {
        background: rgba(0,255,136,0.1);
        border: 1px solid var(--success);
        padding: 15px;
        border-radius: 8px;
        color: var(--success);
    }
    
    .load-status .error {
        background: rgba(255,68,68,0.1);
        border: 1px solid var(--error);
        padding: 15px;
        border-radius: 8px;
        color: var(--error);
    }
    
    .bipolar-result {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    
    .phase {
        background: var(--bg-dark);
        padding: 15px;
        border-radius: 8px;
    }
    
    .phase h5 {
        margin-bottom: 10px;
        color: var(--accent);
    }
    
    .phase.left { border-left: 3px solid var(--accent); }
    .phase.right { border-left: 3px solid var(--accent-purple); }
    .phase.synthesis { border-left: 3px solid var(--success); }
    
    .status-ok { color: var(--success); }
    .status-wait { color: var(--warning); }
    .status-info { color: var(--text-dim); font-size: 12px; }
    
    /* Presets */
    .preset-buttons {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 15px;
    }
    
    .preset-btn {
        width: 50px;
        height: 50px;
        font-size: 24px;
        border-radius: 10px;
        background: var(--bg-dark);
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .preset-btn:hover {
        border-color: var(--accent);
        transform: scale(1.1);
    }
    
    .preset-btn.active {
        border-color: var(--success);
        background: rgba(0,255,136,0.1);
    }
    
    .preset-info {
        background: var(--bg-dark);
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .preset-desc {
        color: var(--text-dim);
        font-style: italic;
    }
    
    .preset-info .preset-label {
        color: var(--accent);
        font-size: 18px;
        font-weight: bold;
    }
    
    /* Expert sliders */
    .expert-section {
        background: var(--bg-dark);
        padding: 15px;
        border-radius: 8px;
    }
    
    .sliders-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
    }
    
    .slider-group {
        display: flex;
        flex-direction: column;
    }
    
    .slider-group label {
        font-size: 12px;
        color: var(--text-dim);
        margin-bottom: 5px;
    }
    
    .slider-group input[type="range"] {
        width: 100%;
    }
`;
document.head.appendChild(style);

// ============ PRESET FUNCTIONALITY ============

let currentPreset = null;

document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const preset = this.dataset.preset;
        applyPreset(preset);
        
        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
    });
});

function applyPreset(presetName) {
    fetch('/api/presets/apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({preset: presetName})
    })
    .then(r => r.json())
    .then(data => {
        if (data.applied) {
            currentPreset = presetName;
            fetch('/api/presets')
                .then(r => r.json())
                .then(pdata => {
                    const infoDiv = document.getElementById('preset-info');
                    if (pdata.presets[presetName]) {
                        const p = pdata.presets[presetName];
                        infoDiv.innerHTML = `
                            <p class="preset-label">${p.emoji} ${p.label}</p>
                            <p class="preset-desc">${p.description}</p>
                            <div class="preset-params">
                                <small>Gauche: temp=${p.left.temp}, top_p=${p.left.top_p}</small><br>
                                <small>Droite: temp=${p.right.temp}, top_p=${p.right.top_p}</small>
                            </div>
                        `;
                    }
                });
        }
    });
}

// Sliders
document.getElementById('temp-left').addEventListener('input', function() {
    document.getElementById('temp-left-val').textContent = this.value;
});
document.getElementById('temp-right').addEventListener('input', function() {
    document.getElementById('temp-right-val').textContent = this.value;
});
document.getElementById('topp-left').addEventListener('input', function() {
    document.getElementById('topp-left-val').textContent = this.value;
});
document.getElementById('topp-right').addEventListener('input', function() {
    document.getElementById('topp-right-val').textContent = this.value;
});
document.getElementById('repeat-penalty').addEventListener('input', function() {
    document.getElementById('repeat-val').textContent = this.value;
});

document.getElementById('apply-sliders').addEventListener('click', function() {
    const tempLeft = parseFloat(document.getElementById('temp-left').value);
    const tempRight = parseFloat(document.getElementById('temp-right').value);
    const toppLeft = parseFloat(document.getElementById('topp-left').value);
    const toppRight = parseFloat(document.getElementById('topp-right').value);
    const repeat = parseFloat(document.getElementById('repeat-penalty').value);
    
    const btn = this;
    btn.disabled = true;
    btn.innerText = "Application...";
    
    fetch('/api/presets/apply', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            preset: '_custom',
            custom: {
                left: { temp: tempLeft, top_p: toppLeft, repeat_penalty: repeat },
                right: { temp: tempRight, top_p: toppRight, repeat_penalty: repeat }
            }
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = "Appliquer les Sliders";
        document.getElementById('preset-info').innerHTML = 
            '<p class="preset-desc">✓ Paramètres personnalisés appliqués</p>';
    });
});

// Load current preset on page load
fetch('/api/presets')
    .then(r => r.json())
    .then(data => {
        if (data.current) {
            currentPreset = data.current;
        }
    });