/**
 * Error Tracker - TypeScript Version
 * Provides comprehensive error tracking and reporting
 */
/**
 * Error Tracker class for capturing and reporting errors
 */
export class ErrorTracker {
    constructor(config = {}) {
        this.errors = [];
        this.breadcrumbs = [];
        this.userContext = {};
        this.config = {
            enabled: true,
            captureUnhandledErrors: true,
            captureUnhandledRejections: true,
            batchSize: 10,
            flushInterval: 30000, // 30 seconds
            maxBreadcrumbs: 100,
            environment: 'production',
            dsn: '',
            ...config,
        };
        this.initialize();
    }
    /**
     * Initialize error tracking
     */
    initialize() {
        if (!this.config.enabled) {
            console.debug('Error tracking is disabled');
            return;
        }
        if (this.config.captureUnhandledErrors) {
            window.addEventListener('error', (event) => {
                const errorEvent = event;
                this.captureError({
                    type: 'error',
                    message: errorEvent.message || 'Unknown error',
                    stack: errorEvent.error?.stack,
                    lineNumber: errorEvent.lineno,
                    columnNumber: errorEvent.colno,
                    url: errorEvent.filename,
                    timestamp: Date.now(),
                });
            });
        }
        if (this.config.captureUnhandledRejections) {
            window.addEventListener('unhandledrejection', (event) => {
                this.captureError({
                    type: 'error',
                    message: `Unhandled Promise Rejection: ${event.reason}`,
                    timestamp: Date.now(),
                });
            });
        }
        // Start auto-flush
        this.startAutoFlush();
        console.log('✅ Error Tracker initialized');
    }
    /**
     * Capture an error
     */
    captureError(error) {
        if (!this.config.enabled)
            return;
        const enrichedError = {
            ...error,
            context: {
                ...error.context,
                ...this.userContext,
                environment: this.config.environment,
            },
        };
        this.errors.push(enrichedError);
        this.addBreadcrumb('error', error.message, { error });
        // Auto-flush if batch size reached
        if (this.errors.length >= this.config.batchSize) {
            this.flush();
        }
    }
    /**
     * Add a breadcrumb
     */
    addBreadcrumb(type, message, data) {
        const breadcrumb = {
            type,
            message,
            data,
            timestamp: Date.now(),
        };
        this.breadcrumbs.push(breadcrumb);
        // Keep only max breadcrumbs
        if (this.breadcrumbs.length > this.config.maxBreadcrumbs) {
            this.breadcrumbs = this.breadcrumbs.slice(-this.config.maxBreadcrumbs);
        }
    }
    /**
     * Set user context
     */
    setUser(context) {
        this.userContext = context;
        this.addBreadcrumb('user-action', 'User context updated', context);
    }
    /**
     * Flush errors to backend
     */
    async flush() {
        if (this.errors.length === 0) {
            return;
        }
        const payload = {
            errors: this.errors,
            context: {
                userAgent: navigator.userAgent,
                url: window.location.href,
                timestamp: Date.now(),
            },
        };
        try {
            const response = await fetch('/api/errors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            // Clear errors on successful flush
            this.errors = [];
            console.debug('✅ Errors flushed successfully');
        }
        catch (error) {
            console.error('❌ Failed to flush errors:', error);
            // Keep errors for retry
        }
    }
    /**
     * Start auto-flush timer
     */
    startAutoFlush() {
        this.flushTimer = setInterval(() => {
            this.flush();
        }, this.config.flushInterval);
    }
    /**
     * Stop auto-flush timer
     */
    stopAutoFlush() {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }
    }
    /**
     * Get captured errors
     */
    getErrors() {
        return [...this.errors];
    }
    /**
     * Get breadcrumb trail
     */
    getBreadcrumbs() {
        return [...this.breadcrumbs];
    }
    /**
     * Clear errors
     */
    clear() {
        this.errors = [];
        this.breadcrumbs = [];
    }
    /**
     * Destroy tracker
     */
    destroy() {
        this.stopAutoFlush();
        this.clear();
        console.debug('Error Tracker destroyed');
    }
}
// Export singleton instance
export const errorTracker = new ErrorTracker({
    enabled: true,
    environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
});
//# sourceMappingURL=error-tracker.js.map