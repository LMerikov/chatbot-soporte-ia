/**
 * Chatbot - Lógica Principal
 * Versión Profesional con funcionalidades avanzadas
 */

class ChatBot {
    constructor() {
        this.config = window.chatConfig;
        this.isOpen = false;
        this.isTyping = false;
        this.connectionStatus = 'checking';
        this.messageHistory = [];
        this.currentTheme = 'light';

        this.init();
    }

    /**
     * Inicialización
     */
    init() {
        this.loadHistory();
        this.loadTheme();
        this.attachEventListeners();
        this.checkConnection();
        this.startConnectionMonitor();
        this.loadQuickQuestions();

        console.log('✅ Chatbot inicializado correctamente');
    }

    /**
     * Event Listeners
     */
    attachEventListeners() {
        // Toggle chat
        const toggleBtn = document.getElementById('chatWidgetButton');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleChat());
        }

        // Send message
        const sendBtn = document.getElementById('sendButton');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Input eventos
        const input = document.getElementById('chatInput');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Sugerencias mientras escribe
            input.addEventListener('input', (e) => {
                this.handleInputChange(e.target.value);
            });
        }

        // Theme toggle
        const themeBtn = document.getElementById('themeToggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Clear history
        const clearBtn = document.getElementById('clearHistory');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearHistory());
        }

        // Export chat
        const exportBtn = document.getElementById('exportChat');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.toggleExportMenu());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // ESC para cerrar
            if (e.key === 'Escape' && this.isOpen) {
                this.toggleChat();
            }
        });

        // Click outside para cerrar export menu
        document.addEventListener('click', (e) => {
            const exportMenu = document.querySelector('.export-menu');
            const exportBtn = document.getElementById('exportChat');
            if (exportMenu && !exportMenu.contains(e.target) && e.target !== exportBtn) {
                exportMenu.classList.remove('active');
            }
        });
    }

    /**
     * Toggle Chat Widget
     */
    toggleChat() {
        const widget = document.getElementById('chatWidget');
        const button = document.getElementById('chatWidgetButton');

        if (widget && button) {
            this.isOpen = !this.isOpen;
            widget.classList.toggle('active');
            button.classList.toggle('active');

            if (this.isOpen) {
                // Auto-focus input
                setTimeout(() => {
                    const input = document.getElementById('chatInput');
                    if (input) input.focus();
                }, 300);

                // Scroll to bottom
                this.scrollToBottom();
            }
        }
    }

    /**
     * Send Message
     */
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const query = input?.value.trim();

        if (!query || this.isTyping) return;

        // Validar longitud
        if (query.length < 3) {
            this.showToast('Por favor escribe al menos 3 caracteres', 'warning');
            return;
        }

        if (query.length > 500) {
            this.showToast('El mensaje es demasiado largo (máximo 500 caracteres)', 'warning');
            return;
        }

        // Add user message
        this.addMessage(query, true);
        input.value = '';
        sendButton.disabled = true;

        // Remove welcome message
        this.removeWelcomeMessage();

        // Show typing indicator
        this.showTyping(true);

        try {
            // Send request with retry
            const response = await this.sendWithRetry(query);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Hide typing indicator
            this.showTyping(false);

            // Create bot message with typing effect
            await this.addBotMessageWithTyping(response);

        } catch (error) {
            this.showTyping(false);
            console.error('Error:', error);

            let errorMessage = '❌ Error de conexión. ';
            if (error.message.includes('429')) {
                errorMessage += 'Demasiadas solicitudes. Por favor espera un momento.';
            } else if (error.message.includes('timeout')) {
                errorMessage += 'La solicitud tardó demasiado. Intenta nuevamente.';
            } else {
                errorMessage += 'Por favor, intenta nuevamente.';
            }

            this.addMessage(errorMessage, false);
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    }

    /**
     * Send with Retry (Exponential Backoff)
     */
    async sendWithRetry(query, attempt = 1) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.config.REQUEST_TIMEOUT);

            const response = await fetch(`${this.config.API_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Si es rate limit y tenemos intentos, esperar y reintentar
            if (response.status === 429 && attempt < this.config.MAX_RETRIES) {
                const delay = this.config.RETRY_DELAY * Math.pow(2, attempt - 1);
                console.log(`Rate limited. Retrying in ${delay}ms... (attempt ${attempt}/${this.config.MAX_RETRIES})`);
                await this.sleep(delay);
                return this.sendWithRetry(query, attempt + 1);
            }

            return response;

        } catch (error) {
            // Si es timeout o error de red y tenemos intentos, reintentar
            if (attempt < this.config.MAX_RETRIES &&
                (error.name === 'AbortError' || error.message.includes('fetch'))) {
                const delay = this.config.RETRY_DELAY * Math.pow(2, attempt - 1);
                console.log(`Request failed. Retrying in ${delay}ms... (attempt ${attempt}/${this.config.MAX_RETRIES})`);
                await this.sleep(delay);
                return this.sendWithRetry(query, attempt + 1);
            }
            throw error;
        }
    }

    /**
     * Add Bot Message with Realistic Typing Effect
     */
    async addBotMessageWithTyping(response) {
        const messagesDiv = document.getElementById('chatMessages');
        const typingIndicator = document.getElementById('typingIndicator');

        // Create bot message container
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        messageDiv.setAttribute('role', 'article');
        messageDiv.setAttribute('aria-live', 'polite');

        // Insert before typing indicator
        messagesDiv.insertBefore(messageDiv, typingIndicator);

        // Read stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let displayedText = '';

        this.isTyping = true;

        // Read all chunks first
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.trim()) {
                    try {
                        const data = JSON.parse(line);
                        fullText += data.token;
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

        // Now type it out with realistic effect
        for (let i = 0; i < fullText.length; i++) {
            displayedText += fullText[i];

            // Process and display
            const processedText = this.processMarkdown(displayedText);
            messageDiv.innerHTML = processedText;

            // Scroll to bottom
            this.scrollToBottom();

            // Variable typing speed (más realista)
            let delay = this.config.TYPING_SPEED;

            // Pausas más largas en puntuación
            const char = fullText[i];
            if (char === '.' || char === '!' || char === '?') {
                delay += 300; // Pausa después de punto
            } else if (char === ',' || char === ';') {
                delay += 150; // Pausa después de coma
            } else if (char === '\n') {
                delay += 200; // Pausa en salto de línea
            } else if (char === ' ') {
                delay += 20; // Pequeña pausa en espacio
            }

            // Variación aleatoria para más realismo
            delay += Math.random() * this.config.TYPING_VARIATION - (this.config.TYPING_VARIATION / 2);

            await this.sleep(delay);
        }

        this.isTyping = false;

        // Add copy button and feedback
        this.addMessageActions(messageDiv, fullText);

        // Save to history
        this.saveMessage(fullText, false);

        // Scroll final
        this.scrollToBottom();
    }

    /**
     * Process Markdown to HTML
     */
    processMarkdown(text) {
        let processed = text;

        // 1. Procesar negritas ANTES de escapar HTML
        processed = processed.replace(/\*\*([^\*]+)\*\*/g, '<!BOLD!>$1<!/BOLD!>');

        // 2. Procesar cursiva
        processed = processed.replace(/\*([^\*\n]+)\*/g, '<!ITALIC!>$1<!/ITALIC!>');

        // 3. Procesar links markdown
        processed = processed.replace(
            /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
            '<!LINK!>$2<!LINKTEXT!>$1<!/LINK!>'
        );

        // 4. Escapar HTML del resto del texto
        const tempDiv = document.createElement('div');
        tempDiv.textContent = processed;
        processed = tempDiv.innerHTML;

        // 5. Restaurar formato
        processed = processed.replace(/&lt;!BOLD!&gt;([^&]+)&lt;!\/BOLD!&gt;/g, '<strong>$1</strong>');
        processed = processed.replace(/&lt;!ITALIC!&gt;([^&]+)&lt;!\/ITALIC!&gt;/g, '<em>$1</em>');
        processed = processed.replace(
            /&lt;!LINK!&gt;(https?:\/\/[^&]+)&lt;!LINKTEXT!&gt;([^&]+)&lt;!\/LINK!&gt;/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$2</a>'
        );

        // 6. Convertir saltos de línea
        processed = processed.replace(/\n/g, '<br>');

        // 7. Convertir listas con viñetas
        processed = processed.replace(/^[\*\-]\s+/gm, '• ');

        // 8. Convertir URLs sueltas (que no estén ya en un link)
        processed = processed.replace(
            /(?<!href="|">)(https?:\/\/[^\s<>"]+)(?!<\/a>)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        return processed;
    }

    /**
     * Add Message (Simple - for user and errors)
     */
    addMessage(text, isUser) {
        const messagesDiv = document.getElementById('chatMessages');
        const typingIndicator = document.getElementById('typingIndicator');

        // Remove welcome message on first interaction
        if (isUser) {
            this.removeWelcomeMessage();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + (isUser ? 'user' : 'bot');
        messageDiv.setAttribute('role', 'article');
        messageDiv.setAttribute('aria-live', 'polite');

        // Process markdown for bot messages
        const processedText = isUser ? this.escapeHtml(text) : this.processMarkdown(text);
        messageDiv.innerHTML = processedText;

        // Insert before typing indicator
        messagesDiv.insertBefore(messageDiv, typingIndicator);

        // Add actions for bot messages
        if (!isUser && !text.includes('❌')) {
            this.addMessageActions(messageDiv, text);
        }

        // Save to history
        this.saveMessage(text, isUser);

        // Scroll to bottom
        this.scrollToBottom();

        return messageDiv;
    }

    /**
     * Add Message Actions (Copy + Feedback)
     */
    addMessageActions(messageDiv, originalText) {
        // Copy button - ELIMINADO por solicitud del usuario
        // const copyBtn = document.createElement('button');
        // copyBtn.className = 'copy-btn';
        // copyBtn.innerHTML = '📋';
        // copyBtn.title = 'Copiar respuesta';
        // copyBtn.setAttribute('aria-label', 'Copiar respuesta');
        // copyBtn.onclick = () => this.copyToClipboard(originalText, copyBtn);
        // messageDiv.appendChild(copyBtn);

        // Feedback buttons
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-buttons';
        feedbackDiv.innerHTML = `
            <button class="feedback-btn" data-feedback="positive" aria-label="Respuesta útil">
                👍 Útil
            </button>
            <button class="feedback-btn" data-feedback="negative" aria-label="Respuesta no útil">
                👎 No útil
            </button>
        `;

        // Feedback event listeners
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.onclick = () => this.submitFeedback(btn, originalText);
        });

        messageDiv.appendChild(feedbackDiv);
    }

    /**
     * Copy to Clipboard
     */
    async copyToClipboard(text, button) {
        try {
            // Remover markdown antes de copiar
            const plainText = text.replace(/\*\*([^\*]+)\*\*/g, '$1')
                                  .replace(/\*([^\*]+)\*/g, '$1')
                                  .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

            await navigator.clipboard.writeText(plainText);
            button.innerHTML = '✅';
            button.style.opacity = '1';
            setTimeout(() => {
                button.innerHTML = '📋';
                button.style.opacity = '';
            }, 2000);

            this.showToast('Texto copiado al portapapeles', 'success');
        } catch (error) {
            console.error('Error copying:', error);
            this.showToast('Error al copiar texto', 'error');
        }
    }

    /**
     * Submit Feedback
     */
    async submitFeedback(button, messageText) {
        const feedback = button.dataset.feedback;
        const feedbackDiv = button.parentElement;

        // Marcar como activo
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.classList.remove('active', 'negative');
        });

        button.classList.add('active');
        if (feedback === 'negative') {
            button.classList.add('negative');
        }

        // Enviar feedback al backend
        try {
            await fetch(`${this.config.API_URL}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: messageText.substring(0, 100),
                    feedback: feedback,
                    timestamp: new Date().toISOString()
                })
            });

            this.showToast(
                feedback === 'positive' ? '¡Gracias por tu feedback!' : 'Gracias, trabajaremos en mejorar',
                'success'
            );
        } catch (error) {
            console.error('Error sending feedback:', error);
        }
    }

    /**
     * Show/Hide Typing Indicator
     */
    showTyping(show) {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            if (show) {
                typingIndicator.classList.add('active');
            } else {
                typingIndicator.classList.remove('active');
            }
            this.scrollToBottom();
        }
    }

    /**
     * Remove Welcome Message
     */
    removeWelcomeMessage() {
        const messagesDiv = document.getElementById('chatMessages');
        const welcomeMsg = messagesDiv?.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => welcomeMsg.remove(), 300);
        }
    }

    /**
     * Scroll to Bottom
     */
    scrollToBottom() {
        const messagesDiv = document.getElementById('chatMessages');
        if (messagesDiv) {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    }

    /**
     * Load Quick Questions
     */
    loadQuickQuestions() {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (!welcomeMessage) return;

        const quickQuestionsDiv = document.createElement('div');
        quickQuestionsDiv.className = 'quick-questions';

        this.config.QUICK_QUESTIONS.forEach(q => {
            const btn = document.createElement('button');
            btn.className = 'quick-question-btn';
            btn.innerHTML = `${q.icon} ${q.text}`;
            btn.onclick = () => this.askQuickQuestion(q.query);
            btn.setAttribute('aria-label', `Preguntar: ${q.query}`);
            quickQuestionsDiv.appendChild(btn);
        });

        welcomeMessage.appendChild(quickQuestionsDiv);
    }

    /**
     * Ask Quick Question
     */
    askQuickQuestion(question) {
        const input = document.getElementById('chatInput');
        if (input) {
            input.value = question;
            this.sendMessage();
        }
    }

    /**
     * Handle Input Change (Suggestions)
     */
    handleInputChange(value) {
        // Aquí podrías implementar sugerencias en tiempo real
        // Por ahora lo dejamos simple
        if (value.length >= 3) {
            // Future: mostrar sugerencias
        }
    }

    /**
     * Check Connection
     */
    async checkConnection() {
        try {
            const response = await fetch(`${this.config.API_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });

            this.updateConnectionStatus(response.ok);
        } catch (error) {
            this.updateConnectionStatus(false);
        }
    }

    /**
     * Update Connection Status
     */
    updateConnectionStatus(isOnline) {
        this.connectionStatus = isOnline ? 'online' : 'offline';

        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');

        if (statusDot) {
            statusDot.classList.toggle('offline', !isOnline);
        }

        if (statusText) {
            statusText.textContent = isOnline ? 'En línea' : 'Desconectado';
        }

        if (!isOnline && this.isOpen) {
            this.showToast('Conexión perdida. Reintentando...', 'warning');
        }
    }

    /**
     * Start Connection Monitor
     */
    startConnectionMonitor() {
        setInterval(() => {
            this.checkConnection();
        }, this.config.CONNECTION_CHECK_INTERVAL);
    }

    /**
     * Toggle Theme
     */
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        document.body.classList.toggle('dark-theme');
        localStorage.setItem(this.config.STORAGE_KEY_THEME, this.currentTheme);

        const themeBtn = document.getElementById('themeToggle');
        if (themeBtn) {
            themeBtn.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
        }
    }

    /**
     * Load Theme
     */
    loadTheme() {
        const savedTheme = localStorage.getItem(this.config.STORAGE_KEY_THEME);
        if (savedTheme === 'dark') {
            this.currentTheme = 'dark';
            document.body.classList.add('dark-theme');
            const themeBtn = document.getElementById('themeToggle');
            if (themeBtn) themeBtn.innerHTML = '☀️';
        }
    }

    /**
     * Save Message to History
     */
    saveMessage(text, isUser) {
        this.messageHistory.push({
            text,
            isUser,
            timestamp: new Date().toISOString()
        });

        // Limitar historial
        if (this.messageHistory.length > this.config.MAX_HISTORY_MESSAGES) {
            this.messageHistory = this.messageHistory.slice(-this.config.MAX_HISTORY_MESSAGES);
        }

        localStorage.setItem(
            this.config.STORAGE_KEY_HISTORY,
            JSON.stringify(this.messageHistory)
        );
    }

    /**
     * Load History
     */
    loadHistory() {
        try {
            const saved = localStorage.getItem(this.config.STORAGE_KEY_HISTORY);
            if (saved) {
                this.messageHistory = JSON.parse(saved);

                // Restaurar mensajes en el DOM
                const messagesDiv = document.getElementById('chatMessages');
                const typingIndicator = document.getElementById('typingIndicator');

                if (this.messageHistory.length > 0) {
                    // Remove welcome message
                    const welcomeMsg = messagesDiv?.querySelector('.welcome-message');
                    if (welcomeMsg) welcomeMsg.remove();

                    // Restore messages
                    this.messageHistory.forEach(msg => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = 'message ' + (msg.isUser ? 'user' : 'bot');
                        messageDiv.innerHTML = msg.isUser ? this.escapeHtml(msg.text) : this.processMarkdown(msg.text);

                        if (!msg.isUser) {
                            this.addMessageActions(messageDiv, msg.text);
                        }

                        messagesDiv.insertBefore(messageDiv, typingIndicator);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    /**
     * Clear History
     */
    clearHistory() {
        if (!confirm('¿Estás seguro de que deseas borrar todo el historial?')) {
            return;
        }

        this.messageHistory = [];
        localStorage.removeItem(this.config.STORAGE_KEY_HISTORY);

        // Clear DOM
        const messagesDiv = document.getElementById('chatMessages');
        const messages = messagesDiv?.querySelectorAll('.message');
        messages?.forEach(msg => msg.remove());

        // Show welcome message again
        this.showWelcomeMessage();

        this.showToast('Historial borrado', 'success');
    }

    /**
     * Show Welcome Message
     */
    showWelcomeMessage() {
        const messagesDiv = document.getElementById('chatMessages');
        const typingIndicator = document.getElementById('typingIndicator');

        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.innerHTML = `
            <div class="welcome-icon galaxy-welcome"></div>
            <h3>¡Hola! 👋</h3>
            <p>Soy tu asistente de soporte técnico para la Universidad de los Andes y Clínica Uandes.</p>
            <p style="margin-top: 12px; font-size: 13px;">¿En qué puedo ayudarte hoy?</p>
        `;

        messagesDiv.insertBefore(welcomeDiv, typingIndicator);
        this.loadQuickQuestions();
    }

    /**
     * Toggle Export Menu
     */
    toggleExportMenu() {
        const menu = document.querySelector('.export-menu');
        if (menu) {
            menu.classList.toggle('active');
        }
    }

    /**
     * Export Chat
     */
    exportChat(format = 'json') {
        if (this.messageHistory.length === 0) {
            this.showToast('No hay conversación para exportar', 'warning');
            return;
        }

        const timestamp = new Date().toISOString().split('T')[0];
        let content, filename, mimeType;

        if (format === 'json') {
            content = JSON.stringify(this.messageHistory, null, 2);
            filename = `chat-${timestamp}.json`;
            mimeType = 'application/json';
        } else if (format === 'txt') {
            content = this.messageHistory.map(msg =>
                `[${msg.isUser ? 'Usuario' : 'Bot'}] ${msg.text}`
            ).join('\n\n');
            filename = `chat-${timestamp}.txt`;
            mimeType = 'text/plain';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        this.showToast('Conversación exportada', 'success');
        this.toggleExportMenu();
    }

    /**
     * Show Toast Notification
     */
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : '⚠️';
        toast.innerHTML = `
            <span style="font-size: 20px;">${icon}</span>
            <span>${message}</span>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Utility: Sleep
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Utility: Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new ChatBot();
});
