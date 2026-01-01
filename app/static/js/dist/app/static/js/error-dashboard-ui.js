/**
 * Error Dashboard UI - TypeScript Version
 * Display and manage errors from frontend
 */
/**
 * Error Dashboard UI
 */
export class ErrorDashboardUI {
    constructor() {
        this.container = null;
        this.errorTracker = window.errorTracker;
        this.init();
    }
    /**
     * Initialize dashboard
     */
    init() {
        // Create dashboard HTML
        this.createDashboard();
        this.attachEventListeners();
        this.loadErrors();
        console.log('✅ Error Dashboard UI initialized');
    }
    /**
     * Create dashboard HTML
     */
    createDashboard() {
        const dashboard = document.createElement('div');
        dashboard.id = 'error-dashboard';
        dashboard.className = 'error-dashboard';
        dashboard.innerHTML = `
            <style>
                .error-dashboard {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 350px;
                    max-height: 500px;
                    background: white;
                    border: 2px solid #5B4BF2;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    display: flex;
                    flex-direction: column;
                    z-index: 10000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }

                .error-dashboard.collapsed {
                    max-height: 50px;
                }

                .error-dashboard.collapsed .error-dashboard-content {
                    display: none;
                }

                .error-dashboard-header {
                    padding: 15px;
                    background: #5B4BF2;
                    color: white;
                    border-radius: 6px 6px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                }

                .error-dashboard-header h3 {
                    margin: 0;
                    font-size: 14px;
                    font-weight: 600;
                }

                .error-count {
                    display: inline-block;
                    background: #ff6b6b;
                    color: white;
                    border-radius: 12px;
                    padding: 2px 8px;
                    font-size: 12px;
                    margin-left: 8px;
                }

                .error-dashboard-content {
                    overflow-y: auto;
                    flex-grow: 1;
                    padding: 10px;
                }

                .error-item {
                    padding: 10px;
                    margin-bottom: 8px;
                    background: #f8f9fa;
                    border-left: 3px solid #ef4444;
                    border-radius: 4px;
                    font-size: 12px;
                }

                .error-item.warning {
                    border-left-color: #f59e0b;
                }

                .error-item.info {
                    border-left-color: #3b82f6;
                }

                .error-item-message {
                    font-weight: 500;
                    margin-bottom: 4px;
                    color: #1f2937;
                }

                .error-item-time {
                    color: #6b7280;
                    font-size: 11px;
                }
            </style>
            <div class="error-dashboard-header">
                <h3>Fehler-Monitor</h3>
                <span class="error-count">0</span>
                <button style="background: none; border: none; color: white; cursor: pointer; font-size: 18px;">×</button>
            </div>
            <div class="error-dashboard-content"></div>
        `;
        document.body.appendChild(dashboard);
        this.container = dashboard;
    }
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        if (!this.container)
            return;
        const header = this.container.querySelector('.error-dashboard-header');
        const closeBtn = header?.querySelector('button');
        if (header) {
            header.addEventListener('click', (e) => {
                if (e.target === closeBtn) {
                    this.container?.classList.remove('collapsed');
                }
                else {
                    this.container?.classList.toggle('collapsed');
                }
            });
        }
    }
    /**
     * Load errors
     */
    loadErrors() {
        // Set up observer to watch for new errors
        if (this.errorTracker) {
            console.log('Error tracker available, monitoring errors');
        }
    }
    /**
     * Add error to dashboard
     */
    addError(error, type = 'error') {
        if (!this.container)
            return;
        const content = this.container.querySelector('.error-dashboard-content');
        if (!content)
            return;
        const errorItem = document.createElement('div');
        errorItem.className = `error-item ${type}`;
        const now = new Date();
        const timeStr = now.toLocaleTimeString('de-DE');
        errorItem.innerHTML = `
            <div class="error-item-message">${error.message || String(error)}</div>
            <div class="error-item-time">${timeStr}</div>
        `;
        content.insertBefore(errorItem, content.firstChild);
        // Keep only latest 10 errors
        const items = content.querySelectorAll('.error-item');
        while (items.length > 10) {
            items[items.length - 1].remove();
        }
        // Update count
        const countBadge = this.container.querySelector('.error-count');
        if (countBadge) {
            countBadge.textContent = String(items.length);
        }
    }
    /**
     * Clear errors
     */
    clearErrors() {
        if (!this.container)
            return;
        const content = this.container.querySelector('.error-dashboard-content');
        if (content) {
            content.innerHTML = '';
        }
        const countBadge = this.container.querySelector('.error-count');
        if (countBadge) {
            countBadge.textContent = '0';
        }
    }
    /**
     * Show dashboard
     */
    show() {
        if (this.container) {
            this.container.classList.remove('collapsed');
        }
    }
    /**
     * Hide dashboard
     */
    hide() {
        if (this.container) {
            this.container.remove();
            this.container = null;
        }
    }
}
// Global instance
export const errorDashboardUI = new ErrorDashboardUI();
window.errorDashboardUI = errorDashboardUI;
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorDashboardUI, errorDashboardUI };
}
//# sourceMappingURL=error-dashboard-ui.js.map