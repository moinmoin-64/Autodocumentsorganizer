/**
 * Mobile Navigation Menu - TypeScript Version
 * Hamburger Menu for Touch Devices
 * Improves Mobile UX
 */
/**
 * Mobile Menu Manager
 */
export declare class MobileMenu {
    private isOpen;
    private menuButton;
    private menu;
    constructor();
    /**
     * Initialize mobile menu
     */
    private init;
    /**
     * Create menu button
     */
    private createMenuButton;
    /**
     * Setup event listeners
     */
    private setupEventListeners;
    /**
     * Make search box responsive
     */
    private makeSearchBoxResponsive;
    /**
     * Toggle menu
     */
    private toggleMenu;
    /**
     * Open menu
     */
    private openMenu;
    /**
     * Close menu
     */
    private closeMenu;
    /**
     * Reinitialize on window resize
     */
    reinitialize(): void;
    /**
     * Get menu open state
     */
    getIsOpen(): boolean;
}
export declare const mobileMenu: MobileMenu;
declare global {
    interface Window {
        mobileMenu: MobileMenu;
    }
}
//# sourceMappingURL=mobile-menu.d.ts.map