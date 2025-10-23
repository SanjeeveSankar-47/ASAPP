document.addEventListener('DOMContentLoaded', function() {
    const chatHistory = document.getElementById('chatHistory');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const conversationList = document.getElementById('conversationList');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    let currentConversationId = generateConversationId();
    let conversations = loadConversationsFromStorage();
    let isSidebarCollapsed = false;
    
    // Initialize the UI
    renderConversationList();
    loadCurrentConversation();
    
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('input', adjustTextareaHeight);
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', startNewConversation);
    sidebarToggle.addEventListener('click', toggleSidebar);
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToConversation({
            content: message,
            type: 'user',
            timestamp: new Date().toISOString()
        });
        
        userInput.value = '';
        adjustTextareaHeight();
        sendBtn.disabled = true;
        
        showTypingIndicator();
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                conversationId: currentConversationId,
                history: getCurrentConversation().messages
            })
        })
        .then(handleResponse)
        .then(data => {
            removeTypingIndicator();
            
            if (data.error) {
                addMessageToConversation({
                    content: `Error: ${data.error}`,
                    type: 'system',
                    timestamp: new Date().toISOString()
                });
            } else {
                addMessageToConversation({
                    content: data.response,
                    type: 'assistant',
                    timestamp: new Date().toISOString()
                });
                
                // Update conversation title if first assistant message
                updateConversationTitle(data.response);
            }
        })
        .catch(error => {
            removeTypingIndicator();
            addMessageToConversation({
                content: `Error: ${error.message}`,
                type: 'system',
                timestamp: new Date().toISOString()
            });
            console.error('Error:', error);
        })
        .finally(() => {
            sendBtn.disabled = false;
            userInput.focus();
        });
    }
    
    function adjustTextareaHeight() {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
        sendBtn.disabled = !userInput.value.trim();
    }
    
    function addMessageToConversation(message) {
        const conversation = getCurrentConversation();
        
        // Add message
        conversation.messages.push(message);
        conversation.updatedAt = new Date().toISOString();
        
        // Update or add conversation
        const index = conversations.findIndex(c => c.id === currentConversationId);
        if (index === -1) {
            conversations.unshift(conversation);
        } else {
            conversations[index] = conversation;
        }
        
        // Save and update UI
        saveConversationsToStorage();
        renderConversationList();
        renderMessages(conversation.messages);
    }
    
    function getCurrentConversation() {
        return conversations.find(c => c.id === currentConversationId) || {
            id: currentConversationId,
            title: 'New Conversation',
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
    }
    
    function updateConversationTitle(assistantResponse) {
        const conversation = getCurrentConversation();
        
        // Only update title if it's still the default and we have enough messages
        if (conversation.title === 'New Conversation' && conversation.messages.length >= 2) {
            // Create a short title from the first user message
            const firstUserMessage = conversation.messages.find(m => m.type === 'user');
            if (firstUserMessage) {
                const shortTitle = firstUserMessage.content.length > 30 
                    ? firstUserMessage.content.substring(0, 30) + '...' 
                    : firstUserMessage.content;
                
                conversation.title = shortTitle;
                saveConversationsToStorage();
                renderConversationList();
            }
        }
    }
    
    function startNewConversation() {
        currentConversationId = generateConversationId();
        chatHistory.innerHTML = '';
        userInput.focus();
        
        // Add welcome message to new conversation
        addMessageToConversation({
            content: 'Hello! I\'m NexusAI. How can I assist you today? I can help with flight cancellations, travel information, and more.',
            type: 'assistant',
            timestamp: new Date().toISOString()
        });
    }
    
    function loadConversation(conversationId) {
        currentConversationId = conversationId;
        const conversation = conversations.find(c => c.id === conversationId);
        if (conversation) {
            renderMessages(conversation.messages);
        }
        userInput.focus();
        renderConversationList();
        
        // Auto-collapse sidebar on mobile
        if (window.innerWidth <= 768) {
            collapseSidebar();
        }
    }
    
    function deleteConversation(conversationId, event) {
        event.stopPropagation();
        
        if (confirm('Are you sure you want to delete this conversation?')) {
            conversations = conversations.filter(c => c.id !== conversationId);
            saveConversationsToStorage();
            
            if (currentConversationId === conversationId) {
                startNewConversation();
            }
            
            renderConversationList();
        }
    }
    
    function renderMessages(messages) {
        chatHistory.innerHTML = '';
        
        if (messages.length === 0) {
            // Show welcome message for empty conversation
            const welcomeGroup = document.createElement('div');
            welcomeGroup.className = 'message-group';
            welcomeGroup.innerHTML = `
                <div class="message-container assistant">
                    <div class="avatar assistant">N</div>
                    <div class="message-content">
                        <p>Hello! I'm NexusAI, your intelligent travel assistant. I can help you with:</p>
                        <ul>
                            <li>Flight cancellations and modifications</li>
                            <li>Travel policy information</li>
                            <li>Flight status updates</li>
                            <li>Seat availability</li>
                            <li>Pet travel policies</li>
                        </ul>
                        <p>How can I assist you today?</p>
                    </div>
                </div>
            `;
            chatHistory.appendChild(welcomeGroup);
        } else {
            // Group messages by sender for better visual grouping
            let currentGroup = null;
            
            messages.forEach(message => {
                if (!currentGroup || currentGroup.sender !== message.type) {
                    currentGroup = document.createElement('div');
                    currentGroup.className = 'message-group';
                    currentGroup.sender = message.type;
                    chatHistory.appendChild(currentGroup);
                }
                
                const messageDiv = document.createElement('div');
                messageDiv.className = `message-container ${message.type}`;
                
                const avatar = document.createElement('div');
                avatar.className = `avatar ${message.type}`;
                avatar.textContent = message.type === 'user' ? 'U' : 'N';
                
                const content = document.createElement('div');
                content.className = 'message-content';
                content.innerHTML = formatResponse(message.content);
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(content);
                currentGroup.appendChild(messageDiv);
            });
        }
        
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    function renderConversationList() {
        conversationList.innerHTML = '';
        
        // Sort conversations by updated time (newest first)
        const sortedConversations = [...conversations].sort((a, b) => 
            new Date(b.updatedAt) - new Date(a.updatedAt)
        );
        
        sortedConversations.forEach(conversation => {
            const isActive = conversation.id === currentConversationId;
            const item = document.createElement('div');
            item.className = `conversation-item ${isActive ? 'active' : ''}`;
            item.innerHTML = `
                <div class="conversation-title">${conversation.title}</div>
                <div class="conversation-delete" onclick="deleteConversation('${conversation.id}', event)">
                    <i class="fas fa-trash-alt"></i>
                </div>
            `;
            item.addEventListener('click', () => loadConversation(conversation.id));
            conversationList.appendChild(item);
        });
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="avatar assistant">N</div>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatHistory.appendChild(typingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function toggleSidebar() {
        if (isSidebarCollapsed) {
            expandSidebar();
        } else {
            collapseSidebar();
        }
    }
    
    function collapseSidebar() {
        sidebar.classList.add('collapsed');
        isSidebarCollapsed = true;
    }
    
    function expandSidebar() {
        sidebar.classList.remove('collapsed');
        isSidebarCollapsed = false;
    }
    
    function handleResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }
    
    function formatResponse(text) {
        if (!text) return '';
        
        // Enhanced markdown to HTML conversion
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/- (.*?)(?=\n|$)/g, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/✅/g, '<span style="color: #10a37f;">✅</span>')
            .replace(/❌/g, '<span style="color: #ef4444;">❌</span>')
            .replace(/ℹ️/g, '<span style="color: #3b82f6;">ℹ️</span>');
    }
    
    function generateConversationId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }
    
    function loadConversationsFromStorage() {
        try {
            const saved = localStorage.getItem('nexusai_conversations');
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    }
    
    function saveConversationsToStorage() {
        localStorage.setItem('nexusai_conversations', JSON.stringify(conversations));
    }
    
    function loadCurrentConversation() {
        const conversation = getCurrentConversation();
        renderMessages(conversation.messages);
    }
    
    // Auto-collapse sidebar on mobile
    if (window.innerWidth <= 768) {
        collapseSidebar();
    }
    
    // Make functions available globally
    window.deleteConversation = deleteConversation;
});