// Models configuration page - New Version

let scanInterval = null;
let foundModels = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initMainTabs();
    initSubTabs();
    initFolderHandlers();
    checkModelsStatus();
    setInterval(checkModelsStatus, 5000);
    pollScanResults();
    
    // Load default LM Studio path
    fetch('/api/models/default-path')
        .then(r => r.json())
        .then(data => {
            if (data.path) {
                const input = document.getElementById('scan-path');
                if (input && !input.value) {
                    input.value = data.path;
                }
            }
        });
});

// ============ TAB HANDLING ============

function initMainTabs() {
    const tabs = document.querySelectorAll('.main-tabs .tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`tab-${target}`).classList.add('active');
        });
    });
}

function initSubTabs() {
    const tabs = document.querySelectorAll('.sub-tabs .sub-tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.subtab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            document.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`subtab-${target}`).classList.add('active');
        });
    });
}

// ============ FOLDER SELECTION & SCANNER ============

// Initialize folder selection handlers
function initFolderHandlers() {
    // Handle Enter key in input field
    const pathInput = document.getElementById('scan-path');
    if (pathInput) {
        pathInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('btn-scan').click();
            }
        });
    }

    // Scan button - use text input
    const scanBtn = document.getElementById('btn-scan');
    if (scanBtn) {
        scanBtn.addEventListener('click', function() {
            const pathInput = document.getElementById('scan-path');
            const path = pathInput ? pathInput.value.trim() : '';
            
            if (!path) {
                alert('Entrez un chemin de dossier.');
                return;
            }
            
            const btn = this;
            const status = document.getElementById('scan-status');
            const progress = document.getElementById('scan-progress');
            
            btn.disabled = true;
            btn.textContent = 'Recherche...';
            progress.style.display = 'block';
            status.textContent = 'Scan de: ' + path;
            
            fetch('/api/models/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path})
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'started') {
                    status.textContent = 'Recherche en cours...';
                    scanInterval = setInterval(pollScanResults, 1000);
                } else {
                    status.textContent = 'Erreur: ' + (data.message || 'Inconnue');
                    btn.disabled = false;
                    btn.textContent = 'OK';
                }
            })
            .catch(err => {
                status.textContent = 'Erreur: ' + err.message;
                btn.disabled = false;
                btn.textContent = 'OK';
            });
        });
    }

    // Scan usual folders button
    const scanUsualBtn = document.getElementById('btn-scan-usual');
    if (scanUsualBtn) {
        scanUsualBtn.addEventListener('click', scanUsualFolders);
    }
}

function scanUsualFolders() {
    const btn = document.getElementById('btn-scan-usual');
    const progress = document.getElementById('scan-progress');
    const status = document.getElementById('scan-status');
    
    btn.disabled = true;
    btn.textContent = 'Recherche...';
    progress.style.display = 'block';
    status.textContent = 'Scan des dossiers habituels...';
    
    fetch('/api/models/scan-usual', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'started') {
            scanInterval = setInterval(pollScanResults, 1000);
        } else if (data.status === 'error') {
            status.textContent = 'Erreur: ' + (data.message || '');
            btn.disabled = false;
            btn.textContent = 'Scanner automatiquement';
        }
    });
}

function pollScanResults() {
    fetch('/api/models/results')
        .then(r => r.json())
        .then(data => {
            const progress = document.querySelector('.scan-progress .progress-fill');
            const status = document.getElementById('scan-status');
            
            if (data.is_scanning) {
                if (progress) progress.style.width = '50%';
            } else {
                if (scanInterval) clearInterval(scanInterval);
                
                const btn = document.getElementById('btn-scan');
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Scanner ce dossier';
                }
                
                if (progress) progress.style.width = '100%';
                status.textContent = `✓ ${data.count} modèles GGUF trouvés`;
                
                // Update dropdowns
                if (data.models && data.models.length > 0) {
                    foundModels = data.models;
                    updateModelDropdowns(data.models);
                    const notice = document.getElementById('local-models-notice');
                    if (notice) notice.style.display = 'none';
                }
            }
        });
}

function updateModelDropdowns(models) {
    const leftSelect = document.getElementById('left-model-select');
    const rightSelect = document.getElementById('right-model-select');
    
    if (!leftSelect || !rightSelect) return;
    
    const options = models.map(m => 
        `<option value="${m.path}">${m.name} (${m.size_gb || m.size_mb})</option>`
    ).join('');
    
    const defaultOption = '<option value="">Sélectionner un modèle...</option>';
    leftSelect.innerHTML = defaultOption + options;
    rightSelect.innerHTML = defaultOption + '<option value="EMPTY">-- Laisser Vide --</option>' + options;
}

// ============ STATUS CHECK ============

function checkModelsStatus() {
    fetch('/api/models/status')
        .then(r => r.json())
        .then(data => {
            const statusDiv = document.getElementById('models-status');
            if (!statusDiv) return;
            
            let html = '';
            
            if (data.is_split_mode) {
                html += '<div class="status-info mb-2">🧠 Mode Split Actif</div>';
            }
            
            if (data.left && data.left.loaded) {
                html += `<div class="status-ok">✓ Gauche: ${data.left.model_name || 'Chargé'}</div>`;
            } else {
                html += '<div class="status-wait">⏳ Gauche non chargé</div>';
            }
            
            if (data.right && data.right.loaded) {
                html += `<div class="status-ok">✓ Droit: ${data.right.model_name || 'Chargé'}</div>`;
            } else {
                html += '<div class="status-wait">⏳ Droit non chargé</div>';
            }
            
            if (data.corps_calleux && data.corps_calleux.total_cycles > 0) {
                html += `<div class="status-info mt-2">📊 ${data.corps_calleux.total_cycles} cycles</div>`;
            }
            
            statusDiv.innerHTML = html;
        });
}

// ============ LOCAL MODEL LOADING ============

document.getElementById('btn-load-local').addEventListener('click', loadLocalModels);

function loadLocalModels() {
    const leftPath = document.getElementById('left-model-select').value;
    const rightPath = document.getElementById('right-model-select').value;
    const bothHemi = document.getElementById('both-hemispheres').checked;
    
    if (!leftPath) {
        alert('Sélectionnez au moins un modèle dans l\'hémisphère gauche!');
        return;
    }
    
    const btn = document.getElementById('btn-load-local');
    const status = document.getElementById('load-status');
    
    btn.disabled = true;
    btn.innerText = '⏳ Initialisation...';
    status.innerHTML = '<div class="loading">Configuration du cerveau...</div>';
    
    fetch('/api/models/load', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            left_path: leftPath,
            right_path: bothHemi ? leftPath : (rightPath === 'EMPTY' ? null : rightPath),
            split_mode: bothHemi,
            method: 'local'
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = '⚡ Initialiser les Modèles';
        
        if (data.status === 'ok') {
            status.innerHTML = '<div class="success">✓ Cerveau initialisé avec succès!</div>';
            checkModelsStatus();
        } else {
            status.innerHTML = `<div class="error">✗ Erreur: ${data.error || 'Inconnue'}</div>`;
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerText = '⚡ Initialiser les Modèles';
        status.innerHTML = `<div class="error">✗ Erreur réseau: ${err.message}</div>`;
    });
}

// ============ LM STUDIO ============

document.getElementById('btn-check-lmstudio').addEventListener('click', checkLmStudio);

function checkLmStudio() {
    const url = document.getElementById('lmstudio-url').value;
    const btn = this;
    const status = document.getElementById('lmstudio-status');
    
    btn.disabled = true;
    btn.innerText = 'Vérification...';
    
    fetch('/api/models/lmstudio/check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: url})
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = 'Vérifier';
        
        if (data.status === 'ok') {
            status.innerHTML = '<span style="color: #00ff88">✓ Connecté à LM Studio!</span>';
            if (data.models) {
                updateLmStudioDropdowns(data.models);
            }
        } else {
            status.innerHTML = `<span style="color: #ff4444">✗ ${data.error || 'Erreur'}</span>`;
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerText = 'Vérifier';
        status.innerHTML = `<span style="color: #ff4444">✗ Erreur réseau</span>`;
    });
}

function updateLmStudioDropdowns(models) {
    const leftSelect = document.getElementById('lm-left-model');
    const rightSelect = document.getElementById('lm-right-model');
    
    if (!leftSelect || !rightSelect) return;
    
    const options = models.map(m => 
        `<option value="${m.id}">${m.id}</option>`
    ).join('');
    
    const defaultOption = '<option value="">Sélectionner un modèle...</option>';
    leftSelect.innerHTML = defaultOption + options;
    rightSelect.innerHTML = defaultOption + '<option value="EMPTY">-- Laisser Vide --</option>' + options;
}

document.getElementById('btn-load-lmstudio').addEventListener('click', loadLmStudioModels);

function loadLmStudioModels() {
    const leftModel = document.getElementById('lm-left-model').value;
    const rightModel = document.getElementById('lm-right-model').value;
    const bothHemi = document.getElementById('lm-both-hemispheres').checked;
    const url = document.getElementById('lmstudio-url').value;
    
    if (!leftModel) {
        alert('Sélectionnez au moins un modèle!');
        return;
    }
    
    const btn = document.getElementById('btn-load-lmstudio');
    const status = document.getElementById('lm-load-status');
    
    btn.disabled = true;
    btn.innerText = '⏳ Connexion...';
    status.innerHTML = '<div class="loading">Connexion à LM Studio...</div>';
    
    fetch('/api/models/load', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            left_path: leftModel,
            right_path: bothHemi ? leftModel : (rightModel === 'EMPTY' ? null : rightModel),
            split_mode: bothHemi,
            method: 'lmstudio',
            lmstudio_url: url
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = '⚡ Connecter à LM Studio';
        
        if (data.status === 'ok') {
            status.innerHTML = '<div class="success">✓ Connecté à LM Studio!</div>';
            checkModelsStatus();
        } else {
            status.innerHTML = `<div class="error">✗ ${data.error || 'Erreur'}</div>`;
        }
    });
}

// ============ API KEYS ============

document.getElementById('btn-save-keys').addEventListener('click', saveApiKeys);

function saveApiKeys() {
    const gemini = document.getElementById('key-gemini').value;
    const groq = document.getElementById('key-groq').value;
    const openrouter = document.getElementById('key-openrouter').value;
    
    const btn = document.getElementById('btn-save-keys');
    const status = document.getElementById('keys-status');
    
    btn.disabled = true;
    btn.innerText = 'Enregistrement...';
    
    fetch('/api/models/keys/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            gemini: gemini,
            groq: groq,
            openrouter: openrouter
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = '💾 Sauvegarder les Clés';
        
        if (data.status === 'ok') {
            status.innerHTML = '<span style="color: #00ff88">✓ Clés enregistrées!</span>';
        } else {
            status.innerHTML = `<span style="color: #ff4444">✗ Erreur</span>`;
        }
    });
}

document.getElementById('btn-load-api').addEventListener('click', loadApiModels);

function loadApiModels() {
    const leftProvider = document.getElementById('api-left-model').value;
    const rightProvider = document.getElementById('api-right-model').value;
    
    if (!leftProvider) {
        alert('Sélectionnez au moins un provider!');
        return;
    }
    
    const btn = document.getElementById('btn-load-api');
    const status = document.getElementById('api-load-status');
    
    btn.disabled = true;
    btn.innerText = '⏳ Activation...';
    status.innerHTML = '<div class="loading">Activation des APIs...</div>';
    
    fetch('/api/models/load', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            left_path: leftProvider,
            right_path: rightProvider === 'EMPTY' ? null : rightProvider,
            method: 'api'
        })
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = '⚡ Activer les APIs';
        
        if (data.status === 'ok') {
            status.innerHTML = '<div class="success">✓ APIs activées!</div>';
            checkModelsStatus();
        } else {
            status.innerHTML = `<div class="error">✗ ${data.error || 'Erreur'}</div>`;
        }
    });
}

// ============ STYLES ============

const style = document.createElement('style');
style.textContent = `
    .status-ok { color: #00ff88; }
    .status-wait { color: #ffaa00; }
    .status-info { color: #888; font-size: 12px; }
    
    .hidden { display: none !important; }
    
    .loading { color: #00d4ff; }
    
    .success { color: #00ff88; background: rgba(0,255,136,0.1); padding: 12px; border-radius: 6px; }
    .error { color: #ff4444; background: rgba(255,68,68,0.1); padding: 12px; border-radius: 6px; }
    
    .btn-primary { background: #00d4ff; color: #000; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
    .btn-primary:hover { background: #00aacc; }
    .btn-primary:disabled { background: #555; cursor: not-allowed; }
    
    .btn-secondary { background: #333; color: #fff; border: 1px solid #555; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
    .btn-secondary:hover { background: #444; }
    .btn-secondary:disabled { background: #222; cursor: not-allowed; }
`;
document.head.appendChild(style);

// ============ HARDWARE SETTINGS ============

let hardwareConfig = {
    n_gpu_layers: -1,
    n_threads: 0,
    os_vram_reserve: 2.0,
    kv_cache_reserve: 1.5,
    use_mmap: true,
    use_mlock: false
};

function initHardwareSettings() {
    fetchHardwareTopology();
    loadHardwareConfig();
    initHardwareSliders();
}

function fetchHardwareTopology() {
    fetch('/api/hardware/topology')
        .then(r => r.json())
        .then(data => {
            const div = document.getElementById('hardware-topology');
            if (div) {
                div.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                        <div>🖥️ <strong>CPU:</strong> ${data.cpu_threads || '?'} threads</div>
                        <div>💾 <strong>RAM:</strong> ${data.ram_gb?.toFixed(1) || '?'} Go</div>
                        <div>🎮 <strong>VRAM:</strong> ${data.vram_gb?.toFixed(1) || '?'} Go</div>
                    </div>
                `;
            }
        })
        .catch(() => {
            const div = document.getElementById('hardware-topology');
            if (div) div.innerHTML = '<p style="color: #ff4444">Erreur chargement topologie</p>';
        });
}

function loadHardwareConfig() {
    fetch('/api/hardware/config')
        .then(r => r.json())
        .then(data => {
            if (data.config) {
                hardwareConfig = {...hardwareConfig, ...data.config};
                updateSliderDisplays();
            }
        });
}

function initHardwareSliders() {
    const gpuSlider = document.getElementById('gpu-layers-slider');
    const cpuSlider = document.getElementById('cpu-threads-slider');
    const vramSlider = document.getElementById('vram-reserve-slider');
    const kvSlider = document.getElementById('kv-cache-slider');
    
    if (gpuSlider) {
        gpuSlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            document.getElementById('gpu-layers-value').textContent = val === -1 ? 'Auto' : val;
            hardwareConfig.n_gpu_layers = val;
        });
    }
    
    if (cpuSlider) {
        cpuSlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            document.getElementById('cpu-threads-value').textContent = val === 0 ? 'Auto' : val;
            hardwareConfig.n_threads = val;
        });
    }
    
    if (vramSlider) {
        vramSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            document.getElementById('vram-reserve-value').textContent = val.toFixed(1) + ' Go';
            hardwareConfig.os_vram_reserve = val;
        });
    }
    
    if (kvSlider) {
        kvSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            document.getElementById('kv-cache-value').textContent = val.toFixed(1) + ' Go';
            hardwareConfig.kv_cache_reserve = val;
        });
    }
    
    document.getElementById('use-mmap').addEventListener('change', (e) => {
        hardwareConfig.use_mmap = e.target.checked;
    });
    
    document.getElementById('use-mlock').addEventListener('change', (e) => {
        hardwareConfig.use_mlock = e.target.checked;
    });
    
    document.getElementById('btn-save-hardware').addEventListener('click', saveHardwareConfig);
}

function updateSliderDisplays() {
    const gpuSlider = document.getElementById('gpu-layers-slider');
    const cpuSlider = document.getElementById('cpu-threads-slider');
    const vramSlider = document.getElementById('vram-reserve-slider');
    const kvSlider = document.getElementById('kv-cache-slider');
    
    if (gpuSlider) {
        gpuSlider.value = hardwareConfig.n_gpu_layers;
        document.getElementById('gpu-layers-value').textContent = 
            hardwareConfig.n_gpu_layers === -1 ? 'Auto' : hardwareConfig.n_gpu_layers;
    }
    if (cpuSlider) {
        cpuSlider.value = hardwareConfig.n_threads;
        document.getElementById('cpu-threads-value').textContent = 
            hardwareConfig.n_threads === 0 ? 'Auto' : hardwareConfig.n_threads;
    }
    if (vramSlider) {
        vramSlider.value = hardwareConfig.os_vram_reserve;
        document.getElementById('vram-reserve-value').textContent = 
            hardwareConfig.os_vram_reserve.toFixed(1) + ' Go';
    }
    if (kvSlider) {
        kvSlider.value = hardwareConfig.kv_cache_reserve;
        document.getElementById('kv-cache-value').textContent = 
            hardwareConfig.kv_cache_reserve.toFixed(1) + ' Go';
    }
    
    document.getElementById('use-mmap').checked = hardwareConfig.use_mmap;
    document.getElementById('use-mlock').checked = hardwareConfig.use_mlock;
}

function saveHardwareConfig() {
    const btn = document.getElementById('btn-save-hardware');
    const status = document.getElementById('hardware-status');
    
    btn.disabled = true;
    btn.innerText = 'Sauvegarde...';
    
    fetch('/api/hardware/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(hardwareConfig)
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        btn.innerText = '💾 Sauvegarder la Configuration';
        
        if (data.status === 'ok') {
            status.innerHTML = '<span style="color: #00ff88">✓ Configuration sauvegardée!</span>';
        } else {
            status.innerHTML = `<span style="color: #ff4444">✗ Erreur</span>`;
        }
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerText = '💾 Sauvegarder la Configuration';
        status.innerHTML = `<span style="color: #ff4444">✗ Erreur: ${err.message}</span>`;
    });
}

// Initialize hardware settings when tab is shown
document.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        if (btn.dataset.subtab === 'hardware') {
            setTimeout(initHardwareSettings, 100);
        }
    });
});
