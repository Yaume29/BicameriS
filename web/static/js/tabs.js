class TabController {
  constructor() {
    this.tabButtons = document.querySelectorAll('.tab-bar .tab-btn');
    this.pages = document.querySelectorAll('.page-container > .page');
    this.activeTab = localStorage.getItem('activeTab') || 'models';
    this.init();
  }

  init() {
    this.tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        this.switchTab(tabId);
      });
    });

    this.switchTab(this.activeTab);
    
    this.initSubTabs();
  }

  initSubTabs() {
    document.querySelectorAll('.tabs-header.main-tabs').forEach(header => {
      const buttons = header.querySelectorAll('.tab-btn');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          const tabId = btn.dataset.tab;
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          
          const container = header.closest('.tabs-container');
          if (container) {
            container.querySelectorAll('.tab-content').forEach(content => {
              content.classList.remove('active');
            });
            const target = container.querySelector(`#tab-${tabId}`);
            if (target) target.classList.add('active');
          }
        });
      });
    });
    
    document.querySelectorAll('.tabs-header.sub-tabs').forEach(header => {
      const buttons = header.querySelectorAll('.sub-tab-btn');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          const subtabId = btn.dataset.subtab;
          buttons.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          
          const container = header.closest('.sub-tabs-container');
          if (container) {
            container.querySelectorAll('.sub-tab-content').forEach(content => {
              content.classList.remove('active');
            });
            const target = container.querySelector(`#subtab-${subtabId}`);
            if (target) target.classList.add('active');
          }
        });
      });
    });
  }

  switchTab(tabId) {
    this.tabButtons.forEach(btn => {
      btn.classList.remove('active');
      if (btn.dataset.tab === tabId) {
        btn.classList.add('active');
      }
    });

    this.pages.forEach(page => {
      page.classList.remove('active');
      if (page.id === `page-${tabId}`) {
        page.classList.add('active');
      }
    });

    this.activeTab = tabId;
    localStorage.setItem('activeTab', tabId);

    document.dispatchEvent(new CustomEvent('tabChange', {
      detail: { tab: tabId }
    }));
  }

  getActiveTab() {
    return this.activeTab;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.tabController = new TabController();
});
