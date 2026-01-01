/**
 * Advanced Search Module - TypeScript Version
 * Handles advanced search UI with filters, tags, and saved searches
 * Modernized with APIClient
 */

import { api } from './api-client';

/**
 * Search filters
 */
export interface SearchFilters {
    query?: string | null;
    category?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    tags?: string[];
    limit?: number;
}

/**
 * Saved search
 */
export interface SavedSearch {
    id: string;
    name: string;
    filters: SearchFilters;
    created_at: string;
}

/**
 * Advanced Search Manager
 */
export class AdvancedSearch {
    private currentFilters: SearchFilters = {};
    private savedSearches: SavedSearch[] = [];
    private allTags: any[] = [];

    constructor() {
        this.init();
    }

    /**
     * Initialize advanced search
     */
    private async init(): Promise<void> {
        await this.loadTags();
        await this.loadSavedSearches();
        this.setupEventListeners();
    }

    /**
     * Load all tags
     */
    private async loadTags(): Promise<void> {
        try {
            const data = await api.tags.list();
            this.allTags = (data as any).tags || [];
            this.renderTagSuggestions();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    /**
     * Load saved searches
     */
    private async loadSavedSearches(): Promise<void> {
        try {
            const data = await api.search.saved();
            this.savedSearches = ((data as any).searches || []) as SavedSearch[];
            this.renderSavedSearches();
        } catch (error) {
            console.error('Error loading saved searches:', error);
        }
    }

    /**
     * Setup event listeners
     */
    private setupEventListeners(): void {
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
    private toggleAdvancedSearch(): void {
        const panel = document.getElementById('advanced-search-panel');
        if (panel) {
            panel.classList.toggle('hidden');
        }
    }

    /**
     * Perform advanced search
     */
    private async performAdvancedSearch(): Promise<void> {
        // Collect filter values
        const filters: SearchFilters = {
            query: (document.getElementById('search-query') as HTMLInputElement)?.value?.trim() || null,
            category: (document.getElementById('filter-category') as HTMLSelectElement)?.value || null,
            start_date: (document.getElementById('filter-start-date') as HTMLInputElement)?.value || null,
            end_date: (document.getElementById('filter-end-date') as HTMLInputElement)?.value || null,
            tags: this.getSelectedTags(),
            limit: 100
        };

        // Remove null values
        Object.keys(filters).forEach(key => {
            if ((filters as any)[key] === null || (filters as any)[key] === '') {
                delete (filters as any)[key];
            }
        });

        this.currentFilters = filters;

        try {
            const results = await api.search.advanced(filters);
            this.displayResults(results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    /**
     * Get selected tags
     */
    private getSelectedTags(): string[] {
        const checkboxes = document.querySelectorAll<HTMLInputElement>('.tag-filter:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    /**
     * Display search results
     */
    private displayResults(results: any[]): void {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

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
    private clearFilters(): void {
        (document.getElementById('search-query') as HTMLInputElement).value = '';
        (document.getElementById('filter-category') as HTMLSelectElement).value = '';
        (document.getElementById('filter-start-date') as HTMLInputElement).value = '';
        (document.getElementById('filter-end-date') as HTMLInputElement).value = '';

        document.querySelectorAll<HTMLInputElement>('.tag-filter').forEach(cb => {
            cb.checked = false;
        });

        this.currentFilters = {};
    }

    /**
     * Show save search dialog
     */
    private showSaveSearchDialog(): void {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.remove('hidden');
        }
    }

    /**
     * Close save search dialog
     */
    private closeSaveSearchDialog(): void {
        const dialog = document.getElementById('save-search-dialog');
        if (dialog) {
            dialog.classList.add('hidden');
        }
    }

    /**
     * Save current search
     */
    private async saveCurrentSearch(): Promise<void> {
        const nameInput = document.getElementById('search-name') as HTMLInputElement;
        const name = nameInput?.value?.trim();

        if (!name) {
            alert('Bitte geben Sie einen Namen ein');
            return;
        }

        try {
            await api.search.save(name, this.currentFilters);
            this.closeSaveSearchDialog();
            await this.loadSavedSearches();
        } catch (error) {
            console.error('Error saving search:', error);
        }
    }

    /**
     * Render tag suggestions
     */
    private renderTagSuggestions(): void {
        const container = document.getElementById('tag-filter-list');
        if (!container) return;

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
    private renderSavedSearches(): void {
        const container = document.getElementById('saved-searches-list');
        if (!container) return;

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
    public async loadSavedSearch(searchId: string): Promise<void> {
        const search = this.savedSearches.find(s => s.id === searchId);
        if (!search) return;

        this.currentFilters = search.filters;
        // Apply filters to UI
        await this.performAdvancedSearch();
    }

    /**
     * Delete saved search
     */
    public async deleteSavedSearch(searchId: string): Promise<void> {
        try {
            await api.search.deleteSaved(searchId);
            await this.loadSavedSearches();
        } catch (error) {
            console.error('Error deleting search:', error);
        }
    }
}

// Global instance
export const advancedSearch = new AdvancedSearch();

// Make global
declare global {
    interface Window {
        advancedSearch: AdvancedSearch;
    }
}
window.advancedSearch = advancedSearch;

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AdvancedSearch, advancedSearch };
}
