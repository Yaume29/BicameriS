/**
 * BICAMERIS - UI Manager
 * Single Page Application controller
 * 
 * Zero page reloads. Continuous stream of consciousness.
 */

class UIManager {
    constructor() {
        this.currentPanel = 'home';
        this.panels = new Map();
        this.streamController = null;
        
        // UI Elements cache
        this.elements = {};
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize UI Manager
     */
    init() {
        // Cache DOM elements
        this.cacheElements();
        
        // Register panels
        this.registerPanels();
        
        // Setup navigation
        this.setupNavigation();
        
        // Initialize brain SVG
        this.initBrainSVG();
        
        // Connect to stream controller
        this.connectStreamController();
        
        console.log('[UIManager] Initialized');
    }
    
    /**
     * Cache frequently used DOM elements
     */
    cacheElements() {
        this.elements = {
            // Brain SVG
            brainLeft: document.getElementById('brain-left'),
            brainRight: document.getElementById('brain-right'),
            corpusCallosum: document.getElementById('corpus-callosum'),
            
            // Status displays
            statusMain: document.getElementById('brain-status-main'),
            statusMeta: document.getElementById('brain-status-meta'),
            
            // Metrics
            pulseValue: document.getElementById('pulse-value'),
            cyclesValue: document.getElementById('cycles-value'),
            modelStatus: document.getElementById('model-status'),
            
            // Activity dots
            activityDots: document.querySelectorAll('.activity-dot'),
            
            // Panels container
            panelsContainer: document.getElementById('panels-container'),
            
            // Sidebar
            sidebar: document.querySelector('.sidebar'),
            
            // Navigation
            navItems: document.querySelectorAll('.nav-item')
        };
    }
    
    /**
     * Register all panels
     */
    registerPanels() {
        const panelIds = ['home', 'chat', 'unified', 'models', 'inception', 
                         'laboratoire', 'think', 'tasks', 'files', 'dashboard',
                         'research', 'settings', 'launcher'];
        
        for (const id of panelIds) {
            const panel = document.getElementById(`panel-${id}`);
            if (panel) {
                this.panels.set(id, panel);
            }
        }
    }
    
    /**
     * Setup navigation click handlers
     */
    setupNavigation() {
        for (const item of this.elements.navItems) {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                
                const target = item.getAttribute('data-panel') || 
                              item.getAttribute('href')?.replace('/', '') || 
                              'home';
                
                this.showPanel(target);
            });
        }
    }
    
    /**
     * Show a specific panel (no page reload!)
     */
    showPanel(panelId) {
        // Hide all panels
        for (const [id, panel] of this.panels) {
            panel.style.display = 'none';
            panel.classList.remove('active');
        }
        
        // Show target panel
        const targetPanel = this.panels.get(panelId);
        if (targetPanel) {
            targetPanel.style.display = 'grid';  // Use CSS Grid
            targetPanel.classList.add('active');
            this.currentPanel = panelId;
            
            // Update navigation highlighting
            this.updateNavHighlight(panelId);
            
            // Update URL without reload (History API)
            history.pushState({ panel: panelId }, '', `/${panelId === 'home' ? '' : panelId}`);
            
            // Emit panel change event
            this.emitPanelChange(panelId);
            
            console.log(`[UIManager] Switched to panel: ${panelId}`);
        }
    }
    
    /**
     * Update navigation highlighting
     */
    updateNavHighlight(panelId) {
        for (const item of this.elements.navItems) {
            const itemPanel = item.getAttribute('data-panel') || 
                            item.getAttribute('href')?.replace('/', '');
            
            if (itemPanel === panelId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        }
    }
    
    /**
     * Initialize brain SVG with CSS variables
     */
    initBrainSVG() {
        // Set initial CSS variables
        document.body.style.setProperty('--pulse-speed', '2s');
        document.body.style.setProperty('--pulse-intensity', '0.5');
        document.body.style.setProperty('--brain-left-intensity', '0.3');
        document.body.style.setProperty('--brain-right-intensity', '0.3');
        document.body.style.setProperty('--bridge-intensity', '0');
    }
    
    /**
     * Connect to stream controller for real-time updates
     */
    connectStreamController() {
        if (window.streamController) {
            this.streamController = window.streamController;
            
            // Listen for pulse updates
            this.streamController.on('pulse', (data) => {
                this.updatePulse(data);
            });
            
            // Listen for models updates
            this.streamController.on('models', (data) => {
                this.updateModels(data);
            });
            
            // Listen for inference updates
            this.streamController.on('inference', (data) => {
                this.updateInference(data);
            });
        }
    }
    
    /**
     * Update pulse visualization
     */
    updatePulse(data) {
        const pulse = data.pulse || 0.5;
        
        // Update pulse value display
        if (this.elements.pulseValue) {
            this.elements.pulseValue.textContent = pulse.toFixed(2);
        }
        
        // Update CSS variables for SVG animations
        const pulseSpeed = 3 - (pulse * 2);
        document.body.style.setProperty('--pulse-speed', `${pulseSpeed}s`);
        document.body.style.setProperty('--pulse-intensity', pulse);
        
        // Update activity dots
        const dots = this.elements.activityDots;
        if (dots.length > 0) {
            const activeDots = Math.ceil(pulse * dots.length);
            dots.forEach((dot, i) => {
                dot.classList.toggle('active', i < activeDots);
            });
        }
    }
    
    /**
     * Update models status
     */
    updateModels(data) {
        // Update brain SVG hemispheres
        if (this.elements.brainLeft) {
            this.elements.brainLeft.classList.remove('active', 'thinking');
            if (data.left?.loaded) {
                this.elements.brainLeft.classList.add('active');
            }
        }
        
        if (this.elements.brainRight) {
            this.elements.brainRight.classList.remove('active', 'thinking');
            if (data.right?.loaded) {
                this.elements.brainRight.classList.add('active');
            }
        }
        
        // Update corpus callosum
        if (this.elements.corpusCallosum) {
            this.elements.corpusCallosum.classList.toggle('active', data.is_split_mode);
        }
        
        // Update model status display
        if (this.elements.modelStatus) {
            if (data.is_split_mode) {
                this.elements.modelStatus.textContent = 'Bicaméral';
                this.elements.modelStatus.style.color = 'var(--synapse)';
            } else if (data.left?.loaded) {
                this.elements.modelStatus.textContent = 'DIA actif';
                this.elements.modelStatus.style.color = 'var(--diadikos)';
            } else if (data.right?.loaded) {
                this.elements.modelStatus.textContent = 'PAL actif';
                this.elements.modelStatus.style.color = 'var(--palladion)';
            } else {
                this.elements.modelStatus.textContent = 'Non configuré';
                this.elements.modelStatus.style.color = 'var(--text-dim)';
            }
        }
        
        // Update cycles display
        if (this.elements.cyclesValue && data.corps_calleux) {
            this.elements.cyclesValue.textContent = data.corps_calleux.total_cycles || 0;
        }
    }
    
    /**
     * Update inference state
     */
    updateInference(data) {
        // Update brain thinking state
        if (this.elements.brainLeft && data.thinking_left) {
            this.elements.brainLeft.classList.add('thinking');
        }
        
        if (this.elements.brainRight && data.thinking_right) {
            this.elements.brainRight.classList.add('thinking');
        }
        
        // Update status display
        if (this.elements.statusMain) {
            if (data.thinking_left || data.thinking_right) {
                this.elements.statusMain.textContent = 'THINKING';
                this.elements.statusMain.style.color = 'var(--synapse)';
            }
        }
    }
    
    /**
     * Emit panel change event
     */
    emitPanelChange(panelId) {
        const event = new CustomEvent('panelChange', { detail: { panel: panelId } });
        document.dispatchEvent(event);
    }
    
    /**
     * Get current panel
     */
    getCurrentPanel() {
        return this.currentPanel;
    }
    
    /**
     * Check if panel exists
     */
    hasPanel(panelId) {
        return this.panels.has(panelId);
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.uiManager = new UIManager();
    
    // Initialize stream controller
    if (window.streamController) {
        window.streamController.init();
    }
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.panel) {
            window.uiManager.showPanel(event.state.panel);
        }
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.streamController) {
        window.streamController.destroy();
    }
});
