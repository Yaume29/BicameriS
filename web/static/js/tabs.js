/**
 * BICAMERIS - Tab Navigation Controller
 * Handles horizontal tab switching with state persistence
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'bicameris_active_tab';
  const DEFAULT_TAB = 'chat';

  let activeTab = null;

  function init() {
    // Restore tab from localStorage or use default
    activeTab = localStorage.getItem(STORAGE_KEY) || DEFAULT_TAB;

    // Bind tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
    tabButtons.forEach(function(btn) {
      btn.addEventListener('click', function() {
        switchTab(this.dataset.tab);
      });
    });

    // Activate saved tab
    switchTab(activeTab, false);

    // Dispatch ready event
    document.dispatchEvent(new CustomEvent('tabs:ready', {
      detail: { activeTab: activeTab }
    }));
  }

  function switchTab(tabName, saveState) {
    if (saveState === undefined) saveState = true;

    // Update buttons
    const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
    tabButtons.forEach(function(btn) {
      btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content panels
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(function(content) {
      const id = content.id.replace('tab-', '');
      content.classList.toggle('active', id === tabName);
    });

    activeTab = tabName;

    if (saveState) {
      localStorage.setItem(STORAGE_KEY, tabName);
    }

    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('tab:change', {
      detail: { tab: tabName }
    }));
  }

  function getActiveTab() {
    return activeTab;
  }

  // Public API
  window.BicamerisTabs = {
    init: init,
    switchTab: switchTab,
    getActiveTab: getActiveTab
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
