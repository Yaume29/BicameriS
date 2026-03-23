// Chat functionality
let temperature = 0.7;

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
    
    // Disable button to prevent spam
    sendBtn.disabled = true;
    sendBtn.textContent = 'Envoi...';
    
    addMessage('user', message);
    input.value = '';
    
    // Show loading
    const loadingMsg = addMessage('assistant', '<em>Réfléchit...</em>');
    
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: message,
            temperature: parseFloat(temperature),
            max_tokens: 2048
        })
    })
    .then(r => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    })
    .then(data => {
        // Remove loading
        loadingMsg.remove();
        
        if (data.answer) {
            addMessage('assistant', data.answer);
        } else if (data.error) {
            addMessage('assistant', 'Erreur: ' + data.error);
        }
    })
    .catch(err => {
        loadingMsg.remove();
        addMessage('assistant', 'Erreur: ' + err.message);
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
    if (e.key === 'Enter') sendMessage();
});

document.getElementById('clear-chat').addEventListener('click', function() {
    fetch('/api/clear_chat', {method: 'POST'})
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

// Check status on load
checkInceptionStatus();
