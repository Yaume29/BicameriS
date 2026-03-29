/**
 * BICAMERIS - Sidebar Controller
 * Handles sidebar collapse/expand with localStorage persistence
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'bicameris_sidebar_collapsed';
  const SIDEBAR_COLLAPSED_CLASS = 'collapsed';

  let sidebar = null;
  let collapseBtn = null;
  let isCollapsed = false;

  function init() {
    sidebar = document.querySelector('.sidebar');
    collapseBtn = document.querySelector('.collapse-btn');

    if (!sidebar || !collapseBtn) {
      console.warn('[Sidebar] Elements not found');
      return;
    }

    // Restore state from localStorage
    const savedState = localStorage.getItem(STORAGE_KEY);
    isCollapsed = savedState === 'true';

    if (isCollapsed) {
      sidebar.classList.add(SIDEBAR_COLLAPSED_CLASS);
      updateButtonText();
    }

    // Bind events
    collapseBtn.addEventListener('click', toggle);

    // Keyboard shortcut: Ctrl+B
    document.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        toggle();
      }
    });

    // Dispatch ready event
    document.dispatchEvent(new CustomEvent('sidebar:ready', {
      detail: { collapsed: isCollapsed }
    }));
  }

  function toggle() {
    isCollapsed = !isCollapsed;
    sidebar.classList.toggle(SIDEBAR_COLLAPSED_CLASS, isCollapsed);
    localStorage.setItem(STORAGE_KEY, isCollapsed);
    updateButtonText();

    // Dispatch event for other components
    document.dispatchEvent(new CustomEvent('sidebar:toggle', {
      detail: { collapsed: isCollapsed }
    }));
  }

  function updateButtonText() {
    if (!collapseBtn) return;
    collapseBtn.textContent = isCollapsed ? '\u2194' : '\u2190';
    collapseBtn.title = isCollapsed ? 'Expand sidebar (Ctrl+B)' : 'Collapse sidebar (Ctrl+B)';
  }

  function getCollapsed() {
    return isCollapsed;
  }

  function collapse() {
    if (!isCollapsed) toggle();
  }

  function expand() {
    if (isCollapsed) toggle();
  }

  // Public API
  window.BicamerisSidebar = {
    init: init,
    toggle: toggle,
    collapse: collapse,
    expand: expand,
    isCollapsed: getCollapsed
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
