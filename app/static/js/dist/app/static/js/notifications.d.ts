/**
 * Toast Notification System - TypeScript Version
 * Displays non-intrusive notifications
 */
/**
 * Notification types
 */
export type NotificationType = 'success' | 'error' | 'warning' | 'info';
/**
 * Icon mapping for notification types
 */
export interface IconMap {
    success: string;
    error: string;
    warning: string;
    info: string;
}
/**
 * Notification Manager for toast notifications
 */
export declare class NotificationManager {
    private container;
    private readonly iconMap;
    constructor();
    /**
     * Show a toast notification
     * @param title - Title of the notification
     * @param message - Message body
     * @param type - Notification type ('success', 'error', 'info', 'warning')
     * @param duration - Duration in ms (default 5000)
     */
    show(title: string, message: string, type?: NotificationType, duration?: number): void;
    /**
     * Close a toast notification
     */
    private close;
    /**
     * Get icon for notification type
     */
    private getIcon;
    /**
     * HTML escape utility
     */
    private escapeHtml;
    /**
     * Show success notification
     */
    success(title: string, message: string, duration?: number): void;
    /**
     * Show error notification
     */
    error(title: string, message: string, duration?: number): void;
    /**
     * Show warning notification
     */
    warning(title: string, message: string, duration?: number): void;
    /**
     * Show info notification
     */
    info(title: string, message: string, duration?: number): void;
}
export declare const notifications: NotificationManager;
declare global {
    interface Window {
        notifications: NotificationManager;
    }
}
//# sourceMappingURL=notifications.d.ts.map