// API base URL
const API_BASE = '/api';

// State management
let currentSessionId = null;
let isLoading = false;

// DOM elements - will be initialized after DOM loads
let chatMessages, messageInput, sendBtn, newChatBtn, loadingIndicator;
let hamburgerBtn, sidebar, sidebarOverlay, closeSidebarBtn, sessionsList;

// Initialize - create new session on load
window.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements
    chatMessages = document.getElementById('chatMessages');
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    newChatBtn = document.getElementById('newChatBtn');
    loadingIndicator = document.getElementById('loadingIndicator');
    hamburgerBtn = document.getElementById('hamburgerBtn');
    sidebar = document.getElementById('sidebar');
    sidebarOverlay = document.getElementById('sidebarOverlay');
    closeSidebarBtn = document.getElementById('closeSidebarBtn');
    sessionsList = document.getElementById('sessionsList');
    
    // Verify all elements exist
    if (!hamburgerBtn) {
        console.error('Hamburger button not found!');
    }
    if (!sidebar) {
        console.error('Sidebar not found!');
    }
    if (!sidebarOverlay) {
        console.error('Sidebar overlay not found!');
    }
    
    if (hamburgerBtn && sidebar && sidebarOverlay) {
        console.log('All hamburger menu elements found');
    }
    
    createNewSession();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    if (sendBtn) sendBtn.addEventListener('click', handleSendMessage);
    if (newChatBtn) newChatBtn.addEventListener('click', handleNewChat);
    
    // Hamburger menu and sidebar
    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Hamburger button clicked!');
            toggleSidebar();
        });
        console.log('Hamburger button event listener attached');
    } else {
        console.error('Hamburger button not found!');
    }
    
    if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);
    
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
    
    // Load sessions list on initialization
    loadSessions();
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
    // Refresh sessions list
    if (sidebar.classList.contains('active')) {
        loadSessions();
    }
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
        
        // Refresh sessions list to update last message time
        if (sidebar.classList.contains('active')) {
            loadSessions();
        }
        
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

// Sidebar Management
function toggleSidebar() {
    console.log('Toggle sidebar called');
    if (!sidebar || !sidebarOverlay || !hamburgerBtn) {
        console.error('Sidebar elements not found!', { sidebar, sidebarOverlay, hamburgerBtn });
        return;
    }
    
    const isActive = sidebar.classList.contains('active');
    
    if (isActive) {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        hamburgerBtn.classList.remove('active');
    } else {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        hamburgerBtn.classList.add('active');
        // Load sessions when opening
        loadSessions();
    }
}

// Make toggleSidebar available globally for inline onclick
window.toggleSidebar = toggleSidebar;

function closeSidebar() {
    sidebar.classList.remove('active');
    sidebarOverlay.classList.remove('active');
    hamburgerBtn.classList.remove('active');
}

// Load and display sessions
async function loadSessions() {
    if (!sessionsList) {
        console.error('Sessions list element not found!');
        return;
    }
    
    try {
        sessionsList.innerHTML = '<div class="loading-sessions">Loading sessions...</div>';
        
        const response = await fetch(`${API_BASE}/chat/sessions?limit=50`);
        
        if (!response.ok) {
            throw new Error('Failed to load sessions');
        }
        
        const data = await response.json();
        displaySessions(data.sessions);
    } catch (error) {
        console.error('Error loading sessions:', error);
        if (sessionsList) {
            sessionsList.innerHTML = '<div class="empty-sessions"><p>Failed to load sessions</p></div>';
        }
    }
}

// Display sessions in sidebar
function displaySessions(sessions) {
    if (sessions.length === 0) {
        sessionsList.innerHTML = `
            <div class="empty-sessions">
                <p>No previous chats</p>
                <p style="font-size: 12px; margin-top: 10px;">Start a conversation to see it here</p>
            </div>
        `;
        return;
    }
    
    sessionsList.innerHTML = '';
    
    sessions.forEach(session => {
        const sessionItem = document.createElement('div');
        sessionItem.className = 'session-item';
        if (session.session_id === currentSessionId) {
            sessionItem.classList.add('active');
        }
        
        // Format timestamp
        const timeStr = session.last_message_time 
            ? formatTime(session.last_message_time)
            : 'New';
        
        sessionItem.innerHTML = `
            <div class="session-preview">${escapeHtml(session.preview)}</div>
            <div class="session-meta">
                <span class="session-time">${timeStr}</span>
                <span class="session-count">${session.message_count} msgs</span>
            </div>
        `;
        
        sessionItem.addEventListener('click', () => {
            loadSession(session.session_id);
        });
        
        sessionsList.appendChild(sessionItem);
    });
}

// Load a specific session
async function loadSession(sessionId) {
    if (sessionId === currentSessionId) {
        closeSidebar();
        return;
    }
    
    try {
        setLoading(true);
        
        // Fetch full conversation history
        const response = await fetch(`${API_BASE}/chat/${sessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load session');
        }
        
        const data = await response.json();
        
        // Update current session
        currentSessionId = sessionId;
        
        // Clear current messages
        chatMessages.innerHTML = '';
        
        // Load messages into UI
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                addMessageToUI(msg.role, msg.content);
            });
        } else {
            // Re-add welcome message if session is empty
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome-message';
            welcomeDiv.innerHTML = '<p>👋 Welcome! I\'m your study assistant. Ask me questions about your study materials, and I\'ll help you understand the concepts. I can also provide test questions to help you practice!</p>';
            chatMessages.appendChild(welcomeDiv);
        }
        
        // Refresh sessions list to highlight active session
        loadSessions();
        
        // Close sidebar
        closeSidebar();
        
    } catch (error) {
        console.error('Error loading session:', error);
        showError('Failed to load session. Please try again.');
    } finally {
        setLoading(false);
    }
}

// Format timestamp for display
function formatTime(isoString) {
    if (!isoString) return 'New';
    
    try {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        // Format as date
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch (e) {
        return 'Recent';
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

