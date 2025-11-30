/**
 * Error Handler - Zentrale Fehlerbehandlung mit Toast Notifications
 */

class ErrorHandler {
    constructor() {
        this.toastContainer = this.createToastContainer();
    }

    createToastContainer() {
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

    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };

        toast.style.cssText = `
            background: ${colors[type] || colors.info};
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

        toast.innerHTML = `
            <span style="font-size: 18px; font-weight: bold;">${icons[type] || icons.info}</span>
            <span style="flex: 1;">${message}</span>
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 18px;
                padding: 0;
                opacity: 0.7;
                transition: opacity 0.2s;
            " onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'">×</button>
        `;

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

    showSuccess(message, duration = 3000) {
        return this.showToast(message, 'success', duration);
    }

    showError(message, duration = 5000) {
        return this.showToast(message, 'error', duration);
    }

    showWarning(message, duration = 4000) {
        return this.showToast(message, 'warning', duration);
    }

    showInfo(message, duration = 3000) {
        return this.showToast(message, 'info', duration);
    }

    handleAPIError(error) {
        console.error('API Error:', error);

        if (error instanceof APIError) {
            switch (error.code) {
                case 'NOT_FOUND':
                    this.showError('Resource nicht gefunden');
                    break;
                case 'VALIDATION_ERROR':
                    const fields = error.details?.fields || {};
                    const fieldErrors = Object.entries(fields)
                        .map(([field, errors]) => `${field}: ${errors.join(', ')}`)
                        .join('<br>');
                    this.showError(`Validierung fehlgeschlagen:<br>${fieldErrors}`, 7000);
                    break;
                case 'UNAUTHORIZED':
                    this.showError('Nicht autorisiert. Bitte anmelden.');
                    setTimeout(() => window.location.href = '/login', 2000);
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

    confirm(message, onConfirm, onCancel) {
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

        dialog.querySelector('#confirm-btn').onclick = () => {
            overlay.remove();
            if (onConfirm) onConfirm();
        };

        dialog.querySelector('#cancel-btn').onclick = () => {
            overlay.remove();
            if (onCancel) onCancel();
        };

        overlay.onclick = (e) => {
            if (e.target === overlay) {
                overlay.remove();
                if (onCancel) onCancel();
            }
        };
    }
}

// Add CSS animations
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

// Global instance
const errorHandler = new ErrorHandler();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorHandler, errorHandler };
}
