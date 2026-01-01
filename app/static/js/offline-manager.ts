/**
 * Offline Support Manager - TypeScript Version
 * Manages IndexedDB storage, offline data sync, queue
 * Critical for PWA functionality
 */

/**
 * Pending sync operation
 */
export interface PendingSyncOperation {
    id?: number;
    action: 'create' | 'update' | 'delete';
    endpoint: string;
    data: Record<string, any>;
    timestamp: number;
}

/**
 * Offline Manager for PWA functionality
 */
export class OfflineManager {
    private db: IDBDatabase | null = null;
    private online: boolean;
    private pendingSync: PendingSyncOperation[] = [];

    constructor() {
        this.online = navigator.onLine;
        this.init();
    }

    /**
     * Initialize offline manager
     */
    private async init(): Promise<void> {
        try {
            await this.openDatabase();
            this.setupEventListeners();
            await this.registerServiceWorker();
            console.log('✅ Offline Manager initialized');
        } catch (error) {
            console.error('❌ Failed to initialize Offline Manager:', error);
        }
    }

    /**
     * Open IndexedDB database
     */
    private openDatabase(): Promise<IDBDatabase> {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('OrganisationsAI', 2);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };
            request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
                const db = (event.target as IDBOpenDBRequest).result;

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
    private setupEventListeners(): void {
        window.addEventListener('online', () => this.onOnline());
        window.addEventListener('offline', () => this.onOffline());
    }

    /**
     * Handle online event
     */
    private onOnline(): void {
        this.online = true;
        console.log('✅ Back online');
        this.syncPending().catch(console.error);
    }

    /**
     * Handle offline event
     */
    private onOffline(): void {
        this.online = false;
        console.log('⚠️ Went offline');
    }

    /**
     * Register Service Worker
     */
    private async registerServiceWorker(): Promise<void> {
        if (!('serviceWorker' in navigator)) {
            console.warn('⚠️ Service Workers not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register(
                '/app/static/js/service-worker.js',
                { scope: '/' }
            );
            console.log('✅ Service Worker registered:', registration);

            // Check for updates periodically
            setInterval(() => {
                registration.update().catch(console.error);
            }, 60000); // Check every minute

        } catch (error) {
            console.error('❌ Service Worker registration failed:', error);
        }
    }

    /**
     * Cache data
     */
    public async cache(storeName: string, data: Record<string, any>): Promise<void> {
        if (!this.db) return;

        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);

        await new Promise<void>((resolve, reject) => {
            const request = store.put(data);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get cached data
     */
    public async get(storeName: string, key: any): Promise<any> {
        if (!this.db) return null;

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
    public async getAll(storeName: string): Promise<any[]> {
        if (!this.db) return [];

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
    public async clear(storeName: string): Promise<void> {
        if (!this.db) return;

        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);

        await new Promise<void>((resolve, reject) => {
            const request = store.clear();
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Add pending sync operation
     */
    public async addPendingSync(operation: PendingSyncOperation): Promise<void> {
        if (!this.db) return;

        const transaction = this.db.transaction(['pendingSync'], 'readwrite');
        const store = transaction.objectStore('pendingSync');

        await new Promise<void>((resolve, reject) => {
            const request = store.add(operation);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });

        this.pendingSync.push(operation);
    }

    /**
     * Sync pending operations
     */
    public async syncPending(): Promise<void> {
        if (!this.online || !this.db) return;

        const transaction = this.db.transaction(['pendingSync'], 'readonly');
        const store = transaction.objectStore('pendingSync');

        const operations = await new Promise<PendingSyncOperation[]>((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });

        for (const operation of operations) {
            try {
                // Sync operation would be sent to server
                console.log('Syncing:', operation);
                await this.removePendingSync(operation.id!);
            } catch (error) {
                console.error('Failed to sync operation:', error);
            }
        }

        this.pendingSync = [];
    }

    /**
     * Remove pending sync operation
     */
    private async removePendingSync(id: number): Promise<void> {
        if (!this.db) return;

        const transaction = this.db.transaction(['pendingSync'], 'readwrite');
        const store = transaction.objectStore('pendingSync');

        await new Promise<void>((resolve, reject) => {
            const request = store.delete(id);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get online status
     */
    public isOnline(): boolean {
        return this.online;
    }

    /**
     * Get pending sync count
     */
    public getPendingSyncCount(): number {
        return this.pendingSync.length;
    }
}

// Global instance
export const offlineManager = new OfflineManager();

// Make global
declare global {
    interface Window {
        offlineManager: OfflineManager;
    }
}
window.offlineManager = offlineManager;

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OfflineManager, offlineManager };
}
