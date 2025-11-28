/**
 * Advanced Search Module
 * Handles advanced search UI with filters, tags, and saved searches
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
            const response = await fetch('/api/tags');
            const data = await response.json();
            this.allTags = data.tags || [];
            this.renderTagSuggestions();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    async loadSavedSearches() {
        try {
            const response = await fetch('/api/searches/saved');
            const data = await response.json();
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
            const response = await fetch('/api/search/advanced', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });

            if (!response.ok) {
                throw new Error('Search failed');
            }

            const data = await response.json();
            this.displayResults(data.documents);
        } catch (error) {
            console.error('Advanced search error:', error);
            alert('Fehler bei der erweiterten Suche: ' + error.message);
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
                    <span class="date">${doc.date_document || 'Kein Datum'}</span>
                    ${doc.subcategory ? `<span class="subcategory">${doc.subcategory}</span>` : ''}
                </div>
                <div class="document-tags">
                    ${(doc.tags || []).map(tag =>
            `<span class="tag" data-tag-id="${tag.id}">${tag.tag_name}
                            <button class="remove-tag" onclick="advancedSearch.removeTag(${tag.id}, ${doc.id})">×</button>
                        </span>`
        ).join('')}
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
            const response = await fetch(`/api/documents/${documentId}/tags`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tag: tagName })
            });

            if (!response.ok) {
                throw new Error('Failed to add tag');
            }

            // Reload tags and refresh search
            await this.loadTags();
            await this.performAdvancedSearch();
        } catch (error) {
            console.error('Error adding tag:', error);
            alert('Fehler beim Hinzufügen des Tags');
        }
    }

    async removeTag(tagId, documentId) {
        if (!confirm('Tag wirklich entfernen?')) return;

        try {
            const response = await fetch(`/api/tags/${tagId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to remove tag');
            }

            // Reload tags and refresh search
            await this.loadTags();
            await this.performAdvancedSearch();
        } catch (error) {
            console.error('Error removing tag:', error);
            alert('Fehler beim Entfernen des Tags');
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
            const response = await fetch('/api/searches/saved', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    filters: this.currentFilters
                })
            });

            if (!response.ok) {
                throw new Error('Failed to save search');
            }

            alert('Suche gespeichert!');
            await this.loadSavedSearches();
            this.closeSaveSearchDialog();
        } catch (error) {
            console.error('Error saving search:', error);
            alert('Fehler beim Speichern der Suche');
        }
    }

    async loadSavedSearch(searchId) {
        const search = this.savedSearches.find(s => s.id === searchId);
        if (!search) return;

        // Apply saved filters to UI
        if (search.filters.query) {
            document.getElementById('search-query').value = search.filters.query;
        }
        if (search.filters.category) {
            document.getElementById('filter-category').value = search.filters.category;
        }
        if (search.filters.start_date) {
            document.getElementById('filter-start-date').value = search.filters.start_date;
        }
        if (search.filters.end_date) {
            document.getElementById('filter-end-date').value = search.filters.end_date;
        }

        // Perform search with saved filters
        this.currentFilters = search.filters;
        await this.performAdvancedSearch();
    }

    async deleteSavedSearch(searchId) {
        if (!confirm('Gespeicherte Suche wirklich löschen?')) return;

        try {
            const response = await fetch(`/api/searches/saved/${searchId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete search');
            }

            await this.loadSavedSearches();
        } catch (error) {
            console.error('Error deleting search:', error);
            alert('Fehler beim Löschen der Suche');
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

        container.innerHTML = this.allTags.map(tag => `
            <label class="tag-checkbox-label">
                <input type="checkbox" class="tag-checkbox" value="${tag}">
                ${tag}
            </label>
        `).join('');
    }

    clearFilters() {
        document.getElementById('search-query').value = '';
        document.getElementById('filter-category').value = '';
        document.getElementById('filter-start-date').value = '';
        document.getElementById('filter-end-date').value = '';

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
        document.getElementById('search-name-input').value = '';
    }
}

// Initialize on page load
let advancedSearch;
document.addEventListener('DOMContentLoaded', () => {
    advancedSearch = new AdvancedSearch();
});
