/**
 * Main Application Dashboard - TypeScript Version
 * Handles dashboard functionality, charts, and API interactions
 * Modernized with APIClient and async/await
 */
import { api } from './api-client';
import { errorHandler } from './error-handler';
import { notifications } from './notifications';
/**
 * Dashboard initialization
 */
export async function initializeDashboard() {
    try {
        await loadOverviewStats();
        populateYearSelectors();
        await initializeCharts();
        await loadInsurances();
        setupEventListeners();
    }
    catch (error) {
        console.error('Error initializing dashboard:', error);
        errorHandler.showError('Dashboard konnte nicht geladen werden');
    }
}
/**
 * Load overview statistics
 */
async function loadOverviewStats() {
    try {
        const data = await api.stats.overview();
        // Update stat cards
        const totalDocsElem = document.getElementById('totalDocs');
        if (totalDocsElem) {
            totalDocsElem.textContent = String(data.overview?.total_documents || 0);
        }
        const categories = data.overview?.categories || {};
        const totalCategoriesElem = document.getElementById('totalCategories');
        if (totalCategoriesElem) {
            totalCategoriesElem.textContent = String(Object.keys(categories).length);
        }
        // Insurance count
        const insuranceCount = categories['Versicherung'] ||
            categories['Versicherungen'] || 0;
        const totalInsurancesElem = document.getElementById('totalInsurances');
        if (totalInsurancesElem) {
            totalInsurancesElem.textContent = String(insuranceCount);
        }
        // Load current year expenses
        const currentYear = new Date().getFullYear();
        await loadYearExpenses(currentYear);
    }
    catch (error) {
        console.error('Error loading overview stats:', error);
        notifications.error('Fehler', 'Statistiken konnten nicht geladen werden');
    }
}
/**
 * Load year expenses
 */
async function loadYearExpenses(year) {
    try {
        const data = await api.stats.monthly(year);
        let total = 0;
        const monthlyData = data.total_by_month || {};
        if (Object.keys(monthlyData).length > 0) {
            total = Object.values(monthlyData).reduce((a, b) => a + b, 0);
        }
        const totalExpensesElem = document.getElementById('totalExpenses');
        if (totalExpensesElem) {
            totalExpensesElem.textContent = total.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR'
            });
        }
    }
    catch (error) {
        console.error('Error loading year expenses:', error);
    }
}
/**
 * Populate year selectors
 */
function populateYearSelectors() {
    const currentYear = new Date().getFullYear();
    const years = [];
    // 5 Jahre zurück
    for (let i = 0; i < 5; i++) {
        years.push(currentYear - i);
    }
    // Expenses Year Selector
    const expensesYearSelect = document.getElementById('expensesYear');
    if (expensesYearSelect) {
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = String(year);
            option.textContent = String(year);
            if (year === currentYear)
                option.selected = true;
            expensesYearSelect.appendChild(option);
        });
        expensesYearSelect.addEventListener('change', (e) => {
            const target = e.target;
            updateExpensesPieChart(parseInt(target.value, 10)).catch(console.error);
        });
    }
    // Compare Years Selectors
    const compareYear1 = document.getElementById('compareYear1');
    const compareYear2 = document.getElementById('compareYear2');
    if (compareYear1 && compareYear2) {
        years.forEach(year => {
            const option1 = document.createElement('option');
            option1.value = String(year);
            option1.textContent = String(year);
            if (year === currentYear - 1)
                option1.selected = true;
            compareYear1.appendChild(option1);
            const option2 = document.createElement('option');
            option2.value = String(year);
            option2.textContent = String(year);
            if (year === currentYear)
                option2.selected = true;
            compareYear2.appendChild(option2);
        });
        compareYear1.addEventListener('change', updateYearComparison);
        compareYear2.addEventListener('change', updateYearComparison);
    }
}
/**
 * Initialize charts
 */
async function initializeCharts() {
    const currentYear = new Date().getFullYear();
    // Expenses Pie Chart
    await updateExpensesPieChart(currentYear);
    // Year Comparison Chart
    await updateYearComparison();
}
/**
 * Update expenses pie chart
 */
async function updateExpensesPieChart(year) {
    try {
        const data = await api.stats.monthly(year);
        const categoryTotals = {};
        const categoriesByMonth = data.categories_by_month || {};
        Object.values(categoriesByMonth).forEach((monthCats) => {
            Object.entries(monthCats).forEach(([cat, amount]) => {
                categoryTotals[cat] = (categoryTotals[cat] || 0) + amount;
            });
        });
        const labels = Object.keys(categoryTotals);
        const values = Object.values(categoryTotals);
        // Destroy old chart
        const windowWithChart = window;
        if (windowWithChart.expensesPieChart) {
            windowWithChart.expensesPieChart.destroy();
        }
        // Colors
        const colors = [
            '#5B4BF2', '#10B981', '#F59E0B', '#EF4444',
            '#3B82F6', '#8B5CF6', '#06B6D4', '#EC4899'
        ];
        // Create new chart
        const ctx = document.getElementById('expensesPieChart');
        if (!ctx)
            return;
        const Chart = window.Chart;
        windowWithChart.expensesPieChart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                        data: values,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 2,
                        borderColor: '#FFFFFF',
                        hoverOffset: 8
                    }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    }
    catch (error) {
        console.error('Error updating expenses pie chart:', error);
    }
}
/**
 * Update year comparison chart
 */
async function updateYearComparison() {
    const year1Select = document.getElementById('compareYear1');
    const year2Select = document.getElementById('compareYear2');
    if (!year1Select || !year2Select)
        return;
    const year1 = parseInt(year1Select.value, 10);
    const year2 = parseInt(year2Select.value, 10);
    try {
        const data = await api.stats.compareExpenses(year1, year2);
        const comparison = data.comparison || {};
        const categories = Object.keys(comparison);
        const year1Data = categories.map((cat) => comparison[cat]?.year1 || 0);
        const year2Data = categories.map((cat) => comparison[cat]?.year2 || 0);
        // Destroy old chart
        const windowWithChart = window;
        if (windowWithChart.yearComparisonChart) {
            windowWithChart.yearComparisonChart.destroy();
        }
        // Create new chart
        const ctx = document.getElementById('yearComparisonChart');
        if (!ctx)
            return;
        const Chart = window.Chart;
        windowWithChart.yearComparisonChart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: categories,
                datasets: [
                    {
                        label: String(year1),
                        data: year1Data,
                        backgroundColor: '#5B4BF2',
                        borderRadius: 4
                    },
                    {
                        label: String(year2),
                        data: year2Data,
                        backgroundColor: '#10B981',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
    catch (error) {
        console.error('Error updating year comparison chart:', error);
    }
}
/**
 * Load insurances
 */
async function loadInsurances() {
    const tbody = document.getElementById('insurancesBody');
    if (!tbody)
        return;
    try {
        const data = await api.stats.getInsurances();
        const insurances = data.insurances || [];
        if (insurances.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Keine Versicherungen gefunden</td></tr>';
            return;
        }
        tbody.innerHTML = '';
        insurances.forEach((insurance) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${insurance.versicherer || '-'}</td>
                <td>${insurance.typ || '-'}</td>
                <td>${insurance.betrag || '-'}</td>
                <td>${insurance.startdatum || '-'}</td>
                <td>${insurance.enddatum || '-'}</td>
                <td>
                    <button class="btn-small" onclick="editInsurance('${insurance.id}')">Bearbeiten</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    catch (error) {
        console.error('Error loading insurances:', error);
    }
}
/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add custom event listeners here
    document.addEventListener('DOMContentLoaded', () => {
        console.log('Dashboard event listeners ready');
    });
}
/**
 * Edit insurance
 */
export function editInsurance(insuranceId) {
    console.log('Editing insurance:', insuranceId);
    // TODO: Implement insurance editing
}
// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDashboard);
}
else {
    initializeDashboard().catch(console.error);
}
// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeDashboard,
        editInsurance,
        loadOverviewStats,
        loadYearExpenses,
        populateYearSelectors,
        initializeCharts,
        updateExpensesPieChart,
        updateYearComparison,
        loadInsurances,
        setupEventListeners
    };
}
//# sourceMappingURL=app.js.map