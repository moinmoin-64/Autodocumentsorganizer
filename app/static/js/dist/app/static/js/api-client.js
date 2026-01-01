/**
 * API Client - Zentrale Kommunikation mit Backend
 * TypeScript Version mit vollständiger Typensicherheit
 */
/**
 * Custom Error class für API Fehler
 */
export class APIError extends Error {
    constructor(error) {
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
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }
    /**
     * Zentrale Request-Methode
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
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
                return response;
            }
            const data = await response.json();
            // Check for API errors
            if (!data.success) {
                throw new APIError(data.error);
            }
            return (data.data || {});
        }
        catch (error) {
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
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }
    /**
     * POST Request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    /**
     * PUT Request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    /**
     * DELETE Request
     */
    async remove(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
    /**
     * Upload File (FormData)
     */
    async upload(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            headers: {}, // Let browser set Content-Type for FormData
            body: formData
        });
    }
    /**
     * Download File
     */
    async download(endpoint, filename) {
        const response = (await this.request(endpoint, { method: 'GET' }));
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
    async list(params = {}) {
        const response = await this.get('/documents', params);
        return response;
    }
    async getOne(id) {
        const response = await this.get(`/documents/${id}`);
        return response;
    }
    async create(data) {
        const response = await this.post('/documents', data);
        return response;
    }
    async update(id, data) {
        const response = await this.put(`/documents/${id}`, data);
        return response;
    }
    async delete(id) {
        await this.remove(`/documents/${id}`);
    }
    async download(id, filename) {
        await super.download(`/documents/${id}/download`, filename || 'download');
    }
    async search(query, params = {}) {
        const response = await this.get('/search', { query, ...params });
        return response;
    }
}
/**
 * Tags API
 */
export class TagsAPI extends APIClient {
    constructor() {
        super('/api');
    }
    async list() {
        const response = await this.get('/tags');
        return response;
    }
    async create(name) {
        const response = await this.post('/tags', { name });
        return response;
    }
    async delete(id) {
        await this.remove(`/tags/${id}`);
    }
    async addToDocument(documentId, tagId) {
        await this.post(`/documents/${documentId}/tags`, { tag_id: tagId });
    }
    async removeFromDocument(documentId, tagId) {
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
    async overview() {
        const response = await this.get('/stats/overview');
        return response;
    }
    async monthly(year) {
        const response = await this.get(`/stats/monthly/${year}`);
        return response;
    }
    async predictions(category, months = 3) {
        const response = await this.get(`/stats/predictions/${category}`, { months });
        return response;
    }
    async compareExpenses(year1, year2) {
        const response = await this.get('/stats/expenses/compare', { year1, year2 });
        return response;
    }
    async getInsurances() {
        const response = await this.get('/stats/insurance/list');
        return response;
    }
}
/**
 * Search API
 */
export class SearchAPI extends APIClient {
    constructor() {
        super('/api/search');
    }
    async advanced(filters) {
        const response = await this.post('/advanced', filters);
        return response;
    }
    async saved() {
        const response = await this.get('/saved');
        return response;
    }
    async save(name, filters) {
        const response = await this.post('/saved', { name, filters });
        return response;
    }
    async deleteSaved(id) {
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
    async send(message) {
        const response = await this.post('', { message });
        return response;
    }
}
/**
 * Budgets API
 */
export class BudgetsAPI extends APIClient {
    constructor() {
        super('/api/budgets');
    }
    async create(data) {
        const response = await this.post('', data);
        return response;
    }
}
/**
 * Upload API
 */
export class UploadAPI extends APIClient {
    constructor() {
        super('/api');
    }
    async uploadFile(file, metadata = {}) {
        const formData = new FormData();
        formData.append('file', file);
        Object.keys(metadata).forEach(key => {
            formData.append(key, metadata[key]);
        });
        const response = await super.upload('/upload', formData);
        return response;
    }
    async process(tempPath, metadata = {}) {
        const response = await this.post(`/upload/process/${encodeURIComponent(tempPath)}`, metadata);
        return response;
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
//# sourceMappingURL=api-client.js.map