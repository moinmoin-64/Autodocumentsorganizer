/**
 * Chatbot JavaScript
 * Handles Ollama chatbot integration
 */

// Toggle chatbot visibility
function toggleChatbot() {
    const overlay = document.getElementById('chatbotOverlay');
    overlay.classList.toggle('hidden');

    // Focus input when opening
    if (!overlay.classList.contains('hidden')) {
        document.getElementById('chatInput').focus();
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat(message, 'user');

    // Clear input
    input.value = '';

    // Show loading
    const loadingId = addMessageToChat('Denke nach...', 'bot');

    try {
        // Send to API
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        // Remove loading message
        document.getElementById(loadingId).remove();

        // Add bot response
        addMessageToChat(data.response || 'Entschuldigung, ich konnte keine Antwort generieren.', 'bot');

    } catch (error) {
        console.error('Error sending message:', error);

        // Remove loading message
        document.getElementById(loadingId).remove();

        // Show error
        addMessageToChat('Fehler beim Senden der Nachricht. Bitte versuche es erneut.', 'bot');
    }
}

// Add message to chat UI
function addMessageToChat(message, sender) {
    const messagesContainer = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now();
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${sender}-message`;

    const p = document.createElement('p');
    p.textContent = message;
    messageDiv.appendChild(p);

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return messageId;
}

// Send message on Enter key
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
