// Dashboard functionality
function loadStats() {
    fetch('/api/stats')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            const fluxStats = document.getElementById('flux-stats');
            if (fluxStats && data.flux && data.flux.by_type) {
                let html = '';
                for (const [type, count] of Object.entries(data.flux.by_type)) {
                    html += `<div class="stat-item"><span>${type}</span><span>${count}</span></div>`;
                }
                fluxStats.innerHTML = html;
            }
        })
        .catch(err => console.error('Erreur stats:', err));
        
    // Load errors separately
    const errorsDiv = document.getElementById('recent-errors');
    if (errorsDiv) {
        fetch('/api/logs?type=ERREUR&limit=5')
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(logs => {
                if (!logs || logs.length === 0) {
                    errorsDiv.innerHTML = '<p class="no-data">Aucune erreur récente</p>';
                } else {
                    errorsDiv.innerHTML = logs.map(l => 
                        `<div class="error-item">${l.timestamp} - ${l.message}</div>`
                    ).join('');
                }
            })
            .catch(() => errorsDiv.innerHTML = '<p class="no-data">Aucune erreur récente</p>');
    }
}

function loadEntropy() {
    fetch('/api/entropy')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            const pulse = data.pulse || 0;
            const cpuLoad = data.cpu_load || 0;
            const ramLoad = data.ram_load || 0;
            const gpu = data.gpu || {};
            const vramPercent = gpu.vram_percent || 0;
            const mood = data.mood || 'UNKNOWN';

            // Update pulse gauge
            const pulseDisplay = document.getElementById('pulse-display');
            if (pulseDisplay) pulseDisplay.textContent = pulse.toFixed(2);

            const entropyArc = document.getElementById('entropy-arc');
            if (entropyArc) {
                const circumference = 251.2;
                const offset = circumference * (1 - pulse);
                entropyArc.style.strokeDashoffset = offset;
            }

            // Update bars
            const cpuBar = document.getElementById('cpu-bar');
            const ramBar = document.getElementById('ram-bar');
            const vramBar = document.getElementById('vram-bar');
            const cpuVal = document.getElementById('cpu-val');
            const ramVal = document.getElementById('ram-val');
            const vramVal = document.getElementById('vram-val');

            if (cpuBar) cpuBar.style.width = `${cpuLoad * 100}%`;
            if (ramBar) ramBar.style.width = `${ramLoad * 100}%`;
            if (vramBar) vramBar.style.width = `${vramPercent * 100}%`;
            if (cpuVal) cpuVal.textContent = `${(cpuLoad * 100).toFixed(0)}%`;
            if (ramVal) ramVal.textContent = `${(ramLoad * 100).toFixed(0)}%`;
            if (vramVal) vramVal.textContent = `${(vramPercent * 100).toFixed(0)}%`;

            // Update mood badge
            const moodDisplay = document.getElementById('mood-display');
            if (moodDisplay) {
                const moodClasses = {
                    'REPOS': 'mood-calm',
                    'ACTIF': 'mood-normal',
                    'CHARGE': 'mood-high',
                    'STRESS': 'mood-critical'
                };
                moodDisplay.innerHTML = `<span class="mood-badge ${moodClasses[mood] || ''}">${mood}</span>`;
            }
        })
        .catch(err => console.error('Erreur entropy:', err));
}

function loadMemory() {
    fetch('/api/memory/stats')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            if (data.error) return;
            
            const totalEl = document.getElementById('mem-total');
            const embedEl = document.getElementById('mem-embedding-type');
            const cloudEl = document.getElementById('concept-cloud');
            
            if (totalEl) totalEl.textContent = data.total_memories || 0;
            if (embedEl) embedEl.textContent = data.sentence_transformers ? 'ST' : 'Hash';
            
            if (cloudEl && data.top_concepts) {
                const concepts = Object.entries(data.top_concepts);
                cloudEl.innerHTML = concepts.map(([concept, count]) => 
                    `<span class="concept-tag" style="font-size: ${12 + count * 2}px">${concept}</span>`
                ).join('');
            }
        })
        .catch(err => console.error('Erreur mémoire:', err));
    
    fetch('/api/memory/summary?hours=24')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            const recentEl = document.getElementById('memory-recent');
            if (recentEl && data.summary) {
                recentEl.innerHTML = `<p class="memory-summary">${data.summary.replace(/\n/g, '<br>')}</p>`;
            }
        })
        .catch(err => console.error('Erreur summary:', err));
}

loadStats();
loadEntropy();
loadMemory();

// Polling intervals - reduced entropy to 5s to avoid overload
function loadAgents() {
    fetch('/api/agents')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            if (data.error) {
                document.getElementById('agents-list').innerHTML = '<p class="no-data">Agent Manager non disponible</p>';
                return;
            }
            
            document.getElementById('vram-status').textContent = 
                `VRAM: ${data.vram?.available_mb || '?'}MB libre`;
            
            const agents = Object.values(data.agents || {});
            if (agents.length === 0) {
                document.getElementById('agents-list').innerHTML = '<p class="no-data">Aucun agent chargé</p>';
                return;
            }
            
            document.getElementById('agents-list').innerHTML = agents.map(agent => `
                <div class="agent-item">
                    <span class="agent-name">${agent.name}</span>
                    <span class="agent-type ${agent.type}">${agent.type}</span>
                    <span class="agent-vram">${agent.vram_estimate_mb}MB</span>
                </div>
            `).join('');
        })
        .catch(err => {
            document.getElementById('agents-list').innerHTML = '<p class="no-data">Erreur chargement agents</p>';
        });
    
    fetch('/api/agents/providers')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(providers => {
            document.getElementById('providers-list').innerHTML = providers.map(p => `
                <div class="provider-item ${p.available ? 'available' : 'unavailable'}">
                    <span class="provider-name">${p.name}</span>
                    <span class="provider-status">${p.available ? '✅ Configuré' : '❌ Non configuré'}</span>
                    <span class="provider-rate">${p.rate_limit}</span>
                </div>
            `).join('');
        })
        .catch(() => {});
}

document.getElementById('save-api-key')?.addEventListener('click', function() {
    const provider = document.getElementById('provider-select').value;
    const apiKey = document.getElementById('api-key-input').value;
    
    if (!provider) {
        alert('Sélectionne un provider');
        return;
    }
    if (!apiKey) {
        alert('Entre une API key');
        return;
    }
    
    this.disabled = true;
    this.textContent = '⏳ Configuration...';
    
    fetch('/api/agents/configure', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({provider, api_key: apiKey})
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`✅ ${provider} configuré avec succès!`);
            document.getElementById('api-key-input').value = '';
            loadAgents();
        } else {
            alert('Erreur: ' + (data.error || 'Unknown'));
        }
    })
    .catch(err => alert('Erreur: ' + err.message))
    .finally(() => {
        this.disabled = false;
        this.textContent = '💾 Configurer';
    });
});

document.getElementById('refresh-agents')?.addEventListener('click', loadAgents);

loadAgents();

setInterval(loadStats, 5000);
setInterval(loadEntropy, 5000);
setInterval(loadMemory, 10000);
setInterval(loadAgents, 30000);
