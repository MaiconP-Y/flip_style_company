// ==========================================================================
// FLIP STYLE COMPANY - MOBILE ONLY JAVASCRIPT
// ==========================================================================

(function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const toggleSubmenuBtns = document.querySelectorAll('.toggle-submenu');
    const overlay = document.getElementById('js-menu-overlay'); // Captura a cortina

    // Função centralizada para fechar todo o menu e resetar os estados
    function fecharMenuMobile() {
        navLinks.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.classList.remove('scroll-lock');
        
        // Reseta os acordeões internos para o padrão fechado (+)
        const submenus = document.querySelectorAll('.submenu');
        submenus.forEach(sub => sub.classList.remove('active'));
        toggleSubmenuBtns.forEach(btn => btn.textContent = '+');
    }

    // 1. Abrir/Fechar pelo botão Hambúrguer
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            const isMenuAberto = navLinks.classList.toggle('active');
            document.body.classList.toggle('scroll-lock');
            
            // Liga/Desliga a cortina de fundo
            if (overlay) {
                overlay.classList.toggle('active', isMenuAberto);
            }
        });
    }

    // 2. EFICIÊNCIA: Clicou na cortina (fora do menu), fecha tudo na hora!
    if (overlay) {
        overlay.addEventListener('click', fecharMenuMobile);
    }

    // 3. Controlar os Acordeões do Submenu (+ / -)
    toggleSubmenuBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); 

            const parentLi = btn.closest('li');
            const submenu = parentLi.querySelector('.submenu');

            if (submenu) {
                submenu.classList.toggle('active');
                btn.textContent = submenu.classList.contains('active') ? '-' : '+';
            }
        });
    });
})();