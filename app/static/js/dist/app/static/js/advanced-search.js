/**
 * Advanced Search Module - TypeScript Version
 * Handles advanced search UI with filters, tags, and saved searches
 * Modernized with APIClient
 */
import { api } from './api-client';
/**
 * Advanced Search Manager
 */
export class AdvancedSearch {
    constructor() {
        this.currentFilters = {};
        this.savedSearches = [];
        this.allTags = [];
        this.init();
    }
    /**
     * Initialize advanced search
     */
    async init() {
        await this.loadTags();
        await this.loadSavedSearches();
        this.setupEventListeners();
    }
    /**
     * Load all tags
     */
    async loadTags() {
        try {
            const data = await api.tags.list();
            this.allTags = data.tags || [];
            this.renderTagSuggestions();
        }
        catch (error) {
            console.error('Error loading tags:', error);
        }
    }
    /**
     * Load saved searches
     */
    async loadSavedSearches() {
        try {
            const data = await api.search.saved();
            this.savedSearches = (data.searches || []);
            this.renderSavedSearches();
        }
        catch (error) {
            console.error('Error loading saved searches:', error);
        }
    }
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Toggle advanced search
        const toggleBtn = document.getElementById('toggle-advanced-search');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleAdvancedSearch());
        }
        // Apply filters button
        const applyBtn = document.getElementById('apply-filters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.performAdvancedSearch().catch(console.error));
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
            saveConfirmBtn.addEventListener('click', () => this.saveCurrentSearch().catch(console.error));
        }
        // Save dialog cancel
        const saveCancelBtn = document.getElementById('save-search-cancel');
        if (saveCancelBtn) {
            saveCancelBtn.addEventListener('click', () => this.closeSaveSearchDialog());
        }
    }
    /**
     * Toggle advanced search panel
     */
    toggleAdvancedSearch() {
        const panel = document.getElementById('advanced-search-panel');
        if (panel) {
            panel.classList.toggle('hidden');
        }
    }
    /**
     * Perform advanced search
     */
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
            const results = await api.search.advanced(filters);
            this.displayResults(results);
        }
        catch (error) {
            console.error('Search error:', error);
        }
    }
    /**
     * Get selected tags
     */
    getSelectedTags() {
        const checkboxes = document.querySelectorAll('.tag-filter:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }
    /**
     * Display search results
     */
    displayResults(results) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer)
            return;
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">Keine Ergebnisse gefunden</div>';
            return;
        }
        resultsContainer.innerHTML = results
            .map(result => `
                <div class="search-result">
                    <h3>${result.title}</h3>
                    <p>${result.description || ''}</p>
                    <small>${result.date}</small>
                </div>
            `)
            .join('');
    }
    /**
     * Clear all filters
     */
    clearFilters() {
        document.getElementById('search-query').value = '';
        document.getElementById('filter-category').value = '';
        document.getElementById('filter-start-date').value = '';
        document.getElementById('filter-end-date').value = '';
        document.querySelectorAll('.tag-filter').forEach(cb => {
            cb.checked = false;
        });
        this.currentFilters = {};
    }
    /**
     * Show save search dialog
     */
    showSaveSearchDialog() {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.remove('hidden');
        }
    }
    /**
     * Close save search dialog
     */
    closeSaveSearchDialog() {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }
    /**
     * Save current search
     */
    async saveCurrentSearch() {
        const nameInput = document.getElementById('search-name');
        const name = nameInput?.value?.trim();
        if (!name) {
            alert('Bitte geben Sie einen Namen ein');
            return;
        }
        try {
            await api.search.save(name, this.currentFilters);
            this.closeSaveSearchDialog();
            await this.loadSavedSearches();
        }
        catch (error) {
            console.error('Error saving search:', error);
        }
    }
    /**
     * Render tag suggestions
     */
    renderTagSuggestions() {
        const container = document.getElementById('tag-filter-list');
        if (!container)
            return;
        container.innerHTML = this.allTags
            .map(tag => `
                <label>
                    <input type="checkbox" class="tag-filter" value="${tag.id}">
                    ${tag.name}
                </label>
            `)
            .join('');
    }
    /**
     * Render saved searches
     */
    renderSavedSearches() {
        const container = document.getElementById('saved-searches-list');
        if (!container)
            return;
        container.innerHTML = this.savedSearches
            .map(search => `
                <div class="saved-search">
                    <a href="#" onclick="advancedSearch.loadSavedSearch('${search.id}')">${search.name}</a>
                    <button onclick="advancedSearch.deleteSavedSearch('${search.id}')">×</button>
                </div>
            `)
            .join('');
    }
    /**
     * Load saved search
     */
    async loadSavedSearch(searchId) {
        const search = this.savedSearches.find(s => s.id === searchId);
        if (!search)
            return;
        this.currentFilters = search.filters;
        // Apply filters to UI
        await this.performAdvancedSearch();
    }
    /**
     * Delete saved search
     */
    async deleteSavedSearch(searchId) {
        try {
            await api.search.deleteSaved(searchId);
            await this.loadSavedSearches();
        }
        catch (error) {
            console.error('Error deleting search:', error);
        }
    }
}
// Global instance
export const advancedSearch = new AdvancedSearch();
window.advancedSearch = advancedSearch;
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AdvancedSearch, advancedSearch };
}
//# sourceMappingURL=advanced-search.js.map