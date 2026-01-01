/**
 * API Type Definitions for OrganisationsAI Frontend
 * Provides comprehensive type safety for all API interactions
 */
/**
 * Error object structure for error tracking
 */
export interface ErrorEvent {
    type: 'error' | 'warning' | 'info';
    message: string;
    stack?: string;
    context?: Record<string, any>;
    timestamp: number;
    userId?: string;
    url?: string;
    lineNumber?: number;
    columnNumber?: number;
}
/**
 * Error tracking request payload
 */
export interface ErrorTrackingRequest {
    errors: ErrorEvent[];
    context?: {
        userAgent?: string;
        url?: string;
        timestamp?: number;
    };
}
/**
 * Error tracking response
 */
export interface ErrorTrackingResponse {
    success: boolean;
    errors_received: number;
    message: string;
}
/**
 * Error group for dashboard visualization
 */
export interface ErrorGroup {
    id: string;
    type: string;
    message: string;
    count: number;
    lastOccurred: string;
    firstOccurred: string;
    resolved: boolean;
    context?: Record<string, any>;
}
/**
 * Core Web Vitals metrics
 */
export interface CoreWebVitals {
    lcp?: number;
    fid?: number;
    cls?: number;
    fcp?: number;
    tti?: number;
}
/**
 * Performance metrics for API calls
 */
export interface APIMetric {
    endpoint: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    status: number;
    duration: number;
    timestamp: number;
    size?: number;
}
/**
 * Complete performance analytics payload
 */
export interface PerformanceAnalytics {
    vitals: CoreWebVitals;
    api: APIMetric[];
    errors: number;
    resourceTiming?: PerformanceResourceTiming[];
}
/**
 * Health check endpoint response
 */
export interface HealthCheckResponse {
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp: string;
    version: string;
    checks: {
        database?: HealthCheckStatus;
        cache?: HealthCheckStatus;
        memory?: HealthCheckStatus;
        disk?: HealthCheckStatus;
        cpu?: HealthCheckStatus;
    };
}
/**
 * Individual health check status
 */
export interface HealthCheckStatus {
    status: 'up' | 'down' | 'degraded';
    message?: string;
    value?: number;
    unit?: string;
}
/**
 * Document metadata
 */
export interface Document {
    id: string;
    title: string;
    filepath?: string;
    category?: string;
    tags?: string[];
    created_at: string;
    updated_at: string;
    content?: string;
    size?: number;
}
/**
 * Document search result
 */
export interface DocumentSearchResult {
    documents: Document[];
    total: number;
    page: number;
    pageSize: number;
    hasMore: boolean;
}
/**
 * Standard API response wrapper
 */
export interface APIResponse<T = any> {
    success: boolean;
    data?: T;
    error?: APIError;
    message?: string;
}
/**
 * Standard API error structure
 */
export interface APIError {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp?: string;
}
/**
 * User context for error tracking and analytics
 */
export interface UserContext {
    userId?: string;
    sessionId?: string;
    email?: string;
    metadata?: Record<string, any>;
}
/**
 * UI notification
 */
export interface Notification {
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message: string;
    duration?: number;
    action?: {
        label: string;
        callback: () => void;
    };
}
/**
 * Cache storage entry
 */
export interface CacheEntry<T = any> {
    key: string;
    value: T;
    timestamp: number;
    ttl?: number;
}
/**
 * Offline queue item
 */
export interface OfflineQueueItem {
    id: string;
    type: 'document' | 'update' | 'delete';
    data: any;
    timestamp: number;
    retries: number;
}
/**
 * Breadcrumb for error tracking context
 */
export interface Breadcrumb {
    type: 'navigation' | 'user-action' | 'api-call' | 'error' | 'custom';
    message: string;
    data?: Record<string, any>;
    timestamp: number;
}
/**
 * Error tracker configuration
 */
export interface ErrorTrackerConfig {
    enabled: boolean;
    captureUnhandledErrors: boolean;
    captureUnhandledRejections: boolean;
    batchSize?: number;
    flushInterval?: number;
    maxBreadcrumbs?: number;
    environment?: 'development' | 'staging' | 'production';
    dsn?: string;
}
/**
 * Performance monitor configuration
 */
export interface PerformanceMonitorConfig {
    enabled: boolean;
    trackCoreWebVitals: boolean;
    trackAPIMetrics: boolean;
    trackErrors: boolean;
    captureResourceTiming: boolean;
    sampleRate?: number;
}
/**
 * Async operation result
 */
export type AsyncResult<T, E = Error> = {
    success: true;
    data: T;
} | {
    success: false;
    error: E;
};
/**
 * Pagination options
 */
export interface PaginationOptions {
    page: number;
    pageSize: number;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
}
/**
 * Filter options for document search
 */
export interface FilterOptions {
    categories?: string[];
    tags?: string[];
    dateFrom?: string;
    dateTo?: string;
    searchQuery?: string;
}
//# sourceMappingURL=api.d.ts.map