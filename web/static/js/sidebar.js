/**
 * BICAMERIS - Sidebar Controller
 * Collapsible sidebar with animation
 * 
 * No external dependencies. 100% local.
 */

class SidebarController {
    constructor() {
        this.layout = document.querySelector('.app-layout');
        this.sidebar = document.querySelector('.app-sidebar');
        this.collapseArrow = document.querySelector('.collapse-arrow');
        this.collapsedToggle = document.querySelector('.collapsed-toggle');
        
        this.isCollapsed = false;
        this.storageKey = 'bicameris_sidebar_collapsed';
        
        this.init();
    }
    
    init() {
        // Restore state from localStorage
        const saved = localStorage.getItem(this.storageKey);
        if (saved === 'true') {
            this.collapse();
        }
        
        // Setup toggle buttons
        if (this.collapseArrow) {
            this.collapseArrow.addEventListener('click', () => this.toggle());
        }
        
        if (this.collapsedToggle) {
            this.collapsedToggle.addEventListener('click', () => this.expand());
        }
        
        // Keyboard shortcut (Ctrl+B)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                this.toggle();
            }
        });
        
        console.log('[SidebarController] Initialized');
    }
    
    toggle() {
        if (this.isCollapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    }
    
    collapse() {
        this.isCollapsed = true;
        this.layout.classList.add('sidebar-collapsed');
        localStorage.setItem(this.storageKey, 'true');
        
        // Update arrow icon
        if (this.collapseArrow) {
            this.collapseArrow.textContent = '→';
        }
        
        // Dispatch event
        document.dispatchEvent(new CustomEvent('sidebarCollapse', {
            detail: { collapsed: true }
        }));
        
        console.log('[SidebarController] Collapsed');
    }
    
    expand() {
        this.isCollapsed = false;
        this.layout.classList.remove('sidebar-collapsed');
        localStorage.setItem(this.storageKey, 'false');
        
        // Update arrow icon
        if (this.collapseArrow) {
            this.collapseArrow.textContent = '←';
        }
        
        // Dispatch event
        document.dispatchEvent(new CustomEvent('sidebarCollapse', {
            detail: { collapsed: false }
        }));
        
        console.log('[SidebarController] Expanded');
    }
    
    isSidebarCollapsed() {
        return this.isCollapsed;
    }
}

// Initialize on DOM ready
let sidebarController = null;

document.addEventListener('DOMContentLoaded', () => {
    sidebarController = new SidebarController();
    window.sidebarController = sidebarController;
});

// Export for use in other modules
window.SidebarController = SidebarController;
