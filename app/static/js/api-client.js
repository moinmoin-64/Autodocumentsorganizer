/**
 * API Client - Zentrale Kommunikation mit Backend
 * Konsistente Error-Handling und moderne async/await Patterns
 */

class APIError extends Error {
    constructor(error) {
        super(error.message);
        this.name = 'APIError';
        this.code = error.code;
        this.details = error.details;
    }
}

class APIClient {
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

            return data;

        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }

            // Network or parsing error
            console.error(`API Request failed: ${error.message}`);
            throw new Error('Network error or invalid response');
        }
    }

    /**
     * GET Request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
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
    async delete(endpoint) {
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
        const response = await this.request(endpoint, { method: 'GET' });

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

class DocumentsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async list(params = {}) {
        const response = await this.get('/documents', params);
        return response.data;
    }

    async get(id) {
        const response = await this.get(`/documents/${id}`);
        return response.data;
    }

    async create(data) {
        const response = await this.post('/documents', data);
        return response.data;
    }

    async update(id, data) {
        const response = await this.put(`/documents/${id}`, data);
        return response.data;
    }

    async delete(id) {
        await this.delete(`/documents/${id}`);
    }

    async download(id, filename) {
        await super.download(`/documents/${id}/download`, filename);
    }

    async search(query, params = {}) {
        const response = await this.get('/search', { query, ...params });
        return response.data;
    }
}

class TagsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async list() {
        const response = await this.get('/tags');
        return response.data;
    }

    async create(name) {
        const response = await this.post('/tags', { name });
        return response.data;
    }

    async delete(id) {
        await this.delete(`/tags/${id}`);
    }

    async addToDocument(documentId, tagId) {
        const response = await this.post(`/documents/${documentId}/tags`, { tag_id: tagId });
        return response.data;
    }

    async removeFromDocument(documentId, tagId) {
        await this.delete(`/documents/${documentId}/tags/${tagId}`);
    }
}

class StatsAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async overview() {
        const response = await this.get('/stats/overview');
        return response.data;
    }

    async monthly(year) {
        const response = await this.get(`/stats/monthly/${year}`);
        return response.data;
    }

    async predictions(category, months = 3) {
        const response = await this.get(`/stats/predictions/${category}`, { months });
        return response.data;
    }

    async compareExpenses(year1, year2) {
        const response = await this.get('/stats/expenses/compare', { year1, year2 });
        return response.data;
    }

    async getInsurances() {
        const response = await this.get('/stats/insurance/list');
        return response.data;
    }
}

class SearchAPI extends APIClient {
    constructor() {
        super('/api/search');
    }

    async advanced(filters) {
        const response = await this.post('/advanced', filters);
        return response.data;
    }

    async saved() {
        const response = await this.get('/saved');
        return response.data;
    }

    async save(name, filters) {
        const response = await this.post('/saved', { name, filters });
        return response.data;
    }

    async deleteSaved(id) {
        await this.delete(`/saved/${id}`);
    }
}

class ChatAPI extends APIClient {
    constructor() {
        super('/api/chat');
    }

    async send(message) {
        const response = await this.post('', { message });
        return response.data;
    }
}

class BudgetsAPI extends APIClient {
    constructor() {
        super('/api/budgets');
    }

    async create(data) {
        const response = await this.post('', data);
        return response.data;
    }
}

class UploadAPI extends APIClient {
    constructor() {
        super('/api');
    }

    async upload(file, metadata = {}) {
        const formData = new FormData();
        formData.append('file', file);

        Object.keys(metadata).forEach(key => {
            formData.append(key, metadata[key]);
        });

        const response = await super.upload('/upload', formData);
        return response.data;
    }

    async process(tempPath, metadata = {}) {
        const response = await this.post(`/upload/process/${encodeURIComponent(tempPath)}`, metadata);
        return response.data;
    }
}

// === Global API Instances ===
const api = {
    documents: new DocumentsAPI(),
    tags: new TagsAPI(),
    stats: new StatsAPI(),
    search: new SearchAPI(),
    chat: new ChatAPI(),
    budgets: new BudgetsAPI(),
    upload: new UploadAPI(),

    // Direct access for custom calls
    client: new APIClient()
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, APIClient, APIError };
}
