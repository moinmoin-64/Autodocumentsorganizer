/**
 * Statistics Module - TypeScript Version
 * Handles advanced statistics, budget tracking, and predictions
 * Modernized with APIClient
 */
import { api } from './api-client';
/**
 * Statistics Module Manager
 */
export class StatisticsModule {
    constructor() {
        this.charts = {};
        this.currentYear = new Date().getFullYear();
        this.init();
    }
    /**
     * Initialize statistics module
     */
    init() {
        this.setupEventListeners();
        // Load initial data if on statistics tab
        const statsTab = document.getElementById('statistics-tab');
        if (statsTab?.classList.contains('active')) {
            this.loadAllStats().catch(console.error);
        }
    }
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Year selector change
        const yearSelect = document.getElementById('stats-year-select');
        if (yearSelect) {
            yearSelect.addEventListener('change', (e) => {
                const target = e.target;
                this.currentYear = parseInt(target.value, 10);
                this.loadAllStats().catch(console.error);
            });
        }
        // Budget form submission
        const budgetForm = document.getElementById('budget-form');
        if (budgetForm) {
            budgetForm.addEventListener('submit', (e) => this.handleBudgetSubmit(e));
        }
    }
    /**
     * Load all statistics
     */
    async loadAllStats() {
        await Promise.all([
            this.loadMonthlyTrends(),
            this.loadBudgets(),
            this.loadPredictions()
        ]);
    }
    /**
     * Load monthly trends
     */
    async loadMonthlyTrends() {
        try {
            const data = await api.stats.monthly(this.currentYear);
            this.renderTrendsChart(data);
        }
        catch (error) {
            console.error('Error loading trends:', error);
        }
    }
    /**
     * Render trends chart
     */
    renderTrendsChart(data) {
        const ctx = document.getElementById('trends-chart')?.getContext('2d');
        if (!ctx)
            return;
        if (this.charts.trends) {
            this.charts.trends.destroy();
        }
        const labels = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
        const datasets = [];
        // Add total expenses line
        const totals = new Array(12).fill(0);
        if (data.total_by_month) {
            Object.entries(data.total_by_month).forEach(([month, amount]) => {
                totals[parseInt(month, 10) - 1] = amount;
            });
        }
        datasets.push({
            label: 'Gesamtausgaben',
            data: totals,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            fill: true,
            tension: 0.4
        });
        const Chart = window.Chart;
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
    /**
     * Load budgets
     */
    async loadBudgets() {
        try {
            const data = await api.budgets.create({});
            console.log('Budgets loaded:', data);
        }
        catch (error) {
            console.error('Error loading budgets:', error);
        }
    }
    /**
     * Load predictions
     */
    async loadPredictions() {
        try {
            const data = await api.stats.predictions('all', 3);
            console.log('Predictions loaded:', data);
        }
        catch (error) {
            console.error('Error loading predictions:', error);
        }
    }
    /**
     * Handle budget form submission
     */
    handleBudgetSubmit(e) {
        e.preventDefault();
        console.log('Budget form submitted');
    }
}
// Global instance
export const statisticsModule = new StatisticsModule();
window.statisticsModule = statisticsModule;
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StatisticsModule, statisticsModule };
}
//# sourceMappingURL=statistics.js.map