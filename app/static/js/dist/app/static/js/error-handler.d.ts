/**
 * Error Handler - TypeScript Version
 * Zentrale Fehlerbehandlung mit Toast Notifications
 */
import { APIError } from './api-client';
/**
 * Toast notification types
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';
/**
 * Toast configuration
 */
export interface ToastConfig {
    message: string;
    type: ToastType;
    duration: number;
}
/**
 * Error Handler für zentrale Fehlerbehandlung
 */
export declare class ErrorHandler {
    private toastContainer;
    private readonly toastColors;
    private readonly toastIcons;
    constructor();
    /**
     * Create or retrieve toast container
     */
    private createToastContainer;
    /**
     * Add CSS animations
     */
    private addStyles;
    /**
     * Show toast notification
     */
    showToast(message: string, type?: ToastType, duration?: number): HTMLElement;
    /**
     * Show success toast
     */
    showSuccess(message: string, duration?: number): HTMLElement;
    /**
     * Show error toast
     */
    showError(message: string, duration?: number): HTMLElement;
    /**
     * Show warning toast
     */
    showWarning(message: string, duration?: number): HTMLElement;
    /**
     * Show info toast
     */
    showInfo(message: string, duration?: number): HTMLElement;
    /**
     * Handle API errors
     */
    handleAPIError(error: APIError | Error): void;
    /**
     * Show confirmation dialog
     */
    confirm(message: string, onConfirm?: () => void, onCancel?: () => void): void;
}
export declare const errorHandler: ErrorHandler;
//# sourceMappingURL=error-handler.d.ts.map