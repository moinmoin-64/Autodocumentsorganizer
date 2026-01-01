/**
 * Image Lazy Loading Module - TypeScript Version
 * Implements Intersection Observer for optimal performance
 * Progressive Image Loading with blur-up effect
 */
/**
 * Lazy image loader options
 */
export interface LazyImageLoaderOptions {
    rootMargin?: string;
    threshold?: number;
    placeholderQuality?: 'low' | 'medium' | 'high';
    enableBlurUp?: boolean;
}
/**
 * Lazy Image Loader
 */
export declare class LazyImageLoader {
    private options;
    private observer;
    constructor(options?: LazyImageLoaderOptions);
    /**
     * Initialize lazy image loader
     */
    private init;
    /**
     * Observe all images with data-lazy-src
     */
    private observeImages;
    /**
     * Handle intersection observer callback
     */
    private onIntersection;
    /**
     * Manually trigger load for an image
     */
    forceLoad(element: HTMLImageElement): void;
    /**
     * Reload all images (useful after DOM changes)
     */
    reload(): void;
    /**
     * Get observer
     */
    getObserver(): IntersectionObserver | null;
    /**
     * Stop observing (cleanup)
     */
    destroy(): void;
}
export declare const lazyImageLoader: LazyImageLoader;
declare global {
    interface Window {
        lazyImageLoader: LazyImageLoader;
    }
}
//# sourceMappingURL=image-optimizer.d.ts.map