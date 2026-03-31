/**
 * BICAMERIS - Brain WebSocket Connection
 * Real-time updates for brain SVG and page borders
 */

class BrainWebSocket {
  constructor() {
    this.ws = null;
    this.retryCount = 0;
    this.maxRetries = 10;
    this.state = {
      left: { active: false, thinking: false, intensity: 0.3 },
      right: { active: false, thinking: false, intensity: 0.3 },
      corpus: { active: false, intensity: 0 },
      pulse: 0.5
    };
    this.init();
  }

  init() {
    this.connect();
    this.startPulseAnimation();
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/neural`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[BrainWS] Connected');
        this.retryCount = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleUpdate(data);
        } catch (e) {
          console.error('[BrainWS] Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('[BrainWS] Disconnected');
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('[BrainWS] Error:', error);
      };

    } catch (e) {
      console.error('[BrainWS] Connection failed:', e);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.retryCount >= this.maxRetries) {
      console.log('[BrainWS] Max retries reached, falling back to polling');
      this.startPolling();
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000);
    this.retryCount++;

    console.log(`[BrainWS] Reconnecting in ${delay}ms`);
    setTimeout(() => this.connect(), delay);
  }

  handleUpdate(data) {
    // Update state
    if (data.left) {
      this.state.left.active = data.left.active || false;
      this.state.left.thinking = data.left.thinking || false;
      this.state.left.intensity = data.left.thinking ? 1 : (data.left.active ? 0.5 : 0.3);
    }

    if (data.right) {
      this.state.right.active = data.right.active || false;
      this.state.right.thinking = data.right.thinking || false;
      this.state.right.intensity = data.right.thinking ? 1 : (data.right.active ? 0.5 : 0.3);
    }

    if (data.corpus) {
      this.state.corpus.active = data.corpus.active || false;
      this.state.corpus.intensity = data.corpus.active ? 0.8 : 0;
    }

    // Update visuals
    this.updateVisuals();
  }

  updateVisuals() {
    // Update brain SVG
    this.updateBrainSVG();

    // Update all pulse borders
    this.updatePulseBorders();

    // Update CSS variables
    this.updateCSSVars();

    // Update status indicators
    this.updateStatusIndicators();
  }

  updateBrainSVG() {
    // Left hemisphere
    const leftPath = document.getElementById('brain-left');
    if (leftPath) {
      leftPath.style.opacity = this.state.left.intensity;
      leftPath.style.filter = this.state.left.thinking 
        ? 'url(#glow-cyan) brightness(1.5)' 
        : 'url(#glow-cyan)';
    }

    // Right hemisphere
    const rightPath = document.getElementById('brain-right');
    if (rightPath) {
      rightPath.style.opacity = this.state.right.intensity;
      rightPath.style.filter = this.state.right.thinking 
        ? 'url(#glow-magenta) brightness(1.5)' 
        : 'url(#glow-magenta)';
    }

    // Corpus callosum
    const corpusPath = document.getElementById('brain-corpus');
    if (corpusPath) {
      corpusPath.style.opacity = this.state.corpus.intensity;
      corpusPath.style.filter = this.state.corpus.active 
        ? 'url(#glow-amber) brightness(1.5)' 
        : 'url(#glow-amber)';
    }
  }

  updatePulseBorders() {
    // Find all elements with pulse-border class
    const borders = document.querySelectorAll('.pulse-border');

    // Determine dominant hemisphere and color
    let color = 'rgba(0, 212, 255, 0.3)';
    let glowColor = 'rgba(0, 212, 255, 0.2)';

    if (this.state.left.thinking) {
      color = 'rgba(0, 212, 255, 0.5)';
      glowColor = 'rgba(0, 212, 255, 0.3)';
    } else if (this.state.right.thinking) {
      color = 'rgba(255, 0, 110, 0.5)';
      glowColor = 'rgba(255, 0, 110, 0.3)';
    } else if (this.state.corpus.active) {
      color = 'rgba(139, 92, 246, 0.5)';
      glowColor = 'rgba(139, 92, 246, 0.3)';
    }

    // Apply to all pulse borders
    borders.forEach(el => {
      el.style.setProperty('--pulse-color', color);
      el.style.borderColor = color;
      el.style.boxShadow = `0 0 15px ${glowColor}`;
    });
  }

  updateCSSVars() {
    const root = document.documentElement;
    
    // Update brain state variables
    root.style.setProperty('--brain-left', this.state.left.intensity);
    root.style.setProperty('--brain-right', this.state.right.intensity);
    root.style.setProperty('--brain-corpus', this.state.corpus.intensity);

    // Update pulse speed based on activity
    const totalActivity = this.state.left.intensity + this.state.right.intensity + this.state.corpus.intensity;
    const pulseSpeed = Math.max(0.5, 3 - totalActivity);
    root.style.setProperty('--pulse-speed', `${pulseSpeed}s`);

    // Update entropy colors
    let entropyColor = 'rgba(0, 212, 255, 0.3)';
    if (this.state.left.thinking) {
      entropyColor = 'rgba(0, 212, 255, 0.5)';
    } else if (this.state.right.thinking) {
      entropyColor = 'rgba(255, 0, 110, 0.5)';
    } else if (this.state.corpus.active) {
      entropyColor = 'rgba(139, 92, 246, 0.5)';
    }
    root.style.setProperty('--pulse-color', entropyColor);
  }

  updateStatusIndicators() {
    // Update pulse indicator
    const pulseValue = document.getElementById('pulse-value');
    if (pulseValue) {
      const total = this.state.left.intensity + this.state.right.intensity + this.state.corpus.intensity;
      pulseValue.textContent = `Pulse: ${(total / 3).toFixed(2)}`;
    }

    // Update activity dots
    const dots = document.querySelectorAll('.activity-dot');
    if (dots.length >= 3) {
      dots[0].style.background = this.state.left.intensity > 0.5 ? '#00d4ff' : 'var(--text-muted)';
      dots[1].style.background = this.state.corpus.intensity > 0.5 ? '#8b5cf6' : 'var(--text-muted)';
      dots[2].style.background = this.state.right.intensity > 0.5 ? '#ff006e' : 'var(--text-muted)';
    }
  }

  startPulseAnimation() {
    // Continuous pulse animation
    setInterval(() => {
      this.state.pulse = 0.3 + Math.random() * 0.4;
      this.updateCSSVars();
    }, 2000);
  }

  startPolling() {
    // Fallback polling when WebSocket fails
    setInterval(async () => {
      try {
        const resp = await fetch('/api/dashboard/pulse');
        const data = await resp.json();
        this.handleUpdate(data);
      } catch (e) {
        // Silent fail
      }
    }, 2000);
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  getState() {
    return this.state;
  }

  destroy() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.brainWS = new BrainWebSocket();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.brainWS) {
    window.brainWS.destroy();
  }
});
