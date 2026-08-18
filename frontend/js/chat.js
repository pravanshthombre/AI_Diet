const chat = {
    init() {
        const sendBtn = document.getElementById('btn-send-chat');
        const input = document.getElementById('chat-input');

        if (sendBtn) {
            sendBtn.onclick = () => this.sendMessage();
        }

        if (input) {
            input.onkeypress = (e) => {
                if (e.key === 'Enter') this.sendMessage();
            };
        }
    },

    sendQuick(text) {
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = text;
            this.sendMessage();
        }
    },

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        input.value = '';
        this.appendMessage('user', text);

        if (!app.state.userId) {
            this.appendMessage('ai', "Please set up or select your user profile first so I can tailor dietary advice specifically for your metrics and regional cuisine!");
            return;
        }

        const typingId = this.appendTyping();

        try {
            const res = await api.chat(app.state.userId, text);
            this.removeTyping(typingId);
            const reply = res.reply || res.response || "I'm analyzing your nutritional targets! Try asking about healthy Indian breakfast options or protein swaps.";
            this.appendMessage('ai', reply);
        } catch (e) {
            this.removeTyping(typingId);
            this.appendMessage('ai', "I apologize, I encountered a temporary connection issue. Please check your backend connection and try again.");
        }
    },

    appendMessage(sender, text) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        const msg = document.createElement('div');
        msg.className = `message ${sender}`;
        
        const avatar = sender === 'user' ? '👤' : '🌿';
        
        // Basic markdown formatting for bold and line breaks
        const formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');

        msg.innerHTML = `
            <div class="msg-avatar">${avatar}</div>
            <div class="msg-bubble"><p>${formatted}</p></div>
        `;

        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    },

    appendTyping() {
        const container = document.getElementById('chat-messages');
        const id = 'typing-' + Date.now();
        const msg = document.createElement('div');
        msg.className = 'message ai';
        msg.id = id;
        msg.innerHTML = `
            <div class="msg-avatar">🌿</div>
            <div class="msg-bubble"><p><em>AI Dietitian is thinking...</em></p></div>
        `;
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
        return id;
    },

    removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
};

window.chat = chat;
