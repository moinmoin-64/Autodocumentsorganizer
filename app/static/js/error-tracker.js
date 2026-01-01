/**
 * Error Tracking & Monitoring
 * Production error tracking compatible with Sentry
 */

class ErrorTracker {
    constructor(options = {}) {
        this.endpoint = options.endpoint || '/api/errors';
        this.environment = options.environment || 'production';
        this.release = options.release || '1.0.0';
        this.userId = options.userId || null;
        this.batchSize = options.batchSize || 10;
        this.errors = [];
        
        this.init();
    }

    init() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.captureError({
                type: 'error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // Unhandled promise rejection
        window.addEventListener('unhandledrejection', (event) => {
            this.captureError({
                type: 'unhandledRejection',
                message: event.reason?.message || String(event.reason),
                stack: event.reason?.stack
            });
        });

        // Periodic error flushing
        setInterval(() => {
            if (this.errors.length > 0) {
                this.flush();
            }
        }, 60000); // Every minute

        console.log('✅ Error Tracker initialized');
    }

    /**
     * Capture error
     */
    captureError(error) {
        const errorRecord = {
            type: error.type || 'error',
            message: error.message,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            stack: error.stack,
            context: {
                environment: this.environment,
                release: this.release,
                userId: this.userId,
                offline: !navigator.onLine
            }
        };

        // Add additional data if available
        if (error.filename) {
            errorRecord.filename = error.filename;
            errorRecord.lineno = error.lineno;
            errorRecord.colno = error.colno;
        }

        this.errors.push(errorRecord);

        // Log to console in development
        if (this.environment === 'development') {
            console.error('🔴 Error captured:', errorRecord);
        }

        // Flush if batch is full
        if (this.errors.length >= this.batchSize) {
            this.flush();
        }
    }

    /**
     * Capture message (not necessarily an error)
     */
    captureMessage(message, level = 'info') {
        const record = {
            type: 'message',
            message: message,
            level: level,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            context: {
                environment: this.environment,
                userId: this.userId
            }
        };

        this.errors.push(record);

        if (level === 'error' && this.errors.length >= this.batchSize) {
            this.flush();
        }
    }

    /**
     * Capture user action for context
     */
    captureBreadcrumb(message, data = {}) {
        const breadcrumb = {
            type: 'breadcrumb',
            message: message,
            timestamp: new Date().toISOString(),
            data: data
        };

        console.log(`🔵 Breadcrumb: ${message}`);
    }

    /**
     * Set user context
     */
    setUser(userId, userData = {}) {
        this.userId = userId;
        console.log(`👤 User set: ${userId}`);
    }

    /**
     * Clear user context
     */
    clearUser() {
        this.userId = null;
    }

    /**
     * Flush errors to server
     */
    async flush() {
        if (this.errors.length === 0) {
            return;
        }

        const batch = this.errors.splice(0, this.batchSize);

        try {
            const response = await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    errors: batch,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                console.log(`📤 Sent ${batch.length} errors to server`);
            } else {
                console.warn(`⚠️ Error tracking server returned ${response.status}`);
                // Put back in queue
                this.errors.unshift(...batch);
            }
        } catch (error) {
            console.error('❌ Failed to send errors:', error);
            // Put back in queue for retry
            this.errors.unshift(...batch);
        }
    }

    /**
     * Get error statistics
     */
    getStats() {
        return {
            total: this.errors.length,
            errors: this.errors.filter(e => e.type === 'error').length,
            messages: this.errors.filter(e => e.type === 'message').length,
            warnings: this.errors.filter(e => e.level === 'warning').length
        };
    }
}

/**
 * Sentry-compatible wrapper
 * For easy migration to Sentry if needed
 */
class SentryWrapper {
    constructor(dsn, options = {}) {
        this.tracker = new ErrorTracker({
            endpoint: options.endpoint || '/api/errors',
            environment: options.environment || 'production',
            release: options.release || '1.0.0'
        });
    }

    captureException(error) {
        this.tracker.captureError({
            type: 'exception',
            message: error.message,
            stack: error.stack
        });
    }

    captureMessage(message, level = 'info') {
        this.tracker.captureMessage(message, level);
    }

    setUser(userId) {
        this.tracker.setUser(userId);
    }

    addBreadcrumb(message, data) {
        this.tracker.captureBreadcrumb(message, data);
    }
}

// Initialize Error Tracker
const errorTracker = new ErrorTracker({
    environment: 'production',
    release: '1.0.0'
});

// Export globally
window.errorTracker = errorTracker;

console.log('✅ Error Tracker loaded');

/**
 * Sentry Integration (optional)
 * Uncomment to use actual Sentry
 * 
 * import * as Sentry from "@sentry/browser";
 * 
 * Sentry.init({
 *   dsn: "your-sentry-dsn",
 *   environment: "production",
 *   tracesSampleRate: 0.1,
 *   beforeSend(event) {
 *     // Filter out errors
 *     return event;
 *   }
 * });
 */
