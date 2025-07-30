document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById('userInput');
    const chatBox = document.getElementById('chatBox');
    const sendButton = document.getElementById('sendButton');
    const resetButton = document.getElementById('resetButton');

    const addMessage = (message, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = message;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const sendMessage = async () => {
        const messageText = userInput.value.trim();
        if (messageText === '') return;

        addMessage(messageText, 'user');
        userInput.value = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: messageText }),
            });
            const data = await response.json();
            addMessage(data.response || data.error, 'bot');
        } catch (error) {
            addMessage('Sorry, something went wrong.', 'bot');
        }
    };

    const resetConversation = async () => {
        try {
            await fetch('/api/reset', { method: 'POST' });
            chatBox.innerHTML = '';
            addMessage('Conversation reset. How can I help?', 'bot');
        } catch (error) {
            addMessage('Could not reset conversation.', 'bot');
        }
    };

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => e.key === 'Enter' && sendMessage());
    resetButton.addEventListener('click', resetConversation);
});