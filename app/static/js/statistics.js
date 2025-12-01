/**
 * Statistics Module
 * Handles advanced statistics, budget tracking, and predictions
 * Modernized with APIClient
 */

class StatisticsModule {
    constructor() {
        this.charts = {};
        this.currentYear = new Date().getFullYear();
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Load initial data if on statistics tab
        if (document.getElementById('statistics-tab')?.classList.contains('active')) {
            this.loadAllStats();
        }
    }

    setupEventListeners() {
        // Year selector change
        const yearSelect = document.getElementById('stats-year-select');
        if (yearSelect) {
            yearSelect.addEventListener('change', (e) => {
                this.currentYear = parseInt(e.target.value);
                this.loadAllStats();
            });
        }

        // Budget form submission
        const budgetForm = document.getElementById('budget-form');
        if (budgetForm) {
            budgetForm.addEventListener('submit', (e) => this.handleBudgetSubmit(e));
        }
    }

    async loadAllStats() {
        await Promise.all([
            this.loadMonthlyTrends(),
            this.loadBudgets(),
            this.loadPredictions()
        ]);
    }

    async loadMonthlyTrends() {
        try {
            const data = await api.stats.monthly(this.currentYear);
            this.renderTrendsChart(data);
        } catch (error) {
            console.error('Error loading trends:', error);
        }
    }

    renderTrendsChart(data) {
        const ctx = document.getElementById('trends-chart')?.getContext('2d');
        if (!ctx) return;

        if (this.charts.trends) {
            this.charts.trends.destroy();
        }

        const labels = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
        const datasets = [];

        // Add total expenses line
        const totals = new Array(12).fill(0);
        if (data.total_by_month) {
            Object.entries(data.total_by_month).forEach(([month, amount]) => {
                totals[parseInt(month) - 1] = amount;
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

        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: `Monatliche Trends ${this.currentYear}`,
                        color: '#fff'
                    },
                    legend: {
                        labels: { color: '#a0aec0' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#a0aec0' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#a0aec0' }
                    }
                }
            }
        });
    }

    async loadBudgets() {
        // Implementation for budget visualization
        // This would typically load budget status for key categories
    }

    async handleBudgetSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        try {
            await api.budgets.create({
                category: data.category,
                month: `${this.currentYear}-${new Date().getMonth() + 1}`, // Current month
                amount: parseFloat(data.amount)
            });

            notifications.show('Erfolg', 'Budget gespeichert!', 'success');
            this.loadBudgets();
        } catch (error) {
            console.error('Error saving budget:', error);
            notifications.show('Fehler', 'Budget konnte nicht gespeichert werden', 'error');
        }
    }

    async loadPredictions() {
        // Load predictions for top categories
        const categories = ['Lebensmittel', 'Strom', 'Versicherungen'];

        for (const cat of categories) {
            try {
                const data = await api.stats.predictions(cat, 3);
                this.renderPrediction(cat, data);
            } catch (error) {
                console.error(`Error predicting for ${cat}:`, error);
            }
        }
    }

    renderPrediction(category, data) {
        // Render prediction widget
        const container = document.getElementById('predictions-container');
        if (!container) return;

        // Create or update prediction card
        let card = document.getElementById(`prediction-${category}`);
        if (!card) {
            card = document.createElement('div');
            card.id = `prediction-${category}`;
            card.className = 'prediction-card';
            container.appendChild(card);
        }

        if (data.error || !data.predictions || data.predictions.length === 0) return;

        const nextMonth = data.predictions[0];
        card.innerHTML = `
            <h4>${category} Prognose</h4>
            <div class="prediction-value">
                €${nextMonth.predicted_amount.toFixed(2)}
                <small>±€${(nextMonth.confidence_upper - nextMonth.predicted_amount).toFixed(2)}</small>
            </div>
            <div class="prediction-trend">
                Nächster Monat
            </div>
        `;
    }
}

// Initialize
let statisticsModule;
document.addEventListener('DOMContentLoaded', () => {
    statisticsModule = new StatisticsModule();
});
