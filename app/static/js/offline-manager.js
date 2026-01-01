/**
 * Offline Support Manager
 * Manages IndexedDB storage, offline data sync, queue
 * Critical for PWA functionality
 */

class OfflineManager {
    constructor() {
        this.db = null;
        this.online = navigator.onLine;
        this.pendingSync = [];
        this.init();
    }

    /**
     * Initialize offline manager
     */
    async init() {
        try {
            await this.openDatabase();
            this.setupEventListeners();
            this.registerServiceWorker();
            console.log('✅ Offline Manager initialized');
        } catch (error) {
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
     * Register Service Worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('⚠️ Service Workers not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/app/static/js/service-worker.js', {
                scope: '/'
            });
            console.log('✅ Service Worker registered:', registration);
            
            // Check for updates periodically
            setInterval(() => {
                registration.update();
            }, 60000); // Check every minute
        } catch (error) {
            console.error('❌ Service Worker registration failed:', error);
        }
    }

    /**
     * Handle online event
     */
    async onOnline() {
        this.online = true;
        console.log('🌐 Back online!');
        
        // Notify user
        notifications.show('Verbindung wiederhergestellt', 'Offline-Daten werden synchronisiert...', 'success');
        
        // Sync pending data
        await this.syncPendingData();
    }

    /**
     * Handle offline event
     */
    onOffline() {
        this.online = false;
        console.log('📴 Offline mode activated');
        
        // Notify user
        notifications.show('Offline', 'Sie sind offline. Änderungen werden lokal gespeichert.', 'warning');
    }

    /**
     * Save document for offline access
     */
    async saveDocumentOffline(document) {
        try {
            const store = this.getObjectStore('documents', 'readwrite');
            await this.putInStore(store, document);
            console.log('💾 Document saved offline:', document.id);
        } catch (error) {
            console.error('❌ Failed to save document offline:', error);
        }
    }

    /**
     * Get document from offline storage
     */
    async getDocumentOffline(id) {
        try {
            const store = this.getObjectStore('documents', 'readonly');
            return await this.getFromStore(store, id);
        } catch (error) {
            console.error('❌ Failed to get document offline:', error);
            return null;
        }
    }

    /**
     * Get all documents from offline storage
     */
    async getDocumentsOffline() {
        try {
            const store = this.getObjectStore('documents', 'readonly');
            return await this.getAllFromStore(store);
        } catch (error) {
            console.error('❌ Failed to get documents offline:', error);
            return [];
        }
    }

    /**
     * Queue document upload for sync
     */
    async queueDocumentUpload(documentData) {
        try {
            const store = this.getObjectStore('pendingDocuments', 'readwrite');
            const id = await this.putInStore(store, {
                data: documentData,
                timestamp: Date.now(),
                status: 'pending'
            });
            
            console.log('📤 Document queued for upload:', id);
            
            // Attempt immediate sync
            await this.syncPendingData();
            
            return id;
        } catch (error) {
            console.error('❌ Failed to queue document:', error);
            throw error;
        }
    }

    /**
     * Queue generic data for sync
     */
    async queueDataSync(url, method, data, headers) {
        try {
            const store = this.getObjectStore('pendingSync', 'readwrite');
            const id = await this.putInStore(store, {
                url,
                method: method || 'POST',
                body: data,
                headers: headers || {},
                timestamp: Date.now(),
                status: 'pending'
            });
            
            console.log('📤 Data queued for sync:', id);
            
            // Request background sync
            if ('sync' in registration) {
                registration.sync.register('sync-data');
            }
            
            return id;
        } catch (error) {
            console.error('❌ Failed to queue data:', error);
            throw error;
        }
    }

    /**
     * Sync pending data with server
     */
    async syncPendingData() {
        if (!this.online) {
            console.log('⚠️ Offline - cannot sync');
            return;
        }

        try {
            // Sync pending documents
            await this.syncPendingDocuments();
            
            // Sync pending data
            await this.syncPendingUpdates();
            
            console.log('✅ All pending data synced');
        } catch (error) {
            console.error('❌ Sync failed:', error);
        }
    }

    /**
     * Sync pending document uploads
     */
    async syncPendingDocuments() {
        try {
            const store = this.getObjectStore('pendingDocuments', 'readwrite');
            const documents = await this.getAllFromStore(store);
            
            for (const doc of documents) {
                try {
                    const response = await fetch('/api/documents', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(doc.data)
                    });

                    if (response.ok) {
                        await this.deleteFromStore(store, doc.id);
                        console.log('✅ Document uploaded:', doc.id);
                    }
                } catch (error) {
                    console.error('❌ Failed to upload document:', error);
                }
            }
        } catch (error) {
            console.error('❌ Failed to sync documents:', error);
        }
    }

    /**
     * Sync pending updates
     */
    async syncPendingUpdates() {
        try {
            const store = this.getObjectStore('pendingSync', 'readwrite');
            const items = await this.getAllFromStore(store);
            
            for (const item of items) {
                try {
                    const response = await fetch(item.url, {
                        method: item.method,
                        headers: item.headers,
                        body: JSON.stringify(item.body)
                    });

                    if (response.ok) {
                        await this.deleteFromStore(store, item.id);
                        console.log('✅ Update synced:', item.id);
                    }
                } catch (error) {
                    console.error('❌ Failed to sync update:', error);
                }
            }
        } catch (error) {
            console.error('❌ Failed to sync updates:', error);
        }
    }

    /**
     * Get pending items count
     */
    async getPendingCount() {
        try {
            const docStore = this.getObjectStore('pendingDocuments', 'readonly');
            const syncStore = this.getObjectStore('pendingSync', 'readonly');
            
            const docCount = await this.countInStore(docStore);
            const syncCount = await this.countInStore(syncStore);
            
            return docCount + syncCount;
        } catch (error) {
            console.error('❌ Failed to get pending count:', error);
            return 0;
        }
    }

    /**
     * Clear all offline data
     */
    async clearOfflineData() {
        try {
            const stores = ['documents', 'pendingDocuments', 'pendingSync', 'offlineCache'];
            
            for (const storeName of stores) {
                const store = this.getObjectStore(storeName, 'readwrite');
                await this.clearStore(store);
            }
            
            console.log('✅ Offline data cleared');
        } catch (error) {
            console.error('❌ Failed to clear offline data:', error);
        }
    }

    /**
     * Get object store
     */
    getObjectStore(storeName, mode) {
        const transaction = this.db.transaction(storeName, mode);
        return transaction.objectStore(storeName);
    }

    /**
     * Helper: Put in store
     */
    putInStore(store, value) {
        return new Promise((resolve, reject) => {
            const request = store.add(value);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    /**
     * Helper: Get from store
     */
    getFromStore(store, key) {
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    /**
     * Helper: Get all from store
     */
    getAllFromStore(store) {
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    /**
     * Helper: Delete from store
     */
    deleteFromStore(store, key) {
        return new Promise((resolve, reject) => {
            const request = store.delete(key);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    /**
     * Helper: Clear store
     */
    clearStore(store) {
        return new Promise((resolve, reject) => {
            const request = store.clear();
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    /**
     * Helper: Count in store
     */
    countInStore(store) {
        return new Promise((resolve, reject) => {
            const request = store.count();
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }
}

// Initialize Offline Manager
const offlineManager = new OfflineManager();

// Export globally
window.offlineManager = offlineManager;

console.log('✅ Offline Manager loaded');
