/**
 * Statistics Module - TypeScript Version
 * Handles advanced statistics, budget tracking, and predictions
 * Modernized with APIClient
 */

import { api } from './api-client';

/**
 * Chart instance
 */
interface ChartInstance {
    destroy(): void;
}

/**
 * Statistics Module Manager
 */
export class StatisticsModule {
    private charts: Record<string, ChartInstance> = {};
    private currentYear: number;

    constructor() {
        this.currentYear = new Date().getFullYear();
        this.init();
    }

    /**
     * Initialize statistics module
     */
    private init(): void {
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
    private setupEventListeners(): void {
        // Year selector change
        const yearSelect = document.getElementById('stats-year-select') as HTMLSelectElement;
        if (yearSelect) {
            yearSelect.addEventListener('change', (e: Event) => {
                const target = e.target as HTMLSelectElement;
                this.currentYear = parseInt(target.value, 10);
                this.loadAllStats().catch(console.error);
            });
        }

        // Budget form submission
        const budgetForm = document.getElementById('budget-form') as HTMLFormElement;
        if (budgetForm) {
            budgetForm.addEventListener('submit', (e) => this.handleBudgetSubmit(e));
        }
    }

    /**
     * Load all statistics
     */
    private async loadAllStats(): Promise<void> {
        await Promise.all([
            this.loadMonthlyTrends(),
            this.loadBudgets(),
            this.loadPredictions()
        ]);
    }

    /**
     * Load monthly trends
     */
    private async loadMonthlyTrends(): Promise<void> {
        try {
            const data = await api.stats.monthly(this.currentYear);
            this.renderTrendsChart(data);
        } catch (error) {
            console.error('Error loading trends:', error);
        }
    }

    /**
     * Render trends chart
     */
    private renderTrendsChart(data: any): void {
        const ctx = (document.getElementById('trends-chart') as HTMLCanvasElement)?.getContext('2d');
        if (!ctx) return;

        if (this.charts.trends) {
            this.charts.trends.destroy();
        }

        const labels = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
        const datasets = [];

        // Add total expenses line
        const totals = new Array(12).fill(0);
        if (data.total_by_month) {
            Object.entries(data.total_by_month).forEach(([month, amount]: [string, any]) => {
                totals[parseInt(month, 10) - 1] = amount as number;
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

        const Chart = (window as any).Chart;
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
    private async loadBudgets(): Promise<void> {
        try {
            const data = await api.budgets.create({});
            console.log('Budgets loaded:', data);
        } catch (error) {
            console.error('Error loading budgets:', error);
        }
    }

    /**
     * Load predictions
     */
    private async loadPredictions(): Promise<void> {
        try {
            const data = await api.stats.predictions('all', 3);
            console.log('Predictions loaded:', data);
        } catch (error) {
            console.error('Error loading predictions:', error);
        }
    }

    /**
     * Handle budget form submission
     */
    private handleBudgetSubmit(e: Event): void {
        e.preventDefault();
        console.log('Budget form submitted');
    }
}

// Global instance
export const statisticsModule = new StatisticsModule();

// Make global
declare global {
    interface Window {
        statisticsModule: StatisticsModule;
    }
}
window.statisticsModule = statisticsModule;

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StatisticsModule, statisticsModule };
}
