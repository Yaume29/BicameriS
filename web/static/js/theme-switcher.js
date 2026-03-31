/**
 * BICAMERIS - Theme Switcher
 * Handles theme loading, switching, and persistence
 */

class ThemeSwitcher {
  constructor() {
    this.themes = [
      {
        id: 'dark-cyberpunk',
        name: 'Cyberpunk Dark',
        description: 'Default dark theme with neon accents',
        file: '/static/css/themes/dark-cyberpunk.css',
        isDefault: true
      },
      {
        id: 'matrix-green',
        name: 'Matrix Green',
        description: 'Terminal green style',
        file: '/static/css/themes/matrix-green.css',
        isDefault: false
      },
      {
        id: 'warm-ember',
        name: 'Warm Ember',
        description: 'Warm amber tones',
        file: '/static/css/themes/warm-ember.css',
        isDefault: false
      }
    ];

    this.currentTheme = null;
    this.themeLink = null;
    this.init();
  }

  init() {
    // Create theme link element
    this.themeLink = document.createElement('link');
    this.themeLink.rel = 'stylesheet';
    this.themeLink.id = 'theme-css';
    document.head.appendChild(this.themeLink);

    // Load saved theme or default
    const savedTheme = localStorage.getItem('bicameris-theme');
    if (savedTheme) {
      this.loadTheme(savedTheme);
    } else {
      this.loadTheme('dark-cyberpunk');
    }

    // Listen for theme change events
    document.addEventListener('themeChange', (e) => {
      this.loadTheme(e.detail.themeId);
    });
  }

  loadTheme(themeId) {
    const theme = this.themes.find(t => t.id === themeId);
    if (!theme) {
      console.error(`Theme not found: ${themeId}`);
      return;
    }

    // Update link href
    this.themeLink.href = theme.file;
    this.currentTheme = theme;

    // Save preference
    localStorage.setItem('bicameris-theme', themeId);

    // Dispatch event
    document.dispatchEvent(new CustomEvent('themeLoaded', {
      detail: { themeId, theme }
    }));

    console.log(`[ThemeSwitcher] Loaded: ${theme.name}`);
  }

  getThemes() {
    return this.themes;
  }

  getCurrentTheme() {
    return this.currentTheme;
  }

  addTheme(theme) {
    // Validate theme
    if (!theme.id || !theme.name || !theme.file) {
      console.error('Invalid theme definition');
      return false;
    }

    // Check for duplicates
    if (this.themes.find(t => t.id === theme.id)) {
      console.error(`Theme already exists: ${theme.id}`);
      return false;
    }

    this.themes.push(theme);
    console.log(`[ThemeSwitcher] Added theme: ${theme.name}`);
    return true;
  }

  removeTheme(themeId) {
    const index = this.themes.findIndex(t => t.id === themeId);
    if (index > -1) {
      this.themes.splice(index, 1);
      console.log(`[ThemeSwitcher] Removed theme: ${themeId}`);
      return true;
    }
    return false;
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.themeSwitcher = new ThemeSwitcher();
});
