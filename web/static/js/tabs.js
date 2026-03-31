/**
 * BICAMERIS - Tab Navigation Controller
 * Handles tab switching with state persistence
 */

class TabController {
  constructor() {
    this.tabButtons = document.querySelectorAll('.tab-btn');
    this.pages = document.querySelectorAll('.page');
    this.activeTab = localStorage.getItem('activeTab') || 'models';
    this.init();
  }

  init() {
    // Setup click handlers
    this.tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        this.switchTab(tabId);
      });
    });

    // Apply initial state
    this.switchTab(this.activeTab);
  }

  switchTab(tabId) {
    // Update buttons
    this.tabButtons.forEach(btn => {
      btn.classList.remove('active');
      if (btn.dataset.tab === tabId) {
        btn.classList.add('active');
      }
    });

    // Update pages
    this.pages.forEach(page => {
      page.classList.remove('active');
      if (page.id === `page-${tabId}`) {
        page.classList.add('active');
      }
    });

    // Save state
    this.activeTab = tabId;
    localStorage.setItem('activeTab', tabId);

    // Dispatch event
    document.dispatchEvent(new CustomEvent('tabChange', {
      detail: { tab: tabId }
    }));
  }

  getActiveTab() {
    return this.activeTab;
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.tabController = new TabController();
});
