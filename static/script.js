// API base URL
const API_BASE = '/api';

// State management
let currentSessionId = null;
let isLoading = false;

// DOM elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const loadingIndicator = document.getElementById('loadingIndicator');

// Initialize - create new session on load
window.addEventListener('DOMContentLoaded', () => {
    createNewSession();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    newChatBtn.addEventListener('click', handleNewChat);
    
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });
}

// Create a new chat session
async function createNewSession() {
    try {
        const response = await fetch(`${API_BASE}/chat/new`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            throw new Error('Failed to create session');
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Clear messages except welcome
        clearMessages();
    } catch (error) {
        console.error('Error creating session:', error);
        showError('Failed to start a new chat. Please refresh the page.');
    }
}

// Handle new chat button
async function handleNewChat() {
    await createNewSession();
}

// Handle sending a message
async function handleSendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isLoading) {
        return;
    }
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Show loading indicator
    setLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
            }),
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get response');
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        // Add assistant response to UI
        addMessageToUI('assistant', data.response);
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToUI('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`);
    } finally {
        setLoading(false);
    }
}

// Add message to UI
function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    bubbleDiv.appendChild(contentDiv);
    messageDiv.appendChild(bubbleDiv);
    
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Clear messages (keep welcome message)
function clearMessages() {
    const messages = chatMessages.querySelectorAll('.message');
    messages.forEach(msg => msg.remove());
    
    // Re-add welcome message if it doesn't exist
    if (!chatMessages.querySelector('.welcome-message')) {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.innerHTML = '<p>👋 Welcome! I\'m your study assistant. Ask me questions about your study materials, and I\'ll help you understand the concepts. I can also provide test questions to help you practice!</p>';
        chatMessages.appendChild(welcomeDiv);
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Set loading state
function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
    loadingIndicator.style.display = loading ? 'block' : 'none';
    
    if (loading) {
        scrollToBottom();
    }
}

// Show error message
function showError(message) {
    addMessageToUI('assistant', `⚠️ ${message}`);
}

