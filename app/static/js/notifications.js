/**
 * Toast Notification System
 * Displays non-intrusive notifications
 */
class NotificationManager {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    /**
     * Show a toast notification
     * @param {string} title - Title of the notification
     * @param {string} message - Message body
     * @param {string} type - 'success', 'error', 'info'
     * @param {number} duration - Duration in ms (default 5000)
     */
    show(title, message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = this.getIcon(type);

        toast.innerHTML = `
            <div class="toast-icon"><i class="${icon}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close"><i class="fas fa-times"></i></button>
        `;

        // Close button
        toast.querySelector('.toast-close').onclick = () => this.close(toast);

        this.container.appendChild(toast);

        // Auto close
        setTimeout(() => this.close(toast), duration);
    }

    close(toast) {
        toast.style.animation = 'slideIn 0.3s ease-in reverse';
        setTimeout(() => toast.remove(), 300);
    }

    getIcon(type) {
        switch (type) {
            case 'success': return 'fas fa-check-circle';
            case 'error': return 'fas fa-exclamation-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            default: return 'fas fa-info-circle';
        }
    }
}

// Export global instance
window.notifications = new NotificationManager();
