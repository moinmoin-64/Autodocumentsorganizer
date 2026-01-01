/**
 * Error Tracker - TypeScript Version
 * Provides comprehensive error tracking and reporting
 */
import type { ErrorEvent as ErrorEventType, ErrorTrackerConfig, UserContext, Breadcrumb } from '../../../types/api';
/**
 * Error Tracker class for capturing and reporting errors
 */
export declare class ErrorTracker {
    private config;
    private errors;
    private breadcrumbs;
    private userContext;
    private flushTimer?;
    constructor(config?: Partial<ErrorTrackerConfig>);
    /**
     * Initialize error tracking
     */
    private initialize;
    /**
     * Capture an error
     */
    captureError(error: ErrorEventType): void;
    /**
     * Add a breadcrumb
     */
    addBreadcrumb(type: Breadcrumb['type'], message: string, data?: Record<string, any>): void;
    /**
     * Set user context
     */
    setUser(context: UserContext): void;
    /**
     * Flush errors to backend
     */
    flush(): Promise<void>;
    /**
     * Start auto-flush timer
     */
    private startAutoFlush;
    /**
     * Stop auto-flush timer
     */
    stopAutoFlush(): void;
    /**
     * Get captured errors
     */
    getErrors(): ErrorEventType[];
    /**
     * Get breadcrumb trail
     */
    getBreadcrumbs(): Breadcrumb[];
    /**
     * Clear errors
     */
    clear(): void;
    /**
     * Destroy tracker
     */
    destroy(): void;
}
export declare const errorTracker: ErrorTracker;
//# sourceMappingURL=error-tracker.d.ts.map