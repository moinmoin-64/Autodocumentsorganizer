/**
 * Mobile Navigation Menu - TypeScript Version
 * Hamburger Menu for Touch Devices
 * Improves Mobile UX
 */
/**
 * Mobile Menu Manager
 */
export class MobileMenu {
    constructor() {
        this.isOpen = false;
        this.menuButton = null;
        this.menu = null;
        this.init();
    }
    /**
     * Initialize mobile menu
     */
    init() {
        // Only initialize on mobile
        if (window.innerWidth > 768)
            return;
        this.createMenuButton();
        this.setupEventListeners();
        this.makeSearchBoxResponsive();
    }
    /**
     * Create menu button
     */
    createMenuButton() {
        const header = document.querySelector('.header');
        if (!header)
            return;
        // Check if button already exists
        if (document.getElementById('mobileMenuBtn')) {
            this.menuButton = document.getElementById('mobileMenuBtn');
            return;
        }
        // Create hamburger button
        this.menuButton = document.createElement('button');
        this.menuButton.id = 'mobileMenuBtn';
        this.menuButton.className = 'mobile-menu-btn';
        this.menuButton.innerHTML = '<i class="fas fa-bars"></i>';
        this.menuButton.setAttribute('aria-label', 'Toggle menu');
        this.menuButton.setAttribute('aria-expanded', 'false');
        // Insert before search box or at start of header-content
        const headerContent = document.querySelector('.header-content');
        if (headerContent) {
            headerContent.insertBefore(this.menuButton, headerContent.firstChild);
        }
        // Get menu reference
        this.menu = document.querySelector('.nav-menu');
    }
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        if (!this.menuButton)
            return;
        // Toggle menu on button click
        this.menuButton.addEventListener('click', () => this.toggleMenu());
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            const target = e.target;
            if (!this.menuButton?.contains(target) && !this.menu?.contains(target)) {
                if (this.isOpen)
                    this.closeMenu();
            }
        });
        // Close menu on window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && this.isOpen) {
                this.closeMenu();
            }
        });
        // Close menu on link click
        const links = this.menu?.querySelectorAll('a');
        links?.forEach(link => {
            link.addEventListener('click', () => this.closeMenu());
        });
    }
    /**
     * Make search box responsive
     */
    makeSearchBoxResponsive() {
        const searchBox = document.querySelector('.search-box');
        if (searchBox) {
            searchBox.classList.add('mobile-responsive');
        }
    }
    /**
     * Toggle menu
     */
    toggleMenu() {
        if (this.isOpen) {
            this.closeMenu();
        }
        else {
            this.openMenu();
        }
    }
    /**
     * Open menu
     */
    openMenu() {
        this.isOpen = true;
        this.menuButton?.setAttribute('aria-expanded', 'true');
        this.menuButton?.classList.add('active');
        // Disable body scroll
        document.body.style.overflow = 'hidden';
        // Show menu with animation
        if (this.menu) {
            this.menu.classList.add('open');
        }
    }
    /**
     * Close menu
     */
    closeMenu() {
        this.isOpen = false;
        this.menuButton?.setAttribute('aria-expanded', 'false');
        this.menuButton?.classList.remove('active');
        // Enable body scroll
        document.body.style.overflow = 'auto';
        // Hide menu with animation
        if (this.menu) {
            this.menu.classList.remove('open');
        }
    }
    /**
     * Reinitialize on window resize
     */
    reinitialize() {
        if (window.innerWidth > 768) {
            this.closeMenu();
        }
        else {
            this.init();
        }
    }
    /**
     * Get menu open state
     */
    getIsOpen() {
        return this.isOpen;
    }
}
// Global instance
export const mobileMenu = new MobileMenu();
window.mobileMenu = mobileMenu;
// Handle window resize
window.addEventListener('resize', () => {
    mobileMenu.reinitialize();
});
// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MobileMenu, mobileMenu };
}
//# sourceMappingURL=mobile-menu.js.map