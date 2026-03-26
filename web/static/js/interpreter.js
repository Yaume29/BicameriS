// Real-time Interpreter for Bicameral Brain Activity
class BrainInterpreter {
    constructor() {
        this.feedEl = document.getElementById('interpreter-feed');
        this.statusText = document.getElementById('interpreter-status-text');
        this.filter = 'all';
        this.maxItems = 50;
        this.lastTimestamp = null;
        this.init();
    }

    init() {
        if (!this.feedEl) return;
        
        // Setup filters
        document.querySelectorAll('.filter-badge').forEach(badge => {
            badge.addEventListener('click', () => {
                document.querySelectorAll('.filter-badge').forEach(b => b.classList.remove('active'));
                badge.classList.add('active');
                this.filter = badge.dataset.type;
                this.refreshDisplay();
            });
        });

        // Start polling
        this.poll();
        setInterval(() => this.poll(), 3000);
    }

    async poll() {
        try {
            // We fetch from multiple sources to reconstruct the "brain activity"
            // 1. Thoughts (autonomous_thinker)
            // 2. Flux logs (flux_logger)
            // 3. Corps Calleux history
            
            const [thoughtsRes, logsRes] = await Promise.all([
                fetch('/api/think/history?limit=10'),
                fetch('/api/logs?limit=20')
            ]);
            
            const thoughts = await thoughtsRes.json();
            const logs = await logsRes.json();
            
            this.processData(thoughts, logs);
        } catch (error) {
            this.statusText.textContent = 'Erreur de connexion';
        }
    }

    processData(thoughts, logs) {
        let items = [];

        // Process thoughts
        thoughts.forEach(t => {
            items.push({
                type: 'thought',
                label: 'Pensée Autonome',
                content: t.thought,
                timestamp: t.timestamp,
                raw: t
            });
        });

        // Process logs (filtering system messages)
        logs.forEach(l => {
            let type = 'system';
            let label = 'Système';
            
            if (l.type === 'PENSEE') {
                type = 'thought';
                label = 'Flux Pensée';
            } else if (l.message.includes('Corps Calleux') || l.message.includes('Inter-hémisphérique')) {
                type = 'corps';
                label = 'Corps Calleux';
            } else if (l.message.includes('Hémisphère Gauche')) {
                type = 'left';
                label = 'Logique (L)';
            } else if (l.message.includes('Hémisphère Droit')) {
                type = 'right';
                label = 'Intuition (R)';
            } else if (l.type === 'ACTION' || l.type === 'SHELL') {
                type = 'action';
                label = 'Action';
            } else {
                // Skip generic system messages if they are too boring
                if (l.message.includes('Initialisation') || l.message.includes('Check')) return;
            }

            items.push({
                type: type,
                label: label,
                content: l.message,
                timestamp: l.timestamp,
                raw: l
            });
        });

        // Sort by timestamp
        items.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Filter out duplicates (simple check)
        const uniqueItems = [];
        const seen = new Set();
        items.forEach(item => {
            const key = item.content.substring(0, 50) + item.timestamp;
            if (!seen.has(key)) {
                seen.add(key);
                uniqueItems.push(item);
            }
        });

        this.updateDisplay(uniqueItems.slice(0, this.maxItems));
    }

    updateDisplay(items) {
        if (items.length === 0) return;

        // Filter by current selection
        const filtered = items.filter(item => {
            if (this.filter === 'all') return true;
            if (this.filter === 'thought') return item.type === 'thought';
            if (this.filter === 'corps') return item.type === 'corps';
            if (this.filter === 'hemisphere') return ['left', 'right'].includes(item.type);
            return false;
        });

        this.feedEl.innerHTML = filtered.map(item => `
            <div class="feed-item type-${item.type}">
                <div class="item-header">
                    <span class="item-label">${item.label}</span>
                    <span class="item-time">${this.formatTime(item.timestamp)}</span>
                </div>
                <div class="item-content">${this.escapeHtml(item.content)}</div>
            </div>
        `).join('');

        this.statusText.textContent = 'En direct';
    }

    refreshDisplay() {
        // Re-run the last data if we had it, or just wait for next poll
        this.poll();
    }

    formatTime(ts) {
        const date = new Date(ts);
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new BrainInterpreter();
});
