/**
 * Chatbot JavaScript
 * Handles Ollama chatbot integration
 * Modernized with APIClient
 */

// Toggle chatbot visibility
function toggleChatbot() {
    const overlay = document.getElementById('chatbotOverlay');
    if (!overlay) return;

    overlay.classList.toggle('hidden');

    // Focus input when opening
    if (!overlay.classList.contains('hidden')) {
        const input = document.getElementById('chatInput');
        if (input) input.focus();
    }
}

// Send message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat(message, 'user');

    // Clear input
    input.value = '';

    // Show loading
    const loadingId = addMessageToChat('Denke nach...', 'bot');

    try {
        // Send to API using APIClient
        const data = await api.chat.send(message);

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        // Add bot response
        addMessageToChat(data.response || 'Entschuldigung, ich konnte keine Antwort generieren.', 'bot');

    } catch (error) {
        console.error('Error sending message:', error);

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        // Show error
        addMessageToChat('Fehler beim Senden der Nachricht. Bitte versuche es erneut.', 'bot');
    }
}

// Add message to chat UI
function addMessageToChat(message, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return null;

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
    const sendBtn = document.getElementById('sendMessageBtn');
    const toggleBtn = document.getElementById('chatbotToggle');
    const closeBtn = document.getElementById('chatbotClose');

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleChatbot);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', toggleChatbot);
    }
});
