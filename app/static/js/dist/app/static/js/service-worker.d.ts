/**
 * Service Worker - TypeScript Version
 * Offline Support, Caching Strategy, Background Sync
 * PWA Features für Enhanced UX
 */
declare const CACHE_VERSION = "v1.0";
declare const CACHE_NAMES: {
    assets: string;
    api: string;
    documents: string;
    images: string;
};
declare const API_CACHE_DURATION: number;
declare const DOCUMENT_CACHE_DURATION: number;
/**
 * Cache first strategy
 */
declare function cacheFirst(request: Request): Promise<Response>;
/**
 * Network first strategy
 */
declare function networkFirst(request: Request, cacheName: string): Promise<Response>;
/**
 * Cache first with network update
 */
declare function cacheFirstWithUpdate(request: Request, cacheName: string): Promise<Response>;
//# sourceMappingURL=service-worker.d.ts.map