/**
 * Image Lazy Loading Module - TypeScript Version
 * Implements Intersection Observer for optimal performance
 * Progressive Image Loading with blur-up effect
 */
/**
 * Lazy Image Loader
 */
export class LazyImageLoader {
    constructor(options = {}) {
        this.observer = null;
        this.options = {
            rootMargin: options.rootMargin || '50px',
            threshold: options.threshold ?? 0.01,
            placeholderQuality: options.placeholderQuality || 'low',
            enableBlurUp: options.enableBlurUp !== false
        };
        this.init();
    }
    /**
     * Initialize lazy image loader
     */
    init() {
        // Create Intersection Observer for lazy loading
        this.observer = new IntersectionObserver((entries) => this.onIntersection(entries), {
            rootMargin: this.options.rootMargin,
            threshold: this.options.threshold
        });
        // Observe all lazy-load images
        this.observeImages();
        console.log('✅ Lazy Image Loader initialized');
    }
    /**
     * Observe all images with data-lazy-src
     */
    observeImages() {
        const images = document.querySelectorAll('img[data-lazy-src]');
        images.forEach(img => {
            this.observer?.observe(img);
            // Add placeholder blur effect
            if (this.options.enableBlurUp && img.src) {
                img.style.filter = 'blur(10px)';
            }
        });
    }
    /**
     * Handle intersection observer callback
     */
    onIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const lazySrc = img.getAttribute('data-lazy-src');
                if (lazySrc) {
                    // Load high quality image
                    const fullQualityImg = new Image();
                    fullQualityImg.onload = () => {
                        img.src = lazySrc;
                        // Remove blur effect smoothly
                        img.style.filter = 'blur(0px)';
                        img.style.transition = 'filter 0.3s ease';
                        img.classList.add('lazy-loaded');
                        // Remove data attribute
                        img.removeAttribute('data-lazy-src');
                        // Stop observing
                        this.observer?.unobserve(img);
                    };
                    fullQualityImg.onerror = () => {
                        console.error(`Failed to load image: ${lazySrc}`);
                        img.classList.add('lazy-error');
                    };
                    // Start loading
                    fullQualityImg.src = lazySrc;
                }
            }
        });
    }
    /**
     * Manually trigger load for an image
     */
    forceLoad(element) {
        if (element && element.hasAttribute('data-lazy-src')) {
            const mockEntry = {
                target: element,
                isIntersecting: true
            };
            this.onIntersection([mockEntry]);
        }
    }
    /**
     * Reload all images (useful after DOM changes)
     */
    reload() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
        this.init();
    }
    /**
     * Get observer
     */
    getObserver() {
        return this.observer;
    }
    /**
     * Stop observing (cleanup)
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
    }
}
// Global instance
export const lazyImageLoader = new LazyImageLoader();
window.lazyImageLoader = lazyImageLoader;
// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        lazyImageLoader.reload();
    });
}
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LazyImageLoader, lazyImageLoader };
}
//# sourceMappingURL=image-optimizer.js.map