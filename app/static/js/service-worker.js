/**
 * Service Worker
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
 * Install Event - Precache critical assets
 */
self.addEventListener('install', (event) => {
    console.log('⚙️ Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAMES.assets).then((cache) => {
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
        .then(() => self.skipWaiting())
    );
});

/**
 * Activate Event - Clean up old caches
 */
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old cache versions
                    if (!Object.values(CACHE_NAMES).includes(cacheName)) {
                        console.log(`🗑️ Deleting old cache: ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
        .then(() => self.clients.claim())
    );
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
        return event.respondWith(
            networkFirst(request, CACHE_NAMES.api, API_CACHE_DURATION)
        );
    }

    // Document requests - Cache First, fallback to network
    if (url.pathname.startsWith('/api/documents/') || 
        url.pathname.startsWith('/documents/')) {
        return event.respondWith(
            cacheFirst(request, CACHE_NAMES.documents)
        );
    }

    // Image requests - Cache First with network update
    if (request.headers.get('accept')?.includes('image')) {
        return event.respondWith(
            cacheFirstWithUpdate(request, CACHE_NAMES.images)
        );
    }

    // Asset requests (CSS, JS) - Cache First
    if (url.pathname.includes('.css') || 
        url.pathname.includes('.js') ||
        url.pathname.includes('.woff')) {
        return event.respondWith(
            cacheFirst(request, CACHE_NAMES.assets)
        );
    }

    // Default - Network First, fallback to cache
    return event.respondWith(
        networkFirst(request, CACHE_NAMES.assets)
    );
});

/**
 * Cache First Strategy
 * Use cache if available, fallback to network
 */
async function cacheFirst(request, cacheName) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            console.log(`📦 Cache hit: ${request.url}`);
            return cached;
        }

        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('❌ Fetch failed:', error);
        return createOfflineResponse();
    }
}

/**
 * Network First Strategy
 * Try network first, fallback to cache
 */
async function networkFirst(request, cacheName, duration = 0) {
    try {
        const response = await fetch(request);
        
        if (response.ok) {
            const cache = await caches.open(cacheName);
            const responseToCache = response.clone();
            
            // Add timestamp for expiration checking
            const cacheWithTime = new Response(responseToCache.body, {
                status: responseToCache.status,
                statusText: responseToCache.statusText,
                headers: new Headers(responseToCache.headers)
            });
            
            cache.put(request, cacheWithTime);
            console.log(`🌐 Network hit: ${request.url}`);
        }
        
        return response;
    } catch (error) {
        console.log(`📦 Network failed, using cache: ${request.url}`);
        
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        return createOfflineResponse();
    }
}

/**
 * Cache First with Background Update
 * Return cached response but update in background
 */
async function cacheFirstWithUpdate(request, cacheName) {
    const cached = await caches.match(request);
    
    // Update cache in background
    fetch(request).then((response) => {
        if (response.ok) {
            caches.open(cacheName).then((cache) => {
                cache.put(request, response);
            });
        }
    }).catch(() => {
        // Network failed - that's ok
    });

    // Return cached version immediately
    if (cached) {
        console.log(`📦 Image cache hit: ${request.url}`);
        return cached;
    }

    // No cache, try network
    try {
        const response = await fetch(request);
        caches.open(cacheName).then((cache) => {
            cache.put(request, response.clone());
        });
        return response;
    } catch (error) {
        return createOfflineResponse();
    }
}

/**
 * Create offline fallback response
 */
function createOfflineResponse() {
    return new Response(
        JSON.stringify({
            success: false,
            error: 'OFFLINE',
            message: 'Sie sind offline. Einige Funktionen sind nicht verfügbar.',
            offline: true
        }),
        {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        }
    );
}

/**
 * Background Sync (for offline data sync)
 */
self.addEventListener('sync', (event) => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-documents') {
        event.waitUntil(
            syncDocuments()
        );
    } else if (event.tag === 'sync-data') {
        event.waitUntil(
            syncPendingData()
        );
    }
});

/**
 * Sync pending document uploads
 */
async function syncDocuments() {
    try {
        const db = await openIndexedDB();
        const pendingDocs = await getAllFromStore(db, 'pendingDocuments');
        
        for (const doc of pendingDocs) {
            try {
                const response = await fetch('/api/documents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(doc.data)
                });

                if (response.ok) {
                    await deleteFromStore(db, 'pendingDocuments', doc.id);
                    console.log('✅ Document synced:', doc.id);
                }
            } catch (error) {
                console.error('❌ Failed to sync document:', error);
            }
        }
    } catch (error) {
        console.error('❌ Sync failed:', error);
        throw error;
    }
}

/**
 * Sync pending data
 */
async function syncPendingData() {
    try {
        const db = await openIndexedDB();
        const pendingData = await getAllFromStore(db, 'pendingSync');
        
        for (const item of pendingData) {
            try {
                const response = await fetch(item.url, {
                    method: item.method || 'POST',
                    headers: item.headers || {},
                    body: JSON.stringify(item.body)
                });

                if (response.ok) {
                    await deleteFromStore(db, 'pendingSync', item.id);
                    console.log('✅ Data synced:', item.id);
                }
            } catch (error) {
                console.error('❌ Failed to sync data:', error);
            }
        }
    } catch (error) {
        console.error('❌ Sync failed:', error);
        throw error;
    }
}

/**
 * Open IndexedDB
 */
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('OrganisationsAI', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('pendingDocuments')) {
                db.createObjectStore('pendingDocuments', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('pendingSync')) {
                db.createObjectStore('pendingSync', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('documents')) {
                db.createObjectStore('documents', { keyPath: 'id' });
            }
        };
    });
}

/**
 * Get all items from IndexedDB store
 */
function getAllFromStore(db, storeName) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readonly');
        const store = transaction.objectStore(storeName);
        const request = store.getAll();
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

/**
 * Delete from IndexedDB store
 */
function deleteFromStore(db, storeName, key) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(storeName, 'readwrite');
        const store = transaction.objectStore(storeName);
        const request = store.delete(key);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

/**
 * Message Handler - Communication with main thread
 */
self.addEventListener('message', (event) => {
    console.log('📨 Service Worker received message:', event.data);
    
    if (event.data.type === 'CLEAR_CACHE') {
        clearAllCaches();
    } else if (event.data.type === 'CACHE_URLS') {
        precacheUrls(event.data.urls);
    } else if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

/**
 * Clear all caches
 */
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('🗑️ All caches cleared');
}

/**
 * Precache URLs
 */
async function precacheUrls(urls) {
    const cache = await caches.open(CACHE_NAMES.assets);
    await cache.addAll(urls);
    console.log('✅ URLs precached:', urls.length);
}

console.log('✅ Service Worker loaded');
