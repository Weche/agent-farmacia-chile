/**
 * Chat Manager - AI Chat Interface
 * Handles chat UI, messaging, and integration with AI agent
 * Created: August 30, 2025
 */

export class ChatManager {
    constructor() {
        this.sessionId = null;
        this.messages = [];
        this.isConnected = false;
        this.isTyping = false;
        this.chatWindow = null;
        this.chatBubble = null;
        this.isOpen = false;
        
        // Bind methods to preserve context
        this.toggleChat = this.toggleChat.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
        
        this.init();
    }
    
    init() {
        console.log('💬 Initializing Chat Manager...');
        this.setupElements();
        this.setupEventListeners();
        this.initializeSession();
    }
    
    setupElements() {
        this.chatWindow = document.getElementById('chatWindow');
        this.chatBubble = document.getElementById('chatToggle');
        this.messagesContainer = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendMessage');
        this.closeButton = document.getElementById('chatClose');
        this.typingIndicator = document.getElementById('aiThinking');
    }
    
    setupEventListeners() {
        // Chat bubble toggle
        if (this.chatBubble) {
            this.chatBubble.addEventListener('click', this.toggleChat);
        }
        
        // Close button
        if (this.closeButton) {
            this.closeButton.addEventListener('click', this.closeChat.bind(this));
        }
        
        // Send button
        if (this.sendButton) {
            this.sendButton.addEventListener('click', this.handleSendClick.bind(this));
        }
        
        // Input field
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', this.handleKeyPress);
            this.chatInput.addEventListener('input', this.handleTyping.bind(this));
        }
        
        // Click outside to close (optional)
        document.addEventListener('click', (e) => {
            if (this.isOpen && this.chatWindow && !this.chatWindow.contains(e.target) && 
                this.chatBubble && !this.chatBubble.contains(e.target)) {
                // Don't auto-close for now, user should explicitly close
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChat();
            }
        });
    }
    
    async initializeSession() {
        try {
            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.isConnected = true;
                console.log('💬 Chat session initialized:', this.sessionId);
                
                // Load conversation history if any
                await this.loadChatHistory();
            } else {
                console.error('Failed to initialize chat session');
                this.showConnectionError();
            }
        } catch (error) {
            console.error('Error initializing chat session:', error);
            this.showConnectionError();
        }
    }
    
    async loadChatHistory() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/chat/history/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.conversation && data.conversation.length > 0) {
                    this.displayChatHistory(data.conversation);
                }
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    displayChatHistory(conversation) {
        // Clear existing messages except welcome message
        if (this.messagesContainer) {
            const welcomeMessage = this.messagesContainer.querySelector('.ai-message');
            this.messagesContainer.innerHTML = '';
            if (welcomeMessage) {
                this.messagesContainer.appendChild(welcomeMessage);
            }
        }
        
        conversation.forEach(message => {
            this.displayMessage(message.content, message.role === 'user' ? 'user' : 'ai', false);
        });
        
        this.scrollToBottom();
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        if (!this.chatWindow || !this.chatBubble) return;
        
        this.isOpen = true;
        this.chatWindow.style.display = 'flex';
        this.chatBubble.classList.add('chat-open');
        
        // Animate in
        requestAnimationFrame(() => {
            this.chatWindow.classList.add('chat-window-open');
        });
        
        // Focus input
        setTimeout(() => {
            if (this.chatInput) {
                this.chatInput.focus();
            }
        }, 300);
        
        // Hide notification badge
        const badge = document.getElementById('chatNotificationBadge');
        if (badge) {
            badge.style.display = 'none';
        }
        
        console.log('💬 Chat opened');
    }
    
    closeChat() {
        if (!this.chatWindow || !this.chatBubble) return;
        
        this.isOpen = false;
        this.chatWindow.classList.remove('chat-window-open');
        this.chatBubble.classList.remove('chat-open');
        
        // Hide after animation
        setTimeout(() => {
            this.chatWindow.style.display = 'none';
        }, 300);
        
        console.log('💬 Chat closed');
    }
    
    handleSendClick() {
        if (!this.chatInput) return;
        
        const message = this.chatInput.value.trim();
        if (message) {
            this.sendMessage(message);
            this.chatInput.value = '';
        }
    }
    
    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSendClick();
        }
    }
    
    handleTyping() {
        // Could implement typing indicators here
        // For now, we'll keep it simple
    }
    
    async sendMessage(message, fromUser = true) {
        if (!message.trim() || !this.sessionId) return;
        
        // Open chat if not already open
        if (!this.isOpen) {
            this.openChat();
        }
        
        // Display user message immediately
        if (fromUser) {
            this.displayMessage(message, 'user');
        }
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.hideTypingIndicator();
                
                // Display AI response
                this.displayMessage(data.response, 'ai');
                
                // Handle any tools that were used
                if (data.tools_used && data.tools_used.length > 0) {
                    this.handleToolsUsed(data.tools_used);
                }
                
                console.log('💬 Message sent and response received');
            } else {
                this.hideTypingIndicator();
                this.displayMessage('Lo siento, hubo un error al procesar tu mensaje. Por favor intenta nuevamente.', 'ai', true);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.displayMessage('Error de conexión. Por favor verifica tu conexión a internet.', 'ai', true);
        }
    }
    
    displayMessage(content, sender, isError = false) {
        if (!this.messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${isError ? 'error' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString('es-CL', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${this.escapeHtml(content)}</p>
                    <span class="message-time">${timestamp}</span>
                </div>
                <div class="message-avatar">👤</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="ai-response-content">${this.formatAIResponse(content)}</div>
                    <span class="message-time">${timestamp}</span>
                </div>
            `;
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Add message to local storage
        this.messages.push({
            content,
            sender,
            timestamp: new Date().toISOString(),
            isError
        });
    }
    
    formatAIResponse(content) {
        // Basic formatting for AI responses
        let formatted = this.escapeHtml(content);
        
        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        // ⚡ CONVERT MARKDOWN LINKS TO CLICKABLE HTML LINKS
        // Pattern: [texto](url) -> <a href="url" target="_blank">texto</a>
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="pharmacy-link">$1</a>');
        
        // ⚡ CONVERT PHONE LINKS TO CLICKABLE
        // Pattern: tel:+56... -> clickable phone link
        formatted = formatted.replace(/\b(tel:\+\d+[0-9\-\s]*)/g, '<a href="$1" class="phone-link">📞 Llamar</a>');
        
        // ⚡ MAKE MAP LINKS MORE PROMINENT
        // Enhance map links with better styling
        formatted = formatted.replace(/🌐\s*<a([^>]*href[^>]*maps[^>]*)>([^<]*)<\/a>/gi, 
                                    '<span class="map-link">🗺️ <a$1><strong>$2</strong></a></span>');
        
        // ⚡ MAKE EMERGENCY PHARMACY NAMES BOLD AND PROMINENT
        formatted = formatted.replace(/🏪\s*([^📍\n<]+)/g, '<div class="pharmacy-name">🏪 <strong>$1</strong></div>');
        
        // ⚡ ENHANCE ADDRESSES
        formatted = formatted.replace(/📍\s*([^<\n⏰📞🌐]+)/g, '<div class="pharmacy-address">📍 <em>$1</em></div>');
        
        // ⚡ ENHANCE PHONE NUMBERS
        formatted = formatted.replace(/📞\s*([^<\n⏰📍🌐]+)/g, '<div class="pharmacy-phone">📞 $1</div>');
        
        // ⚡ ENHANCE SCHEDULE INFO
        formatted = formatted.replace(/⏰\s*([^<\n📍📞🌐]+)/g, '<div class="pharmacy-hours">⏰ $1</div>');
        
        // ⚡ EMERGENCY INDICATORS
        formatted = formatted.replace(/�([^<\n]*)/g, '<span class="emergency-indicator">�$1</span>');
        
        return formatted;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    handleToolsUsed(tools) {
        // Handle different tools that were used by the AI
        tools.forEach(tool => {
            switch (tool) {
                case 'buscar_farmacias':
                    this.showToolFeedback('🔍 Busqué farmacias en la base de datos');
                    break;
                case 'buscar_medicamentos':
                    this.showToolFeedback('💊 Consulté el vademécum de medicamentos');
                    break;
                case 'farmacias_por_comuna':
                    this.showToolFeedback('🏙️ Filtré farmacias por comuna');
                    break;
                case 'farmacias_de_turno':
                    this.showToolFeedback('🕐 Consulté las farmacias de turno');
                    break;
                default:
                    console.log('Unknown tool used:', tool);
            }
        });
    }
    
    showToolFeedback(message) {
        if (!this.messagesContainer) return;
        
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'tool-feedback';
        feedbackDiv.innerHTML = `
            <div class="tool-feedback-content">
                <span class="tool-icon">⚡</span>
                <span>${message}</span>
            </div>
        `;
        
        this.messagesContainer.appendChild(feedbackDiv);
        this.scrollToBottom();
        
        // Remove after a few seconds
        setTimeout(() => {
            if (feedbackDiv.parentNode) {
                feedbackDiv.remove();
            }
        }, 3000);
    }
    
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
            this.isTyping = true;
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
            this.isTyping = false;
        }
    }
    
    showConnectionError() {
        this.displayMessage(
            'No se pudo conectar con el asistente. Por favor recarga la página e intenta nuevamente.',
            'ai',
            true
        );
    }
    
    scrollToBottom() {
        if (this.messagesContainer) {
            setTimeout(() => {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }, 100);
        }
    }
    
    showNotification() {
        const badge = document.getElementById('chatNotificationBadge');
        if (badge && !this.isOpen) {
            badge.style.display = 'block';
        }
    }
    
    // Public API methods
    isConnected() {
        return this.isConnected;
    }
    
    getSessionId() {
        return this.sessionId;
    }
    
    getMessages() {
        return this.messages;
    }
    
    clearChat() {
        if (this.messagesContainer) {
            // Keep only the welcome message
            const welcomeMessage = this.messagesContainer.querySelector('.ai-message');
            this.messagesContainer.innerHTML = '';
            if (welcomeMessage) {
                this.messagesContainer.appendChild(welcomeMessage);
            }
        }
        
        this.messages = [];
        console.log('💬 Chat cleared');
    }
    
    // Method to be called from other components
    sendQuickMessage(message) {
        this.sendMessage(message, true);
    }
}

// Make ChatManager available globally
window.ChatManager = ChatManager;
