/**
 * Error Dashboard UI
 * Display and manage errors from frontend
 */

class ErrorDashboardUI {
    constructor() {
        this.container = null;
        this.errorTracker = window.errorTracker;
        this.init();
    }

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

                .error-dashboard-controls {
                    display: flex;
                    gap: 8px;
                }

                .error-dashboard-btn {
                    background: rgba(255,255,255,0.3);
                    border: none;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                }

                .error-dashboard-btn:hover {
                    background: rgba(255,255,255,0.5);
                }

                .error-dashboard-content {
                    flex: 1;
                    overflow-y: auto;
                    padding: 15px;
                }

                .error-item {
                    padding: 10px;
                    margin-bottom: 10px;
                    background: #f8f9fa;
                    border-left: 4px solid #ff6b6b;
                    border-radius: 4px;
                    font-size: 12px;
                    line-height: 1.4;
                }

                .error-item.warning {
                    border-left-color: #ffc107;
                }

                .error-item.info {
                    border-left-color: #17a2b8;
                }

                .error-message {
                    font-weight: 600;
                    margin-bottom: 5px;
                    color: #333;
                    word-break: break-word;
                }

                .error-time {
                    color: #999;
                    font-size: 11px;
                }

                .error-dashboard-empty {
                    text-align: center;
                    padding: 20px;
                    color: #999;
                }

                .error-dashboard-footer {
                    padding: 10px 15px;
                    border-top: 1px solid #eee;
                    background: #f8f9fa;
                    border-radius: 0 0 6px 6px;
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #666;
                }

                @media (max-width: 600px) {
                    .error-dashboard {
                        width: 100%;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        border-radius: 8px 8px 0 0;
                        max-height: 70vh;
                    }
                }
            </style>

            <div class="error-dashboard-header">
                <div>
                    <h3>🔴 Errors</h3>
                </div>
                <div class="error-dashboard-controls">
                    <button class="error-dashboard-btn" id="error-dashboard-clear">Clear</button>
                    <button class="error-dashboard-btn" id="error-dashboard-toggle">−</button>
                </div>
            </div>

            <div class="error-dashboard-content" id="error-list">
                <div class="error-dashboard-empty">No errors yet</div>
            </div>

            <div class="error-dashboard-footer">
                <span id="error-count-footer">0 errors</span>
                <a href="/admin/errors" style="color: #5B4BF2; text-decoration: none;">View all →</a>
            </div>
        `;

        document.body.appendChild(dashboard);
        this.container = dashboard;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Clear button
        document.getElementById('error-dashboard-clear').addEventListener('click', () => {
            this.clearErrors();
        });

        // Toggle button
        document.getElementById('error-dashboard-toggle').addEventListener('click', () => {
            this.container.classList.toggle('collapsed');
        });

        // Header click to toggle
        document.querySelector('.error-dashboard-header').addEventListener('click', (e) => {
            if (!e.target.closest('.error-dashboard-controls')) {
                this.container.classList.toggle('collapsed');
            }
        });
    }

    /**
     * Load errors from tracker
     */
    loadErrors() {
        setInterval(() => {
            const stats = this.errorTracker.getStats();
            const errorList = document.getElementById('error-list');
            
            if (stats.total === 0) {
                errorList.innerHTML = '<div class="error-dashboard-empty">No errors yet</div>';
            } else {
                // Show recent errors
                const errors = this.errorTracker.errors.slice(-5).reverse();
                errorList.innerHTML = errors.map(error => `
                    <div class="error-item ${error.type === 'warning' ? 'warning' : 'info'}">
                        <div class="error-message">${this.escapeHtml(error.message)}</div>
                        <div class="error-time">${new Date(error.timestamp).toLocaleTimeString()}</div>
                    </div>
                `).join('');
            }

            // Update footer
            document.getElementById('error-count-footer').textContent = `${stats.total} error${stats.total !== 1 ? 's' : ''}`;
        }, 1000);
    }

    /**
     * Clear errors
     */
    clearErrors() {
        this.errorTracker.errors = [];
        const errorList = document.getElementById('error-list');
        errorList.innerHTML = '<div class="error-dashboard-empty">No errors yet</div>';
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize Error Dashboard when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.errorDashboard = new ErrorDashboardUI();
    });
} else {
    window.errorDashboard = new ErrorDashboardUI();
}

console.log('✅ Error Dashboard UI loaded');
