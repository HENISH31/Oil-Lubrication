function toggleChat() {
    const panel = document.getElementById('chat-panel');
    const closeIcon = document.getElementById('close-icon');
    const robotIcon = document.querySelector('#chat-bubble .fa-robot');

    if (panel.classList.contains('hidden')) {
        panel.classList.remove('hidden');
        closeIcon.classList.remove('hidden');
        robotIcon.classList.add('hidden');
    } else {
        panel.classList.add('hidden');
        closeIcon.classList.add('hidden');
        robotIcon.classList.remove('hidden');
    }
}

async function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const message = input.value.trim();

    if (!message) return;

    // Add User Message
    addMessage(message, 'user');
    input.value = '';

    // Add Loading State
    const loadingId = 'loading-' + Date.now();
    addLoadingMessage(loadingId);

    try {
        const response = await fetch('/api/ai-chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        removeLoadingMessage(loadingId);

        if (data.status === 'success') {
            addMessage(data.response, 'bot');
        } else {
            addMessage("I apologize, but I'm having trouble connecting to my central processing unit. Please try again later.", 'bot');
        }
    } catch (error) {
        console.error('Chat Error:', error);
        removeLoadingMessage(loadingId);
        addMessage("Transmission error. Please check your connection.", 'bot');
    }
}

function addMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'flex gap-3 ' + (sender === 'user' ? 'flex-row-reverse' : '');

    const icon = sender === 'user' ? 'fa-user' : 'fa-robot';
    const bgColor = sender === 'user' ? 'bg-red-500/20' : 'bg-white/5';
    const border = sender === 'user' ? 'border-red-500/20' : 'border-white/5';
    const rounded = sender === 'user' ? 'rounded-tr-none' : 'rounded-tl-none';

    div.innerHTML = `
        <div class="w-8 h-8 rounded-xl ${bgColor} flex items-center justify-center flex-shrink-0 text-red-500 text-[10px] mt-1 shadow-sm">
            <i class="fas ${icon}"></i>
        </div>
        <div class="${bgColor} p-5 rounded-3xl ${rounded} border ${border} max-w-[85%] shadow-sm">
            <p class="text-[11px] text-white/70 leading-relaxed font-semibold">
                ${formatText(text)}
            </p>
        </div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addLoadingMessage(id) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex gap-3';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0 text-red-500 text-xs mt-1">
            <i class="fas fa-robot"></i>
        </div>
        <div class="bg-white/5 p-4 rounded-2xl rounded-tl-none border border-white/5 max-w-[85%]">
            <div class="flex gap-1">
                <div class="w-1 h-1 bg-red-500 rounded-full animate-bounce"></div>
                <div class="w-1 h-1 bg-red-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                <div class="w-1 h-1 bg-red-500 rounded-full animate-bounce [animation-delay:0.4s]"></div>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function formatText(text) {
    // Simple markdown-ish bold support
    return text.replace(/\*\*(.*?)\*\*/g, '<span class="text-white font-black">$1</span>');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
