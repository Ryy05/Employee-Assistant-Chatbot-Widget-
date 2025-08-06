document.addEventListener("DOMContentLoaded", () => {
    const widget = document.getElementById("chatbot-widget");
    const openButton = document.getElementById("chatbot-open");
    const closeButton = document.getElementById("chatbot-close");
    const resetButton = document.getElementById("chatbot-reset");
    const messageContainer = document.getElementById("chatbot-messages");
    const chatForm = document.getElementById("chatbot-form");
    const chatInput = document.getElementById("chatbot-input");
    const suggestionArea = document.getElementById("suggestion-area");

    const welcomeMessage = "Welcome Employee,\n How can I help you with MPC policies today?";

    // --- Event Listeners ---
    openButton.addEventListener("click", () => {
        widget.style.display = "flex";
        openButton.style.display = "none";
    });

    closeButton.addEventListener("click", () => {
        widget.style.display = "none";
        openButton.style.display = "flex";
    });
    
    const resetChat = async () => {
        messageContainer.innerHTML = '';
        const welcomeWrapper = addMessage("chat-bot", "");
        const welcomeBubble = welcomeWrapper.querySelector('.chat-message');
        welcomeBubble.textContent = "";
        typeMessage(welcomeBubble, welcomeMessage);
        try {
            await fetch('http://127.0.0.1:5000/reset', { method: 'POST' });
        } catch (error) {
            console.error("Could not reset backend memory:", error);
        }
    };
    resetButton.addEventListener("click", resetChat);
    
    // --- FAQ/Suggestion Logic ---
    const faqs = ["Leave Policy", "Dress Code", "Office Timings"];
    faqs.forEach(text => {
        const button = document.createElement("button");
        button.className = "suggestion-chip";
        button.textContent = text;
        button.onclick = () => {
            chatInput.value = text;
            chatForm.dispatchEvent(new Event('submit'));
        };
        suggestionArea.appendChild(button);
    });

    // --- MODIFIED: Message handling to remove the user icon ---
    const addMessage = (sender, text = "") => {
        const wrapper = document.createElement("div");
        wrapper.className = `message-wrapper ${sender === 'chat-user' ? 'user' : 'bot'}`;

        // Only create an icon if the sender is the bot
        if (sender === 'chat-bot') {
            const icon = document.createElement("div");
            icon.className = `message-icon bot-icon`;
            icon.textContent = '🤖';
            wrapper.appendChild(icon);
        }

        const messageDiv = document.createElement("div");
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.textContent = text;
        
        wrapper.appendChild(messageDiv);
        messageContainer.appendChild(wrapper);
        messageContainer.scrollTop = messageContainer.scrollHeight;
        return wrapper; 
    };
    
    // --- Typewriter Effect Logic ---
    const typeMessage = (element, text) => {
        let index = 0;
        const interval = 20;
        const typingInterval = setInterval(() => {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
                messageContainer.scrollTop = messageContainer.scrollHeight;
            } else {
                clearInterval(typingInterval);
            }
        }, interval);
    };
    
    // --- Form submission logic ---
    chatForm.addEventListener("submit", async (event) => {
        event.preventDefault(); 
        const userText = chatInput.value.trim();
        if (userText === "") return;
        addMessage("chat-user", userText);
        chatInput.value = ""; 
        
        const botMessageWrapper = addMessage("chat-bot", "");
        const botMessageBubble = botMessageWrapper.querySelector('.chat-message');
        botMessageBubble.textContent = "";

        try {
            const response = await fetch('http://127.0.0.1:5000/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText })
            });
            if (!response.ok) { throw new Error("Network response was not ok."); }
            const data = await response.json();
            typeMessage(botMessageBubble, data.response);
        } catch (error) {
            console.error("Fetch Error:", error);
            typeMessage(botMessageBubble, "Sorry, I'm having trouble connecting.");
        }
    });

    // Initial welcome message
    const initialWrapper = addMessage("chat-bot", "");
    const initialBubble = initialWrapper.querySelector('.chat-message');
    initialBubble.textContent = "";
    typeMessage(initialBubble, welcomeMessage);
});