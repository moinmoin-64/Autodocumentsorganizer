/**
 * API Client - Zentrale Kommunikation mit Backend
 * TypeScript Version mit vollständiger Typensicherheit
 */

import type {
    APIResponse,
    APIError as APIErrorType,
    Document,
    DocumentSearchResult,
} from '../../../types/api';

/**
 * Custom Error class für API Fehler
 */
export class APIError extends Error {
    public code: string;
    public details: Record<string, any>;

    constructor(error: APIErrorType) {
        super(error.message);
        this.name = 'APIError';
        this.code = error.code;
        this.details = error.details || {};
        Object.setPrototypeOf(this, APIError.prototype);
    }
}

/**
 * Hauptklasse für API-Kommunikation
 */
export class APIClient {
    private baseURL: string;
    private defaultHeaders: Record<string, string>;

    constructor(baseURL: string = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Zentrale Request-Methode
     */
    private async request<T = any>(
        endpoint: string,
        options: RequestInit & { headers?: Record<string, string> } = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;
        const config: RequestInit = {
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            // Handle non-JSON responses (file downloads)
            const contentType = response.headers.get('content-type');
            if (contentType && !contentType.includes('application/json')) {
                return response as any;
            }

            const data: APIResponse<T> = await response.json();

            // Check for API errors
            if (!data.success) {
                throw new APIError(data.error as APIErrorType);
            }

            return (data.data || {}) as T;

        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }

            // Network or parsing error
            console.error(`API Request failed: ${error instanceof Error ? error.message : String(error)}`);
            throw new Error('Network error or invalid response');
        }
    }

    /**
     * GET Request
     */
    async get<T = any>(
        endpoint: string,
        params: Record<string, any> = {}
    ): Promise<T> {
        const queryString = new URLSearchParams(
            Object.entries(params).map(([k, v]) => [k, String(v)])
        ).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request<T>(url, { method: 'GET' });
    }

    /**
     * POST Request
     */
    async post<T = any>(
        endpoint: string,
        data: any
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT Request
     */
    async put<T = any>(
        endpoint: string,
        data: any
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE Request
     */
    async remove<T = any>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'DELETE' });
    }

    /**
     * Upload File (FormData)
     */
    async upload<T = any>(
        endpoint: string,
        formData: FormData
    ): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            headers: {}, // Let browser set Content-Type for FormData
            body: formData
        });
    }

    /**
     * Download File
     */
    async download(endpoint: string, filename: string): Promise<void> {
        const response = (await this.request(endpoint, { method: 'GET' })) as Response;

        if (response instanceof Response) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename || 'download';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    }
}

// === Specialized API Endpoints ===

/**
 * Documents API
 */
export class DocumentsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async list(params: Record<string, any> = {}): Promise<Document[]> {
        const response = await this.get<APIResponse<Document[]>>('/documents', params);
        return response as any;
    }

    async getOne(id: string): Promise<Document> {
        const response = await this.get<APIResponse<Document>>(`/documents/${id}`);
        return response as any;
    }

    async create(data: Partial<Document>): Promise<Document> {
        const response = await this.post<APIResponse<Document>>('/documents', data);
        return response as any;
    }

    async update(id: string, data: Partial<Document>): Promise<Document> {
        const response = await this.put<APIResponse<Document>>(`/documents/${id}`, data);
        return response as any;
    }

    async delete(id: string): Promise<void> {
        await this.remove(`/documents/${id}`);
    }

    async download(id: string, filename?: string): Promise<void> {
        await super.download(`/documents/${id}/download`, filename || 'download');
    }

    async search(query: string, params: Record<string, any> = {}): Promise<DocumentSearchResult[]> {
        const response = await this.get<APIResponse<DocumentSearchResult[]>>('/search', { query, ...params });
        return response as any;
    }
}

/**
 * Tags API
 */
export class TagsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async list(): Promise<any[]> {
        const response = await this.get<APIResponse<any[]>>('/tags');
        return response as any;
    }

    async create(name: string): Promise<any> {
        const response = await this.post<APIResponse<any>>('/tags', { name });
        return response as any;
    }

    async delete(id: string): Promise<void> {
        await this.remove(`/tags/${id}`);
    }

    async addToDocument(documentId: string, tagId: string): Promise<void> {
        await this.post<void>(`/documents/${documentId}/tags`, { tag_id: tagId });
    }

    async removeFromDocument(documentId: string, tagId: string): Promise<void> {
        await this.remove(`/documents/${documentId}/tags/${tagId}`);
    }
}

/**
 * Statistics API
 */
export class StatsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async overview(): Promise<any> {
        const response = await this.get<APIResponse<any>>('/stats/overview');
        return response as any;
    }

    async monthly(year: number): Promise<Record<string, number>> {
        const response = await this.get<APIResponse<Record<string, number>>>(`/stats/monthly/${year}`);
        return response as any;
    }

    async predictions(category: string, months: number = 3): Promise<any> {
        const response = await this.get<APIResponse<any>>(
            `/stats/predictions/${category}`,
            { months }
        );
        return response as any;
    }

    async compareExpenses(year1: number, year2: number): Promise<any> {
        const response = await this.get<APIResponse<any>>(
            '/stats/expenses/compare',
            { year1, year2 }
        );
        return response as any;
    }

    async getInsurances(): Promise<any[]> {
        const response = await this.get<APIResponse<any[]>>('/stats/insurance/list');
        return response as any;
    }
}

/**
 * Search API
 */
export class SearchAPI extends APIClient {
    constructor() {
        super('/api/search');
    }

    async advanced(filters: Record<string, any>): Promise<any> {
        const response = await this.post<APIResponse<any>>('/advanced', filters);
        return response as any;
    }

    async saved(): Promise<any[]> {
        const response = await this.get<APIResponse<any[]>>('/saved');
        return response as any;
    }

    async save(name: string, filters: Record<string, any>): Promise<any> {
        const response = await this.post<APIResponse<any>>('/saved', { name, filters });
        return response as any;
    }

    async deleteSaved(id: string): Promise<void> {
        await this.remove(`/saved/${id}`);
    }
}

/**
 * Chat API
 */
export class ChatAPI extends APIClient {
    constructor() {
        super('/api/chat');
    }

    async send(message: string): Promise<any> {
        const response = await this.post<APIResponse<any>>('', { message });
        return response as any;
    }
}

/**
 * Budgets API
 */
export class BudgetsAPI extends APIClient {
    constructor() {
        super('/api/budgets');
    }

    async create(data: Record<string, any>): Promise<any> {
        const response = await this.post<APIResponse<any>>('', data);
        return response as any;
    }
}

/**
 * Upload API
 */
export class UploadAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async uploadFile(file: File, metadata: Record<string, any> = {}): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);

        Object.keys(metadata).forEach(key => {
            formData.append(key, metadata[key]);
        });

        const response = await super.upload<APIResponse<any>>('/upload', formData);
        return response as any;
    }

    async process(tempPath: string, metadata: Record<string, any> = {}): Promise<any> {
        const response = await this.post<APIResponse<any>>(
            `/upload/process/${encodeURIComponent(tempPath)}`,
            metadata
        );
        return response as any;
    }
}

// === Global API Instances ===
export const api = {
    documents: new DocumentsAPI(),
    tags: new TagsAPI(),
    stats: new StatsAPI(),
    search: new SearchAPI(),
    chat: new ChatAPI(),
    budgets: new BudgetsAPI(),
    upload: new UploadAPI(),
    client: new APIClient()
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, APIClient, APIError };
}
