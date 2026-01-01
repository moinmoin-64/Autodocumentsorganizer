/**
 * Performance Analytics - TypeScript Version
 * Tracks Core Web Vitals and API performance metrics
 */
import type { PerformanceAnalytics as PerformanceAnalyticsType, PerformanceMonitorConfig } from '../../../types/api';
/**
 * Performance Analytics class
 */
export declare class PerformanceAnalyticsClass {
    private config;
    private vitals;
    private apiMetrics;
    private errorCount;
    private resourceTiming;
    constructor(config?: Partial<PerformanceMonitorConfig>);
    /**
     * Initialize performance analytics
     */
    private initialize;
    /**
     * Track Core Web Vitals
     */
    private trackCoreWebVitals;
    /**
     * Capture resource timing
     */
    private captureResourceTiming;
    /**
     * Track JavaScript errors
     */
    private trackErrors;
    /**
     * Track API call metrics
     */
    trackAPICall(endpoint: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH', status: number, duration: number, size?: number): void;
    /**
     * Get current analytics snapshot
     */
    getAnalytics(): PerformanceAnalyticsType;
    /**
     * Get performance score (0-100)
     */
    getPerformanceScore(): number;
    /**
     * Get average API latency
     */
    getAverageAPILatency(): number;
    /**
     * Reset metrics
     */
    reset(): void;
    /**
     * Send analytics to backend
     */
    sendAnalytics(): Promise<void>;
}
export declare const performanceAnalytics: PerformanceAnalyticsClass;
//# sourceMappingURL=performance-analytics.d.ts.map