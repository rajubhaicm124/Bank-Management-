document.addEventListener("DOMContentLoaded", () => {
    // Light & Dark Theme Swapping Toggle Logic
    const toggleBtn = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem("theme") || "light";
    
    document.documentElement.setAttribute("data-theme", currentTheme);
    if(toggleBtn) {
        toggleBtn.innerText = currentTheme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode";
        
        toggleBtn.addEventListener("click", () => {
            let theme = document.documentElement.getAttribute("data-theme");
            let newTheme = theme === "dark" ? "light" : "dark";
            
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            toggleBtn.innerText = newTheme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode";
        });
    }

    // AI Chat Panel Interface Handler Logic
    const sendChatBtn = document.getElementById("sendChatBtn");
    const chatInput = document.getElementById("chatInput");
    const chatLogs = document.getElementById("chatLogs");

    if (sendChatBtn && chatInput) {
        sendChatBtn.addEventListener("click", () => {
            const userText = chatInput.value.trim();
            if(!userText) return;

            appendMsg(userText, 'user');
            chatInput.value = '';

            fetch('/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText })
            })
            .then(res => res.json())
            .then(data => {
                appendMsg(data.response, 'ai');
            });
        });
    }

    function appendMsg(text, sender) {
        const div = document.createElement('div');
        div.classList.add('chat-msg', sender);
        div.innerText = text;
        chatLogs.appendChild(div);
        chatLogs.scrollTop = chatLogs.scrollHeight;
    }
});
