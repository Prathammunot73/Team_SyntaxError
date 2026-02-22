/**
 * Real-time Notification System
 * Handles WebSocket connections, notification display, and user interactions
 */

class NotificationManager {
    constructor() {
        this.socket = null;
        this.unreadCount = 0;
        this.notifications = [];
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.soundEnabled = localStorage.getItem('notificationSound') !== 'false';
        
        this.init();
    }
    
    init() {
        // Initialize Socket.IO connection
        this.connectWebSocket();
        
        // Create notification UI
        this.createNotificationUI();
        
        // Load initial notifications
        this.loadNotifications();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check for offline notifications on page load
        this.checkOfflineNotifications();
    }
    
    connectWebSocket() {
        try {
            // Connect to Socket.IO server
            this.socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: this.maxReconnectAttempts
            });
            
            // Connection events
            this.socket.on('connect', () => {
                console.log('✅ WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('WebSocket connection error:', error);
                this.reconnectAttempts++;
                
                if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    console.error('Max reconnection attempts reached');
                    this.showToast('Connection lost. Please refresh the page.', 'error');
                }
            });
            
            // Notification events
            this.socket.on('new_notification', (data) => {
                this.handleNewNotification(data);
            });
            
            this.socket.on('notification_read', (data) => {
                this.handleNotificationRead(data);
            });
            
            this.socket.on('all_notifications_read', () => {
                this.handleAllNotificationsRead();
            });
            
            this.socket.on('unread_count', (data) => {
                this.updateUnreadCount(data.count);
            });
            
            this.socket.on('connected', (data) => {
                console.log('Connected to notification service:', data);
            });
            
            this.socket.on('error', (data) => {
                console.error('WebSocket error:', data);
                this.showToast(data.message || 'An error occurred', 'error');
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }
    
    createNotificationUI() {
        // Check if notification bell already exists
        if (document.querySelector('.notification-bell')) {
            return;
        }
        
        // Create notification bell container
        const bellContainer = document.createElement('div');
        bellContainer.className = 'notification-bell';
        bellContainer.innerHTML = `
            <button class="notification-btn" aria-label="Notifications">
                <span class="bell-icon">🔔</span>
                <span class="notification-badge" style="display: none;">0</span>
            </button>
            <div class="notification-dropdown" style="display: none;">
                <div class="notification-header">
                    <h3>Notifications</h3>
                    <button class="mark-all-read-btn" title="Mark all as read">✓</button>
                </div>
                <div class="notification-list">
                    <div class="notification-loading">Loading...</div>
                </div>
                <div class="notification-footer">
                    <label class="sound-toggle">
                        <input type="checkbox" ${this.soundEnabled ? 'checked' : ''}>
                        <span>🔊 Sound</span>
                    </label>
                </div>
            </div>
        `;
        
        // Insert into sidebar or header
        const sidebar = document.querySelector('.sidebar-header');
        if (sidebar) {
            sidebar.appendChild(bellContainer);
        } else {
            document.body.appendChild(bellContainer);
        }
    }
    
    setupEventListeners() {
        // Notification bell click
        const bellBtn = document.querySelector('.notification-btn');
        if (bellBtn) {
            bellBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotificationDropdown();
            });
        }
        
        // Mark all as read
        const markAllBtn = document.querySelector('.mark-all-read-btn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
        
        // Sound toggle
        const soundToggle = document.querySelector('.sound-toggle input');
        if (soundToggle) {
            soundToggle.addEventListener('change', (e) => {
                this.soundEnabled = e.target.checked;
                localStorage.setItem('notificationSound', this.soundEnabled);
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.querySelector('.notification-dropdown');
            const bell = document.querySelector('.notification-bell');
            
            if (dropdown && bell && !bell.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    }
    
    toggleNotificationDropdown() {
        const dropdown = document.querySelector('.notification-dropdown');
        if (dropdown) {
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
            
            if (!isVisible) {
                this.loadNotifications();
            }
        }
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.updateUnreadCount(data.unread_count);
                this.renderNotifications();
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showNotificationError();
        }
    }
    
    renderNotifications() {
        const listContainer = document.querySelector('.notification-list');
        if (!listContainer) return;
        
        if (this.notifications.length === 0) {
            listContainer.innerHTML = `
                <div class="notification-empty">
                    <span class="empty-icon">📭</span>
                    <p>No notifications yet</p>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = this.notifications.map(notification => `
            <div class="notification-item ${notification.is_read ? 'read' : 'unread'}" 
                 data-id="${notification.id}">
                <div class="notification-icon ${notification.type}">
                    ${this.getNotificationIcon(notification.type)}
                </div>
                <div class="notification-content">
                    <h4>${this.escapeHtml(notification.title)}</h4>
                    <p>${this.escapeHtml(notification.message)}</p>
                    <span class="notification-time">${this.formatTime(notification.created_at)}</span>
                </div>
                <button class="notification-close" data-id="${notification.id}" title="Mark as read">
                    ${notification.is_read ? '✓' : '○'}
                </button>
            </div>
        `).join('');
        
        // Add click handlers
        listContainer.querySelectorAll('.notification-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = parseInt(btn.dataset.id);
                this.markAsRead(id);
            });
        });
        
        // Add notification item click handlers
        listContainer.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                this.markAsRead(id);
                // Optional: Navigate to related page
                this.handleNotificationClick(id);
            });
        });
    }
    
    handleNewNotification(data) {
        console.log('📬 New notification received:', data);
        
        // Add to notifications array
        this.notifications.unshift(data);
        
        // Update UI
        this.updateUnreadCount(this.unreadCount + 1);
        this.renderNotifications();
        
        // Show popup toast
        this.showNotificationToast(data);
        
        // Play sound
        if (this.soundEnabled) {
            this.playNotificationSound();
        }
        
        // Animate bell
        this.animateBell();
    }
    
    showNotificationToast(notification) {
        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.innerHTML = `
            <div class="toast-icon ${notification.type}">
                ${this.getNotificationIcon(notification.type)}
            </div>
            <div class="toast-content">
                <h4>${this.escapeHtml(notification.title)}</h4>
                <p>${this.escapeHtml(notification.message)}</p>
            </div>
            <button class="toast-close">×</button>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.closeToast(toast);
        });
        
        // Auto close after 5 seconds
        setTimeout(() => this.closeToast(toast), 5000);
        
        // Click to mark as read
        toast.addEventListener('click', () => {
            if (notification.id) {
                this.markAsRead(notification.id);
            }
            this.closeToast(toast);
        });
    }
    
    closeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }
    
    async markAsRead(notificationId) {
        try {
            // Emit to server
            if (this.socket && this.isConnected) {
                this.socket.emit('mark_read', { notification_id: notificationId });
            }
            
            // Update locally
            const notification = this.notifications.find(n => n.id === notificationId);
            if (notification && !notification.is_read) {
                notification.is_read = 1;
                this.updateUnreadCount(this.unreadCount - 1);
                this.renderNotifications();
            }
            
            // Also update via API
            await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            // Emit to server
            if (this.socket && this.isConnected) {
                this.socket.emit('mark_all_read');
            }
            
            // Update locally
            this.notifications.forEach(n => n.is_read = 1);
            this.updateUnreadCount(0);
            this.renderNotifications();
            
            // Also update via API
            await fetch('/api/notifications/mark-all-read', {
                method: 'POST'
            });
            
            this.showToast('All notifications marked as read', 'success');
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }
    
    handleNotificationRead(data) {
        const notification = this.notifications.find(n => n.id === data.notification_id);
        if (notification && !notification.is_read) {
            notification.is_read = 1;
            this.updateUnreadCount(this.unreadCount - 1);
            this.renderNotifications();
        }
    }
    
    handleAllNotificationsRead() {
        this.notifications.forEach(n => n.is_read = 1);
        this.updateUnreadCount(0);
        this.renderNotifications();
    }
    
    updateUnreadCount(count) {
        this.unreadCount = count;
        const badge = document.querySelector('.notification-badge');
        
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    }
    
    animateBell() {
        const bell = document.querySelector('.bell-icon');
        if (bell) {
            bell.classList.add('ring');
            setTimeout(() => bell.classList.remove('ring'), 1000);
        }
    }
    
    playNotificationSound() {
        try {
            // Create a simple beep sound using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    }
    
    updateConnectionStatus(isConnected) {
        const bell = document.querySelector('.notification-bell');
        if (bell) {
            bell.classList.toggle('disconnected', !isConnected);
        }
    }
    
    checkOfflineNotifications() {
        // Request unread count from server
        if (this.socket && this.isConnected) {
            this.socket.emit('get_unread_count');
        }
    }
    
    handleNotificationClick(notificationId) {
        // Optional: Navigate to related page based on notification type
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;
        
        // Example navigation logic
        switch (notification.type) {
            case 'marks':
            case 'result':
                window.location.href = '/student/results';
                break;
            case 'grievance':
                window.location.href = '/student/dashboard';
                break;
            default:
                break;
        }
    }
    
    getNotificationIcon(type) {
        const icons = {
            'marks': '📝',
            'result': '📊',
            'grievance': '📋',
            'notice': '📢',
            'announcement': '📣',
            'pdf_upload': '📄'
        };
        return icons[type] || '🔔';
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `simple-toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    showNotificationError() {
        const listContainer = document.querySelector('.notification-list');
        if (listContainer) {
            listContainer.innerHTML = `
                <div class="notification-error">
                    <span class="error-icon">⚠️</span>
                    <p>Failed to load notifications</p>
                    <button onclick="notificationManager.loadNotifications()">Retry</button>
                </div>
            `;
        }
    }
}

// Initialize notification manager when DOM is ready
let notificationManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Only initialize for students
        const userType = document.body.dataset.userType;
        if (userType === 'student') {
            notificationManager = new NotificationManager();
        }
    });
} else {
    const userType = document.body.dataset.userType;
    if (userType === 'student') {
        notificationManager = new NotificationManager();
    }
}
