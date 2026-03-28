// Chat functionality with Markdown + Syntax Highlighting
let temperature = 0.7;

// Simple markdown parser (no external dependencies)
function parseMarkdown(text) {
    let html = text;
    
    // Escape HTML
    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Code blocks with syntax highlighting
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
        const langClass = lang ? 'language-' + lang : 'language-text';
        const highlighted = highlightCode(code.trim(), lang || 'text');
        return `<div class="code-block"><div class="code-header"><span class="code-lang">${lang || 'code'}</span><button class="copy-btn" onclick="copyCode(this)">Copy</button></div><pre class="${langClass}"><code>${highlighted}</code></pre></div>`;
    });
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    
    // Lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Simple syntax highlighter
function highlightCode(code, language) {
    const keywords = {
        python: ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return', 'import', 'from', 'as', 'try', 'except', 'with', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'yield', 'async', 'await'],
        javascript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'import', 'export', 'class', 'try', 'catch', 'async', 'await', 'true', 'false', 'null', 'undefined'],
        bash: ['echo', 'export', 'cd', 'ls', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep', 'pip', 'python', 'git'],
    };
    
    const lang = keywords[language] || keywords.python;
    
    let highlighted = code
        .replace(/&lt;/g, '&amp;lt;').replace(/&gt;/g, '&amp;gt;')
        .replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Strings
    highlighted = highlighted.replace(/(["'`])(?:(?!\1)[^\\]|\\.)*\1/g, '<span class="string">$&</span>');
    
    // Comments
    highlighted = highlighted.replace(/(#.*$|\/\/.*$)/gm, '<span class="comment">$1</span>');
    
    // Keywords
    for (const kw of lang) {
        const regex = new RegExp(`\\b(${kw})\\b`, 'g');
        highlighted = highlighted.replace(regex, '<span class="keyword">$1</span>');
    }
    
    // Numbers
    highlighted = highlighted.replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>');
    
    return highlighted;
}

// Copy code to clipboard
function copyCode(btn) {
    const code = btn.closest('.code-block').querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 1500);
    });
}

// Temperature slider
document.getElementById('temperature').addEventListener('input', function(e) {
    temperature = e.target.value;
    document.getElementById('temp-value').textContent = temperature;
});

// Send message
function sendMessage() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const message = input.value.trim();
    if (!message) return;
    
    sendBtn.disabled = true;
    sendBtn.textContent = 'Envoi...';
    
    addMessage('user', parseMarkdown(message));
    input.value = '';
    
    const loadingMsg = addMessage('assistant', '<em class="typing">Réfléchit...</em>');
    
    fetch('/api/chat/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: message,
            temperature: parseFloat(temperature)
        })
    })
    .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    })
    .then(data => {
        loadingMsg.remove();
        
        if (data.response) {
            addMessage('assistant', parseMarkdown(data.response));
        } else if (data.error) {
            addMessage('assistant', parseMarkdown('Erreur: ' + data.error));
        }
    })
    .catch(err => {
        loadingMsg.remove();
        addMessage('assistant', parseMarkdown('Erreur: ' + err.message));
    })
    .finally(() => {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Envoyer';
    });
}

function addMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

// Event listeners
document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

document.getElementById('clear-chat').addEventListener('click', function() {
    fetch('/api/chat/clear', {method: 'POST'})
        .then(r => r.json())
        .then(() => {
            document.getElementById('chat-messages').innerHTML = '';
        });
});

// Thought Inception
let inceptionAcknowledged = false;

function checkInceptionStatus() {
    fetch('/api/inception_status')
        .then(r => r.json())
        .then(data => {
            if (data.acknowledged) {
                inceptionAcknowledged = true;
                document.getElementById('inception-warning').style.display = 'none';
                document.getElementById('inception-form').style.display = 'block';
            }
        });
}

document.getElementById('acknowledge-btn').addEventListener('click', function() {
    const checkbox = document.getElementById('acknowledge-check');
    if (checkbox.checked) {
        fetch('/api/inception_ack', {method: 'POST'})
            .then(r => r.json())
            .then(() => {
                inceptionAcknowledged = true;
                document.getElementById('inception-warning').style.display = 'none';
                document.getElementById('inception-form').style.display = 'block';
            });
    }
});

document.getElementById('inception-btn').addEventListener('click', function() {
    const content = document.getElementById('inception-text').value.trim();
    if (!content) return;
    
    const level = document.getElementById('inception-level').value;
    const type = document.getElementById('inception-type').value;
    
    fetch('/api/inception', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            content: content,
            influence: level,
            type: type
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.id) {
            document.getElementById('inception-text').value = '';
            alert('Pensée induite créée!');
        } else if (data.error) {
            alert(data.error);
        }
    });
});

checkInceptionStatus();
