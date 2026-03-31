/**
 * BICAMERIS - Sidebar Controller
 * Collapsible sidebar with state persistence
 */

class SidebarController {
  constructor() {
    this.sidebar = document.getElementById('sidebar');
    this.toggleBtn = document.getElementById('sidebar-toggle');
    this.isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    this.init();
  }

  init() {
    // Apply initial state
    if (this.isCollapsed) {
      this.sidebar.classList.add('collapsed');
    }

    // Toggle button click
    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => this.toggle());
    }

    // Keyboard shortcut (Ctrl+B)
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        this.toggle();
      }
    });
  }

  toggle() {
    this.isCollapsed = !this.isCollapsed;
    this.sidebar.classList.toggle('collapsed', this.isCollapsed);
    localStorage.setItem('sidebarCollapsed', this.isCollapsed);

    // Dispatch event
    document.dispatchEvent(new CustomEvent('sidebarToggle', {
      detail: { collapsed: this.isCollapsed }
    }));
  }

  collapse() {
    if (!this.isCollapsed) {
      this.toggle();
    }
  }

  expand() {
    if (this.isCollapsed) {
      this.toggle();
    }
  }

  getState() {
    return this.isCollapsed;
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.sidebarController = new SidebarController();
});
