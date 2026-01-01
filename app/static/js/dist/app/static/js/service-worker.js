"use strict";
/**
 * Service Worker - TypeScript Version
 * Offline Support, Caching Strategy, Background Sync
 * PWA Features für Enhanced UX
 */
const CACHE_VERSION = 'v1.0';
const CACHE_NAMES = {
    assets: `${CACHE_VERSION}-assets`,
    api: `${CACHE_VERSION}-api`,
    documents: `${CACHE_VERSION}-documents`,
    images: `${CACHE_VERSION}-images`
};
const API_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const DOCUMENT_CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours
/**
 * Cache first strategy
 */
async function cacheFirst(request) {
    const cache = await caches.open(CACHE_NAMES.api);
    const cached = await cache.match(request);
    if (cached)
        return cached;
    try {
        const response = await fetch(request);
        cache.put(request, response.clone());
        return response;
    }
    catch (error) {
        throw new Error('No cached response available');
    }
}
/**
 * Network first strategy
 */
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    try {
        const response = await fetch(request);
        cache.put(request, response.clone());
        return response;
    }
    catch (error) {
        const cached = await cache.match(request);
        if (cached)
            return cached;
        throw error;
    }
}
/**
 * Cache first with network update
 */
async function cacheFirstWithUpdate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    // Return cached response immediately
    if (cached) {
        // Update cache in background
        fetch(request)
            .then(response => {
            if (response.ok) {
                cache.put(request, response);
            }
        })
            .catch(() => {
            // Ignore network errors in background update
        });
        return cached;
    }
    // No cache, fetch from network
    const response = await fetch(request);
    cache.put(request, response.clone());
    return response;
}
/**
 * Install Event - Precache critical assets
 */
self.addEventListener('install', (event) => {
    console.log('⚙️ Service Worker installing...');
    event.waitUntil(caches.open(CACHE_NAMES.assets).then((cache) => {
        // Precache critical assets
        return cache.addAll([
            '/',
            '/index.html',
            '/app/static/css/style.css',
            '/app/static/css/mobile.css',
            '/app/static/js/app.js',
            '/app/static/js/api-client.js',
            '/app/static/js/performance-monitor.js',
            '/app/static/js/mobile-menu.js',
            '/app/static/js/error-handler.js',
            '/app/static/js/notifications.js'
        ]).catch((error) => {
            console.warn('⚠️ Failed to precache assets:', error);
        });
    })
        .then(() => {
        const sw = self;
        sw.skipWaiting();
    }));
});
/**
 * Activate Event - Clean up old caches
 */
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker activating...');
    event.waitUntil(caches.keys().then((cacheNames) => {
        return Promise.all(cacheNames.map((cacheName) => {
            // Delete old cache versions
            if (!Object.values(CACHE_NAMES).includes(cacheName)) {
                console.log(`🗑️ Deleting old cache: ${cacheName}`);
                return caches.delete(cacheName);
            }
            return Promise.resolve();
        }));
    })
        .then(() => {
        const sw = self;
        sw.clients.claim();
    }));
});
/**
 * Fetch Event - Smart caching strategies
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    // API requests - Network First, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request, CACHE_NAMES.api).catch(() => new Response(JSON.stringify({
            success: false,
            error: { message: 'Offline - cached data unavailable' }
        }), { status: 503, headers: { 'Content-Type': 'application/json' } })));
        return;
    }
    // Document requests - Cache First, fallback to network
    if (url.pathname.startsWith('/api/documents/') ||
        url.pathname.startsWith('/documents/')) {
        event.respondWith(cacheFirst(request).catch(() => new Response('Document not available offline', { status: 503 })));
        return;
    }
    // Image requests - Cache First with network update
    if (request.headers.get('accept')?.includes('image')) {
        event.respondWith(cacheFirstWithUpdate(request, CACHE_NAMES.images).catch(() => new Response('Image not available', { status: 503 })));
        return;
    }
    // Asset requests - Cache First, fallback to network
    if (url.pathname.startsWith('/app/static/') ||
        url.pathname.endsWith('.css') ||
        url.pathname.endsWith('.js')) {
        event.respondWith(cacheFirst(request).catch(() => new Response('Asset not available offline', { status: 503 })));
        return;
    }
    // Default - Network First, fallback to cache
    event.respondWith(networkFirst(request, CACHE_NAMES.assets).catch(() => new Response('Resource unavailable', { status: 503 })));
});
/**
 * Background Sync Event (when connection restored)
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-pending') {
        event.waitUntil((async () => {
            try {
                console.log('🔄 Syncing pending operations...');
                // TODO: Implement actual sync logic
            }
            catch (error) {
                console.error('Sync failed:', error);
                throw error;
            }
        })());
    }
});
/**
 * Message Event (communication from client)
 */
self.addEventListener('message', (event) => {
    const { data } = event;
    if (data.type === 'SKIP_WAITING') {
        const sw = self;
        sw.skipWaiting();
    }
    if (data.type === 'CLEAR_CACHE') {
        caches.keys().then((names) => {
            names.forEach(name => caches.delete(name));
        });
    }
});
console.log('✅ Service Worker script loaded');
//# sourceMappingURL=service-worker.js.map