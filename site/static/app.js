const themes = {
    purple: { primary: '#7c3aed', secondary: '#ec4899' },
    blue: { primary: '#3b82f6', secondary: '#60a5fa' },
    green: { primary: '#10b981', secondary: '#34d399' },
    pink: { primary: '#ec4899', secondary: '#f43f5e' }
};

class ChatApp {
    constructor() {
        this.isBusy = false;
        this.initEventListeners();
    }

    initEventListeners() {
        document.getElementById('send-btn').addEventListener('click', () => this.send());
        document.getElementById('input').addEventListener('keydown', (e) => this.handleKeyPress(e));
    }

    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.send();
        }
    }

    async send() {
        const input = document.getElementById('input');
        if (this.isBusy || !input.value.trim()) return;

        const msg = input.value;
        input.value = '';
        this.addMsg(msg, 'user');
        this.isBusy = true;

        try {
            const response = await fetch('/send-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            const data = await response.json();
            data.choices?.length
                ? this.showChoices(data.choices)
                : this.addMsg("🤖 Не удалось получить ответ", 'bot');
        } catch(error) {
            this.addMsg(`⚠️ Ошибка: ${error.message}`, 'bot');
        }
        this.isBusy = false;
    }

    addMsg(text, role, model) {
        const msgEl = document.createElement('div');
        msgEl.className = `msg ${role}`;
        msgEl.innerHTML = `
            <div class="message-content">${text}</div>
            ${model ? `<div class="model-badge">${model}</div>` : ''}
        `;
        document.getElementById('chat').appendChild(msgEl);
        msgEl.scrollIntoView({ behavior: 'smooth' });
    }

    showChoices(choices) {
        const container = document.createElement('div');
        container.className = 'choice-container';

        const userMessages = document.querySelectorAll('.user');
        const lastQuestion = userMessages[userMessages.length -1]?.querySelector('.message-content')?.innerText || '';

        choices.forEach(choice => {
            const choiceEl = document.createElement('div');
            choiceEl.className = 'msg bot choice-msg';
            choiceEl.innerHTML = `
                <div class="message-content">${choice.text}</div>
                <div class="model-badge">${choice.model}</div>
            `;
            choiceEl.addEventListener('click', () => this.selectChoice(choiceEl, container, lastQuestion, choice));
            container.appendChild(choiceEl);
        });

        document.getElementById('chat').appendChild(container);
        container.scrollIntoView({ behavior: 'smooth' });
    }

    selectChoice(selected, container, question, choice) {
        const finalMsg = selected.cloneNode(true);
        finalMsg.className = 'msg bot';
        container.replaceWith(finalMsg);
        this.saveChoice(question, selected, choice);
    }

    async saveChoice(question, selected, choice) {
        try {
            const response = await fetch('/save-choice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    question: question,
                    selected_answer: selected.querySelector('.message-content').innerText,
                    model: choice.model
                })
            });

            if (!response.ok) throw new Error('Ошибка сохранения');
            this.showNotification('✅ Выбор успешно сохранен');
        } catch(error) {
            console.error('Ошибка:', error);
            this.showNotification('❌ Ошибка сохранения', 5000);
        }
    }

    getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) return decodeURIComponent(value);
        }
        return null;
    }

    showNotification(text, duration = 3000) {
        const notification = document.createElement('div');
        notification.className = 'notification show';
        notification.textContent = text;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), duration);
    }
}

// Инициализация приложения
new ChatApp();