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
export class ErrorHandler {
    private toastContainer: HTMLElement;
    private readonly toastColors: Record<ToastType, string> = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    private readonly toastIcons: Record<ToastType, string> = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };

    constructor() {
        this.toastContainer = this.createToastContainer();
        this.addStyles();
    }

    /**
     * Create or retrieve toast container
     */
    private createToastContainer(): HTMLElement {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Add CSS animations
     */
    private addStyles(): void {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(400px);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Show toast notification
     */
    public showToast(
        message: string,
        type: ToastType = 'info',
        duration: number = 3000
    ): HTMLElement {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const color = this.toastColors[type] || this.toastColors.info;
        const icon = this.toastIcons[type] || this.toastIcons.info;

        toast.style.cssText = `
            background: ${color};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 250px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
            font-size: 14px;
        `;

        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.style.cssText = `
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 18px;
            padding: 0;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        closeButton.onmouseover = () => closeButton.style.opacity = '1';
        closeButton.onmouseout = () => closeButton.style.opacity = '0.7';
        closeButton.onclick = () => toast.remove();

        toast.innerHTML = `
            <span style="font-size: 18px; font-weight: bold;">${icon}</span>
            <span style="flex: 1;">${message}</span>
        `;
        toast.appendChild(closeButton);

        this.toastContainer.appendChild(toast);

        // Auto-remove
        if (duration > 0) {
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    }

    /**
     * Show success toast
     */
    public showSuccess(message: string, duration: number = 3000): HTMLElement {
        return this.showToast(message, 'success', duration);
    }

    /**
     * Show error toast
     */
    public showError(message: string, duration: number = 5000): HTMLElement {
        return this.showToast(message, 'error', duration);
    }

    /**
     * Show warning toast
     */
    public showWarning(message: string, duration: number = 4000): HTMLElement {
        return this.showToast(message, 'warning', duration);
    }

    /**
     * Show info toast
     */
    public showInfo(message: string, duration: number = 3000): HTMLElement {
        return this.showToast(message, 'info', duration);
    }

    /**
     * Handle API errors
     */
    public handleAPIError(error: APIError | Error): void {
        console.error('API Error:', error);

        if (error instanceof APIError) {
            switch (error.code) {
                case 'NOT_FOUND':
                    this.showError('Resource nicht gefunden');
                    break;
                case 'VALIDATION_ERROR': {
                    const fields = (error.details?.fields || {}) as Record<string, string[]>;
                    const fieldErrors = Object.entries(fields)
                        .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
                        .join('<br>');
                    this.showError(`Validierung fehlgeschlagen:<br>${fieldErrors}`, 7000);
                    break;
                }
                case 'UNAUTHORIZED':
                    this.showError('Nicht autorisiert. Bitte anmelden.');
                    setTimeout(() => { window.location.href = '/login'; }, 2000);
                    break;
                case 'FORBIDDEN':
                    this.showError('Zugriff verweigert');
                    break;
                case 'SERVER_ERROR':
                    this.showError('Server-Fehler. Bitte später erneut versuchen.');
                    break;
                default:
                    this.showError(error.message || 'Ein unerwarteter Fehler ist aufgetreten');
            }
        } else {
            this.showError(error.message || 'Netzwerkfehler');
        }
    }

    /**
     * Show confirmation dialog
     */
    public confirm(
        message: string,
        onConfirm?: () => void,
        onCancel?: () => void
    ): void {
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10001;
        `;

        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
            max-width: 400px;
            width: 90%;
        `;

        dialog.innerHTML = `
            <h3 style="margin: 0 0 16px 0; font-size: 18px; color: #111;">Bestätigung</h3>
            <p style="margin: 0 0 20px 0; color: #666;">${message}</p>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button id="cancel-btn" style="
                    padding: 8px 16px;
                    border: 1px solid #ddd;
                    background: white;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                ">Abbrechen</button>
                <button id="confirm-btn" style="
                    padding: 8px 16px;
                    border: none;
                    background: #3b82f6;
                    color: white;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                ">Bestätigen</button>
            </div>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        const confirmBtn = dialog.querySelector<HTMLButtonElement>('#confirm-btn');
        const cancelBtn = dialog.querySelector<HTMLButtonElement>('#cancel-btn');

        if (confirmBtn) {
            confirmBtn.onclick = () => {
                overlay.remove();
                onConfirm?.();
            };
        }

        if (cancelBtn) {
            cancelBtn.onclick = () => {
                overlay.remove();
                onCancel?.();
            };
        }

        overlay.onclick = (e: MouseEvent) => {
            if (e.target === overlay) {
                overlay.remove();
                onCancel?.();
            }
        };
    }
}

// Global instance
export const errorHandler = new ErrorHandler();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorHandler, errorHandler };
}
