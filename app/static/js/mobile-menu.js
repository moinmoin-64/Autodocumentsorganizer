/**
 * Mobile Navigation Menu
 * Hamburger Menu for Touch Devices
 * Improves Mobile UX
 */

class MobileMenu {
    constructor() {
        this.isOpen = false;
        this.menuButton = null;
        this.menu = null;
        this.init();
    }

    init() {
        // Only initialize on mobile
        if (window.innerWidth > 768) return;

        this.createMenuButton();
        this.setupEventListeners();
        this.makeSearchBoxResponsive();
    }

    createMenuButton() {
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
    }

    setupEventListeners() {
        if (!this.menuButton) return;

        // Toggle menu on button click
        this.menuButton.addEventListener('click', () => this.toggleMenu());

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.menuButton?.contains(e.target) && !this.menu?.contains(e.target)) {
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
        const links = this.menu?.querySelectorAll('a');
        links?.forEach(link => {
            link.addEventListener('click', () => this.closeMenu());
        });
    }

    toggleMenu() {
        if (this.isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    openMenu() {
        this.isOpen = true;
        this.menuButton.setAttribute('aria-expanded', 'true');
        this.menuButton.classList.add('active');

        // Disable body scroll
        document.body.style.overflow = 'hidden';

        // Show menu with animation
        if (this.menu) {
            this.menu.classList.add('open');
        }
    }

    closeMenu() {
        this.isOpen = false;
        this.menuButton?.setAttribute('aria-expanded', 'false');
        this.menuButton?.classList.remove('active');

        // Re-enable body scroll
        document.body.style.overflow = '';

        // Hide menu with animation
        if (this.menu) {
            this.menu.classList.remove('open');
        }
    }

    makeSearchBoxResponsive() {
        const searchBox = document.querySelector('.search-box');
        if (!searchBox) return;

        // Add mobile search icon handler
        const input = searchBox.querySelector('input');
        if (input) {
            input.addEventListener('focus', () => {
                searchBox.style.width = '100%';
            });

            input.addEventListener('blur', () => {
                if (!input.value.trim()) {
                    searchBox.style.width = '';
                }
            });
        }
    }

    // Responsive refresh on window resize
    static initResponsive() {
        window.addEventListener('resize', () => {
            // Re-initialize menu on size change if needed
            if (window.innerWidth <= 768 && !document.getElementById('mobileMenuBtn')) {
                new MobileMenu();
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const mobileMenu = new MobileMenu();
    MobileMenu.initResponsive();
});

// Export for use in other modules
window.mobileMenu = MobileMenu;
