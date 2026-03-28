// Think page functionality

function loadThoughts() {
    fetch('/api/cognitive/thoughts?limit=30')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(thoughts => {
            const container = document.getElementById('thoughts-list');
            if (container) {
                if (thoughts.length === 0) {
                    container.innerHTML = '<p class="no-data">Aucune réflexion pour le moment</p>';
                } else {
                    container.innerHTML = thoughts.map(t => `
                        <div class="thought-item">
                            <span class="thought-time">${t.timestamp.split('T')[1].split('.')[0]}</span>
                            <span class="thought-type">${t.type}</span>
                            <p class="thought-text">${t.content}</p>
                            ${t.continued_from ? '<span class="chain-link">↩️ Suite de...</span>' : ''}
                            ${t.continues_to ? '<span class="chain-link">↪️ Continue vers...</span>' : ''}
                        </div>
                    `).join('');
                }
            }
            
            // Update last thought
            if (thoughts.length > 0) {
                const last = thoughts[thoughts.length - 1];
                const lastDiv = document.getElementById('last-thought');
                if (lastDiv) {
                    lastDiv.innerHTML = `
                        <p class="thought-timestamp">${last.timestamp}</p>
                        <p class="thought-content">${last.content}</p>
                    `;
                }
            }
        })
        .catch(err => console.error('Erreur chargement pensées:', err));
        
    // Update stats (separate to not block thoughts load)
    fetch('/api/cognitive/stats')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            const statusSpan = document.getElementById('think-status');
            if (statusSpan && data.thinker) {
                statusSpan.textContent = data.thinker.is_thinking ? 'Actif' : 'Inactif';
            }
        })
        .catch(err => console.error('Erreur stats:', err));
}

// Start thinking
document.getElementById('start-think').addEventListener('click', function() {
    this.disabled = true;
    fetch('/api/cognitive/think/start', {method: 'POST'})
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            document.getElementById('think-status').textContent = 'Actif';
        })
        .catch(err => console.error('Erreur:', err))
        .finally(() => this.disabled = false);
});

// Stop thinking
document.getElementById('stop-think').addEventListener('click', function() {
    this.disabled = true;
    fetch('/api/cognitive/think/stop', {method: 'POST'})
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            document.getElementById('think-status').textContent = 'Inactif';
        })
        .catch(err => console.error('Erreur:', err))
        .finally(() => this.disabled = false);
});

// Interval change
document.getElementById('interval').addEventListener('input', function(e) {
    document.getElementById('interval-value').textContent = e.target.value;
});

document.getElementById('interval').addEventListener('change', function(e) {
    fetch('/api/cognitive/think/set_interval', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({interval: parseInt(e.target.value)})
    })
    .catch(err => console.error('Erreur intervalle:', err));
});

// Trigger thought manually
document.getElementById('trigger-think').addEventListener('click', function() {
    this.disabled = true;
    this.textContent = 'Réfléchit...';
    
    fetch('/api/cognitive/think', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: '', context: ''})
    })
    .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    })
    .then(data => {
        loadThoughts();
    })
    .catch(err => console.error('Erreur:', err))
    .finally(() => {
        this.disabled = false;
        this.textContent = '⚡ Réfléchir maintenant';
    });
});

// Refresh
document.getElementById('refresh-thoughts').addEventListener('click', function() {
    this.disabled = true;
    loadThoughts();
    setTimeout(() => this.disabled = false, 500);
});

// Load on init
loadThoughts();

// Auto-refresh every 5s
setInterval(loadThoughts, 5000);
