/**
 * Mobile Navigation Menu - TypeScript Version
 * Hamburger Menu for Touch Devices
 * Improves Mobile UX
 */

/**
 * Mobile Menu Manager
 */
export class MobileMenu {
    private isOpen: boolean = false;
    private menuButton: HTMLElement | null = null;
    private menu: HTMLElement | null = null;

    constructor() {
        this.init();
    }

    /**
     * Initialize mobile menu
     */
    private init(): void {
        // Only initialize on mobile
        if (window.innerWidth > 768) return;

        this.createMenuButton();
        this.setupEventListeners();
        this.makeSearchBoxResponsive();
    }

    /**
     * Create menu button
     */
    private createMenuButton(): void {
        const header = document.querySelector('.header');
        if (!header) return;

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
    private setupEventListeners(): void {
        if (!this.menuButton) return;

        // Toggle menu on button click
        this.menuButton.addEventListener('click', () => this.toggleMenu());

        // Close menu when clicking outside
        document.addEventListener('click', (e: MouseEvent) => {
            const target = e.target as HTMLElement;
            if (!this.menuButton?.contains(target) && !this.menu?.contains(target)) {
                if (this.isOpen) this.closeMenu();
            }
        });

        // Close menu on window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && this.isOpen) {
                this.closeMenu();
            }
        });

        // Close menu on link click
        const links = this.menu?.querySelectorAll<HTMLAnchorElement>('a');
        links?.forEach(link => {
            link.addEventListener('click', () => this.closeMenu());
        });
    }

    /**
     * Make search box responsive
     */
    private makeSearchBoxResponsive(): void {
        const searchBox = document.querySelector('.search-box');
        if (searchBox) {
            searchBox.classList.add('mobile-responsive');
        }
    }

    /**
     * Toggle menu
     */
    private toggleMenu(): void {
        if (this.isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    /**
     * Open menu
     */
    private openMenu(): void {
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
    private closeMenu(): void {
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
    public reinitialize(): void {
        if (window.innerWidth > 768) {
            this.closeMenu();
        } else {
            this.init();
        }
    }

    /**
     * Get menu open state
     */
    public getIsOpen(): boolean {
        return this.isOpen;
    }
}

// Global instance
export const mobileMenu = new MobileMenu();

// Make global
declare global {
    interface Window {
        mobileMenu: MobileMenu;
    }
}
window.mobileMenu = mobileMenu;

// Handle window resize
window.addEventListener('resize', () => {
    mobileMenu.reinitialize();
});

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MobileMenu, mobileMenu };
}
