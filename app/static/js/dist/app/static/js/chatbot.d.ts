/**
 * Chatbot - TypeScript Version
 * Handles Ollama chatbot integration
 * Modernized with APIClient
 */
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
export declare function toggleChatbot(): void;
/**
 * Send message
 */
export declare function sendMessage(): Promise<void>;
/**
 * Initialize chatbot event listeners
 */
export declare function initializeChatbot(): void;
/**
 * Clear chat history
 */
export declare function clearChatHistory(): void;
/**
 * Get chat history
 */
export declare function getChatHistory(): ChatMessage[];
//# sourceMappingURL=chatbot.d.ts.map