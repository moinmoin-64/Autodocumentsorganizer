/**
 * Image Lazy Loading Module
 * Implements Intersection Observer for optimal performance
 * Progressive Image Loading with blur-up effect
 */

class LazyImageLoader {
    constructor(options = {}) {
        this.options = {
            rootMargin: options.rootMargin || '50px',
            threshold: options.threshold || 0.01,
            placeholderQuality: options.placeholderQuality || 'low',
            enableBlurUp: options.enableBlurUp !== false
        };

        this.observer = null;
        this.init();
    }

    init() {
        // Create Intersection Observer for lazy loading
        this.observer = new IntersectionObserver(
            (entries) => this.onIntersection(entries),
            {
                rootMargin: this.options.rootMargin,
                threshold: this.options.threshold
            }
        );

        // Observe all lazy-load images
        this.observeImages();

        console.log('✅ Lazy Image Loader initialized');
    }

    observeImages() {
        const images = document.querySelectorAll('img[data-lazy-src]');
        images.forEach(img => {
            this.observer.observe(img);
            // Add placeholder blur effect
            if (this.options.enableBlurUp && img.src) {
                img.style.filter = 'blur(10px)';
            }
        });
    }

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
                        this.observer.unobserve(img);
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
            this.onIntersection([{ target: element, isIntersecting: true }]);
        }
    }

    /**
     * Reload all images (useful after DOM changes)
     */
    reload() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.init();
    }
}

/**
 * Responsive Image Service
 * Serves appropriately sized images based on device
 */
class ResponsiveImageService {
    constructor() {
        this.breakpoints = {
            xs: { width: 320, quality: 60 },
            sm: { width: 480, quality: 70 },
            md: { width: 768, quality: 80 },
            lg: { width: 1200, quality: 85 },
            xl: { width: 1600, quality: 90 }
        };
    }

    /**
     * Get appropriate image URL based on device width
     */
    getImageUrl(baseUrl, options = {}) {
        const width = window.innerWidth;
        const dpr = window.devicePixelRatio || 1;
        const breakpoint = this.getBreakpoint(width);

        // Calculate actual width needed (considering DPR)
        const targetWidth = Math.ceil(width * dpr);
        const quality = this.breakpoints[breakpoint].quality;

        // Build URL with parameters
        const params = new URLSearchParams({
            w: targetWidth,
            q: quality,
            ...options
        });

        return `${baseUrl}?${params.toString()}`;
    }

    /**
     * Get current breakpoint
     */
    getBreakpoint(width = window.innerWidth) {
        if (width < 480) return 'xs';
        if (width < 768) return 'sm';
        if (width < 1200) return 'md';
        if (width < 1600) return 'lg';
        return 'xl';
    }

    /**
     * Generate srcset string for responsive images
     */
    generateSrcset(baseUrl) {
        return Object.entries(this.breakpoints)
            .map(([bp, config]) => {
                const url = this.getImageUrl(baseUrl, { w: config.width });
                return `${url} ${config.width}w`;
            })
            .join(', ');
    }
}

/**
 * Image Optimization Utility
 * Compression, caching, and delivery optimization
 */
class ImageOptimizer {
    constructor() {
        this.supportedFormats = {
            webp: this.supportsWebP(),
            avif: this.supportsAVIF(),
            jpeg: true,
            png: true
        };
        this.cache = new Map();
    }

    /**
     * Check WebP support
     */
    supportsWebP() {
        const canvas = document.createElement('canvas');
        return canvas.toDataURL('image/webp').indexOf('image/webp') === 5;
    }

    /**
     * Check AVIF support
     */
    supportsAVIF() {
        const canvas = document.createElement('canvas');
        return canvas.toDataURL('image/avif').indexOf('image/avif') === 5;
    }

    /**
     * Get optimal format for image delivery
     */
    getOptimalFormat(originalFormat) {
        // AVIF > WebP > Original
        if (this.supportedFormats.avif) return 'avif';
        if (this.supportedFormats.webp) return 'webp';
        return originalFormat;
    }

    /**
     * Convert image to optimal format
     */
    convertToOptimalFormat(imageUrl) {
        if (!imageUrl) return imageUrl;

        const url = new URL(imageUrl, window.location.origin);
        const format = this.getOptimalFormat(this.getFormat(imageUrl));

        // Cache converted URL
        const cacheKey = `${imageUrl}:${format}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        // Add format parameter to URL
        url.searchParams.set('format', format);
        const optimized = url.toString();
        this.cache.set(cacheKey, optimized);

        return optimized;
    }

    /**
     * Extract format from URL
     */
    getFormat(url) {
        const ext = url.split('.').pop().split('?')[0].toLowerCase();
        return ext || 'jpeg';
    }

    /**
     * Get cache-busting version string
     */
    getCacheVersion(url) {
        // Add version parameter for cache busting if needed
        const version = this.getFormat(url).charCodeAt(0);
        return `v=${version}`;
    }
}

/**
 * Document Image Preprocessor
 * Optimizes images in document preview
 */
class DocumentImageOptimizer {
    constructor() {
        this.lazyLoader = new LazyImageLoader();
        this.responsiveService = new ResponsiveImageService();
        this.imageOptimizer = new ImageOptimizer();
    }

    /**
     * Optimize all document preview images
     */
    optimizeDocumentImages(container = document) {
        const images = container.querySelectorAll('.document-preview img, .document-thumbnail img');
        
        images.forEach(img => {
            // Set responsive srcset
            const srcset = this.responsiveService.generateSrcset(img.src);
            img.setAttribute('srcset', srcset);
            img.setAttribute('sizes', '(max-width: 480px) 100vw, (max-width: 768px) 50vw, 33vw');

            // Convert to optimal format
            const optimized = this.imageOptimizer.convertToOptimalFormat(img.src);
            img.setAttribute('data-lazy-src', optimized);
            img.src = this.getPlaceholder();

            // Add lazy loading
            this.lazyLoader.observer.observe(img);
        });
    }

    /**
     * Get base64 encoded placeholder
     * Tiny blurred placeholder for blur-up effect
     */
    getPlaceholder() {
        return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3C/svg%3E';
    }
}

// Initialize services
const lazyLoader = new LazyImageLoader();
const responsiveImages = new ResponsiveImageService();
const imageOptimizer = new ImageOptimizer();
const docImageOptimizer = new DocumentImageOptimizer();

// Reload lazy loader after dynamic content loaded
const originalLoadRecentDocuments = window.loadRecentDocuments;
if (originalLoadRecentDocuments) {
    window.loadRecentDocuments = async function(...args) {
        const result = await originalLoadRecentDocuments.apply(this, args);
        // Reload lazy images after documents loaded
        setTimeout(() => {
            lazyLoader.reload();
            docImageOptimizer.optimizeDocumentImages();
        }, 100);
        return result;
    };
}

// Re-optimize on search results
const originalPerformSearch = window.performSearch;
if (originalPerformSearch) {
    window.performSearch = async function(...args) {
        const result = await originalPerformSearch.apply(this, args);
        setTimeout(() => {
            lazyLoader.reload();
            docImageOptimizer.optimizeDocumentImages();
        }, 100);
        return result;
    };
}

// Export services globally
window.lazyLoader = lazyLoader;
window.responsiveImages = responsiveImages;
window.imageOptimizer = imageOptimizer;
window.docImageOptimizer = docImageOptimizer;

console.log('✅ Image Optimization Services loaded');
