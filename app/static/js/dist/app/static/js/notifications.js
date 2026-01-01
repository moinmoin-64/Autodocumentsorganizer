/**
 * Toast Notification System - TypeScript Version
 * Displays non-intrusive notifications
 */
/**
 * Notification Manager for toast notifications
 */
export class NotificationManager {
    constructor() {
        this.iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }
    /**
     * Show a toast notification
     * @param title - Title of the notification
     * @param message - Message body
     * @param type - Notification type ('success', 'error', 'info', 'warning')
     * @param duration - Duration in ms (default 5000)
     */
    show(title, message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = this.getIcon(type);
        toast.innerHTML = `
            <div class="toast-icon"><i class="${icon}"></i></div>
            <div class="toast-content">
                <div class="toast-title">${this.escapeHtml(title)}</div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
            <button class="toast-close"><i class="fas fa-times"></i></button>
        `;
        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.onclick = () => this.close(toast);
        }
        this.container.appendChild(toast);
        // Auto close
        setTimeout(() => this.close(toast), duration);
    }
    /**
     * Close a toast notification
     */
    close(toast) {
        toast.style.animation = 'slideIn 0.3s ease-in reverse';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
    /**
     * Get icon for notification type
     */
    getIcon(type) {
        return this.iconMap[type] || this.iconMap.info;
    }
    /**
     * HTML escape utility
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    /**
     * Show success notification
     */
    success(title, message, duration = 5000) {
        this.show(title, message, 'success', duration);
    }
    /**
     * Show error notification
     */
    error(title, message, duration = 5000) {
        this.show(title, message, 'error', duration);
    }
    /**
     * Show warning notification
     */
    warning(title, message, duration = 5000) {
        this.show(title, message, 'warning', duration);
    }
    /**
     * Show info notification
     */
    info(title, message, duration = 5000) {
        this.show(title, message, 'info', duration);
    }
}
// Export global instance for window
export const notifications = new NotificationManager();
window.notifications = notifications;
// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NotificationManager, notifications };
}
//# sourceMappingURL=notifications.js.map