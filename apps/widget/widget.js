// Carai Chat Widget JavaScript
class CaraiWidget {
    constructor(config) {
        this.config = {
            position: 'bottom-right',
            theme: 'light',
            greeting: 'Hello! How can I help you today?',
            avatar: '🤖',
            welcomeText: 'Welcome to our website! I\'m here to help you.',
            agentMessageEndpoint: '/api/v1/agent/message',
            agentStreamEndpoint: '/api/v1/agent/stream',
            brandingEndpoint: '/api/v1/business-profiles',
            analyticsEndpoint: '/api/v1/analytics/widget',
            maxMessagesPerMinute: 10,
            retryDelayMs: 5000,
            maxRetries: 2,
            ...config
        };
        this.isOpen = false;
        this.conversationId = null;
        this.customerId = null;
        this.messageQueue = [];
        this.currentStreamElement = null;
        this.rateLimit = {
            count: 0,
            resetTime: Date.now() + 60000,
            maxMessages: this.config.maxMessagesPerMinute
        };
        this.init();
    }

    init() {
        this.createWidgetHTML();
        this.attachEventListeners();
        this.loadBranding();
    }

    createWidgetHTML() {
        const container = document.createElement('div');
        container.className = `widget-container ${this.config.position} ${this.config.theme}`;
        container.innerHTML = `
            <button class="floating-button" id="chat-button">${this.config.avatar}</button>
            <div class="chat-container">
                <div class="chat-header">
                    <div class="brand-logo"></div>
                    <div class="brand-info">
                        <h3 class="greeting">${this.config.greeting}</h3>
                        <div class="status-text" id="status-text"></div>
                    </div>
                </div>
                <div class="chat-messages"></div>
                <div class="typing-indicator" id="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
                <div class="error-banner" id="error-banner" aria-live="assertive"></div>
                <form class="chat-form">
                    <input type="text" id="message-input" placeholder="Type your message..." maxlength="1000">
                    <button type="submit">Send</button>
                </form>
            </div>
        `;
        document.body.appendChild(container);
        this.elements = {
            container: container,
            button: container.querySelector('#chat-button'),
            chatContainer: container.querySelector('.chat-container'),
            messages: container.querySelector('.chat-messages'),
            form: container.querySelector('.chat-form'),
            input: container.querySelector('#message-input'),
            typingIndicator: container.querySelector('#typing-indicator'),
            brandLogo: container.querySelector('.brand-logo'),
            greeting: container.querySelector('.greeting'),
            statusText: container.querySelector('#status-text'),
            errorBanner: container.querySelector('#error-banner')
        };
    }

    attachEventListeners() {
        this.elements.button.addEventListener('click', () => this.toggleChat());
        this.elements.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.elements.input.addEventListener('keypress', (e) => this.handleKeyPress(e));
        document.addEventListener('click', (e) => {
            if (!this.elements.container.contains(e.target)) {
                this.closeChat();
            }
        });
    }

    async loadBranding() {
        const businessId = this.getBusinessId();
        if (!businessId) {
            return;
        }

        try {
            const response = await fetch(`${this.config.brandingEndpoint}/${encodeURIComponent(businessId)}`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Branding fetch failed with status ${response.status}`);
            }

            const brandProfile = await response.json();
            this.applyBranding(brandProfile);
            this.updateAnalytics('branding_loaded', { business_id: businessId });
        } catch (error) {
            console.error('Failed to load branding:', error);
            this.showError('Unable to load branding. The widget may not match the business theme.');
        }
    }

    applyBranding(brandProfile) {
        const root = document.documentElement;
        if (brandProfile.primary_color) {
            root.style.setProperty('--brand-primary', brandProfile.primary_color);
        }
        if (brandProfile.secondary_color) {
            root.style.setProperty('--brand-secondary', brandProfile.secondary_color);
        }
        if (brandProfile.accent_color) {
            root.style.setProperty('--brand-accent', brandProfile.accent_color);
        }

        if (brandProfile.logo_url) {
            this.elements.brandLogo.innerHTML = `<img src="${brandProfile.logo_url}" alt="Logo">`;
        }

        if (brandProfile.theme) {
            this.config.theme = brandProfile.theme;
            this.elements.container.className = `widget-container ${this.config.position} ${this.config.theme}`;
        }

        if (brandProfile.greeting) {
            this.config.greeting = brandProfile.greeting;
            this.elements.greeting.textContent = this.config.greeting;
        }

        if (brandProfile.business_name) {
            this.elements.statusText.textContent = brandProfile.business_name;
        }
    }

    getBusinessId() {
        const businessId = this.config.businessId || this.getDatasetValue('businessId') || this.getDatasetValue('business_id');
        if (businessId) {
            return businessId;
        }

        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('business_id') || this.getCookie('carai_business_id');
    }

    getWidgetToken() {
        return this.config.widgetToken || this.getDatasetValue('widgetToken') || this.getDatasetValue('widget_token');
    }

    getWidgetApiKey() {
        return this.config.widgetApiKey || this.getDatasetValue('widgetApiKey') || this.getDatasetValue('widget_api_key');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.config.authToken) {
            headers['Authorization'] = `Bearer ${this.config.authToken}`;
        }

        const widgetToken = this.getWidgetToken();
        if (widgetToken) {
            headers['x-widget-token'] = widgetToken;
        }

        const widgetApiKey = this.getWidgetApiKey();
        if (widgetApiKey) {
            headers['x-widget-api-key'] = widgetApiKey;
        }

        return headers;
    }

    getDatasetValue(key) {
        const script = document.currentScript || document.querySelector('script[src*="widget.js"]');
        return script?.dataset?.[key];
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        this.isOpen = true;
        this.elements.container.classList.add('open');
        this.elements.button.setAttribute('aria-expanded', 'true');
        this.elements.input.focus();
        this.scrollToBottom();
        this.updateAnalytics('chat_opened');
    }

    closeChat() {
        this.isOpen = false;
        this.elements.container.classList.remove('open');
        this.elements.button.setAttribute('aria-expanded', 'false');
        this.updateAnalytics('chat_closed');
    }

    async handleSubmit(e) {
        e.preventDefault();
        const message = this.elements.input.value.trim();
        if (!message) return;

        if (!this.validateMessage(message)) return;

        this.addMessage(message, 'user');
        this.elements.input.value = '';
        this.showTypingIndicator();

        try {
            await this.sendToAgent(message);
            this.hideTypingIndicator();
            this.updateAnalytics('message_sent', { response_length: this.currentStreamElement?.textContent?.length || 0 });
        } catch (error) {
            this.hideTypingIndicator();
            this.finishStreamingMessage();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            this.showError('Chat service unavailable. Please try again later.');
            console.error('Error sending message:', error);
        }
    }

    validateMessage(message) {
        if (!this.checkRateLimit()) {
            this.addMessage('You\'re sending messages too quickly. Please wait a moment.', 'assistant');
            return false;
        }

        if (message.length > 1000) {
            this.addMessage('Message too long. Please keep it under 1000 characters.', 'assistant');
            return false;
        }

        if (this.containsInappropriateContent(message)) {
            this.addMessage('I\'m sorry, I can\'t help with that. Please ask something else.', 'assistant');
            return false;
        }

        return true;
    }

    checkRateLimit() {
        const now = Date.now();
        if (now > this.rateLimit.resetTime) {
            this.rateLimit.count = 0;
            this.rateLimit.resetTime = now + 60000;
        }

        if (this.rateLimit.count >= this.rateLimit.maxMessages) {
            return false;
        }

        this.rateLimit.count++;
        return true;
    }

    containsInappropriateContent(message) {
        const inappropriateWords = ['spam', 'scam', 'fraud'];
        const lowerMessage = message.toLowerCase();
        return inappropriateWords.some(word => lowerMessage.includes(word));
    }

    async sendToAgent(message) {
        const businessId = this.getBusinessId();
        const payload = {
            message,
            business_id: businessId,
            conversation_id: this.conversationId,
            customer_id: this.customerId,
            channel: 'website',
            widget_token: this.getWidgetToken(),
            widget_api_key: this.getWidgetApiKey(),
            stream: true
        };

        try {
            await this.streamAgentResponse(payload);
        } catch (error) {
            console.warn('Stream failed, falling back to non-streaming agent endpoint', error);
            await this.sendAgentMessageFallback(payload);
        }
    }

    async streamAgentResponse(payload) {
        this.startStreamingMessage();
        const response = await fetch(this.config.agentStreamEndpoint, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Stream request failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let done = false;
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            if (readerDone) {
                done = true;
            }
            buffer += value ? decoder.decode(value, { stream: true }) : '';
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for (const part of parts) {
                const trimmed = part.trim();
                if (!trimmed.startsWith('data:')) continue;
                const dataString = trimmed.slice(5).trim();
                if (!dataString || dataString === '[DONE]') {
                    continue;
                }

                let event;
                try {
                    event = JSON.parse(dataString);
                } catch (err) {
                    console.warn('Invalid SSE payload', err);
                    continue;
                }

                if (event.type === 'token' && event.content) {
                    this.appendStreamingToken(event.content);
                }

                if (event.type === 'done') {
                    if (event.response?.conversation_id) {
                        this.conversationId = event.response.conversation_id;
                    }
                    if (event.response?.customer_id) {
                        this.customerId = event.response.customer_id;
                    }
                }
            }
        }

        this.finishStreamingMessage();
    }

    async sendAgentMessageFallback(payload) {
        const response = await fetch(this.config.agentMessageEndpoint, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                ...payload,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`Message request failed with status ${response.status}`);
        }

        const data = await response.json();
        if (data.conversation_id) {
            this.conversationId = data.conversation_id;
        }
        if (data.customer_id) {
            this.customerId = data.customer_id;
        }

        this.finishStreamingMessage();
        const content = data.content || data.response || '';
        if (content) {
            this.appendStreamingToken(content);
        }
    }

    startStreamingMessage() {
        this.currentStreamElement = document.createElement('div');
        this.currentStreamElement.className = 'message assistant streaming';
        this.currentStreamElement.textContent = '';
        this.elements.messages.appendChild(this.currentStreamElement);
        this.scrollToBottom();
    }

    appendStreamingToken(token) {
        if (!this.currentStreamElement) {
            this.startStreamingMessage();
        }
        this.currentStreamElement.textContent += token;
        this.scrollToBottom();
    }

    finishStreamingMessage() {
        if (this.currentStreamElement) {
            this.currentStreamElement.classList.remove('streaming');
            this.currentStreamElement = null;
        }
    }

    addMessage(content, sender) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        messageElement.textContent = content;
        this.elements.messages.appendChild(messageElement);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.elements.typingIndicator.classList.add('active');
    }

    hideTypingIndicator() {
        this.elements.typingIndicator.classList.remove('active');
    }

    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.elements.form.dispatchEvent(new Event('submit'));
        }
    }

    updateAnalytics(event, properties = {}) {
        if (!this.config.analyticsEndpoint) {
            return;
        }

        const analyticsData = {
            event,
            timestamp: Date.now(),
            business_id: this.getBusinessId(),
            ...properties
        };

        if (navigator.sendBeacon) {
            navigator.sendBeacon(this.config.analyticsEndpoint, JSON.stringify(analyticsData));
        } else {
            fetch(this.config.analyticsEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(analyticsData)
            }).catch(() => {});
        }
    }

    showError(message) {
        if (this.elements.errorBanner) {
            this.elements.errorBanner.textContent = message;
            this.elements.errorBanner.classList.add('visible');
            setTimeout(() => {
                this.elements.errorBanner.classList.remove('visible');
            }, 7000);
        }
    }

    destroy() {
        if (this.elements.container) {
            this.elements.container.remove();
        }
    }
}

function initCaraiWidget(config = {}) {
    return new CaraiWidget(config);
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CaraiWidget, initCaraiWidget };
}

if (typeof window !== 'undefined') {
    window.CaraiWidget = CaraiWidget;
    window.initCaraiWidget = initCaraiWidget;
}
