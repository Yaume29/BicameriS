// Tasks & Flux functionality
function loadFlux() {
    const filterType = document.getElementById('filter-type').value;
    
    fetch(`/api/logs?type=${filterType}&limit=100`)
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(logs => {
            const container = document.getElementById('flux-list');
            if (container) {
                if (logs.length === 0) {
                    container.innerHTML = '<p class="no-data">Aucun flux pour le moment</p>';
                } else {
                    container.innerHTML = logs.map(log => `
                        <div class="flux-item">
                            <span class="flux-time">${log.timestamp.split('T')[1] ? log.timestamp.split('T')[1].split('.')[0] : ''}</span>
                            <span class="flux-icon">${log.icon || ''}</span>
                            <span class="flux-message">${log.message || ''}</span>
                        </div>
                    `).join('');
                }
            }
        })
        .catch(err => console.error('Erreur flux:', err));
    
    // Load by type stats
    fetch('/api/logs_by_type')
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            const container = document.getElementById('flux-by-type');
            if (container) {
                let html = '<h4>Par Type</h4>';
                for (const [type, count] of Object.entries(data)) {
                    html += `<div class="stat-item"><span>${type}</span><span>${count}</span></div>`;
                }
                container.innerHTML = html;
            }
        })
        .catch(err => console.error('Erreur stats flux:', err));
}

document.getElementById('filter-type').addEventListener('change', loadFlux);
document.getElementById('refresh-flux').addEventListener('click', function() {
    this.disabled = true;
    loadFlux();
    setTimeout(() => this.disabled = false, 500);
});

// Load on init
loadFlux();

// Auto-refresh every 3s
setInterval(loadFlux, 3000);
