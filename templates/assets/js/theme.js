/**
 * Theme Manager - Light/Dark mode toggle system
 * Handles theme switching with smooth transitions and persistence
 * Created: August 30, 2025
 */

export class ThemeManager {
  constructor() {
    this.currentTheme = this.getSavedTheme() || this.getSystemPreference();
    this.isInitialized = false;
    
    // Bind methods to preserve context
    this.toggleTheme = this.toggleTheme.bind(this);
    this.handleSystemChange = this.handleSystemChange.bind(this);
    this.handleKeyboardToggle = this.handleKeyboardToggle.bind(this);
    
    this.init();
  }
  
  init() {
    // Prevent flash of wrong theme
    this.addNoTransitionClass();
    
    // Apply theme immediately
    this.applyTheme(this.currentTheme);
    
    // Setup toggle button
    this.setupToggle();
    
    // Listen for system theme changes
    this.detectSystemPreference();
    
    // Setup keyboard shortcut (Ctrl/Cmd + Shift + T)
    this.setupKeyboardShortcut();
    
    // Remove no-transition class after a small delay
    setTimeout(() => {
      this.removeNoTransitionClass();
      this.isInitialized = true;
    }, 100);
    
    console.log(`🎨 Theme Manager initialized - Current theme: ${this.currentTheme}`);
  }
  
  addNoTransitionClass() {
    document.documentElement.classList.add('no-transitions');
  }
  
  removeNoTransitionClass() {
    document.documentElement.classList.remove('no-transitions');
  }
  
  setupToggle() {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.addEventListener('click', this.toggleTheme);
      
      // Add accessibility attributes
      this.updateToggleAccessibility(toggle);
      
      // Add visual feedback for interaction
      toggle.addEventListener('mouseenter', () => {
        if (this.isInitialized) {
          toggle.style.transform = 'scale(1.05)';
        }
      });
      
      toggle.addEventListener('mouseleave', () => {
        if (this.isInitialized) {
          toggle.style.transform = 'scale(1)';
        }
      });
    }
  }
  
  updateToggleAccessibility(toggle) {
    const isLight = this.currentTheme === 'light';
    toggle.setAttribute('aria-label', `Cambiar a tema ${isLight ? 'oscuro' : 'claro'}`);
    toggle.setAttribute('aria-pressed', isLight.toString());
    toggle.title = `Cambiar a tema ${isLight ? 'oscuro' : 'claro'} (Ctrl+Shift+T)`;
  }
  
  setupKeyboardShortcut() {
    document.addEventListener('keydown', this.handleKeyboardToggle);
  }
  
  handleKeyboardToggle(event) {
    // Ctrl+Shift+T or Cmd+Shift+T
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'T') {
      event.preventDefault();
      this.toggleTheme();
      
      // Visual feedback for keyboard users
      const toggle = document.getElementById('themeToggle');
      if (toggle) {
        toggle.focus();
        toggle.style.transform = 'scale(0.95)';
        setTimeout(() => {
          toggle.style.transform = 'scale(1)';
        }, 150);
      }
    }
  }
  
  toggleTheme() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
    
    // Haptic feedback if supported
    this.triggerHapticFeedback();
    
    // Analytics event (if analytics is available)
    this.trackThemeChange(newTheme);
  }
  
  setTheme(theme) {
    if (theme !== 'light' && theme !== 'dark') {
      console.warn(`Invalid theme: ${theme}. Using 'dark' as fallback.`);
      theme = 'dark';
    }
    
    const previousTheme = this.currentTheme;
    this.currentTheme = theme;
    
    this.applyTheme(theme);
    this.saveTheme(theme);
    this.announceThemeChange(theme, previousTheme);
    
    // Update toggle accessibility
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      this.updateToggleAccessibility(toggle);
    }
    
    // Dispatch custom event for other components
    this.dispatchThemeChangeEvent(theme, previousTheme);
  }
  
  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.updateMetaThemeColor(theme);
    this.updateColorScheme(theme);
    
    // Update local storage immediately
    localStorage.setItem('pharmacy-finder-theme', theme);
  }
  
  updateMetaThemeColor(theme) {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.name = 'theme-color';
      document.head.appendChild(metaThemeColor);
    }
    
    const themeColors = {
      dark: '#1a1a2e',
      light: '#ffffff'
    };
    
    metaThemeColor.setAttribute('content', themeColors[theme]);
  }
  
  updateColorScheme(theme) {
    // Update the color-scheme CSS property for better browser integration
    document.documentElement.style.colorScheme = theme;
  }
  
  saveTheme(theme) {
    try {
      localStorage.setItem('pharmacy-finder-theme', theme);
    } catch (error) {
      console.warn('Could not save theme preference:', error);
    }
  }
  
  getSavedTheme() {
    try {
      return localStorage.getItem('pharmacy-finder-theme');
    } catch (error) {
      console.warn('Could not retrieve saved theme:', error);
      return null;
    }
  }
  
  getSystemPreference() {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark'; // Default fallback
  }
  
  detectSystemPreference() {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Listen for system theme changes
    mediaQuery.addEventListener('change', this.handleSystemChange);
  }
  
  handleSystemChange(event) {
    // Only auto-switch if user hasn't manually set a preference
    if (!this.getSavedTheme()) {
      const systemTheme = event.matches ? 'dark' : 'light';
      this.setTheme(systemTheme);
      console.log(`🎨 System theme changed to: ${systemTheme}`);
    }
  }
  
  announceThemeChange(theme, previousTheme) {
    if (!this.isInitialized) return;
    
    // Announce theme change for screen readers
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    
    const themeNames = {
      dark: 'oscuro',
      light: 'claro'
    };
    
    announcement.textContent = `Tema cambiado a ${themeNames[theme]}`;
    document.body.appendChild(announcement);
    
    // Remove announcement after screen reader has processed it
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 1000);
  }
  
  dispatchThemeChangeEvent(theme, previousTheme) {
    const event = new CustomEvent('themeChange', {
      detail: {
        theme,
        previousTheme,
        timestamp: Date.now()
      }
    });
    
    document.dispatchEvent(event);
  }
  
  triggerHapticFeedback() {
    // Subtle haptic feedback if supported (mobile devices)
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
  }
  
  trackThemeChange(theme) {
    // Analytics tracking (if available)
    if (typeof gtag !== 'undefined') {
      gtag('event', 'theme_change', {
        event_category: 'UI',
        event_label: theme,
        value: theme === 'dark' ? 0 : 1
      });
    }
    
    console.log(`🎨 Theme changed to: ${theme}`);
  }
  
  // Public API methods
  getCurrentTheme() {
    return this.currentTheme;
  }
  
  isDarkMode() {
    return this.currentTheme === 'dark';
  }
  
  isLightMode() {
    return this.currentTheme === 'light';
  }
  
  resetToSystemPreference() {
    const systemTheme = this.getSystemPreference();
    this.setTheme(systemTheme);
    
    // Clear saved preference
    try {
      localStorage.removeItem('pharmacy-finder-theme');
    } catch (error) {
      console.warn('Could not clear saved theme:', error);
    }
  }
  
  // Cleanup method
  destroy() {
    const toggle = document.getElementById('themeToggle');
    if (toggle) {
      toggle.removeEventListener('click', this.toggleTheme);
    }
    
    document.removeEventListener('keydown', this.handleKeyboardToggle);
    
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.removeEventListener('change', this.handleSystemChange);
    }
  }
}

// Utility function to get theme manager instance
export function getThemeManager() {
  if (!window.themeManager) {
    window.themeManager = new ThemeManager();
  }
  return window.themeManager;
}

// Auto-initialize if running in browser
if (typeof window !== 'undefined') {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      window.themeManager = new ThemeManager();
    });
  } else {
    window.themeManager = new ThemeManager();
  }
}
