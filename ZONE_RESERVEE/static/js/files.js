// Files functionality
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        // Show corresponding panel
        const tabId = this.dataset.tab;
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById('panel-' + tabId).classList.add('active');
    });
});

// Save buttons
document.querySelectorAll('[data-save]').forEach(btn => {
    btn.addEventListener('click', function() {
        const fileType = this.dataset.save;
        let content = '';
        let filename = '';
        
        switch(fileType) {
            case 'journal':
                content = document.getElementById('journal-editor').value;
                filename = 'journal';
                break;
            case 'seed':
                content = document.getElementById('seed-editor').value;
                filename = 'seed';
                break;
            case 'config':
                content = document.getElementById('config-editor').value;
                filename = 'config';
                break;
            case 'tasks':
                content = document.getElementById('tasks-editor').value;
                filename = 'tasks';
                break;
        }
        
        fetch('/api/save_file', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                filename: filename,
                content: content
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'saved') {
                alert('Fichier sauvegardé!');
            } else if (data.error) {
                alert('Erreur: ' + data.error);
            }
        });
    });
});
