document.addEventListener("DOMContentLoaded", () => {
    const widget = document.getElementById("chatbot-widget");
    const openButton = document.getElementById("chatbot-open");
    const closeButton = document.getElementById("chatbot-close");
    const resetButton = document.getElementById("chatbot-reset");
    const messageContainer = document.getElementById("chatbot-messages");
    const chatForm = document.getElementById("chatbot-form");
    const chatInput = document.getElementById("chatbot-input");
    const suggestionArea = document.getElementById("suggestion-area");

    const welcomeMessage = "Welcome Employee,\nHow can I help you with MPC policies today?\nYou can provide your Employee ID for personalized assistance";

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

    // --- Message handling with separate icons ---
    const addMessage = (sender, text = "") => {
        const wrapper = document.createElement("div");
        wrapper.className = `message-wrapper ${sender === 'chat-user' ? 'user' : 'bot'}`;
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
                const lowerText = text.toLowerCase();
                if (lowerText.includes("what type of leave")) {
                    showLeaveTypeChoices();
                } else if (lowerText.includes("what category does this expense")) {
                    showExpenseTypeChoices();
                } else if (lowerText.includes("select the date")) {
                    showCalendar();
                } else if (lowerText.includes("upload a photo or pdf")) {
                    showUploadButton();
                }
            }
        }, interval);
    };

    // --- Interactive UI Functions ---
    const clearChoiceBubbles = () => {
        const existingBubbles = document.querySelector('.choice-bubble-container');
        if (existingBubbles) existingBubbles.remove();
    };

    const createChoiceBubbles = (choices, onOther) => {
        clearChoiceBubbles();
        const container = document.createElement('div');
        container.className = 'choice-bubble-container';
        choices.forEach(type => {
            const button = document.createElement('button');
            button.className = 'choice-bubble';
            button.textContent = type;
            if (type === "Other" && onOther) {
                button.onclick = onOther;
            } else {
                button.onclick = () => {
                    chatInput.value = type;
                    chatForm.dispatchEvent(new Event('submit'));
                    clearChoiceBubbles();
                };
            }
            container.appendChild(button);
        });
        messageContainer.appendChild(container);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    };

    const showLeaveTypeChoices = () => {
        const leaveTypes = ["Sick", "Casual", "Maternity", "Paternity", "Bereavement", "Unpaid"];
        createChoiceBubbles(leaveTypes);
    };

    const showExpenseTypeChoices = () => {
        const expenseTypes = ["Travel", "Meals", "Software", "Other"];
        createChoiceBubbles(expenseTypes, () => {
            clearChoiceBubbles();
            addMessage("chat-bot", "Please type the category for your expense.");
            chatInput.focus();
        });
    };
    
    const showCalendar = () => {
        const calendarContainer = document.createElement("div");
        calendarContainer.className = 'message-wrapper bot'; 
        messageContainer.appendChild(calendarContainer);
        messageContainer.scrollTop = messageContainer.scrollHeight;

        flatpickr(calendarContainer, {
            inline: true, mode: "range", dateFormat: "F j, Y",
            onClose: (selectedDates) => {
                if (selectedDates.length > 0) {
                    const startDate = selectedDates[0];
                    const endDate = selectedDates.length > 1 ? selectedDates[1] : null;
                    let dateString = startDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
                    if (endDate && startDate.getTime() !== endDate.getTime()) {
                        dateString += ` to ${endDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}`;
                    }
                    calendarContainer.remove();
                    chatInput.value = dateString;
                    chatForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    };

    const showUploadButton = () => {
        const existingButton = document.getElementById("upload-button-container");
        if (existingButton) return;

        const container = document.createElement("div");
        container.id = "upload-button-container";
        container.className = 'message-wrapper bot';
        
        const input = document.createElement("input");
        input.type = "file";
        input.style.display = "none";
        input.accept = "image/*,.pdf";

        const button = document.createElement("button");
        button.className = "upload-button";
        button.textContent = "Upload Receipt";
        button.onclick = () => input.click();

        input.onchange = async () => {
            const file = input.files[0];
            if (file) {
                button.textContent = "Uploading...";
                button.disabled = true;
                const formData = new FormData();
                formData.append("file", file);
                try {
                    const response = await fetch('http://127.0.0.1:5000/upload', {
                        method: 'POST',
                        body: formData,
                    });
                    const data = await response.json();
                    if (response.ok) {
                        chatInput.value = `receipt_uploaded: ${data.file_path}`;
                        chatForm.dispatchEvent(new Event('submit'));
                        container.remove();
                    } else {
                        throw new Error(data.error || "Unknown upload error");
                    }
                } catch (error) {
                    console.error("Upload failed:", error);
                    addMessage("chat-bot", `Upload failed: ${error.message}. Please try again.`);
                    button.textContent = "Upload Receipt";
                    button.disabled = false;
                }
            }
        };
        
        container.appendChild(button);
        container.appendChild(input);
        messageContainer.appendChild(container);
    };
    
    // --- Form submission logic ---
    const handleFormSubmit = async (event) => {
        event.preventDefault(); 
        const userText = chatInput.value.trim();
        if (userText === "") return;
        clearChoiceBubbles();
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
    };
    chatForm.addEventListener("submit", handleFormSubmit);

    // Initial welcome message
    const initialWrapper = addMessage("chat-bot", "");
    const initialBubble = initialWrapper.querySelector('.chat-message');
    initialBubble.textContent = "";
    typeMessage(initialBubble, welcomeMessage);
});