/**
 * Advanced Search Module
 * Handles advanced search UI with filters, tags, and saved searches
 * Modernized with APIClient
 */

class AdvancedSearch {
    constructor() {
        this.currentFilters = {};
        this.savedSearches = [];
        this.allTags = [];
        this.init();
    }

    async init() {
        await this.loadTags();
        await this.loadSavedSearches();
        this.setupEventListeners();
    }

    async loadTags() {
        try {
            const data = await api.tags.list();
            this.allTags = data.tags || [];
            this.renderTagSuggestions();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    async loadSavedSearches() {
        try {
            const data = await api.search.saved();
            this.savedSearches = data.searches || [];
            this.renderSavedSearches();
        } catch (error) {
            console.error('Error loading saved searches:', error);
        }
    }

    setupEventListeners() {
        // Toggle advanced search
        const toggleBtn = document.getElementById('toggle-advanced-search');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleAdvancedSearch());
        }

        // Apply filters button
        const applyBtn = document.getElementById('apply-filters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.performAdvancedSearch());
        }

        // Clear filters button
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFilters());
        }

        // Save search button
        const saveBtn = document.getElementById('save-search-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.showSaveSearchDialog());
        }

        // Save dialog confirm
        const saveConfirmBtn = document.getElementById('save-search-confirm');
        if (saveConfirmBtn) {
            saveConfirmBtn.addEventListener('click', () => this.saveCurrentSearch());
        }

        // Save dialog cancel
        const saveCancelBtn = document.getElementById('save-search-cancel');
        if (saveCancelBtn) {
            saveCancelBtn.addEventListener('click', () => this.closeSaveSearchDialog());
        }
    }

    toggleAdvancedSearch() {
        const panel = document.getElementById('advanced-search-panel');
        if (panel) {
            panel.classList.toggle('hidden');
        }
    }

    async performAdvancedSearch() {
        // Collect filter values
        const filters = {
            query: document.getElementById('search-query')?.value?.trim() || null,
            category: document.getElementById('filter-category')?.value || null,
            start_date: document.getElementById('filter-start-date')?.value || null,
            end_date: document.getElementById('filter-end-date')?.value || null,
            tags: this.getSelectedTags(),
            limit: 100
        };

        // Remove null values
        Object.keys(filters).forEach(key => {
            if (filters[key] === null || filters[key] === '') {
                delete filters[key];
            }
        });

        this.currentFilters = filters;

        try {
            const data = await api.search.advanced(filters);
            this.displayResults(data.results || data.documents || []);
        } catch (error) {
            console.error('Advanced search error:', error);
            notifications.show('Fehler', 'Suche fehlgeschlagen: ' + error.message, 'error');
        }
    }

    getSelectedTags() {
        const tagInputs = document.querySelectorAll('.tag-checkbox:checked');
        return Array.from(tagInputs).map(input => input.value);
    }

    displayResults(documents) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        if (documents.length === 0) {
            resultsContainer.innerHTML = '<p class="no-results">Keine Dokumente gefunden.</p>';
            return;
        }

        resultsContainer.innerHTML = documents.map(doc => `
            <div class="document-card" data-id="${doc.id}">
                <div class="document-header">
                    <h3>${doc.filename}</h3>
                    <span class="category-badge">${doc.category}</span>
                </div>
                <div class="document-meta">
                    <span class="date">${formatDate(doc.date_document)}</span>
                    ${doc.subcategory ? `<span class="subcategory">${doc.subcategory}</span>` : ''}
                </div>
                <div class="document-tags">
                    ${(doc.tags || []).map(tag => {
            // Handle tag object or string
            const tagName = typeof tag === 'object' ? tag.tag_name : tag;
            const tagId = typeof tag === 'object' ? tag.id : null; // We might not have ID if string

            // If we don't have ID, we can't easily remove it via API unless we lookup
            // But for now let's assume we have objects if loaded from API
            return `<span class="tag" data-tag-id="${tagId}">${tagName}
                            ${tagId ? `<button class="remove-tag" onclick="advancedSearch.removeTag(${tagId}, ${doc.id})">×</button>` : ''}
                        </span>`;
        }).join('')}
                    <button class="add-tag-btn" onclick="advancedSearch.showAddTagDialog(${doc.id})">+ Tag</button>
                </div>
                <div class="document-actions">
                    <button onclick="downloadDocument(${doc.id})">Download</button>
                    <button onclick="viewDocument(${doc.id})">Details</button>
                </div>
            </div>
        `).join('');
    }

    async addTag(documentId, tagName) {
        try {
            // Use modernized endpoint that accepts tag_name
            await api.tags.addToDocument(documentId, { tag_name: tagName });

            // Reload tags and refresh search
            await this.loadTags();
            await this.performAdvancedSearch();
            notifications.show('Erfolg', 'Tag hinzugefügt', 'success');
        } catch (error) {
            console.error('Error adding tag:', error);
            notifications.show('Fehler', 'Tag konnte nicht hinzugefügt werden', 'error');
        }
    }

    async removeTag(tagId, documentId) {
        if (!confirm('Tag wirklich entfernen?')) return;

        try {
            // Correct API call: remove from document, not delete tag globally
            await api.tags.removeFromDocument(documentId, tagId);

            // Reload tags and refresh search
            await this.loadTags();
            await this.performAdvancedSearch();
            notifications.show('Erfolg', 'Tag entfernt', 'success');
        } catch (error) {
            console.error('Error removing tag:', error);
            notifications.show('Fehler', 'Tag konnte nicht entfernt werden', 'error');
        }
    }

    showAddTagDialog(documentId) {
        const tagName = prompt('Tag-Name eingeben:');
        if (tagName && tagName.trim()) {
            this.addTag(documentId, tagName.trim());
        }
    }

    async saveCurrentSearch() {
        const name = document.getElementById('search-name-input')?.value?.trim();
        if (!name) {
            alert('Bitte geben Sie einen Namen für die Suche ein');
            return;
        }

        try {
            await api.search.save(name, this.currentFilters);

            notifications.show('Erfolg', 'Suche gespeichert!', 'success');
            await this.loadSavedSearches();
            this.closeSaveSearchDialog();
        } catch (error) {
            console.error('Error saving search:', error);
            notifications.show('Fehler', 'Suche konnte nicht gespeichert werden', 'error');
        }
    }

    async loadSavedSearch(searchId) {
        const search = this.savedSearches.find(s => s.id === searchId);
        if (!search) return;

        // Apply saved filters to UI
        if (search.filters.query) {
            const el = document.getElementById('search-query');
            if (el) el.value = search.filters.query;
        }
        if (search.filters.category) {
            const el = document.getElementById('filter-category');
            if (el) el.value = search.filters.category;
        }
        if (search.filters.start_date) {
            const el = document.getElementById('filter-start-date');
            if (el) el.value = search.filters.start_date;
        }
        if (search.filters.end_date) {
            const el = document.getElementById('filter-end-date');
            if (el) el.value = search.filters.end_date;
        }

        // Perform search with saved filters
        this.currentFilters = search.filters;
        await this.performAdvancedSearch();
    }

    async deleteSavedSearch(searchId) {
        if (!confirm('Gespeicherte Suche wirklich löschen?')) return;

        try {
            await api.search.deleteSaved(searchId);
            await this.loadSavedSearches();
            notifications.show('Erfolg', 'Suche gelöscht', 'success');
        } catch (error) {
            console.error('Error deleting search:', error);
            notifications.show('Fehler', 'Suche konnte nicht gelöscht werden', 'error');
        }
    }

    renderSavedSearches() {
        const container = document.getElementById('saved-searches-list');
        if (!container) return;

        if (this.savedSearches.length === 0) {
            container.innerHTML = '<p class="no-results">Keine gespeicherten Suchen</p>';
            return;
        }

        container.innerHTML = this.savedSearches.map(search => `
            <div class="saved-search-item">
                <button class="search-name" onclick="advancedSearch.loadSavedSearch(${search.id})">
                    ${search.name}
                </button>
                <button class="delete-search" onclick="advancedSearch.deleteSavedSearch(${search.id})">×</button>
            </div>
        `).join('');
    }

    renderTagSuggestions() {
        const container = document.getElementById('tag-suggestions');
        if (!container) return;

        // Ensure tags are unique strings
        const uniqueTags = [...new Set(this.allTags.map(t => typeof t === 'object' ? t.name : t))];

        container.innerHTML = uniqueTags.map(tag => `
            <label class="tag-checkbox-label">
                <input type="checkbox" class="tag-checkbox" value="${tag}">
                ${tag}
            </label>
        `).join('');
    }

    clearFilters() {
        const query = document.getElementById('search-query');
        if (query) query.value = '';

        const cat = document.getElementById('filter-category');
        if (cat) cat.value = '';

        const start = document.getElementById('filter-start-date');
        if (start) start.value = '';

        const end = document.getElementById('filter-end-date');
        if (end) end.value = '';

        // Uncheck all tag checkboxes
        document.querySelectorAll('.tag-checkbox').forEach(cb => cb.checked = false);

        this.currentFilters = {};
    }

    showSaveSearchDialog() {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.remove('hidden');
        }
    }

    closeSaveSearchDialog() {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
        const input = document.getElementById('search-name-input');
        if (input) input.value = '';
    }
}

// Initialize on page load
let advancedSearch;
document.addEventListener('DOMContentLoaded', () => {
    // Only init if advanced search elements exist
    if (document.getElementById('advanced-search-panel')) {
        advancedSearch = new AdvancedSearch();
    }
});
