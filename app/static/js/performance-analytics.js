/**
 * Performance Analytics Dashboard
 * Real-time monitoring of system performance
 */

class PerformanceAnalytics {
    constructor() {
        this.metrics = {
            pageLoadTime: null,
            firstContentfulPaint: null,
            largestContentfulPaint: null,
            firstInputDelay: null,
            cumulativeLayoutShift: null,
            timeToInteractive: null,
            totalBlockingTime: null,
            domContentLoaded: null,
            apiLatencies: [],
            resourceTiming: {}
        };

        this.thresholds = {
            good: {
                lcp: 2500,    // 2.5s
                fid: 100,     // 100ms
                cls: 0.1,     // 0.1
                fcp: 1800,    // 1.8s
                tti: 3500,    // 3.5s
                api: 500      // 500ms
            },
            poor: {
                lcp: 4000,    // 4s
                fid: 300,     // 300ms
                cls: 0.25,    // 0.25
                fcp: 3000,    // 3s
                tti: 5500,    // 5.5s
                api: 1000     // 1s
            }
        };

        this.init();
    }

    init() {
        // Use PerformanceObserver for Core Web Vitals
        this.observeWebVitals();
        this.observeResourceTiming();
        this.measurePageLoad();
        
        console.log('✅ Performance Analytics initialized');
    }

    /**
     * Observe Web Vitals using PerformanceObserver
     */
    observeWebVitals() {
        if (!window.PerformanceObserver) {
            console.warn('⚠️ PerformanceObserver not supported');
            return;
        }

        // LCP (Largest Contentful Paint)
        try {
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.largestContentfulPaint = lastEntry.renderTime || lastEntry.loadTime;
                console.log(`📊 LCP: ${Math.round(this.metrics.largestContentfulPaint)}ms`);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        } catch (e) {
            console.warn('⚠️ LCP observer failed:', e);
        }

        // FID (First Input Delay)
        try {
            const fidObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    this.metrics.firstInputDelay = entry.processingDuration;
                    console.log(`📊 FID: ${Math.round(this.metrics.firstInputDelay)}ms`);
                }
            });
            fidObserver.observe({ entryTypes: ['first-input'] });
        } catch (e) {
            console.warn('⚠️ FID observer failed:', e);
        }

        // CLS (Cumulative Layout Shift)
        try {
            const clsObserver = new PerformanceObserver((list) => {
                let clsValue = 0;
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
                this.metrics.cumulativeLayoutShift = clsValue;
                console.log(`📊 CLS: ${clsValue.toFixed(3)}`);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
        } catch (e) {
            console.warn('⚠️ CLS observer failed:', e);
        }

        // FCP (First Contentful Paint)
        try {
            const fcpObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.name === 'first-contentful-paint') {
                        this.metrics.firstContentfulPaint = entry.startTime;
                        console.log(`📊 FCP: ${Math.round(this.metrics.firstContentfulPaint)}ms`);
                    }
                }
            });
            fcpObserver.observe({ entryTypes: ['paint'] });
        } catch (e) {
            console.warn('⚠️ FCP observer failed:', e);
        }
    }

    /**
     * Observe resource timing (API calls, images, etc.)
     */
    observeResourceTiming() {
        if (!window.PerformanceObserver) return;

        try {
            const resourceObserver = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    const duration = entry.duration;
                    
                    if (entry.name.includes('/api/')) {
                        this.metrics.apiLatencies.push({
                            url: entry.name,
                            duration: duration,
                            size: entry.transferSize,
                            type: 'api'
                        });
                    } else {
                        this.metrics.resourceTiming[entry.name] = {
                            duration: duration,
                            size: entry.transferSize
                        };
                    }
                }
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
        } catch (e) {
            console.warn('⚠️ Resource observer failed:', e);
        }
    }

    /**
     * Measure page load time
     */
    measurePageLoad() {
        if (!window.performance || !window.performance.timing) {
            console.warn('⚠️ Performance API not available');
            return;
        }

        window.addEventListener('load', () => {
            const timing = window.performance.timing;
            const navigation = window.performance.navigation;

            this.metrics.pageLoadTime = timing.loadEventEnd - timing.navigationStart;
            this.metrics.domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
            this.metrics.timeToInteractive = timing.domInteractive - timing.navigationStart;

            console.log(`📊 Page Load Time: ${Math.round(this.metrics.pageLoadTime)}ms`);
            console.log(`📊 DOM Content Loaded: ${Math.round(this.metrics.domContentLoaded)}ms`);
            console.log(`📊 Time to Interactive: ${Math.round(this.metrics.timeToInteractive)}ms`);
        });
    }

    /**
     * Get performance rating
     */
    getPerformanceRating() {
        const ratings = {};

        // LCP rating
        if (this.metrics.largestContentfulPaint) {
            ratings.lcp = this.metrics.largestContentfulPaint <= this.thresholds.good.lcp ? 'good' :
                         this.metrics.largestContentfulPaint <= this.thresholds.poor.lcp ? 'needs-improvement' : 'poor';
        }

        // FID rating
        if (this.metrics.firstInputDelay) {
            ratings.fid = this.metrics.firstInputDelay <= this.thresholds.good.fid ? 'good' :
                         this.metrics.firstInputDelay <= this.thresholds.poor.fid ? 'needs-improvement' : 'poor';
        }

        // CLS rating
        if (this.metrics.cumulativeLayoutShift) {
            ratings.cls = this.metrics.cumulativeLayoutShift <= this.thresholds.good.cls ? 'good' :
                         this.metrics.cumulativeLayoutShift <= this.thresholds.poor.cls ? 'needs-improvement' : 'poor';
        }

        // FCP rating
        if (this.metrics.firstContentfulPaint) {
            ratings.fcp = this.metrics.firstContentfulPaint <= this.thresholds.good.fcp ? 'good' :
                         this.metrics.firstContentfulPaint <= this.thresholds.poor.fcp ? 'needs-improvement' : 'poor';
        }

        // API rating
        const avgApiLatency = this.metrics.apiLatencies.length > 0
            ? this.metrics.apiLatencies.reduce((sum, m) => sum + m.duration, 0) / this.metrics.apiLatencies.length
            : 0;

        if (avgApiLatency > 0) {
            ratings.api = avgApiLatency <= this.thresholds.good.api ? 'good' :
                         avgApiLatency <= this.thresholds.poor.api ? 'needs-improvement' : 'poor';
        }

        return ratings;
    }

    /**
     * Get overall Lighthouse-like score
     */
    getPerformanceScore() {
        const ratings = this.getPerformanceRating();
        let score = 0;
        let count = 0;

        Object.values(ratings).forEach(rating => {
            if (rating === 'good') score += 100;
            else if (rating === 'needs-improvement') score += 50;
            else if (rating === 'poor') score += 0;
            count++;
        });

        return count > 0 ? Math.round(score / count) : null;
    }

    /**
     * Get all metrics
     */
    getMetrics() {
        return {
            ...this.metrics,
            rating: this.getPerformanceRating(),
            score: this.getPerformanceScore()
        };
    }

    /**
     * Send metrics to backend
     */
    async sendMetrics() {
        try {
            const response = await fetch('/api/metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.getMetrics())
            });

            if (response.ok) {
                console.log('📤 Metrics sent to backend');
            }
        } catch (error) {
            console.error('❌ Failed to send metrics:', error);
        }
    }

    /**
     * Print performance report
     */
    printReport() {
        const metrics = this.getMetrics();
        console.log('%c═══ PERFORMANCE REPORT ═══', 'color: #5B4BF2; font-weight: bold; font-size: 14px;');
        console.log(`%cPage Load Time: ${Math.round(metrics.pageLoadTime)}ms`, 'color: #2ecc71');
        console.log(`%cLCP: ${Math.round(metrics.largestContentfulPaint)}ms (${metrics.rating.lcp})`, 'color: #2ecc71');
        console.log(`%cFID: ${Math.round(metrics.firstInputDelay)}ms (${metrics.rating.fid})`, 'color: #2ecc71');
        console.log(`%cCLS: ${metrics.cumulativeLayoutShift?.toFixed(3)} (${metrics.rating.cls})`, 'color: #2ecc71');
        console.log(`%cFCP: ${Math.round(metrics.firstContentfulPaint)}ms (${metrics.rating.fcp})`, 'color: #2ecc71');
        console.log(`%cAPI Calls: ${metrics.apiLatencies.length}`, 'color: #2ecc71');
        console.log(`%cPerformance Score: ${metrics.score}/100`, 'color: #5B4BF2; font-weight: bold;');
        console.log('%c═══════════════════════════', 'color: #5B4BF2');
    }
}

// Initialize Performance Analytics
const performanceAnalytics = new PerformanceAnalytics();

// Send metrics periodically
setInterval(() => {
    performanceAnalytics.sendMetrics();
}, 60000); // Every minute

// Export globally
window.performanceAnalytics = performanceAnalytics;

console.log('✅ Performance Analytics loaded');
