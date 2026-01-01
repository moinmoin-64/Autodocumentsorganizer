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
export declare class OfflineManager {
    private db;
    private online;
    private pendingSync;
    constructor();
    /**
     * Initialize offline manager
     */
    private init;
    /**
     * Open IndexedDB database
     */
    private openDatabase;
    /**
     * Setup online/offline event listeners
     */
    private setupEventListeners;
    /**
     * Handle online event
     */
    private onOnline;
    /**
     * Handle offline event
     */
    private onOffline;
    /**
     * Register Service Worker
     */
    private registerServiceWorker;
    /**
     * Cache data
     */
    cache(storeName: string, data: Record<string, any>): Promise<void>;
    /**
     * Get cached data
     */
    get(storeName: string, key: any): Promise<any>;
    /**
     * Get all cached data
     */
    getAll(storeName: string): Promise<any[]>;
    /**
     * Clear store
     */
    clear(storeName: string): Promise<void>;
    /**
     * Add pending sync operation
     */
    addPendingSync(operation: PendingSyncOperation): Promise<void>;
    /**
     * Sync pending operations
     */
    syncPending(): Promise<void>;
    /**
     * Remove pending sync operation
     */
    private removePendingSync;
    /**
     * Get online status
     */
    isOnline(): boolean;
    /**
     * Get pending sync count
     */
    getPendingSyncCount(): number;
}
export declare const offlineManager: OfflineManager;
declare global {
    interface Window {
        offlineManager: OfflineManager;
    }
}
//# sourceMappingURL=offline-manager.d.ts.map