/**
 * Offline Support Manager - TypeScript Version
 * Manages IndexedDB storage, offline data sync, queue
 * Critical for PWA functionality
 */
/**
 * Offline Manager for PWA functionality
 */
export class OfflineManager {
    constructor() {
        this.db = null;
        this.pendingSync = [];
        this.online = navigator.onLine;
        this.init();
    }
    /**
     * Initialize offline manager
     */
    async init() {
        try {
            await this.openDatabase();
            this.setupEventListeners();
            await this.registerServiceWorker();
            console.log('✅ Offline Manager initialized');
        }
        catch (error) {
            console.error('❌ Failed to initialize Offline Manager:', error);
        }
    }
    /**
     * Open IndexedDB database
     */
    openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('OrganisationsAI', 2);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                // Create object stores
                if (!db.objectStoreNames.contains('documents')) {
                    const docStore = db.createObjectStore('documents', { keyPath: 'id' });
                    docStore.createIndex('category', 'category', { unique: false });
                    docStore.createIndex('date', 'date_added', { unique: false });
                }
                if (!db.objectStoreNames.contains('pendingDocuments')) {
                    db.createObjectStore('pendingDocuments', { keyPath: 'id', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('pendingSync')) {
                    db.createObjectStore('pendingSync', { keyPath: 'id', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('offlineCache')) {
                    db.createObjectStore('offlineCache', { keyPath: 'url' });
                }
                console.log('✅ Database upgraded');
            };
        });
    }
    /**
     * Setup online/offline event listeners
     */
    setupEventListeners() {
        window.addEventListener('online', () => this.onOnline());
        window.addEventListener('offline', () => this.onOffline());
    }
    /**
     * Handle online event
     */
    onOnline() {
        this.online = true;
        console.log('✅ Back online');
        this.syncPending().catch(console.error);
    }
    /**
     * Handle offline event
     */
    onOffline() {
        this.online = false;
        console.log('⚠️ Went offline');
    }
    /**
     * Register Service Worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('⚠️ Service Workers not supported');
            return;
        }
        try {
            const registration = await navigator.serviceWorker.register('/app/static/js/service-worker.js', { scope: '/' });
            console.log('✅ Service Worker registered:', registration);
            // Check for updates periodically
            setInterval(() => {
                registration.update().catch(console.error);
            }, 60000); // Check every minute
        }
        catch (error) {
            console.error('❌ Service Worker registration failed:', error);
        }
    }
    /**
     * Cache data
     */
    async cache(storeName, data) {
        if (!this.db)
            return;
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        await new Promise((resolve, reject) => {
            const request = store.put(data);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    /**
     * Get cached data
     */
    async get(storeName, key) {
        if (!this.db)
            return null;
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    /**
     * Get all cached data
     */
    async getAll(storeName) {
        if (!this.db)
            return [];
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }
    /**
     * Clear store
     */
    async clear(storeName) {
        if (!this.db)
            return;
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        await new Promise((resolve, reject) => {
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    /**
     * Add pending sync operation
     */
    async addPendingSync(operation) {
        if (!this.db)
            return;
        const transaction = this.db.transaction(['pendingSync'], 'readwrite');
        const store = transaction.objectStore('pendingSync');
        await new Promise((resolve, reject) => {
            const request = store.add(operation);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
        this.pendingSync.push(operation);
    }
    /**
     * Sync pending operations
     */
    async syncPending() {
        if (!this.online || !this.db)
            return;
        const transaction = this.db.transaction(['pendingSync'], 'readonly');
        const store = transaction.objectStore('pendingSync');
        const operations = await new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
        for (const operation of operations) {
            try {
                // Sync operation would be sent to server
                console.log('Syncing:', operation);
                await this.removePendingSync(operation.id);
            }
            catch (error) {
                console.error('Failed to sync operation:', error);
            }
        }
        this.pendingSync = [];
    }
    /**
     * Remove pending sync operation
     */
    async removePendingSync(id) {
        if (!this.db)
            return;
        const transaction = this.db.transaction(['pendingSync'], 'readwrite');
        const store = transaction.objectStore('pendingSync');
        await new Promise((resolve, reject) => {
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }
    /**
     * Get online status
     */
    isOnline() {
        return this.online;
    }
    /**
     * Get pending sync count
     */
    getPendingSyncCount() {
        return this.pendingSync.length;
    }
}
// Global instance
export const offlineManager = new OfflineManager();
window.offlineManager = offlineManager;
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OfflineManager, offlineManager };
}
//# sourceMappingURL=offline-manager.js.map