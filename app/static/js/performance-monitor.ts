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
export class PerformanceMonitor {
    private metrics: PerformanceMetrics = {
        vitals: {},
        api: [],
        events: [],
        errors: []
    };
    private initialized: boolean = false;

    constructor() {
        this.init();
    }

    /**
     * Initialize performance monitor
     */
    private init(): void {
        // Track Core Web Vitals
        this.trackCoreWebVitals();

        // Track API calls
        this.interceptAPIRequests();

        // Track errors
        this.trackErrors();

        // Track user interactions
        this.trackInteractions();

        this.initialized = true;
        console.log('✅ Performance Monitor initialized');
    }

    /**
     * Track Core Web Vitals
     */
    private trackCoreWebVitals(): void {
        if (!('PerformanceObserver' in window)) return;

        try {
            // Largest Contentful Paint (LCP)
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1] as any;
                const value = lastEntry.renderTime || lastEntry.loadTime;
                this.metrics.vitals.LCP = {
                    value,
                    rating: this.rateMetric('LCP', value),
                    timestamp: performance.now()
                };
                console.log(`📊 LCP: ${value.toFixed(0)}ms [${this.metrics.vitals.LCP.rating}]`);
            });

            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

            // First Input Delay (FID)
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const firstInput = entries[0] as any;
                const value = firstInput.processingDuration;
                this.metrics.vitals.FID = {
                    value,
                    rating: this.rateMetric('FID', value),
                    timestamp: performance.now()
                };
                console.log(`📊 FID: ${value.toFixed(0)}ms [${this.metrics.vitals.FID.rating}]`);
            });

            fidObserver.observe({ entryTypes: ['first-input'] });

            // Cumulative Layout Shift (CLS)
            let clsValue = 0;
            const clsObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry: any) => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                this.metrics.vitals.CLS = {
                    value: clsValue,
                    rating: this.rateMetric('CLS', clsValue),
                    timestamp: performance.now()
                };
                console.log(`📊 CLS: ${clsValue.toFixed(3)} [${this.metrics.vitals.CLS.rating}]`);
            });

            clsObserver.observe({ entryTypes: ['layout-shift'] });

        } catch (error) {
            console.debug('PerformanceObserver error:', error);
        }
    }

    /**
     * Intercept API requests
     */
    private interceptAPIRequests(): void {
        const originalFetch = window.fetch;

        window.fetch = (async (...args: any[]): Promise<Response> => {
            const startTime = performance.now();
            const [resource] = args;
            const config = args[1] || {};
            const method = (config.method || 'GET').toUpperCase();

            try {
                const response = await originalFetch(resource, config);
                const duration = performance.now() - startTime;

                this.metrics.api.push({
                    endpoint: String(resource),
                    method,
                    duration,
                    status: response.status,
                    size: response.headers.get('content-length') ? parseInt(response.headers.get('content-length')!, 10) : 0,
                    timestamp: startTime
                });

                return response;
            } catch (error) {
                const duration = performance.now() - startTime;
                this.metrics.api.push({
                    endpoint: String(resource),
                    method,
                    duration,
                    status: 0,
                    size: 0,
                    timestamp: startTime
                });
                throw error;
            }
        }) as any;
    }

    /**
     * Track errors
     */
    private trackErrors(): void {
        window.addEventListener('error', (event: ErrorEvent) => {
            this.metrics.errors.push({
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                timestamp: performance.now()
            });
        });

        window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
            this.metrics.errors.push({
                type: 'unhandledRejection',
                reason: event.reason,
                timestamp: performance.now()
            });
        });
    }

    /**
     * Track user interactions
     */
    private trackInteractions(): void {
        document.addEventListener('click', (event: MouseEvent) => {
            this.metrics.events.push({
                type: 'click',
                target: (event.target as HTMLElement)?.tagName,
                timestamp: performance.now()
            });
        }, true);

        document.addEventListener('input', () => {
            this.metrics.events.push({
                type: 'input',
                timestamp: performance.now()
            });
        }, true);
    }

    /**
     * Rate metric
     */
    private rateMetric(metric: string, value: number): 'good' | 'needs-improvement' | 'poor' {
        const thresholds: Record<string, [number, number]> = {
            LCP: [2500, 4000],
            FID: [100, 300],
            CLS: [0.1, 0.25],
            FCP: [1800, 3000],
            TTFB: [600, 1800]
        };

        const [good, poor] = thresholds[metric] || [1000, 3000];

        if (value <= good) return 'good';
        if (value <= poor) return 'needs-improvement';
        return 'poor';
    }

    /**
     * Get metrics
     */
    public getMetrics(): PerformanceMetrics {
        return this.metrics;
    }

    /**
     * Get vitals summary
     */
    public getVitalsSummary(): Record<string, number> {
        const summary: Record<string, number> = {};
        Object.entries(this.metrics.vitals).forEach(([key, metric]) => {
            summary[key] = metric.value;
        });
        return summary;
    }

    /**
     * Get API performance
     */
    public getAPIPerformance(): { avgDuration: number; totalCalls: number; errors: number } {
        const totalCalls = this.metrics.api.length;
        const avgDuration = totalCalls > 0
            ? this.metrics.api.reduce((sum, m) => sum + m.duration, 0) / totalCalls
            : 0;
        const errors = this.metrics.api.filter(m => m.status >= 400).length;

        return { avgDuration, totalCalls, errors };
    }

    /**
     * Get performance score (0-100)
     */
    public getPerformanceScore(): number {
        let score = 100;

        // Deduct for vitals
        Object.values(this.metrics.vitals).forEach(vital => {
            if (vital.rating === 'needs-improvement') score -= 5;
            if (vital.rating === 'poor') score -= 15;
        });

        // Deduct for API errors
        const apiPerf = this.getAPIPerformance();
        score -= apiPerf.errors * 2;

        return Math.max(0, Math.min(100, score));
    }

    /**
     * Send metrics to server
     */
    public async sendMetrics(): Promise<void> {
        try {
            await fetch('/api/metrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.metrics)
            });
        } catch (error) {
            console.error('Failed to send metrics:', error);
        }
    }

    /**
     * Clear metrics
     */
    public clearMetrics(): void {
        this.metrics = {
            vitals: {},
            api: [],
            events: [],
            errors: []
        };
    }

    /**
     * Is initialized
     */
    public isInitialized(): boolean {
        return this.initialized;
    }
}

// Global instance
export const performanceMonitor = new PerformanceMonitor();

// Make global
declare global {
    interface Window {
        performanceMonitor: PerformanceMonitor;
    }
}
window.performanceMonitor = performanceMonitor;

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PerformanceMonitor, performanceMonitor };
}
