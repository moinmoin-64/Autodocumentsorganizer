/**
 * API Client - Zentrale Kommunikation mit Backend
 * TypeScript Version mit vollständiger Typensicherheit
 */
import type { APIError as APIErrorType, Document, DocumentSearchResult } from '../../../types/api';
/**
 * Custom Error class für API Fehler
 */
export declare class APIError extends Error {
    code: string;
    details: Record<string, any>;
    constructor(error: APIErrorType);
}
/**
 * Hauptklasse für API-Kommunikation
 */
export declare class APIClient {
    private baseURL;
    private defaultHeaders;
    constructor(baseURL?: string);
    /**
     * Zentrale Request-Methode
     */
    private request;
    /**
     * GET Request
     */
    get<T = any>(endpoint: string, params?: Record<string, any>): Promise<T>;
    /**
     * POST Request
     */
    post<T = any>(endpoint: string, data: any): Promise<T>;
    /**
     * PUT Request
     */
    put<T = any>(endpoint: string, data: any): Promise<T>;
    /**
     * DELETE Request
     */
    remove<T = any>(endpoint: string): Promise<T>;
    /**
     * Upload File (FormData)
     */
    upload<T = any>(endpoint: string, formData: FormData): Promise<T>;
    /**
     * Download File
     */
    download(endpoint: string, filename: string): Promise<void>;
}
/**
 * Documents API
 */
export declare class DocumentsAPI extends APIClient {
    constructor();
    list(params?: Record<string, any>): Promise<Document[]>;
    getOne(id: string): Promise<Document>;
    create(data: Partial<Document>): Promise<Document>;
    update(id: string, data: Partial<Document>): Promise<Document>;
    delete(id: string): Promise<void>;
    download(id: string, filename?: string): Promise<void>;
    search(query: string, params?: Record<string, any>): Promise<DocumentSearchResult[]>;
}
/**
 * Tags API
 */
export declare class TagsAPI extends APIClient {
    constructor();
    list(): Promise<any[]>;
    create(name: string): Promise<any>;
    delete(id: string): Promise<void>;
    addToDocument(documentId: string, tagId: string): Promise<void>;
    removeFromDocument(documentId: string, tagId: string): Promise<void>;
}
/**
 * Statistics API
 */
export declare class StatsAPI extends APIClient {
    constructor();
    overview(): Promise<any>;
    monthly(year: number): Promise<Record<string, number>>;
    predictions(category: string, months?: number): Promise<any>;
    compareExpenses(year1: number, year2: number): Promise<any>;
    getInsurances(): Promise<any[]>;
}
/**
 * Search API
 */
export declare class SearchAPI extends APIClient {
    constructor();
    advanced(filters: Record<string, any>): Promise<any>;
    saved(): Promise<any[]>;
    save(name: string, filters: Record<string, any>): Promise<any>;
    deleteSaved(id: string): Promise<void>;
}
/**
 * Chat API
 */
export declare class ChatAPI extends APIClient {
    constructor();
    send(message: string): Promise<any>;
}
/**
 * Budgets API
 */
export declare class BudgetsAPI extends APIClient {
    constructor();
    create(data: Record<string, any>): Promise<any>;
}
/**
 * Upload API
 */
export declare class UploadAPI extends APIClient {
    constructor();
    uploadFile(file: File, metadata?: Record<string, any>): Promise<any>;
    process(tempPath: string, metadata?: Record<string, any>): Promise<any>;
}
export declare const api: {
    documents: DocumentsAPI;
    tags: TagsAPI;
    stats: StatsAPI;
    search: SearchAPI;
    chat: ChatAPI;
    budgets: BudgetsAPI;
    upload: UploadAPI;
    client: APIClient;
};
//# sourceMappingURL=api-client.d.ts.map