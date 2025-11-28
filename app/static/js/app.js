/**
 * Main Application JavaScript
 * Handles dashboard functionality, charts, and API interactions
 */

const API_BASE = window.location.origin + '/api';
// === Overview Statistics ===
async function loadOverviewStats() {
    try {
        const response = await fetch(`${API_BASE}/stats/overview`);
        const data = await response.json();

        // Update stat cards
        document.getElementById('totalDocs').textContent = data.total_documents || 0;

        const categories = data.categories || {};
        document.getElementById('totalCategories').textContent = Object.keys(categories).length;

        // Insurance count
        const insuranceCount = categories['Versicherungen'] || 0;
        document.getElementById('totalInsurances').textContent = insuranceCount;

        // Load current year expenses
        const currentYear = new Date().getFullYear();
        loadYearExpenses(currentYear);

    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

async function loadYearExpenses(year) {
    try {
        const response = await fetch(`${API_BASE}/expenses/analysis?year=${year}`);
        const data = await response.json();

        const total = data.total || 0;
        document.getElementById('totalExpenses').textContent =
            total.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });

    } catch (error) {
        console.error('Error loading year expenses:', error);
    }
}

// === Charts ===
function populateYearSelectors() {
    const currentYear = new Date().getFullYear();
    const years = [];

    // 5 Jahre zurück
    for (let i = 0; i < 5; i++) {
        years.push(currentYear - i);
    }

    // Expenses Year
    const expensesYearSelect = document.getElementById('expensesYear');
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) option.selected = true;
        expensesYearSelect.appendChild(option);
    });

    // Compare Years
    const compareYear1 = document.getElementById('compareYear1');
    const compareYear2 = document.getElementById('compareYear2');

    years.forEach(year => {
        const option1 = document.createElement('option');
        option1.value = year;
        option1.textContent = year;
        if (year === currentYear - 1) option1.selected = true;
        compareYear1.appendChild(option1);

        const option2 = document.createElement('option');
        option2.value = year;
        option2.textContent = year;
        if (year === currentYear) option2.selected = true;
        compareYear2.appendChild(option2);
    });

    // Event listeners
    expensesYearSelect.addEventListener('change', (e) => {
        updateExpensesPieChart(e.target.value);
    });

    compareYear1.addEventListener('change', updateYearComparison);
    compareYear2.addEventListener('change', updateYearComparison);
}

async function initializeCharts() {
    const currentYear = new Date().getFullYear();

    // Expenses Pie Chart
    await updateExpensesPieChart(currentYear);

    // Year Comparison Chart
    await updateYearComparison();
}

async function updateExpensesPieChart(year) {
    try {
        const response = await fetch(`${API_BASE}/expenses/analysis?year=${year}`);
        const data = await response.json();

        const categories = data.categories || {};
        const labels = Object.keys(categories);
        const values = Object.values(categories);

        // Destroy old chart
        if (expensesPieChart) {
            expensesPieChart.destroy();
        }

        // Create new chart
        const ctx = document.getElementById('expensesPieChart').getContext('2d');
        expensesPieChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        '#4F46E5',
                        '#10B981',
                        '#F59E0B',
                        '#EF4444',
                        '#8B5CF6',
                        '#06B6D4',
                        '#EC4899',
                        '#F97316'
                    ],
                    borderWidth: 2,
                    borderColor: '#1E293B'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#F1F5F9',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${value.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}`;
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error updating expenses pie chart:', error);
    }
}

async function updateYearComparison() {
    const year1 = document.getElementById('compareYear1').value;
    const year2 = document.getElementById('compareYear2').value;

    try {
        const response = await fetch(`${API_BASE}/expenses/compare?year1=${year1}&year2=${year2}`);
        const data = await response.json();

        const comparison = data.comparison || {};
        const categories = Object.keys(comparison);
        const year1Data = categories.map(cat => comparison[cat].year1);
        const year2Data = categories.map(cat => comparison[cat].year2);

        // Destroy old chart
        if (yearComparisonChart) {
            yearComparisonChart.destroy();
        }

        // Create new chart
        const ctx = document.getElementById('yearComparisonChart').getContext('2d');
        yearComparisonChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: categories,
                datasets: [
                    {
                        label: year1,
                        data: year1Data,
                        backgroundColor: '#4F46E5',
                        borderWidth: 0
                    },
                    {
                        label: year2,
                        data: year2Data,
                        backgroundColor: '#10B981',
                        borderWidth: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#F1F5F9',
                            callback: function (value) {
                                return value.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
                            }
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#F1F5F9'
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#F1F5F9'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: ${value.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}`;
                            }
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error updating year comparison chart:', error);
    }
}

// === Insurance List ===
async function loadInsurances() {
    const tbody = document.getElementById('insurancesBody');
    tbody.innerHTML = getSkeletonRow(6) + getSkeletonRow(6) + getSkeletonRow(6);

    try {
        const response = await fetch(`${API_BASE}/insurance/list`);
        const data = await response.json();

        const insurances = data.insurances || [];

        if (insurances.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Keine Versicherungen gefunden</td></tr>';
            return;
        }

        tbody.innerHTML = '';

        insurances.forEach(insurance => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${insurance.versicherer || '-'}</td>
                <td>${insurance.typ || '-'}</td>
                <td>${insurance.police_nummer || '-'}</td>
                <td>${formatCurrency(insurance.beitrag)}</td>
                <td>${insurance.zahlungsintervall || '-'}</td>
                <td>${insurance.laufzeit_ende || '-'}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Error loading insurances:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Fehler beim Laden der Daten</td></tr>';
    }
}

// === Recent Documents (Lazy Loading) ===
let currentPage = 1;
let isLoadingDocuments = false;
let hasMoreDocuments = true;
const DOCUMENTS_PER_PAGE = 9;

async function loadRecentDocuments(reset = false) {
    const container = document.getElementById('recentDocuments');

    if (reset) {
        currentPage = 1;
        hasMoreDocuments = true;
        container.innerHTML = '';
    }

    if (isLoadingDocuments || !hasMoreDocuments) return;

    isLoadingDocuments = true;

    // Show skeleton only on first load
    if (currentPage === 1) {
        container.innerHTML = getSkeletonCards(3);
    } else {
        // Add loading indicator at bottom
        const loader = document.createElement('div');
        loader.id = 'scroll-loader';
        loader.className = 'loading';
        loader.textContent = 'Lade mehr...';
        container.appendChild(loader);
    }

    try {
        const response = await fetch(`${API_BASE}/documents?page=${currentPage}&limit=${DOCUMENTS_PER_PAGE}`);
        const data = await response.json();

        const documents = data.documents || [];
        hasMoreDocuments = data.has_more;

        // Remove skeletons/loader
        if (currentPage === 1) {
            container.innerHTML = '';
        } else {
            const loader = document.getElementById('scroll-loader');
            if (loader) loader.remove();
        }

        if (documents.length === 0 && currentPage === 1) {
            container.innerHTML = '<div class="loading">Keine Dokumente gefunden</div>';
            return;
        }

        documents.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'document-card';
            card.innerHTML = `
                <h4>${doc.filename}</h4>
                <p><strong>Kategorie:</strong> ${doc.category} / ${doc.subcategory || '-'}</p>
                <p><strong>Datum:</strong> ${formatDate(doc.date_document)}</p>
                <p class="summary">${doc.summary ? doc.summary.substring(0, 100) + '...' : ''}</p>
                <div class="tags">
                    ${(doc.tags || []).slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
            `;

            card.addEventListener('click', () => downloadDocument(doc.id));
            container.appendChild(card);
        });

        currentPage++;
        isLoadingDocuments = false;

        // Setup Intersection Observer for Infinite Scroll
        setupInfiniteScroll();

    } catch (error) {
        console.error('Error loading recent documents:', error);
        if (currentPage === 1) {
            container.innerHTML = '<div class="loading">Fehler beim Laden der Dokumente</div>';
        }
        isLoadingDocuments = false;
    }
}

function setupInfiniteScroll() {
    // Remove old observer trigger if exists
    const oldTrigger = document.getElementById('scroll-trigger');
    if (oldTrigger) oldTrigger.remove();

    if (!hasMoreDocuments) return;

    const container = document.getElementById('recentDocuments');
    const trigger = document.createElement('div');
    trigger.id = 'scroll-trigger';
    trigger.style.height = '20px';
    container.appendChild(trigger);

    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !isLoadingDocuments) {
            loadRecentDocuments();
        }
    }, { rootMargin: '100px' });

    observer.observe(trigger);
}

// === Search Function ===
let searchTimeout = null;

function setupSearchFunction() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Hide if empty
        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        // Debounce search
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });

    // Close results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });
}

async function performSearch(query) {
    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = '<div class="search-result-item">Suche...</div>';
    searchResults.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/documents/search?q=${encodeURIComponent(query)}&limit=10`);
        const data = await response.json();

        const results = data.results || [];

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">Keine Ergebnisse gefunden</div>';
            return;
        }

        searchResults.innerHTML = '';

        results.forEach(doc => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
                <strong>${doc.filename}</strong><br>
                <small>${doc.category} / ${doc.subcategory || '-'} - ${formatDate(doc.date_document)}</small>
            `;

            item.addEventListener('click', () => {
                downloadDocument(doc.id);
                searchResults.classList.add('hidden');
            });

            searchResults.appendChild(item);
        });

    } catch (error) {
        console.error('Error performing search:', error);
        searchResults.innerHTML = '<div class="search-result-item">Fehler bei der Suche</div>';
    }
}

// === Upload Functionality ===
function setupUploadFunctionality() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.getElementById('uploadProgress');

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // File selected
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

async function uploadFile(file) {
    const uploadProgress = document.getElementById('uploadProgress');
    const progressText = uploadProgress.querySelector('.progress-text');

    // Validate file type
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        showToast('Nur PDF, JPG und PNG Dateien erlaubt!', 'error');
        return;
    }

    // Show progress
    uploadProgress.classList.remove('hidden');
    progressText.textContent = 'Wird hochgeladen...';

    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            progressText.textContent = 'Wird verarbeitet...';

            // Trigger processing
            const processResponse = await fetch(`${API_BASE}/upload/process/${encodeURIComponent(data.temp_path)}`, {
                method: 'POST'
            });

            const processData = await processResponse.json();

            if (processData.success) {
                progressText.textContent = '✓ Erfolgreich verarbeitet!';

                // Reload data
                setTimeout(() => {
                    loadOverviewStats();
                    loadRecentDocuments();
                    uploadProgress.classList.add('hidden');

                    // Show success message
                    showToast(`Dokument erfolgreich hochgeladen!<br>Kategorie: ${processData.category}`, 'success');
                }, 1000);
            } else {
                throw new Error(processData.error || 'Processing failed');
            }
        } else {
            throw new Error(data.error || 'Upload failed');
        }

    } catch (error) {
        console.error('Upload error:', error);
        progressText.textContent = '✗ Fehler beim Upload';
        showToast('Fehler beim Upload: ' + error.message, 'error');

        setTimeout(() => {
            uploadProgress.classList.add('hidden');
        }, 3000);
    }
}

// === Toast Notifications ===
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';

    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('hiding');
        toast.addEventListener('transitionend', () => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        });
    }, 5000);

    // Click to remove
    toast.addEventListener('click', () => {
        toast.classList.add('hiding');
    });
}

// === Helper Functions ===
function downloadDocument(docId) {
    window.location.href = `${API_BASE}/documents/${docId}/download`;
}

function formatCurrency(value) {
    if (!value) return '-';
    return parseFloat(value).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE');
}

// === Skeleton Loading Helpers ===
function getSkeletonRow(cols = 6) {
    return `
        <tr>
            ${Array(cols).fill('<td><div class="skeleton skeleton-text"></div></td>').join('')}
        </tr>
    `;
}

function getSkeletonCards(count = 3) {
    return Array(count).fill(`
        <div class="document-card">
            <div class="skeleton skeleton-text" style="width: 60%; height: 1.2em;"></div>
            <div class="skeleton skeleton-text" style="width: 40%;"></div>
            <div class="skeleton skeleton-text" style="width: 30%;"></div>
            <div class="skeleton skeleton-text" style="width: 90%; height: 3em; margin-top: 1em;"></div>
        </div>
    `).join('');
}
