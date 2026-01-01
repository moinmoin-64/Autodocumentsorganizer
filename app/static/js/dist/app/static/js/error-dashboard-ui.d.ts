/**
 * Error Dashboard UI - TypeScript Version
 * Display and manage errors from frontend
 */
/**
 * Error Dashboard UI
 */
export declare class ErrorDashboardUI {
    private container;
    private errorTracker;
    constructor();
    /**
     * Initialize dashboard
     */
    private init;
    /**
     * Create dashboard HTML
     */
    private createDashboard;
    /**
     * Attach event listeners
     */
    private attachEventListeners;
    /**
     * Load errors
     */
    private loadErrors;
    /**
     * Add error to dashboard
     */
    addError(error: any, type?: 'error' | 'warning' | 'info'): void;
    /**
     * Clear errors
     */
    clearErrors(): void;
    /**
     * Show dashboard
     */
    show(): void;
    /**
     * Hide dashboard
     */
    hide(): void;
}
export declare const errorDashboardUI: ErrorDashboardUI;
declare global {
    interface Window {
        errorDashboardUI: ErrorDashboardUI;
    }
}
//# sourceMappingURL=error-dashboard-ui.d.ts.map