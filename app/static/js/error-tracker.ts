/**
 * Error Tracker - TypeScript Version
 * Provides comprehensive error tracking and reporting
 */

import type {
    ErrorEvent as ErrorEventType,
    ErrorTrackingRequest,
    ErrorTrackerConfig,
    UserContext,
    Breadcrumb,
} from '../../../types/api';

/**
 * Error Tracker class for capturing and reporting errors
 */
export class ErrorTracker {
    private config: Required<ErrorTrackerConfig>;
    private errors: ErrorEventType[] = [];
    private breadcrumbs: Breadcrumb[] = [];
    private userContext: UserContext = {};
    private flushTimer?: NodeJS.Timeout;

    constructor(config: Partial<ErrorTrackerConfig> = {}) {
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
    private initialize(): void {
        if (!this.config.enabled) {
            console.debug('Error tracking is disabled');
            return;
        }

        if (this.config.captureUnhandledErrors) {
            window.addEventListener('error', (event: Event) => {
                const errorEvent = event as ErrorEvent;
                this.captureError({
                    type: 'error',
                    message: errorEvent.message || 'Unknown error',
                    stack: errorEvent.error?.stack,
                    lineNumber: errorEvent.lineno,
                    columnNumber: errorEvent.colno,
                    url: errorEvent.filename,
                    timestamp: Date.now(),
                } as ErrorEventType);
            });
        }

        if (this.config.captureUnhandledRejections) {
            window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
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
    public captureError(error: ErrorEventType): void {
        if (!this.config.enabled) return;

        const enrichedError: ErrorEventType = {
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
    public addBreadcrumb(
        type: Breadcrumb['type'],
        message: string,
        data?: Record<string, any>
    ): void {
        const breadcrumb: Breadcrumb = {
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
    public setUser(context: UserContext): void {
        this.userContext = context;
        this.addBreadcrumb('user-action', 'User context updated', context);
    }

    /**
     * Flush errors to backend
     */
    public async flush(): Promise<void> {
        if (this.errors.length === 0) {
            return;
        }

        const payload: ErrorTrackingRequest = {
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
        } catch (error) {
            console.error('❌ Failed to flush errors:', error);
            // Keep errors for retry
        }
    }

    /**
     * Start auto-flush timer
     */
    private startAutoFlush(): void {
        this.flushTimer = setInterval(() => {
            this.flush();
        }, this.config.flushInterval);
    }

    /**
     * Stop auto-flush timer
     */
    public stopAutoFlush(): void {
        if (this.flushTimer) {
            clearInterval(this.flushTimer);
        }
    }

    /**
     * Get captured errors
     */
    public getErrors(): ErrorEventType[] {
        return [...this.errors];
    }

    /**
     * Get breadcrumb trail
     */
    public getBreadcrumbs(): Breadcrumb[] {
        return [...this.breadcrumbs];
    }

    /**
     * Clear errors
     */
    public clear(): void {
        this.errors = [];
        this.breadcrumbs = [];
    }

    /**
     * Destroy tracker
     */
    public destroy(): void {
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
