class LabApp {
    constructor() {
        this.modules = [];
        this.activeModule = null;
        this.moduleTabs = document.getElementById('lab-module-tabs');
        this.moduleViewport = document.getElementById('lab-module-viewport');
    }

    async init() {
        try {
            const response = await fetch('/api/lab/modules');
            const data = await response.json();
            this.modules = data.modules || [];
            this.renderTabs();
            if (this.modules.length > 0) {
                this.selectModule(this.modules[0].id);
            }
        } catch (e) {
            console.error('Failed to load lab modules:', e);
            if (this.moduleViewport) {
                this.moduleViewport.innerHTML = '<div class="error-message">Failed to load modules</div>';
            }
        }
    }

    renderTabs() {
        if (!this.moduleTabs) return;
        this.moduleTabs.innerHTML = '';
        this.modules.forEach(mod => {
            const btn = document.createElement('button');
            btn.className = 'tab-btn';
            btn.dataset.moduleId = mod.id;
            btn.innerHTML = `<span class="tab-icon">${mod.icon}</span><span>${mod.name}</span>`;
            btn.addEventListener('click', () => this.selectModule(mod.id));
            this.moduleTabs.appendChild(btn);
        });
    }

    selectModule(moduleId) {
        this.activeModule = moduleId;
        if (this.moduleTabs) {
            this.moduleTabs.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.moduleId === moduleId);
            });
        }
        this.renderModuleViewport(moduleId);
    }

    renderModuleViewport(moduleId) {
        const mod = this.modules.find(m => m.id === moduleId);
        if (!mod || !this.moduleViewport) return;

        let html = `<div class="module-container">`;
        html += `<div class="module-header"><h3>${mod.icon} ${mod.name}</h3><p>${mod.description}</p></div>`;
        html += `<div class="module-form">`;

        const schema = mod.settings_schema || {};
        for (const [key, field] of Object.entries(schema)) {
            html += `<div class="form-group">`;
            html += `<label for="field-${key}">${field.label || key}</label>`;

            if (field.type === 'textarea') {
                html += `<textarea id="field-${key}" rows="4">${field.default || ''}</textarea>`;
            } else if (field.type === 'range') {
                html += `<input type="range" id="field-${key}" min="${field.min || 0}" max="${field.max || 100}" value="${field.default || 50}">`;
                html += `<span class="range-value" id="range-value-${key}">${field.default || 50}</span>`;
            } else if (field.type === 'select') {
                html += `<select id="field-${key}">`;
                (field.options || []).forEach(opt => {
                    html += `<option value="${opt}" ${opt === field.default ? 'selected' : ''}>${opt}</option>`;
                });
                html += `</select>`;
            } else if (field.type === 'checkbox') {
                html += `<input type="checkbox" id="field-${key}" ${field.default ? 'checked' : ''}>`;
            } else {
                html += `<input type="text" id="field-${key}" value="${field.default || ''}">`;
            }

            html += `</div>`;
        }

        html += `<button class="btn-primary" onclick="window.labApp.executeModule('${moduleId}')">Execute</button>`;
        html += `</div></div>`;

        this.moduleViewport.innerHTML = html;

        this.moduleViewport.querySelectorAll('input[type="range"]').forEach(input => {
            const key = input.id.replace('field-', '');
            const valueSpan = document.getElementById(`range-value-${key}`);
            if (valueSpan) {
                input.addEventListener('input', () => {
                    valueSpan.textContent = input.value;
                });
            }
        });
    }

    executeModule(moduleId) {
        const mod = this.modules.find(m => m.id === moduleId);
        if (!mod) return;

        const settings = {};
        const schema = mod.settings_schema || {};
        for (const [key, field] of Object.entries(schema)) {
            const el = document.getElementById(`field-${key}`);
            if (!el) continue;
            if (field.type === 'checkbox') {
                settings[key] = el.checked;
            } else if (field.type === 'range') {
                settings[key] = parseInt(el.value, 10);
            } else {
                settings[key] = el.value;
            }
        }

        const payload = {
            message: "INIT",
            settings: {
                lab_mode: moduleId,
                ...settings
            }
        };

        if (window.Bicameris) {
            window.Bicameris.update('mode', moduleId);
        }

        fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            function read() {
                reader.read().then(({ done, value }) => {
                    if (done) return;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop();
                    lines.forEach(line => {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                console.log('[Lab]', data);
                                if (data.phase && window.Bicameris) {
                                    window.Bicameris.update('inferenceState', data.phase);
                                }
                            } catch (e) {}
                        }
                    });
                    read();
                });
            }
            read();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.labApp = new LabApp();
    window.labApp.init();
});
