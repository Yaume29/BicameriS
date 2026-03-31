class ChatStream {
    constructor() {
        this.messagesContainer = null;
        this.chatInput = null;
        this.sendBtn = null;
        this.thinking = false;
        this.currentMode = 'dialogue_classique';
    }
    
    init() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('send-btn');
        
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }
    
    setMode(mode) {
        this.currentMode = mode;
        if (window.Bicameris) {
            window.Bicameris.setMode(mode);
        }
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.thinking) return;
        
        this.addMessage('user', message);
        this.chatInput.value = '';
        this.thinking = true;
        this.showTyping(true);
        
        if (window.Bicameris) {
            window.Bicameris.setInferenceState('processing');
        }
        
        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    settings: {
                        lab_mode: this.currentMode
                    }
                })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleStreamChunk(data);
                        } catch (e) {
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('Stream error:', error);
            this.addMessage('system', 'Erreur de connexion.');
        }
        
        this.thinking = false;
        this.showTyping(false);
        
        if (window.Bicameris) {
            window.Bicameris.setInferenceState('idle');
        }
    }
    
    handleStreamChunk(data) {
        const phase = data.phase;
        
        if (window.Bicameris) {
            window.Bicameris.setInferenceState(phase);
        }
        
        if (phase === 'left' && data.status === 'start') {
            this.addMessage('system', '🔵 Analyse en cours...');
        } else if (phase === 'left' && data.token) {
            this.appendToLastMessage(data.token);
        } else if (phase === 'left' && data.status === 'complete') {
            this.addNewLine();
        } else if (phase === 'right' && data.status === 'start') {
            this.addMessage('system', '💜 Intuition en cours...');
        } else if (phase === 'right' && data.token) {
            this.appendToLastMessage(data.token);
        } else if (phase === 'right' && data.status === 'complete') {
            this.addNewLine();
        } else if (phase === 'synthesis' && data.status === 'start') {
            this.addMessage('system', '⚡ Synthèse en cours...');
        } else if (phase === 'synthesis' && data.token) {
            this.appendToLastMessage(data.token);
        } else if (phase === 'synthesis' && data.status === 'complete') {
            this.addNewLine();
        } else if (phase === 'complete') {
            this.addMessage('system', '✅ Terminé');
        }
    }
    
    addMessage(role, content) {
        if (!this.messagesContainer) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}`;
        messageEl.textContent = content;
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    appendToLastMessage(text) {
        if (!this.messagesContainer) return;
        
        const messages = this.messagesContainer.querySelectorAll('.message');
        if (messages.length > 0) {
            const last = messages[messages.length - 1];
            last.textContent += text;
            this.scrollToBottom();
        }
    }
    
    addNewLine() {
        if (!this.messagesContainer) return;
        
        const messages = this.messagesContainer.querySelectorAll('.message');
        if (messages.length > 0) {
            const last = messages[messages.length - 1];
            last.textContent += '\n';
        }
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }
    
    showTyping(show) {
        const typingEl = document.getElementById('typing-indicator');
        if (typingEl) {
            typingEl.style.display = show ? 'block' : 'none';
        }
    }
}

window.ChatStream = new ChatStream();

document.addEventListener('DOMContentLoaded', () => {
    if (window.ChatStream) {
        window.ChatStream.init();
    }
});
