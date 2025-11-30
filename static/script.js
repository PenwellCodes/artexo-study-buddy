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
    console.log('Sidebar current state:', {
        isActive: isActive,
        sidebarElement: sidebar,
        sidebarClasses: sidebar.className,
        sidebarTransform: window.getComputedStyle(sidebar).transform,
        sidebarDisplay: window.getComputedStyle(sidebar).display,
        sidebarVisibility: window.getComputedStyle(sidebar).visibility,
        sidebarZIndex: window.getComputedStyle(sidebar).zIndex,
        sidebarLeft: window.getComputedStyle(sidebar).left,
        sidebarWidth: window.getComputedStyle(sidebar).width
    });
    
    if (isActive) {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        hamburgerBtn.classList.remove('active');
        console.log('Sidebar closed');
    } else {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        hamburgerBtn.classList.add('active');
        console.log('Sidebar opened - checking styles after adding active class');
        
        // Check styles after a brief delay to ensure CSS has applied
        setTimeout(() => {
            const styles = window.getComputedStyle(sidebar);
            console.log('Sidebar styles after opening:', {
                transform: styles.transform,
                display: styles.display,
                visibility: styles.visibility,
                zIndex: styles.zIndex,
                left: styles.left,
                width: styles.width,
                hasActiveClass: sidebar.classList.contains('active'),
                offsetLeft: sidebar.offsetLeft,
                offsetWidth: sidebar.offsetWidth
            });
        }, 100);
        
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
    // Re-query to ensure element exists
    const listElement = document.getElementById('sessionsList');
    if (!listElement) {
        console.error('Sessions list element not found!');
        return;
    }
    
    console.log('loadSessions called, listElement found:', listElement);
    
    try {
        listElement.innerHTML = '<div class="loading-sessions">Loading sessions...</div>';
        
        const response = await fetch(`${API_BASE}/chat/sessions?limit=50`);
        
        if (!response.ok) {
            throw new Error('Failed to load sessions');
        }
        
        const data = await response.json();
        console.log('Received sessions data:', data);
        if (data && data.sessions) {
            displaySessions(data.sessions);
        } else {
            console.error('Invalid response format:', data);
            listElement.innerHTML = '<div class="empty-sessions"><p>Invalid response format</p></div>';
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
        if (listElement) {
            listElement.innerHTML = '<div class="empty-sessions"><p>Failed to load sessions</p></div>';
        }
    }
}

// Display sessions in sidebar
function displaySessions(sessions) {
    // Re-query the element to ensure it exists
    const listElement = document.getElementById('sessionsList');
    if (!listElement) {
        console.error('sessionsList element not found in displaySessions!');
        return;
    }
    
    console.log('Displaying sessions:', sessions);
    
    if (!sessions || sessions.length === 0) {
        listElement.innerHTML = `
            <div class="empty-sessions">
                <p>No previous chats</p>
                <p style="font-size: 12px; margin-top: 10px;">Start a conversation to see it here</p>
            </div>
        `;
        return;
    }
    
    // Clear existing content
    listElement.innerHTML = '';
    console.log('Cleared sessionsList, starting to render', sessions.length, 'sessions');
    console.log('List element before rendering:', {
        offsetHeight: listElement.offsetHeight,
        offsetWidth: listElement.offsetWidth,
        computedDisplay: window.getComputedStyle(listElement).display,
        computedVisibility: window.getComputedStyle(listElement).visibility,
        computedOpacity: window.getComputedStyle(listElement).opacity,
        parent: listElement.parentElement,
        parentDisplay: listElement.parentElement ? window.getComputedStyle(listElement.parentElement).display : 'N/A'
    });
    
    // Create and append session items
    sessions.forEach((session, index) => {
        try {
            const sessionItem = document.createElement('div');
            sessionItem.className = 'session-item';
            sessionItem.dataset.sessionId = session.session_id;
            sessionItem.style.display = 'block'; // Ensure it's visible
            sessionItem.style.minHeight = '60px'; // Ensure it has height
            
            if (session.session_id === currentSessionId) {
                sessionItem.classList.add('active');
            }
            
            // Format timestamp - with error handling
            let timeStr = 'New';
            try {
                if (session.last_message_time) {
                    timeStr = formatTime(session.last_message_time);
                }
            } catch (e) {
                console.warn('Error formatting time:', e);
                timeStr = 'Recent';
            }
            
            // Create preview text (truncate if too long)
            const preview = session.preview || 'New conversation';
            const truncatedPreview = preview.length > 60 ? preview.substring(0, 60) + '...' : preview;
            
            // Build HTML safely
            const previewHtml = escapeHtml(truncatedPreview);
            const messageCount = session.message_count || 0;
            
            sessionItem.innerHTML = `
                <div class="session-preview">${previewHtml}</div>
                <div class="session-meta">
                    <span class="session-time">${timeStr}</span>
                    <span class="session-count">${messageCount} msgs</span>
                </div>
            `;
            
            sessionItem.addEventListener('click', () => {
                console.log('Loading session:', session.session_id);
                loadSession(session.session_id);
            });
            
            listElement.appendChild(sessionItem);
            
            // Force visibility check
            const itemStyles = window.getComputedStyle(sessionItem);
            if (itemStyles.display === 'none' || itemStyles.visibility === 'hidden' || itemStyles.opacity === '0') {
                console.warn(`⚠️ Session item ${index + 1} has visibility issues:`, {
                    display: itemStyles.display,
                    visibility: itemStyles.visibility,
                    opacity: itemStyles.opacity
                });
            }
            
            console.log(`✓ Added session ${index + 1}/${sessions.length}: ${session.session_id}`, {
                preview: truncatedPreview,
                timeStr: timeStr,
                messageCount: messageCount,
                offsetHeight: sessionItem.offsetHeight,
                offsetWidth: sessionItem.offsetWidth,
                display: itemStyles.display,
                visibility: itemStyles.visibility
            });
        } catch (error) {
            console.error(`✗ Error rendering session ${index}:`, error, session);
        }
    });
    
    console.log(`✅ Successfully rendered ${sessions.length} sessions in sidebar`);
    
    // Debug: Check visibility of first session item
    if (listElement.children.length > 0) {
        const firstItem = listElement.children[0];
        const firstItemStyles = window.getComputedStyle(firstItem);
        console.log('First session item styles:', {
            display: firstItemStyles.display,
            visibility: firstItemStyles.visibility,
            opacity: firstItemStyles.opacity,
            height: firstItemStyles.height,
            minHeight: firstItemStyles.minHeight,
            offsetHeight: firstItem.offsetHeight,
            offsetWidth: firstItem.offsetWidth,
            backgroundColor: firstItemStyles.backgroundColor,
            color: firstItemStyles.color
        });
    }
    
    // Debug: Check sidebar visibility
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        const sidebarStyles = window.getComputedStyle(sidebar);
        console.log('Sidebar styles:', {
            display: sidebarStyles.display,
            visibility: sidebarStyles.visibility,
            transform: sidebarStyles.transform,
            left: sidebarStyles.left,
            hasActiveClass: sidebar.classList.contains('active'),
            offsetWidth: sidebar.offsetWidth,
            offsetHeight: sidebar.offsetHeight
        });
    }
    
    console.log('List element info:', {
        childrenCount: listElement.children.length,
        offsetHeight: listElement.offsetHeight,
        scrollHeight: listElement.scrollHeight,
        offsetWidth: listElement.offsetWidth,
        computedDisplay: window.getComputedStyle(listElement).display,
        computedVisibility: window.getComputedStyle(listElement).visibility
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

