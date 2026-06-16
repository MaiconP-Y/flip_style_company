// static/js/global.js
document.addEventListener('DOMContentLoaded', () => {
    initGlobalSearch();
    initResponsiveMenu();
    initSmartHeader();
});
function initSmartHeader() {
    let lastScroll = 0;
    const header = document.querySelector('header');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        // Se o scroll atual for maior que o anterior (descendo), esconde
        if (currentScroll > lastScroll && currentScroll > 100) {
            header.classList.add('header-hidden');
        } 
        // Se o scroll for menor (subindo), mostra
        else {
            header.classList.remove('header-hidden');
        }

        lastScroll = currentScroll;
    }, { passive: true });
}

// Chame a função quando o DOM carregar
document.addEventListener('DOMContentLoaded', initSmartHeader);
/**
 * Gerencia o comportamento do formulário de busca
 */
function initGlobalSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-form input');

    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', (e) => {
            if (searchInput.value.trim() === "") {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
}

/**
 * Gerencia o Menu de forma unificada e segura.
 * As manipulações de estilo (como o travamento de scroll) agora são feitas 
 * via classe .scroll-lock no CSS para garantir a separação de responsabilidades.
 */
function initResponsiveMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const toggleSubmenuBtns = document.querySelectorAll('.toggle-submenu');
    const overlay = document.getElementById('js-menu-overlay');

    // Checagem centralizada de responsividade
    const isMobile = () => window.matchMedia("(max-width: 905px)").matches;

    // Função de bloqueio de scroll via classe CSS
    function toggleScrollLock(active) {
        document.documentElement.classList.toggle('scroll-lock', active);
        document.body.classList.toggle('scroll-lock', active);
    }

    // Função central para fechar o menu
    function fecharMenuMobile() {
        if (!navLinks) return;
        
        navLinks.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        toggleScrollLock(false);
        
        // Reset dos estados dos submenus
        document.querySelectorAll('.submenu').forEach(sub => sub.classList.remove('active'));
        toggleSubmenuBtns.forEach(btn => {
            btn.classList.remove('active');
            btn.textContent = '+';
            btn.setAttribute('aria-expanded', 'false');
        });
    }

    // 1. Abertura pelo Hambúrguer
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            const isMenuAberto = navLinks.classList.toggle('active');
            
            toggleScrollLock(isMenuAberto);
            if (overlay) overlay.classList.toggle('active', isMenuAberto);
            menuToggle.setAttribute('aria-expanded', isMenuAberto);
        });
    }

    // 2. Clique no Overlay fecha tudo
    if (overlay) {
        overlay.addEventListener('click', fecharMenuMobile);
    }

    // 3. Acordeões do Submenu (Acessível)
    toggleSubmenuBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!isMobile()) return;

            e.preventDefault();
            e.stopPropagation(); 

            const parentLi = btn.closest('li');
            const submenu = parentLi?.querySelector('.submenu');

            if (submenu) {
                const isSubmenuAtivo = submenu.classList.toggle('active');
                btn.classList.toggle('active', isSubmenuAtivo);
                btn.setAttribute('aria-expanded', isSubmenuAtivo);
                btn.textContent = isSubmenuAtivo ? '-' : '+';
            }
        });
    });

    // 4. Reset automático ao redimensionar para Desktop
    window.addEventListener('resize', () => {
        if (!isMobile() && navLinks.classList.contains('active')) {
            fecharMenuMobile();
        }
    }, { passive: true });

}