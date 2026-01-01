/**
 * Statistics Module - TypeScript Version
 * Handles advanced statistics, budget tracking, and predictions
 * Modernized with APIClient
 */
/**
 * Statistics Module Manager
 */
export declare class StatisticsModule {
    private charts;
    private currentYear;
    constructor();
    /**
     * Initialize statistics module
     */
    private init;
    /**
     * Setup event listeners
     */
    private setupEventListeners;
    /**
     * Load all statistics
     */
    private loadAllStats;
    /**
     * Load monthly trends
     */
    private loadMonthlyTrends;
    /**
     * Render trends chart
     */
    private renderTrendsChart;
    /**
     * Load budgets
     */
    private loadBudgets;
    /**
     * Load predictions
     */
    private loadPredictions;
    /**
     * Handle budget form submission
     */
    private handleBudgetSubmit;
}
export declare const statisticsModule: StatisticsModule;
declare global {
    interface Window {
        statisticsModule: StatisticsModule;
    }
}
//# sourceMappingURL=statistics.d.ts.map