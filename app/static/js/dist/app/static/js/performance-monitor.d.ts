/**
 * Performance Monitoring & RUM (Real User Monitoring) - TypeScript Version
 * Tracks Core Web Vitals, API Performance, and User Interactions
 * Production-ready monitoring solution
 */
/**
 * Web Vitals metric
 */
export interface VitalMetric {
    value: number;
    rating: 'good' | 'needs-improvement' | 'poor';
    timestamp: number;
}
/**
 * API call metric
 */
export interface APIMetric {
    endpoint: string;
    method: string;
    duration: number;
    status: number;
    size: number;
    timestamp: number;
}
/**
 * Performance metrics
 */
export interface PerformanceMetrics {
    vitals: Record<string, VitalMetric>;
    api: APIMetric[];
    events: any[];
    errors: any[];
}
/**
 * Performance Monitor for RUM
 */
export declare class PerformanceMonitor {
    private metrics;
    private initialized;
    constructor();
    /**
     * Initialize performance monitor
     */
    private init;
    /**
     * Track Core Web Vitals
     */
    private trackCoreWebVitals;
    /**
     * Intercept API requests
     */
    private interceptAPIRequests;
    /**
     * Track errors
     */
    private trackErrors;
    /**
     * Track user interactions
     */
    private trackInteractions;
    /**
     * Rate metric
     */
    private rateMetric;
    /**
     * Get metrics
     */
    getMetrics(): PerformanceMetrics;
    /**
     * Get vitals summary
     */
    getVitalsSummary(): Record<string, number>;
    /**
     * Get API performance
     */
    getAPIPerformance(): {
        avgDuration: number;
        totalCalls: number;
        errors: number;
    };
    /**
     * Get performance score (0-100)
     */
    getPerformanceScore(): number;
    /**
     * Send metrics to server
     */
    sendMetrics(): Promise<void>;
    /**
     * Clear metrics
     */
    clearMetrics(): void;
    /**
     * Is initialized
     */
    isInitialized(): boolean;
}
export declare const performanceMonitor: PerformanceMonitor;
declare global {
    interface Window {
        performanceMonitor: PerformanceMonitor;
    }
}
//# sourceMappingURL=performance-monitor.d.ts.map