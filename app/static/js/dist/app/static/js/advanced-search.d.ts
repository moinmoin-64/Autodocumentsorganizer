/**
 * Advanced Search Module - TypeScript Version
 * Handles advanced search UI with filters, tags, and saved searches
 * Modernized with APIClient
 */
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
export declare class AdvancedSearch {
    private currentFilters;
    private savedSearches;
    private allTags;
    constructor();
    /**
     * Initialize advanced search
     */
    private init;
    /**
     * Load all tags
     */
    private loadTags;
    /**
     * Load saved searches
     */
    private loadSavedSearches;
    /**
     * Setup event listeners
     */
    private setupEventListeners;
    /**
     * Toggle advanced search panel
     */
    private toggleAdvancedSearch;
    /**
     * Perform advanced search
     */
    private performAdvancedSearch;
    /**
     * Get selected tags
     */
    private getSelectedTags;
    /**
     * Display search results
     */
    private displayResults;
    /**
     * Clear all filters
     */
    private clearFilters;
    /**
     * Show save search dialog
     */
    private showSaveSearchDialog;
    /**
     * Close save search dialog
     */
    private closeSaveSearchDialog;
    /**
     * Save current search
     */
    private saveCurrentSearch;
    /**
     * Render tag suggestions
     */
    private renderTagSuggestions;
    /**
     * Render saved searches
     */
    private renderSavedSearches;
    /**
     * Load saved search
     */
    loadSavedSearch(searchId: string): Promise<void>;
    /**
     * Delete saved search
     */
    deleteSavedSearch(searchId: string): Promise<void>;
}
export declare const advancedSearch: AdvancedSearch;
declare global {
    interface Window {
        advancedSearch: AdvancedSearch;
    }
}
//# sourceMappingURL=advanced-search.d.ts.map