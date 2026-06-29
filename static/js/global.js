// static/js/global.js
document.addEventListener('DOMContentLoaded', () => {
    initGlobalSearch();
    initResponsiveMenu();
    initSmartHeader();
});

function initSmartHeader() {
    let lastScroll = 0;
    const header = document.querySelector('header');
    const navLinks = document.querySelector('.nav-links');
    if (!header) return;

    let ticking = false;

    window.addEventListener('scroll', () => {
        if (navLinks && navLinks.classList.contains('active')) return;

        if (!ticking) {
            window.requestAnimationFrame(() => {
                const currentScroll = window.pageYOffset || window.scrollY;

                if (currentScroll > lastScroll && currentScroll > 100) {
                    header.classList.add('header-hidden');
                } else {
                    header.classList.remove('header-hidden');
                }

                lastScroll = currentScroll;
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
}

function initGlobalSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-form input');

    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', (e) => {
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
}

function toggleScrollLock(active) {
    document.documentElement.classList.toggle('scroll-lock', active);
    document.body.classList.toggle('scroll-lock', active);
}

function initResponsiveMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const header = document.querySelector('header');
    const toggleSubmenuBtns = document.querySelectorAll('.toggle-submenu');
    const overlay = document.getElementById('js-menu-overlay');

    const isMobile = () => window.matchMedia("(max-width: 905px)").matches;

    function fecharMenuMobile() {
        if (!navLinks) return;
        
        navLinks.classList.remove('active');
        overlay?.classList.remove('active');
        toggleScrollLock(false);
        
        document.querySelectorAll('.submenu').forEach(sub => sub.classList.remove('active'));
        toggleSubmenuBtns.forEach(btn => {
            btn.classList.remove('active');
            btn.textContent = '+';
            btn.setAttribute('aria-expanded', 'false');
        });
    }

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            if (header?.classList.contains('header-hidden')) {
                header.classList.remove('header-hidden');
            }

            const isMenuAberto = navLinks.classList.toggle('active');
            toggleScrollLock(isMenuAberto);
            overlay?.classList.toggle('active', isMenuAberto);
            menuToggle.setAttribute('aria-expanded', isMenuAberto);
        });
    }

    overlay?.addEventListener('click', fecharMenuMobile);

    toggleSubmenuBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!isMobile()) return;

            e.preventDefault();
            e.stopPropagation(); 

            const submenu = btn.closest('li')?.querySelector('.submenu');
            if (submenu) {
                const isSubmenuAtivo = submenu.classList.toggle('active');
                btn.classList.toggle('active', isSubmenuAtivo);
                btn.setAttribute('aria-expanded', isSubmenuAtivo);
                btn.textContent = isSubmenuAtivo ? '-' : '+';
            }
        });
    });

    window.addEventListener('resize', () => {
        if (!isMobile() && navLinks?.classList.contains('active')) {
            fecharMenuMobile();
        }
    }, { passive: true });
}