/**
 * Performance Analytics - TypeScript Version
 * Tracks Core Web Vitals and API performance metrics
 */
/**
 * Performance Analytics class
 */
export class PerformanceAnalyticsClass {
    constructor(config = {}) {
        this.vitals = {};
        this.apiMetrics = [];
        this.errorCount = 0;
        this.resourceTiming = [];
        this.config = {
            enabled: true,
            trackCoreWebVitals: true,
            trackAPIMetrics: true,
            trackErrors: true,
            captureResourceTiming: true,
            sampleRate: 1.0,
            ...config,
        };
        this.initialize();
    }
    /**
     * Initialize performance analytics
     */
    initialize() {
        if (!this.config.enabled)
            return;
        if (this.config.trackCoreWebVitals) {
            this.trackCoreWebVitals();
        }
        if (this.config.captureResourceTiming) {
            this.captureResourceTiming();
        }
        if (this.config.trackErrors) {
            this.trackErrors();
        }
        console.log('✅ Performance Analytics initialized');
    }
    /**
     * Track Core Web Vitals
     */
    trackCoreWebVitals() {
        try {
            // Largest Contentful Paint
            if ('PerformanceObserver' in window) {
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.vitals.lcp = (lastEntry.renderTime || lastEntry.loadTime || lastEntry.startTime);
                    console.debug(`📊 LCP: ${this.vitals.lcp}ms`);
                });
                try {
                    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
                }
                catch (e) {
                    console.debug('LCP observer not supported');
                }
                // First Input Delay / Interaction to Next Paint
                const fidObserver = new PerformanceObserver((list) => {
                    list.getEntries().forEach((entry) => {
                        this.vitals.fid = entry.processingDuration;
                        console.debug(`📊 FID: ${this.vitals.fid}ms`);
                    });
                });
                try {
                    fidObserver.observe({
                        type: 'first-input',
                        buffered: true,
                    });
                }
                catch (e) {
                    console.debug('FID observer not supported');
                }
                // Cumulative Layout Shift
                const clsObserver = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            const firstSessionEntry = this.vitals.cls || 0;
                            this.vitals.cls = firstSessionEntry + entry.value;
                            console.debug(`📊 CLS: ${this.vitals.cls}`);
                        }
                    }
                });
                try {
                    clsObserver.observe({
                        type: 'layout-shift',
                        buffered: true,
                    });
                }
                catch (e) {
                    console.debug('CLS observer not supported');
                }
            }
            // First Contentful Paint
            const fcp = performance
                .getEntriesByName('first-contentful-paint')
                .find((e) => e.name === 'first-contentful-paint');
            if (fcp) {
                this.vitals.fcp = fcp.startTime;
                console.debug(`📊 FCP: ${this.vitals.fcp}ms`);
            }
        }
        catch (error) {
            console.error('❌ Error tracking Core Web Vitals:', error);
        }
    }
    /**
     * Capture resource timing
     */
    captureResourceTiming() {
        try {
            const resources = performance.getEntriesByType('resource');
            this.resourceTiming = resources;
            console.debug(`📊 Resource Timing: ${resources.length} resources`);
        }
        catch (error) {
            console.error('❌ Error capturing resource timing:', error);
        }
    }
    /**
     * Track JavaScript errors
     */
    trackErrors() {
        window.addEventListener('error', () => {
            this.errorCount++;
        });
        window.addEventListener('unhandledrejection', () => {
            this.errorCount++;
        });
    }
    /**
     * Track API call metrics
     */
    trackAPICall(endpoint, method, status, duration, size) {
        if (!this.config.trackAPIMetrics)
            return;
        const metric = {
            endpoint,
            method,
            status,
            duration,
            timestamp: Date.now(),
            size,
        };
        this.apiMetrics.push(metric);
        console.debug(`📊 API: ${method} ${endpoint} - ${status} (${duration}ms)`);
    }
    /**
     * Get current analytics snapshot
     */
    getAnalytics() {
        return {
            vitals: { ...this.vitals },
            api: [...this.apiMetrics],
            errors: this.errorCount,
            resourceTiming: [...this.resourceTiming],
        };
    }
    /**
     * Get performance score (0-100)
     */
    getPerformanceScore() {
        let score = 100;
        // LCP: 0-2500ms is good
        if (this.vitals.lcp) {
            if (this.vitals.lcp > 4000)
                score -= 30;
            else if (this.vitals.lcp > 2500)
                score -= 15;
        }
        // FID: 0-100ms is good
        if (this.vitals.fid) {
            if (this.vitals.fid > 300)
                score -= 30;
            else if (this.vitals.fid > 100)
                score -= 15;
        }
        // CLS: 0-0.1 is good
        if (this.vitals.cls) {
            if (this.vitals.cls > 0.25)
                score -= 30;
            else if (this.vitals.cls > 0.1)
                score -= 15;
        }
        // API errors
        const errorRate = this.apiMetrics.filter((m) => m.status >= 400).length;
        if (errorRate > 0) {
            score -= Math.min(errorRate * 5, 20);
        }
        return Math.max(0, Math.round(score));
    }
    /**
     * Get average API latency
     */
    getAverageAPILatency() {
        if (this.apiMetrics.length === 0)
            return 0;
        const total = this.apiMetrics.reduce((sum, m) => sum + m.duration, 0);
        return Math.round(total / this.apiMetrics.length);
    }
    /**
     * Reset metrics
     */
    reset() {
        this.vitals = {};
        this.apiMetrics = [];
        this.errorCount = 0;
        this.resourceTiming = [];
    }
    /**
     * Send analytics to backend
     */
    async sendAnalytics() {
        const analytics = this.getAnalytics();
        try {
            const response = await fetch('/api/analytics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...analytics,
                    score: this.getPerformanceScore(),
                    averageLatency: this.getAverageAPILatency(),
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            console.debug('✅ Analytics sent successfully');
        }
        catch (error) {
            console.error('❌ Failed to send analytics:', error);
        }
    }
}
// Export singleton instance
export const performanceAnalytics = new PerformanceAnalyticsClass({
    enabled: true,
});
// Auto-send analytics on page unload
window.addEventListener('beforeunload', () => {
    performanceAnalytics.sendAnalytics();
});
//# sourceMappingURL=performance-analytics.js.map