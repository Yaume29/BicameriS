/**
 * BICAMERIS - Settings Manager
 * Handles settings page rendering and theme selection UI
 */

class SettingsManager {
  constructor() {
    this.settingsContainer = document.getElementById('settings-content');
    this.init();
  }

  init() {
    if (this.settingsContainer) {
      this.render();
    }
    
    // Listen for tab changes to render settings when shown
    document.addEventListener('DOMContentLoaded', () => {
      const tabButtons = document.querySelectorAll('.tab-btn');
      tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          if (btn.dataset.tab === 'settings') {
            this.render();
          }
        });
      });
    });
  }

  render() {
    if (!this.settingsContainer) return;
    
    const currentTheme = window.themeSwitcher?.getCurrentTheme();
    const themes = window.themeSwitcher?.getThemes() || [];
    
    this.settingsContainer.innerHTML = `
      <div class="settings-section">
        <h2 class="settings-title">Paramètres</h2>
        
        <!-- Theme Selection -->
        <div class="settings-group">
          <h3 class="settings-group-title">Thème</h3>
          <p class="settings-group-desc">Choisissez l'apparence de l'interface</p>
          
          <div class="theme-grid">
            ${themes.map(theme => `
              <button class="theme-card ${currentTheme?.id === theme.id ? 'active' : ''}" 
                      data-theme-id="${theme.id}"
                      onclick="selectTheme('${theme.id}')">
                <div class="theme-preview theme-preview-${theme.id}"></div>
                <div class="theme-info">
                  <div class="theme-name">${theme.name}</div>
                  <div class="theme-desc">${theme.description}</div>
                </div>
                ${currentTheme?.id === theme.id ? '<div class="theme-check">✓</div>' : ''}
              </button>
            `).join('')}
          </div>
        </div>

        <!-- Appearance Settings -->
        <div class="settings-group">
          <h3 class="settings-group-title">Apparence</h3>
          
          <div class="setting-row">
            <div class="setting-label">
              <span class="setting-name">Animations</span>
              <span class="setting-desc">Activer les animations du cerveau</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" id="setting-animations" checked>
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-row">
            <div class="setting-label">
              <span class="setting-name">Graphique d'entropie</span>
              <span class="setting-desc">Afficher le graphique d'entropie</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" id="setting-entropy" checked>
              <span class="toggle-slider"></span>
            </label>
          </div>
          
          <div class="setting-row">
            <div class="setting-label">
              <span class="setting-name">Indicateur de pulse</span>
              <span class="setting-desc">Afficher la valeur du pulse</span>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" id="setting-pulse" checked>
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <!-- Model Settings -->
        <div class="settings-group">
          <h3 class="settings-group-title">Modèles</h3>
          
          <div class="setting-row">
            <div class="setting-label">
              <span class="setting-name">Hémisphère gauche</span>
              <span class="setting-desc" id="left-model-desc">Non configuré</span>
            </div>
            <button class="btn-secondary" onclick="configureModel('left')">Configurer</button>
          </div>
          
          <div class="setting-row">
            <div class="setting-label">
              <span class="setting-name">Hémisphère droit</span>
              <span class="setting-desc" id="right-model-desc">Non configuré</span>
            </div>
            <button class="btn-secondary" onclick="configureModel('right')">Configurer</button>
          </div>
        </div>

        <!-- About -->
        <div class="settings-group">
          <h3 class="settings-group-title">À propos</h3>
          <div class="about-info">
            <p><strong>BicameriS</strong> v1.0.0.6a</p>
            <p>Système cognitif bicaméral</p>
            <p class="text-muted">Par Hope 'n Mind</p>
          </div>
        </div>
      </div>
    `;
    
    // Add styles for settings
    this.addStyles();
  }

  addStyles() {
    if (document.getElementById('settings-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'settings-styles';
    style.textContent = `
      .settings-section {
        padding: 20px;
        max-width: 800px;
      }
      
      .settings-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 24px;
        color: var(--text-primary);
      }
      
      .settings-group {
        margin-bottom: 32px;
        padding: 20px;
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border-subtle);
      }
      
      .settings-group-title {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--text-primary);
      }
      
      .settings-group-desc {
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: 16px;
      }
      
      /* Theme Grid */
      .theme-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 12px;
      }
      
      .theme-card {
        background: var(--bg-tertiary);
        border: 2px solid var(--border-subtle);
        border-radius: 12px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      
      .theme-card:hover {
        border-color: var(--border-accent);
        transform: translateY(-2px);
      }
      
      .theme-card.active {
        border-color: var(--accent-cyan);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
      }
      
      .theme-preview {
        height: 60px;
        border-radius: 8px;
        background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
      }
      
      .theme-preview-dark-cyberpunk {
        background: linear-gradient(135deg, #08080f, #00d4ff 50%, #ff006e 100%);
      }
      
      .theme-preview-matrix-green {
        background: linear-gradient(135deg, #0a0f0a, #00ff41 50%, #39ff14 100%);
      }
      
      .theme-preview-warm-ember {
        background: linear-gradient(135deg, #1a0f0a, #f59e0b 50%, #ff6b35 100%);
      }
      
      .theme-info {
        flex: 1;
      }
      
      .theme-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
      }
      
      .theme-desc {
        font-size: 11px;
        color: var(--text-secondary);
      }
      
      .theme-check {
        color: var(--accent-cyan);
        font-size: 18px;
      }
      
      /* Setting Rows */
      .setting-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0;
        border-bottom: 1px solid var(--border-subtle);
      }
      
      .setting-row:last-child {
        border-bottom: none;
      }
      
      .setting-label {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      
      .setting-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--text-primary);
      }
      
      .setting-desc {
        font-size: 12px;
        color: var(--text-secondary);
      }
      
      /* Toggle Switch */
      .toggle-switch {
        position: relative;
        width: 44px;
        height: 24px;
      }
      
      .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }
      
      .toggle-slider {
        position: absolute;
        cursor: pointer;
        inset: 0;
        background: var(--bg-tertiary);
        border-radius: 24px;
        transition: 0.2s;
        border: 1px solid var(--border-subtle);
      }
      
      .toggle-slider::before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 2px;
        bottom: 2px;
        background: var(--text-secondary);
        border-radius: 50%;
        transition: 0.2s;
      }
      
      .toggle-switch input:checked + .toggle-slider {
        background: var(--accent-cyan);
        border-color: var(--accent-cyan);
      }
      
      .toggle-switch input:checked + .toggle-slider::before {
        transform: translateX(20px);
        background: white;
      }
      
      /* Buttons */
      .btn-secondary {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-accent);
        color: var(--text-primary);
        padding: 8px 16px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 13px;
        transition: all 0.2s;
      }
      
      .btn-secondary:hover {
        background: var(--bg-hover);
        border-color: var(--accent-cyan);
      }
      
      /* About */
      .about-info {
        font-size: 14px;
        color: var(--text-secondary);
        line-height: 1.8;
      }
      
      .about-info strong {
        color: var(--text-primary);
      }
    `;
    document.head.appendChild(style);
  }
}

// Global functions for theme selection
function selectTheme(themeId) {
  if (window.themeSwitcher) {
    window.themeSwitcher.loadTheme(themeId);
    
    // Update UI
    document.querySelectorAll('.theme-card').forEach(card => {
      card.classList.toggle('active', card.dataset.themeId === themeId);
      const check = card.querySelector('.theme-check');
      if (check) check.remove();
      if (card.dataset.themeId === themeId) {
        card.insertAdjacentHTML('beforeend', '<div class="theme-check">✓</div>');
      }
    });
  }
}

function configureModel(hemisphere) {
  // TODO: Open model configuration modal
  console.log('Configure model:', hemisphere);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  window.settingsManager = new SettingsManager();
});
