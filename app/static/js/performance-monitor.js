/**
 * Performance Monitoring & RUM (Real User Monitoring)
 * Tracks Core Web Vitals, API Performance, and User Interactions
 * Production-ready monitoring solution
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            vitals: {},
            api: [],
            events: [],
            errors: []
        };
        this.initialized = false;
        this.init();
    }

    init() {
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
     * Track Core Web Vitals using Web Vitals API
     * LCP, FID, CLS
     */
    trackCoreWebVitals() {
        // Use native performance API for Core Web Vitals
        if ('PerformanceObserver' in window) {
            // Largest Contentful Paint (LCP)
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.vitals.LCP = {
                    value: lastEntry.renderTime || lastEntry.loadTime,
                    rating: this.rateMetric('LCP', lastEntry.renderTime || lastEntry.loadTime),
                    timestamp: performance.now()
                };
                console.log(`📊 LCP: ${this.metrics.vitals.LCP.value.toFixed(0)}ms [${this.metrics.vitals.LCP.rating}]`);
            });
            
            try {
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                console.debug('LCP observer not supported');
            }

            // First Input Delay (FID)
            const fidObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const firstInput = entries[0];
                this.metrics.vitals.FID = {
                    value: firstInput.processingDuration,
                    rating: this.rateMetric('FID', firstInput.processingDuration),
                    timestamp: performance.now()
                };
                console.log(`📊 FID: ${this.metrics.vitals.FID.value.toFixed(0)}ms [${this.metrics.vitals.FID.rating}]`);
            });
            
            try {
                fidObserver.observe({ entryTypes: ['first-input'] });
            } catch (e) {
                console.debug('FID observer not supported');
            }

            // Cumulative Layout Shift (CLS)
            let clsValue = 0;
            const clsObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                        this.metrics.vitals.CLS = {
                            value: clsValue,
                            rating: this.rateMetric('CLS', clsValue),
                            timestamp: performance.now()
                        };
                    }
                }
                console.log(`📊 CLS: ${clsValue.toFixed(3)} [${this.metrics.vitals.CLS.rating}]`);
            });
            
            try {
                clsObserver.observe({ entryTypes: ['layout-shift'] });
            } catch (e) {
                console.debug('CLS observer not supported');
            }
        }

        // Mark Navigation Timing
        window.addEventListener('load', () => {
            const navTiming = performance.getEntriesByType('navigation')[0];
            this.metrics.vitals.TTI = {
                value: navTiming.domInteractive,
                rating: this.rateMetric('TTI', navTiming.domInteractive),
                timestamp: performance.now()
            };
            this.metrics.vitals.DCL = {
                value: navTiming.domContentLoadedEventEnd,
                timestamp: performance.now()
            };
            console.log(`📊 TTI: ${navTiming.domInteractive.toFixed(0)}ms`);
            console.log(`📊 DCL: ${navTiming.domContentLoadedEventEnd.toFixed(0)}ms`);
        });
    }

    /**
     * Rate metric as Good/Needs Improvement/Poor
     * Based on Web Vitals thresholds
     */
    rateMetric(metric, value) {
        const thresholds = {
            LCP: { good: 2500, poor: 4000 },
            FID: { good: 100, poor: 300 },
            CLS: { good: 0.1, poor: 0.25 },
            TTI: { good: 3000, poor: 5000 }
        };

        const threshold = thresholds[metric];
        if (!threshold) return 'unknown';

        if (value <= threshold.good) return 'good';
        if (value <= threshold.poor) return 'needs-improvement';
        return 'poor';
    }

    /**
     * Intercept and monitor all API requests
     */
    interceptAPIRequests() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const url = typeof args[0] === 'string' ? args[0] : args[0].url;

            try {
                const response = await originalFetch.apply(this, args);
                const duration = performance.now() - startTime;

                this.metrics.api.push({
                    url,
                    method: args[1]?.method || 'GET',
                    status: response.status,
                    duration,
                    timestamp: Date.now(),
                    cached: response.headers.get('x-cached') === 'true'
                });

                // Log slow requests
                if (duration > 1000) {
                    console.warn(`⚠️ Slow API: ${url} took ${duration.toFixed(0)}ms`);
                }

                return response;
            } catch (error) {
                const duration = performance.now() - startTime;
                this.metrics.api.push({
                    url,
                    method: args[1]?.method || 'GET',
                    status: 0,
                    duration,
                    error: error.message,
                    timestamp: Date.now()
                });
                throw error;
            }
        };
    }

    /**
     * Track JavaScript errors and promise rejections
     */
    trackErrors() {
        window.addEventListener('error', (event) => {
            this.metrics.errors.push({
                type: 'error',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                timestamp: Date.now()
            });
            console.error('🔴 Error tracked:', event.message);
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.metrics.errors.push({
                type: 'unhandledRejection',
                message: event.reason?.message || String(event.reason),
                timestamp: Date.now()
            });
            console.error('🔴 Unhandled Rejection tracked:', event.reason);
        });
    }

    /**
     * Track user interactions (clicks, scrolls, etc)
     */
    trackInteractions() {
        // Track clicks
        document.addEventListener('click', (e) => {
            this.metrics.events.push({
                type: 'click',
                target: e.target.className,
                timestamp: Date.now()
            });
        }, true);

        // Track scrolls (debounced)
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.metrics.events.push({
                    type: 'scroll',
                    position: window.scrollY,
                    timestamp: Date.now()
                });
            }, 1000);
        });
    }

    /**
     * Get performance summary
     */
    getSummary() {
        return {
            vitals: this.metrics.vitals,
            apiStats: this.getAPIStats(),
            errorCount: this.metrics.errors.length,
            eventCount: this.metrics.events.length
        };
    }

    /**
     * Calculate API statistics
     */
    getAPIStats() {
        if (this.metrics.api.length === 0) return null;

        const durations = this.metrics.api.map(r => r.duration);
        const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
        const max = Math.max(...durations);
        const min = Math.min(...durations);
        const cached = this.metrics.api.filter(r => r.cached).length;

        return {
            totalRequests: this.metrics.api.length,
            avgDuration: avg.toFixed(0),
            maxDuration: max.toFixed(0),
            minDuration: min.toFixed(0),
            cachedRequests: cached,
            errorCount: this.metrics.api.filter(r => r.status === 0 || r.status >= 400).length
        };
    }

    /**
     * Send metrics to server for analysis
     */
    async sendMetrics(endpoint = '/api/metrics') {
        try {
            const summary = this.getSummary();
            await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    timestamp: Date.now(),
                    url: window.location.href,
                    userAgent: navigator.userAgent,
                    metrics: summary
                })
            });
            console.log('📤 Metrics sent to server');
        } catch (error) {
            console.error('Failed to send metrics:', error);
        }
    }

    /**
     * Display performance dashboard
     */
    displayDashboard() {
        const summary = this.getSummary();
        console.clear();
        console.log('═══════════════════════════════════════');
        console.log('   PERFORMANCE MONITORING DASHBOARD');
        console.log('═══════════════════════════════════════');
        console.log('\n📊 CORE WEB VITALS:');
        Object.entries(summary.vitals).forEach(([key, value]) => {
            if (value) {
                console.log(`  ${key}: ${value.value.toFixed(0)}ms [${value.rating}]`);
            }
        });
        
        const apiStats = summary.apiStats;
        if (apiStats) {
            console.log('\n📡 API PERFORMANCE:');
            console.log(`  Requests: ${apiStats.totalRequests}`);
            console.log(`  Avg Duration: ${apiStats.avgDuration}ms`);
            console.log(`  Cached: ${apiStats.cachedRequests}`);
            console.log(`  Errors: ${apiStats.errorCount}`);
        }
        
        console.log('\n❌ ERRORS:');
        console.log(`  Total: ${summary.errorCount}`);
        
        console.log('\n✅ EVENTS:');
        console.log(`  Total: ${summary.eventCount}`);
        console.log('═══════════════════════════════════════\n');
    }
}

// Initialize Performance Monitor
const perfMonitor = new PerformanceMonitor();

// Send metrics periodically (every 5 minutes)
setInterval(() => {
    perfMonitor.sendMetrics();
}, 5 * 60 * 1000);

// Display dashboard on demand
window.showPerfDashboard = () => {
    perfMonitor.displayDashboard();
};

// Export for global access
window.perfMonitor = perfMonitor;
