/**
 * BICAMERIS - Tab Controller
 * Horizontal tab navigation system
 * 
 * No external dependencies. 100% local.
 */

class TabController {
    constructor() {
        this.tabHeader = document.querySelector('.tab-header');
        this.tabContent = document.querySelector('.tab-content');
        
        this.tabs = [];
        this.panels = [];
        this.activeIndex = 0;
        
        this.init();
    }
    
    init() {
        if (!this.tabHeader || !this.tabContent) {
            console.warn('[TabController] Tab elements not found');
            return;
        }
        
        this.tabs = Array.from(this.tabHeader.querySelectorAll('.tab-btn'));
        this.panels = Array.from(this.tabContent.querySelectorAll('.tab-panel'));
        
        // Setup click handlers
        this.tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => this.activateTab(index));
        });
        
        // Activate first tab
        this.activateTab(0);
        
        // Listen for URL hash changes
        window.addEventListener('hashchange', () => this.handleHashChange());
        this.handleHashChange();
        
        console.log('[TabController] Initialized with', this.tabs.length, 'tabs');
    }
    
    activateTab(index) {
        if (index < 0 || index >= this.tabs.length) {
            return;
        }
        
        // Remove active class from all
        this.tabs.forEach(tab => tab.classList.remove('active'));
        this.panels.forEach(panel => panel.classList.remove('active'));
        
        // Add active to selected
        this.tabs[index].classList.add('active');
        
        if (this.panels[index]) {
            this.panels[index].classList.add('active');
        }
        
        this.activeIndex = index;
        
        // Update URL hash
        const tabId = this.tabs[index].dataset.tabId;
        if (tabId) {
            history.replaceState(null, '', `#${tabId}`);
        }
        
        // Dispatch event
        document.dispatchEvent(new CustomEvent('tabChange', {
            detail: { 
                index: index, 
                tabId: tabId,
                tabName: this.tabs[index].textContent.trim()
            }
        }));
        
        console.log('[TabController] Activated tab:', tabId);
    }
    
    activateTabById(tabId) {
        const index = this.tabs.findIndex(tab => tab.dataset.tabId === tabId);
        if (index !== -1) {
            this.activateTab(index);
        }
    }
    
    handleHashChange() {
        const hash = window.location.hash.slice(1);
        if (hash) {
            this.activateTabById(hash);
        }
    }
    
    getActiveTab() {
        return {
            index: this.activeIndex,
            tabId: this.tabs[this.activeIndex]?.dataset.tabId,
            name: this.tabs[this.activeIndex]?.textContent.trim()
        };
    }
    
    getTabCount() {
        return this.tabs.length;
    }
}

// Initialize on DOM ready
let tabController = null;

document.addEventListener('DOMContentLoaded', () => {
    tabController = new TabController();
    window.tabController = tabController;
});

// Export for use in other modules
window.TabController = TabController;
