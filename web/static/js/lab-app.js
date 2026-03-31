/**
 * LAB APPLICATION - Technical Chat Module
 * INTÉGRATION COMPLÈTE avec le système cognitif bicaméral
 */

class LabApp {
  constructor() {
    this.activeSpecialist = 'research';
    this.activeConversation = null;
    this.activeWorkspace = null;
    this.autonomousMode = false;
    this.conversations = [];
    this.tools = [];
    this.thinking = false;

    this.sidebar = document.getElementById('lab-sidebar');
    this.workspace = document.getElementById('lab-workspace');
    this.messagesContainer = document.getElementById('chat-messages');
    this.chatInput = document.getElementById('chat-input');
    this.sendBtn = document.getElementById('send-btn');

    this.specialists = {
      research: { icon: '🔬', name: 'Research', hemisphere: 'both' },
      python: { icon: '🐍', name: 'Python Expert', hemisphere: 'left' },
      uiux: { icon: '🎨', name: 'UI/UX Designer', hemisphere: 'right' },
      multi: { icon: '🌐', name: 'Multi Expert', hemisphere: 'both' }
    };

    this.init();
  }
  
  init() {
    this.bindEvents();
    this.loadTools();
    this.loadConversations();
    this.updateActiveSpecialistUI();
  }
  
  async loadTools() {
    try {
      const response = await fetch('/api/lab/tools');
      const data = await response.json();
      this.tools = data.tools || [];
      console.log('[Lab] Tools loaded:', this.tools);
    } catch (e) {
      console.error('[Lab] Failed to load tools:', e);
    }
  }
  
  bindEvents() {
    document.getElementById('toggle-left').addEventListener('click', () => {
      this.sidebar.classList.toggle('collapsed');
      const btn = document.getElementById('toggle-left');
      btn.querySelector('span').textContent = this.sidebar.classList.contains('collapsed') ? '▶' : '◀';
    });
    
    document.getElementById('toggle-right').addEventListener('click', () => this.toggleWorkspace());
    document.getElementById('toggle-workspace-btn').addEventListener('click', () => this.toggleWorkspace());
    
    document.querySelectorAll('.specialist-card').forEach(card => {
      card.addEventListener('click', () => this.selectSpecialist(card.dataset.specialist));
    });
    
    document.getElementById('new-chat-btn').addEventListener('click', () => this.createNewConversation());
    
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    document.getElementById('autonomous-mode-btn').addEventListener('click', () => this.toggleAutonomousMode());
    
    document.getElementById('run-btn').addEventListener('click', () => this.runTool());
    document.getElementById('save-btn').addEventListener('click', () => this.saveWorkspace());
    document.getElementById('new-file-btn').addEventListener('click', () => this.createNewFile());
  }
  
  toggleWorkspace() {
    this.workspace.classList.toggle('expanded');
    const btn = document.getElementById('toggle-right');
    btn.querySelector('span').textContent = this.workspace.classList.contains('expanded') ? '◀' : '▶';
  }
  
  selectSpecialist(specialistId) {
    this.activeSpecialist = specialistId;
    document.querySelectorAll('.specialist-card').forEach(card => {
      card.classList.toggle('active', card.dataset.specialist === specialistId);
    });
    this.updateActiveSpecialistUI();
  }
  
  updateActiveSpecialistUI() {
    const specialist = this.specialists[this.activeSpecialist];
    document.getElementById('active-specialist-icon').textContent = specialist.icon;
    document.getElementById('active-specialist-name').textContent = specialist.name;
  }
  
  async createNewConversation() {
    try {
      const response = await fetch('/api/lab/conversation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          specialist_id: this.activeSpecialist,
          workspace_name: 'Projet ' + new Date().toLocaleTimeString('fr-FR')
        })
      });
      
      const data = await response.json();
      if (data.status !== 'ok') {
        this.addMessage('system', 'Erreur: ' + data.message);
        return;
      }
      
      this.activeConversation = data.conversation.id;
      this.activeWorkspace = data.conversation.workspace_id;
      
      this.messagesContainer.innerHTML = '';
      this.addMessage('system', `🔬 Nouveau projet avec ${specialist.name}! L'IA peut maintenant réfléchir avec mes deux hemispheres.`);
      
      document.getElementById('active-workspace-name').textContent = data.conversation.title;
      this.loadConversations();
      
    } catch (error) {
      console.error('Error:', error);
      this.addMessage('system', 'Erreur de connexion.');
    }
  }
  
  async sendMessage() {
    const message = this.chatInput.value.trim();
    if (!message || this.thinking) return;
    
    if (!this.activeConversation) {
      await this.createNewConversation();
    }
    
    this.addMessage('user', message);
    this.chatInput.value = '';
    this.thinking = true;
    this.showTyping(true);
    
    try {
      const response = await fetch(`/api/lab/conversation/${this.activeConversation}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          specialist_id: this.activeSpecialist
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        this.addMessage('specialist', data.response);
        
        if (data.thoughts) {
          this.addMessage('system', `🧠 Pensée: ${data.thoughts.left ? 'Hemisphere gauche activé' : ''} ${data.thoughts.right ? '| Hemisphere droit activé' : ''}`);
        }
      } else {
        this.addMessage('system', 'Erreur: ' + (data.message || 'Inconnu'));
      }
      
    } catch (error) {
      console.error('Error:', error);
      this.addMessage('system', 'Erreur de connexion au cerveau.');
    }
    
    this.thinking = false;
    this.showTyping(false);
  }
  
  addMessage(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    
    const time = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\n/g, '<br>');
    
    messageEl.innerHTML = `
      <div class="message-content">${content}</div>
      <div class="message-time">${time}</div>
    `;
    
    this.messagesContainer.appendChild(messageEl);
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
  
  showTyping(show) {
    const existing = document.querySelector('.typing-indicator');
    if (show && !existing) {
      const indicator = document.createElement('div');
      indicator.className = 'typing-indicator active';
      indicator.innerHTML = `
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
        <span class="typing-text">Aetheris reflechit...</span>
      `;
      this.messagesContainer.appendChild(indicator);
    } else if (!show && existing) {
      existing.remove();
    }
  }
  
  async loadConversations() {
    try {
      const response = await fetch('/api/lab/conversations');
      const data = await response.json();
      this.conversations = data.conversations || [];
      this.renderConversationsList();
    } catch (error) {
      console.error('Error:', error);
    }
  }
  
  renderConversationsList() {
    const container = document.getElementById('conversations-list');
    container.innerHTML = '';
    
    if (this.conversations.length === 0) {
      container.innerHTML = '<div class="empty-state">Aucune conversation</div>';
      return;
    }
    
    this.conversations.forEach(conv => {
      const item = document.createElement('div');
      item.className = `conversation-item ${conv.id === this.activeConversation ? 'active' : ''}`;
      item.innerHTML = `
        <div class="conversation-title">${this.escapeHtml(conv.title)}</div>
        <div class="conversation-preview">${conv.messages?.slice(-1)?.[0]?.content?.substring(0, 40) || ''}...</div>
        <div class="conversation-time">${this.formatDate(conv.updated_at)}</div>
      `;
      item.addEventListener('click', () => this.loadConversation(conv.id));
      container.appendChild(item);
    });
  }
  
  async loadConversation(conversationId) {
    try {
      const response = await fetch(`/api/lab/conversation/${conversationId}`);
      const data = await response.json();
      
      this.activeConversation = conversationId;
      this.activeWorkspace = data.conversation.workspace_id;
      
      document.getElementById('active-workspace-name').textContent = data.conversation.title;
      
      this.messagesContainer.innerHTML = '';
      data.conversation.messages.forEach(msg => {
        this.addMessage(msg.role, msg.content);
      });
      
      this.loadWorkspaceFiles(data.conversation.workspace_id);
      
    } catch (error) {
      console.error('Error:', error);
    }
  }
  
  async loadWorkspaceFiles(workspaceId) {
    try {
      const response = await fetch(`/api/lab/workspace/${workspaceId}`);
      const data = await response.json();
      
      const container = document.getElementById('file-tree');
      
      if (!data.workspace || data.workspace.files.length === 0) {
        container.innerHTML = `
          <div class="empty-workspace">
            <p>Aucun fichier</p>
            <button class="tool-btn" id="create-first-file">+ Creer un fichier</button>
          </div>
        `;
        document.getElementById('create-first-file')?.addEventListener('click', () => this.createNewFile());
        return;
      }
      
      container.innerHTML = '';
      data.workspace.files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        const icon = this.getFileIcon(file.name);
        item.innerHTML = `
          <span class="file-icon ${icon}">${icon === 'folder' ? '📁' : '📄'}</span>
          <span>${this.escapeHtml(file.name)}</span>
        `;
        item.addEventListener('click', () => this.loadFileContent(workspaceId, file.name));
        container.appendChild(item);
      });
      
    } catch (error) {
      console.error('Error:', error);
    }
  }
  
  async loadFileContent(workspaceId, filename) {
    try {
      const response = await fetch(`/api/lab/workspace/${workspaceId}/file/${filename}`);
      const data = await response.json();
      
      document.getElementById('preview-filename').textContent = filename;
      document.getElementById('file-content').textContent = data.content || '// Fichier vide';
      
    } catch (error) {
      console.error('Error:', error);
    }
  }
  
  toggleAutonomousMode() {
    this.autonomousMode = !this.autonomousMode;
    
    const btn = document.getElementById('autonomous-mode-btn');
    
    if (this.autonomousMode) {
      btn.style.background = 'var(--accent-amber)';
      btn.style.color = '#000';
      btn.title = 'Desactiver le mode autonome';
      
      if (!this.activeConversation) {
        this.createNewConversation();
      }
      
      this.addMessage('system', '⚡ MODE AUTONOME ACTIVÉ\nL\'IA va maintenant travailler seule sur votre projet.');
      
      const task = prompt('Quelle tache autonome? (ex: "Analyse ce code et propose des ameliorations")');
      if (task) {
        this.runAutonomousTask(task);
      }
    } else {
      btn.style.background = '';
      btn.style.color = '';
      btn.title = 'Mode autonome';
      this.addMessage('system', '⚡ Mode autonome désactivé');
    }
  }
  
  async runAutonomousTask(task) {
    if (!this.activeConversation) return;
    
    this.showTyping(true);
    this.addMessage('system', `[AUTONOME] Travail sur: ${task}`);
    
    try {
      const response = await fetch(`/api/lab/autonomous/${this.activeConversation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: task })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        this.addMessage('specialist', data.result.response);
      } else {
        this.addMessage('system', 'Erreur: ' + data.message);
      }
      
    } catch (error) {
      console.error('Autonomous error:', error);
      this.addMessage('system', 'Erreur lors de la tache autonome');
    }
    
    this.showTyping(false);
  }
  
  async runTool() {
    const toolName = prompt(`Outils disponibles:\n${this.tools.map(t => `- ${t.name}: ${t.description}`).join('\n')}\n\nQuel outil executer?`);
    if (!toolName) return;
    
    const tool = this.tools.find(t => t.name === toolName);
    if (!tool) {
      this.addMessage('system', `Outil non trouve: ${toolName}`);
      return;
    }
    
    let params = {};
    if (toolName === 'read_file' || toolName === 'write_file') {
      params.path = prompt('Chemin du fichier:');
      if (toolName === 'write_file') {
        params.content = prompt('Contenu:');
      }
    } else if (toolName === 'search_code') {
      params.pattern = prompt('Motif a rechercher:');
    } else if (toolName === 'run_command') {
      params.cmd = prompt('Commande a executer:');
    }
    
    this.addMessage('system', `[OUTIL] Execution de ${toolName}...`);
    
    try {
      const response = await fetch(`/api/lab/tool/${toolName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: this.activeConversation,
          ...params
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        this.addMessage('system', `✅ Resultat: ${JSON.stringify(data.result).substring(0, 500)}`);
      } else {
        this.addMessage('system', `❌ Erreur: ${data.error}`);
      }
      
    } catch (error) {
      console.error('Tool error:', error);
      this.addMessage('system', 'Erreur lors de l\'execution de l\'outil');
    }
  }
  
  async saveWorkspace() {
    const content = document.getElementById('file-content').textContent;
    const filename = document.getElementById('preview-filename').textContent;
    
    if (!filename || filename === 'main.py') {
      this.addMessage('system', 'Creer d\'abord un fichier');
      return;
    }
    
    try {
      const response = await fetch(`/api/lab/workspace/${this.activeWorkspace}/file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename,
          content: content
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        this.addMessage('system', `💾 Fichier ${filename} sauvegardé`);
        this.loadWorkspaceFiles(this.activeWorkspace);
      } else {
        this.addMessage('system', 'Erreur: ' + data.message);
      }
      
    } catch (error) {
      console.error('Save error:', error);
    }
  }
  
  async createNewFile() {
    if (!this.activeWorkspace) {
      await this.createNewConversation();
    }
    
    const filename = prompt('Nom du fichier (ex: main.py, test.js):');
    if (!filename) return;
    
    const content = prompt('Contenu initial (ou vide):', '# ' + filename + '\n');
    
    try {
      const response = await fetch(`/api/lab/workspace/${this.activeWorkspace}/file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename,
          content: content || ''
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'ok') {
        this.addMessage('system', `✅ Fichier ${filename} cree`);
        this.loadWorkspaceFiles(this.activeWorkspace);
        document.getElementById('preview-filename').textContent = filename;
        document.getElementById('file-content').textContent = content || '';
      } else {
        this.addMessage('system', 'Erreur: ' + data.message);
      }
      
    } catch (error) {
      console.error('Create file error:', error);
    }
  }
  
  getFileIcon(filename) {
    if (filename.endsWith('/')) return 'folder';
    if (filename.endsWith('.py')) return 'py';
    if (filename.endsWith('.js')) return 'js';
    if (filename.endsWith('.html')) return 'html';
    if (filename.endsWith('.css')) return 'css';
    return 'file';
  }
  
  formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  async setEditeurMode(mode) {
    try {
      const response = await fetch('/api/lab/editeur-specialiste', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_mode', mode: mode })
      });
      const data = await response.json();
      
      if (data.status === 'ok') {
        document.querySelectorAll('.mode-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        const autoConfirmBtn = document.getElementById('auto-confirm-btn');
        if (mode === 'construire') {
          autoConfirmBtn.style.display = 'block';
        } else {
          autoConfirmBtn.style.display = 'none';
        }
        
        this.addMessage('system', `Mode ${data.mode_info.name} activé.`);
        
        const permsResponse = await fetch('/api/lab/editeur-specialiste', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'get_mode_permissions', mode: mode })
        });
        const permsData = await permsResponse.json();
        
        if (permsData.permissions) {
          this.addMessage('system', `Permissions: Agents: ${permsData.permissions.agents ? '✓' : '✗'}, Écriture: ${permsData.permissions.file_write ? '✓' : '✗'}, Web: ${permsData.permissions.web ? '✓' : '✗'}`);
        }
      }
    } catch (error) {
      console.error('Mode switch error:', error);
    }
  }
  
  async toggleAutoConfirm() {
    try {
      const response = await fetch('/api/lab/editeur-specialiste', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'toggle_auto_confirm', enabled: null })
      });
      const data = await response.json();
      
      const btn = document.getElementById('auto-confirm-btn');
      btn.classList.toggle('active', data.auto_confirm);
      btn.title = data.auto_confirm ? 'Auto-confirmer (activé)' : 'Auto-confirmer (désactivé)';
      
    } catch (error) {
      console.error('Auto-confirm toggle error:', error);
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.labApp = new LabApp();
});

function setEditeurMode(mode) {
  if (window.labApp) {
    window.labApp.setEditeurMode(mode);
  }
}

function toggleAutoConfirm() {
  if (window.labApp) {
    window.labApp.toggleAutoConfirm();
  }
}
