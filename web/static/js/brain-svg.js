/**
 * BICAMERIS - Brain SVG Component
 * Interactive brain visualization with WebSocket connection
 * Converted from React BrainSVG.tsx
 */

class BrainSVG {
  constructor(containerId, size = 100) {
    this.container = document.getElementById(containerId);
    this.size = size;
    this.state = {
      left: { active: false, thinking: false, intensity: 0.3 },
      right: { active: false, thinking: false, intensity: 0.3 },
      corpus: { active: false, intensity: 0 }
    };
    this.render();
  }

  render() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 120 100');
    svg.setAttribute('width', this.size);
    svg.setAttribute('height', this.size * 0.83);
    svg.classList.add('brain-svg');
    svg.style.animation = 'brainwave 4s ease-in-out infinite';

    // Defs (filters and gradients)
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    
    // Glow filter for cyan (left hemisphere)
    defs.innerHTML = `
      <filter id="glow-cyan">
        <feGaussianBlur stdDeviation="2" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <filter id="glow-magenta">
        <feGaussianBlur stdDeviation="2" result="blur"/>
        <feMerge>
          <feMergeNode in="blur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
      <linearGradient id="corpus-grad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#8b5cf6"/>
        <stop offset="100%" stop-color="#6d28d9"/>
      </linearGradient>
    `;
    svg.appendChild(defs);

    // Left Hemisphere (Cyan - Logic)
    const leftPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    leftPath.setAttribute('id', 'brain-left');
    leftPath.setAttribute('d', 'M 60 10 C 35 8, 15 25, 12 50 C 9 75, 25 90, 50 92 L 60 90');
    leftPath.setAttribute('fill', 'none');
    leftPath.setAttribute('stroke', '#00d4ff');
    leftPath.setAttribute('stroke-width', '2');
    leftPath.setAttribute('filter', 'url(#glow-cyan)');
    leftPath.classList.add('brain-path');
    leftPath.style.opacity = '0.3';
    svg.appendChild(leftPath);

    // Right Hemisphere (Magenta - Intuition)
    const rightPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    rightPath.setAttribute('id', 'brain-right');
    rightPath.setAttribute('d', 'M 60 10 C 85 8, 105 25, 108 50 C 111 75, 95 90, 70 92 L 60 90');
    rightPath.setAttribute('fill', 'none');
    rightPath.setAttribute('stroke', '#ff006e');
    rightPath.setAttribute('stroke-width', '2');
    rightPath.setAttribute('filter', 'url(#glow-magenta)');
    rightPath.classList.add('brain-path');
    rightPath.style.opacity = '0.3';
    svg.appendChild(rightPath);

    // Corpus Callosum (Purple - Bridge)
    const corpusPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    corpusPath.setAttribute('id', 'brain-corpus');
    corpusPath.setAttribute('d', 'M 58 25 L 62 25 M 58 50 L 62 50 M 58 75 L 62 75');
    corpusPath.setAttribute('fill', 'none');
    corpusPath.setAttribute('stroke', 'url(#corpus-grad)');
    corpusPath.setAttribute('stroke-width', '3');
    corpusPath.setAttribute('stroke-linecap', 'round');
    corpusPath.classList.add('brain-path');
    corpusPath.style.opacity = '0.5';
    svg.appendChild(corpusPath);

    // Neural Activity Dots (sockets)
    const dots = [
      { cx: 25, cy: 30, class: 'left-dot' },
      { cx: 20, cy: 50, class: 'left-dot' },
      { cx: 25, cy: 70, class: 'left-dot' },
      { cx: 60, cy: 35, class: 'corpus-dot' },
      { cx: 60, cy: 65, class: 'corpus-dot' },
      { cx: 95, cy: 30, class: 'right-dot' },
      { cx: 100, cy: 50, class: 'right-dot' },
      { cx: 95, cy: 70, class: 'right-dot' }
    ];

    dots.forEach((dot, i) => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', dot.cx);
      circle.setAttribute('cy', dot.cy);
      circle.setAttribute('r', '3');
      circle.classList.add('animate-socket-pulse');
      circle.style.animationDelay = `${i * 0.2}s`;
      
      if (dot.class === 'left-dot') {
        circle.setAttribute('fill', '#00d4ff');
      } else if (dot.class === 'right-dot') {
        circle.setAttribute('fill', '#ff006e');
      } else {
        circle.setAttribute('fill', '#8b5cf6');
      }
      
      svg.appendChild(circle);
    });

    // Labels
    const leftLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    leftLabel.setAttribute('x', '15');
    leftLabel.setAttribute('y', '55');
    leftLabel.setAttribute('fill', '#00d4ff');
    leftLabel.setAttribute('font-size', '6');
    leftLabel.setAttribute('opacity', '0.5');
    leftLabel.textContent = 'DIA';
    svg.appendChild(leftLabel);

    const rightLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    rightLabel.setAttribute('x', '105');
    rightLabel.setAttribute('y', '55');
    rightLabel.setAttribute('fill', '#ff006e');
    rightLabel.setAttribute('font-size', '6');
    rightLabel.setAttribute('opacity', '0.5');
    rightLabel.textContent = 'PAL';
    svg.appendChild(rightLabel);

    // Clear container and append
    this.container.innerHTML = '';
    this.container.appendChild(svg);
    this.svg = svg;
  }

  updateState(data) {
    // Update left hemisphere
    if (data.left) {
      this.state.left.active = data.left.active || false;
      this.state.left.thinking = data.left.thinking || false;
      this.state.left.intensity = data.left.thinking ? 1 : (data.left.active ? 0.5 : 0.3);
      
      const leftPath = document.getElementById('brain-left');
      if (leftPath) {
        leftPath.style.opacity = this.state.left.intensity;
        leftPath.style.filter = this.state.left.thinking 
          ? 'url(#glow-cyan) brightness(1.5)' 
          : 'url(#glow-cyan)';
      }
    }

    // Update right hemisphere
    if (data.right) {
      this.state.right.active = data.right.active || false;
      this.state.right.thinking = data.right.thinking || false;
      this.state.right.intensity = data.right.thinking ? 1 : (data.right.active ? 0.5 : 0.3);
      
      const rightPath = document.getElementById('brain-right');
      if (rightPath) {
        rightPath.style.opacity = this.state.right.intensity;
        rightPath.style.filter = this.state.right.thinking 
          ? 'url(#glow-magenta) brightness(1.5)' 
          : 'url(#glow-magenta)';
      }
    }

    // Update corpus callosum
    if (data.corpus) {
      this.state.corpus.active = data.corpus.active || false;
      this.state.corpus.intensity = data.corpus.active ? 0.8 : 0;
      
      const corpusPath = document.getElementById('brain-corpus');
      if (corpusPath) {
        corpusPath.style.opacity = this.state.corpus.intensity;
        corpusPath.style.filter = this.state.corpus.active 
          ? 'url(#glow-amber) brightness(1.5)' 
          : 'url(#glow-amber)';
      }
    }

    // Update CSS variables
    this.updateCSSVars();
    
    // Update page borders
    this.updatePageBorders();
  }

  updateCSSVars() {
    const root = document.documentElement;
    root.style.setProperty('--brain-left', this.state.left.intensity);
    root.style.setProperty('--brain-right', this.state.right.intensity);
    root.style.setProperty('--brain-corpus', this.state.corpus.intensity);
    
    // Update pulse speed based on activity
    const totalActivity = this.state.left.intensity + this.state.right.intensity + this.state.corpus.intensity;
    const pulseSpeed = Math.max(0.5, 3 - totalActivity);
    root.style.setProperty('--pulse-speed', `${pulseSpeed}s`);
  }

  updatePageBorders() {
    // Find all elements with pulse-border class
    const borders = document.querySelectorAll('.pulse-border');
    
    // Determine dominant hemisphere
    let color = 'rgba(0, 212, 255, 0.3)';
    
    if (this.state.left.thinking) {
      color = 'rgba(0, 212, 255, 0.5)';
    } else if (this.state.right.thinking) {
      color = 'rgba(255, 0, 110, 0.5)';
    } else if (this.state.corpus.active) {
      color = 'rgba(139, 92, 246, 0.5)';
    }
    
    // Apply glow to all borders
    borders.forEach(el => {
      el.style.setProperty('--pulse-color', color);
    });
  }

  getState() {
    return this.state;
  }
}

window.BrainSVG = BrainSVG;

document.addEventListener('DOMContentLoaded', () => {
  if (window.Bicameris) {
    window.Bicameris.subscribe('inferenceState', (phase) => {
      const leftEl = document.getElementById('brain-left');
      const rightEl = document.getElementById('brain-right');
      const corpusEl = document.getElementById('brain-corpus');
      
      if (leftEl) leftEl.style.opacity = '0.3';
      if (rightEl) rightEl.style.opacity = '0.3';
      if (corpusEl) corpusEl.style.opacity = '0.3';
      
      if (phase === 'left' || phase === 'audit') {
        if (leftEl) leftEl.style.opacity = '1';
      } else if (phase === 'right' || phase === 'hypotheses') {
        if (rightEl) rightEl.style.opacity = '1';
      } else if (phase === 'synthesis' || phase === 'crucible') {
        if (corpusEl) corpusEl.style.opacity = '1';
      }
    });
    
    window.Bicameris.subscribe('telemetry', (telemetry) => {
      const speed = Math.max(1, 4 - telemetry.pulse * 3);
      document.documentElement.style.setProperty('--pulse-speed', `${speed}s`);
    });
  }
});
