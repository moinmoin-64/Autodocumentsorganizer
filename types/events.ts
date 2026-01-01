/**
 * Event type definitions
 */

/**
 * Window events
 */
export type WindowEventMap = {
    'error': ErrorEvent;
    'unhandledrejection': PromiseRejectionEvent;
    'online': Event;
    'offline': Event;
    'beforeunload': BeforeUnloadEvent;
    'unload': Event;
    'load': Event;
    'DOMContentLoaded': Event;
};

/**
 * Custom application events
 */
export interface AppEvent<T = any> {
    type: string;
    data?: T;
    timestamp: number;
    source?: string;
}

/**
 * Document change event
 */
export interface DocumentChangeEvent extends AppEvent {
    type: 'document:created' | 'document:updated' | 'document:deleted';
    documentId: string;
}

/**
 * Error event with context
 */
export interface ContextualErrorEvent extends AppEvent {
    type: 'error';
    error: Error;
    context?: Record<string, any>;
}

/**
 * Performance event
 */
export interface PerformanceEvent extends AppEvent {
    type: 'performance';
    metric: string;
    value: number;
    unit: string;
}

/**
 * User action event
 */
export interface UserActionEvent extends AppEvent {
    type: 'user-action';
    action: string;
    target?: HTMLElement;
    metadata?: Record<string, any>;
}

/**
 * Network event
 */
export interface NetworkEvent extends AppEvent {
    type: 'network';
    status: 'online' | 'offline';
    latency?: number;
}

/**
 * Offline sync event
 */
export interface OfflineSyncEvent extends AppEvent {
    type: 'offline-sync';
    action: 'start' | 'success' | 'failure';
    itemCount?: number;
    error?: Error;
}

/**
 * Event emitter interface
 */
export interface EventEmitter<T extends Record<string, any>> {
    on<K extends keyof T>(event: K, listener: (data: T[K]) => void): void;
    once<K extends keyof T>(event: K, listener: (data: T[K]) => void): void;
    off<K extends keyof T>(event: K, listener: (data: T[K]) => void): void;
    emit<K extends keyof T>(event: K, data: T[K]): void;
    removeAllListeners(event?: keyof T): void;
}
