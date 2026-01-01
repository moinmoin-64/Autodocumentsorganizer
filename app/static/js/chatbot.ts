/**
 * Chatbot - TypeScript Version
 * Handles Ollama chatbot integration
 * Modernized with APIClient
 */

import { api } from './api-client';

/**
 * Chat message sender
 */
export type ChatSender = 'user' | 'bot';

/**
 * Chat message
 */
export interface ChatMessage {
    id: string;
    text: string;
    sender: ChatSender;
    timestamp: number;
}

/**
 * Toggle chatbot visibility
 */
export function toggleChatbot(): void {
    const overlay = document.getElementById('chatbotOverlay');
    if (!overlay) return;

    overlay.classList.toggle('hidden');

    // Focus input when opening
    if (!overlay.classList.contains('hidden')) {
        const input = document.getElementById('chatInput') as HTMLInputElement;
        if (input) input.focus();
    }
}

/**
 * Send message
 */
export async function sendMessage(): Promise<void> {
    const input = document.getElementById('chatInput') as HTMLInputElement | null;
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
        const response = (data as any).response || 'Entschuldigung, ich konnte keine Antwort generieren.';
        addMessageToChat(response, 'bot');

    } catch (error) {
        console.error('Error sending message:', error);

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        // Show error
        addMessageToChat('Fehler beim Senden der Nachricht. Bitte versuche es erneut.', 'bot');
    }
}

/**
 * Add message to chat UI
 */
function addMessageToChat(message: string, sender: ChatSender): string {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return '';

    const messageDiv = document.createElement('div');
    const messageId = `msg-${Date.now()}`;
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

/**
 * Initialize chatbot event listeners
 */
export function initializeChatbot(): void {
    const chatInput = document.getElementById('chatInput') as HTMLInputElement | null;
    const sendBtn = document.getElementById('sendMessageBtn') as HTMLButtonElement | null;
    const toggleBtn = document.getElementById('chatbotToggle') as HTMLButtonElement | null;
    const closeBtn = document.getElementById('chatbotClose') as HTMLButtonElement | null;

    if (chatInput) {
        chatInput.addEventListener('keypress', (e: KeyboardEvent) => {
            if (e.key === 'Enter') {
                sendMessage().catch(console.error);
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            sendMessage().catch(console.error);
        });
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleChatbot);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', toggleChatbot);
    }
}

/**
 * Clear chat history
 */
export function clearChatHistory(): void {
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
}

/**
 * Get chat history
 */
export function getChatHistory(): ChatMessage[] {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return [];

    const messages: ChatMessage[] = [];
    const messageElements = messagesContainer.querySelectorAll('.chat-message');

    messageElements.forEach((el, index) => {
        const p = el.querySelector('p');
        if (p && p.textContent) {
            const isBotMessage = el.classList.contains('bot-message');
            messages.push({
                id: el.id || `msg-${index}`,
                text: p.textContent,
                sender: isBotMessage ? 'bot' : 'user',
                timestamp: parseInt(el.id?.split('-')[1] || '0', 10)
            });
        }
    });

    return messages;
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChatbot);
} else {
    initializeChatbot();
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleChatbot,
        sendMessage,
        initializeChatbot,
        clearChatHistory,
        getChatHistory
    };
}
