/**
 * BICAMERIS - Entropy Graph Component
 * Real-time visualization with CPU, GPU, and Brain metrics
 * Supports multiple graph types: wave, bar, area, scatter
 */

class EntropyGraph {
  constructor(containerId, width = 260, height = 100) {
    this.container = document.getElementById(containerId);
    this.width = width;
    this.height = height;
    this.padding = 4;
    this.dataPoints = 60;
    this.data = [];
    this.interval = null;
    this.graphType = localStorage.getItem('entropy-graph-type') || 'wave';
    
    this.graphTypes = [
      { id: 'wave', name: 'Onde', icon: '〰️' },
      { id: 'bar', name: 'Barres', icon: '📊' },
      { id: 'area', name: 'Aire', icon: '📈' },
      { id: 'scatter', name: 'Points', icon: '🔹' }
    ];
    
    this.init();
  }

  init() {
    // Initialize with sine/cosine waves + hardware
    const now = Date.now();
    for (let i = 0; i < this.dataPoints; i++) {
      this.data.push({
        timestamp: now - (this.dataPoints - i) * 1000,
        cpu: 0.3 + 0.2 * Math.sin(i * 0.12) + Math.random() * 0.1,
        gpu: 0.4 + 0.25 * Math.cos(i * 0.1) + Math.random() * 0.15,
        left: 0.5 + 0.3 * Math.sin(i * 0.15) + 0.1 * Math.sin(i * 0.3),
        right: 0.5 + 0.3 * Math.cos(i * 0.15) + 0.1 * Math.cos(i * 0.25),
        corpus: 0.5 + 0.2 * Math.sin(i * 0.1 + 1) + 0.15 * Math.sin(i * 0.2),
      });
    }

    this.render();
    this.startAnimation();
  }

  setGraphType(type) {
    this.graphType = type;
    localStorage.setItem('entropy-graph-type', type);
    this.render();
  }

  render() {
    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`);
    svg.setAttribute('width', '100%');
    svg.classList.add('entropy-svg');
    svg.id = 'entropy-svg';

    // Header with graph type selector
    const header = document.createElement('div');
    header.className = 'entropy-header';
    
    let graphTypeButtons = this.graphTypes.map(t => 
      `<button class="graph-type-btn ${this.graphType === t.id ? 'active' : ''}" data-type="${t.id}" title="${t.name}">${t.icon}</button>`
    ).join('');
    
    header.innerHTML = `
      <span class="entropy-title">Entropie</span>
      <div class="graph-type-selector">${graphTypeButtons}</div>
    `;

    // Add click handlers for graph type buttons
    setTimeout(() => {
      header.querySelectorAll('.graph-type-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          this.setGraphType(btn.dataset.type);
        });
      });
    }, 0);

    // Legend
    const legend = document.createElement('div');
    legend.className = 'entropy-legend';
    legend.innerHTML = `
      <span><span class="color-dot" style="background: #f59e0b;"></span> CPU</span>
      <span><span class="color-dot" style="background: #10b981;"></span> GPU</span>
      <span><span class="color-dot" style="background: #00d4ff;"></span> L</span>
      <span><span class="color-dot" style="background: #ff006e;"></span> R</span>
      <span><span class="color-dot" style="background: #8b5cf6;"></span> C</span>
    `;

    // Defs for gradients
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <linearGradient id="entropyGradCPU" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.2"/>
        <stop offset="100%" stop-color="#f59e0b" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="entropyGradGPU" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#10b981" stop-opacity="0.2"/>
        <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="entropyGradL" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#00d4ff" stop-opacity="0.15"/>
        <stop offset="100%" stop-color="#00d4ff" stop-opacity="0"/>
      </linearGradient>
    `;
    svg.appendChild(defs);

    // Grid lines
    const gridLines = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    [0.25, 0.5, 0.75].forEach(ratio => {
      const y = this.padding + ratio * (this.height - 2 * this.padding);
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', this.padding);
      line.setAttribute('y1', y);
      line.setAttribute('x2', this.width - this.padding);
      line.setAttribute('y2', y);
      line.setAttribute('stroke', 'rgba(255,255,255,0.04)');
      line.setAttribute('stroke-width', '0.5');
      gridLines.appendChild(line);
    });
    svg.appendChild(gridLines);

    // Area fills (background layer - hardware)
    const cpuArea = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    cpuArea.setAttribute('id', 'entropy-cpu-area');
    cpuArea.setAttribute('fill', 'url(#entropyGradCPU)');
    cpuArea.setAttribute('stroke', 'none');
    svg.appendChild(cpuArea);

    const gpuArea = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    gpuArea.setAttribute('id', 'entropy-gpu-area');
    gpuArea.setAttribute('fill', 'url(#entropyGradGPU)');
    gpuArea.setAttribute('stroke', 'none');
    svg.appendChild(gpuArea);

    // CPU line
    const cpuLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    cpuLine.setAttribute('id', 'entropy-cpu');
    cpuLine.setAttribute('fill', 'none');
    cpuLine.setAttribute('stroke', '#f59e0b');
    cpuLine.setAttribute('stroke-width', '1');
    cpuLine.setAttribute('opacity', '0.6');
    svg.appendChild(cpuLine);

    // GPU line
    const gpuLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    gpuLine.setAttribute('id', 'entropy-gpu');
    gpuLine.setAttribute('fill', 'none');
    gpuLine.setAttribute('stroke', '#10b981');
    gpuLine.setAttribute('stroke-width', '1');
    gpuLine.setAttribute('opacity', '0.6');
    svg.appendChild(gpuLine);

    // Left line (brain - more visible)
    const leftLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    leftLine.setAttribute('id', 'entropy-left');
    leftLine.setAttribute('fill', 'none');
    leftLine.setAttribute('stroke', '#00d4ff');
    leftLine.setAttribute('stroke-width', '1.5');
    leftLine.setAttribute('opacity', '0.85');
    svg.appendChild(leftLine);

    // Right line (brain)
    const rightLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    rightLine.setAttribute('id', 'entropy-right');
    rightLine.setAttribute('fill', 'none');
    rightLine.setAttribute('stroke', '#ff006e');
    rightLine.setAttribute('stroke-width', '1.5');
    rightLine.setAttribute('opacity', '0.85');
    svg.appendChild(rightLine);

    // Corpus line (dashed)
    const corpusLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    corpusLine.setAttribute('id', 'entropy-corpus');
    corpusLine.setAttribute('fill', 'none');
    corpusLine.setAttribute('stroke', '#8b5cf6');
    corpusLine.setAttribute('stroke-width', '1.2');
    corpusLine.setAttribute('stroke-dasharray', '3 2');
    corpusLine.setAttribute('opacity', '0.7');
    svg.appendChild(corpusLine);

    // Current value dots
    const createDot = (id, color, delay) => {
      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('id', id);
      dot.setAttribute('r', '2.5');
      dot.setAttribute('fill', color);
      dot.classList.add('animate-socket-pulse');
      if (delay) dot.style.animationDelay = delay;
      return dot;
    };

    svg.appendChild(createDot('entropy-dot-cpu', '#f59e0b', '0s'));
    svg.appendChild(createDot('entropy-dot-gpu', '#10b981', '0.3s'));
    svg.appendChild(createDot('entropy-dot-left', '#00d4ff', '0.5s'));
    svg.appendChild(createDot('entropy-dot-right', '#ff006e', '0.8s'));
    svg.appendChild(createDot('entropy-dot-corpus', '#8b5cf6', '1s'));

    // Values display
    const valuesDiv = document.createElement('div');
    valuesDiv.className = 'entropy-values';
    valuesDiv.id = 'entropy-values-display';
    valuesDiv.innerHTML = `
      <span class="val-cpu">0%</span>
      <span class="val-gpu">0%</span>
      <span class="val-left">0%</span>
      <span class="val-right">0%</span>
      <span class="val-corpus">0%</span>
    `;

    // Clear container and add elements
    this.container.innerHTML = '';
    this.container.appendChild(header);
    this.container.appendChild(legend);
    this.container.appendChild(svg);
    this.container.appendChild(valuesDiv);
    this.svg = svg;

    this.updatePaths();
  }

  generatePath(key) {
    return this.data.map((d, i) => {
      const x = this.padding + (i / (this.data.length - 1)) * (this.width - 2 * this.padding);
      const y = this.padding + (1 - d[key]) * (this.height - 2 * this.padding);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');
  }

  generateAreaPath(key) {
    let path = this.generatePath(key);
    const lastX = this.width - this.padding;
    const firstX = this.padding;
    const bottomY = this.height - this.padding;
    path += ` L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
    return path;
  }

  updatePaths() {
    if (this.graphType === 'bar') {
      this.renderBarChart();
    } else if (this.graphType === 'scatter') {
      this.renderScatter();
    } else if (this.graphType === 'area') {
      this.renderAreaChart();
    } else {
      this.renderWaveChart();
    }
    
    this.updateValues();
  }

  renderWaveChart() {
    const keys = ['cpu', 'gpu', 'left', 'right', 'corpus'];
    keys.forEach(key => {
      const el = document.getElementById(`entropy-${key}`);
      if (el) {
        el.setAttribute('d', this.generatePath(key));
        el.style.display = 'block';
      }
      
      const areaEl = document.getElementById(`entropy-${key}-area`);
      if (areaEl) {
        areaEl.setAttribute('d', this.generateAreaPath(key));
        areaEl.style.display = 'block';
      }
    });
    this.updateDots();
  }

  renderBarChart() {
    const last = this.data[this.data.length - 1];
    const keys = [
      { key: 'cpu', color: '#f59e0b' },
      { key: 'gpu', color: '#10b981' },
      { key: 'left', color: '#00d4ff' },
      { key: 'right', color: '#ff006e' },
      { key: 'corpus', color: '#8b5cf6' }
    ];
    
    // Create or get bar group
    let barGroup = document.getElementById('entropy-bar-group');
    if (!barGroup) {
      barGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      barGroup.id = 'entropy-bar-group';
      const svg = document.getElementById('entropy-svg');
      const defs = svg.querySelector('defs');
      svg.insertBefore(barGroup, defs.nextSibling);
    }
    
    // Create bars
    const barWidth = (this.width - 2 * this.padding) / keys.length - 4;
    const maxHeight = this.height - 2 * this.padding;
    
    keys.forEach((k, i) => {
      const value = last[k.key];
      const barHeight = value * maxHeight;
      const x = this.padding + i * ((this.width - 2 * this.padding) / keys.length) + 2;
      const y = this.height - this.padding - barHeight;
      
      let bar = document.getElementById(`bar-${k.key}`);
      if (!bar) {
        bar = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bar.id = `bar-${k.key}`;
        barGroup.appendChild(bar);
      }
      
      bar.setAttribute('x', x);
      bar.setAttribute('y', y);
      bar.setAttribute('width', barWidth);
      bar.setAttribute('height', barHeight);
      bar.setAttribute('fill', k.color);
      bar.setAttribute('opacity', k.key === 'left' || k.key === 'right' ? '0.9' : '0.6');
      bar.setAttribute('rx', '2');
    });
    
    // Hide lines and dots
    ['cpu', 'gpu', 'left', 'right', 'corpus'].forEach(key => {
      const el = document.getElementById(`entropy-${key}`);
      if (el) el.style.display = 'none';
      const areaEl = document.getElementById(`entropy-${key}-area`);
      if (areaEl) areaEl.style.display = 'none';
    });
    this.hideDots();
  }

  renderScatter() {
    const last = this.data.slice(-10); // Last 10 points
    const keys = [
      { key: 'cpu', color: '#f59e0b' },
      { key: 'gpu', color: '#10b981' },
      { key: 'left', color: '#00d4ff' },
      { key: 'right', color: '#ff006e' },
      { key: 'corpus', color: '#8b5cf6' }
    ];
    
    // Create or get scatter group
    let scatterGroup = document.getElementById('entropy-scatter-group');
    if (!scatterGroup) {
      scatterGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      scatterGroup.id = 'entropy-scatter-group';
      const svg = document.getElementById('entropy-svg');
      const defs = svg.querySelector('defs');
      svg.insertBefore(scatterGroup, defs.nextSibling);
    }
    
    scatterGroup.innerHTML = '';
    
    keys.forEach(k => {
      last.forEach((d, i) => {
        const x = this.padding + (i / 10) * (this.width - 2 * this.padding);
        const y = this.padding + (1 - d[k.key]) * (this.height - 2 * this.padding);
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', x);
        circle.setAttribute('cy', y);
        circle.setAttribute('r', k.key === 'left' || k.key === 'right' ? '3' : '2');
        circle.setAttribute('fill', k.color);
        circle.setAttribute('opacity', k.key === 'left' || k.key === 'right' ? '0.9' : '0.6');
        scatterGroup.appendChild(circle);
      });
    });
    
    // Hide lines and dots
    ['cpu', 'gpu', 'left', 'right', 'corpus'].forEach(key => {
      const el = document.getElementById(`entropy-${key}`);
      if (el) el.style.display = 'none';
      const areaEl = document.getElementById(`entropy-${key}-area`);
      if (areaEl) areaEl.style.display = 'none';
    });
    this.hideDots();
  }

  renderAreaChart() {
    const keys = [
      { key: 'cpu', color: '#f59e0b' },
      { key: 'gpu', color: '#10b981' },
      { key: 'left', color: '#00d4ff' },
      { key: 'right', color: '#ff006e' },
      { key: 'corpus', color: '#8b5cf6' }
    ];
    
    keys.forEach(k => {
      const el = document.getElementById(`entropy-${k.key}`);
      if (el) {
        el.setAttribute('d', this.generatePath(k.key));
        el.setAttribute('stroke-width', '2');
        el.setAttribute('opacity', k.key === 'left' || k.key === 'right' ? '1' : '0.7');
        el.style.display = 'block';
      }
      
      const areaEl = document.getElementById(`entropy-${k.key}-area`);
      if (areaEl) {
        areaEl.setAttribute('d', this.generateAreaPath(k.key));
        areaEl.setAttribute('opacity', '0.3');
        areaEl.style.display = 'block';
      }
    });
    this.updateDots();
  }

  hideDots() {
    ['cpu', 'gpu', 'left', 'right', 'corpus'].forEach(key => {
      const dot = document.getElementById(`entropy-dot-${key}`);
      if (dot) dot.style.display = 'none';
    });
  }

  updateDots() {
    const last = this.data[this.data.length - 1];
    const dots = [
      { id: 'entropy-dot-cpu', key: 'cpu' },
      { id: 'entropy-dot-gpu', key: 'gpu' },
      { id: 'entropy-dot-left', key: 'left' },
      { id: 'entropy-dot-right', key: 'right' },
      { id: 'entropy-dot-corpus', key: 'corpus' }
    ];

    dots.forEach(dot => {
      const el = document.getElementById(dot.id);
      if (el) {
        const x = this.width - this.padding;
        const y = this.padding + (1 - last[dot.key]) * (this.height - 2 * this.padding);
        el.setAttribute('cx', x);
        el.setAttribute('cy', y);
      }
    });
  }

  updateValues() {
    const last = this.data[this.data.length - 1];
    const valuesEl = document.getElementById('entropy-values-display');
    if (valuesEl) {
      valuesEl.innerHTML = `
        <span class="val-cpu">${(last.cpu * 100).toFixed(0)}%</span>
        <span class="val-gpu">${(last.gpu * 100).toFixed(0)}%</span>
        <span class="val-left">${(last.left * 100).toFixed(0)}%</span>
        <span class="val-right">${(last.right * 100).toFixed(0)}%</span>
        <span class="val-corpus">${(last.corpus * 100).toFixed(0)}%</span>
      `;
    }
  }

  startAnimation() {
    this.interval = setInterval(() => {
      this.update();
    }, 1000);
  }

  update() {
    const last = this.data[this.data.length - 1];
    const newPoint = {
      timestamp: Date.now(),
      cpu: Math.max(0.1, Math.min(0.9, last.cpu + (Math.random() - 0.5) * 0.06)),
      gpu: Math.max(0.1, Math.min(0.9, last.gpu + (Math.random() - 0.5) * 0.08)),
      left: Math.max(0.1, Math.min(0.9, last.left + (Math.random() - 0.5) * 0.08)),
      right: Math.max(0.1, Math.min(0.9, last.right + (Math.random() - 0.5) * 0.08)),
      corpus: Math.max(0.1, Math.min(0.9, last.corpus + (Math.random() - 0.5) * 0.06)),
    };

    this.data.push(newPoint);
    if (this.data.length > this.dataPoints) {
      this.data.shift();
    }

    this.updatePaths();
  }

  // Method to update with real hardware data
  updateHardware(cpuUsage, gpuUsage) {
    if (this.data.length > 0) {
      const last = this.data[this.data.length - 1];
      this.data.push({
        timestamp: Date.now(),
        cpu: cpuUsage !== undefined ? cpuUsage : last.cpu,
        gpu: gpuUsage !== undefined ? gpuUsage : last.gpu,
        left: last.left,
        right: last.right,
        corpus: last.corpus,
      });
      if (this.data.length > this.dataPoints) {
        this.data.shift();
      }
      this.updatePaths();
    }
  }

  destroy() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
}

// Export
window.EntropyGraph = EntropyGraph;
